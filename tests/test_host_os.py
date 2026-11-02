"""Native behavior tests plus checks of both host macro sequences."""
import ctypes as C
import ctypes.util
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class HostOsTests(unittest.TestCase):
    def test_os_shortcuts_and_browser_encoder(self):
        source = (ROOT/'config/roBa.keymap').read_text()
        pairs = {
            'mc_redo': ('LC(LS(Z))', 'LC(Y)'),
            'mc_task_manager': ('LG(ESC)', 'LC(LS(ESC))'),
            **{f'mc_task_{i}': (f'LG(NUMBER_{i})', f'LS(LG(NUMBER_{i}))')
               for i in range(1, 7)},
        }
        for name, keys in pairs.items():
            for host, key in zip(('linux', 'windows'), keys):
                with self.subTest(name=name, host=host):
                    body = re.search(rf'{name}_{host}: {name}_{host} \{{(.*?)\n        \}};', source, re.S)[1]
                    self.assertEqual(re.findall(r'<&kp ([^>]+)>', body), [key])
            self.assertRegex(source, rf'{name}: {name} \{{\s+compatible = "roba,behavior-os-select";\s+#binding-cells = <0>;\s+bindings = <&{name}_linux>, <&{name}_windows>;')
        service = source.split('        SERVICE {')[1].split('>;')[0]
        bindings = re.findall(r'&\w+(?: [^&\n]+)?', service)
        self.assertEqual(len(bindings), 43)
        self.assertEqual(bindings[0].strip(), '&mc_task_manager')
        self.assertEqual([b.strip() for b in bindings[22:28]],
                         [f'&mc_task_{i}' for i in range(1, 7)])
        arrow = source.split('        ARROW {')[1].split('        MOUSE {')[0]
        self.assertIn('&mc_redo', arrow)
        self.assertIn('sensor-bindings = <&inc_dec_kp LC(PAGE_DOWN) LC(PAGE_UP)>;', arrow)

    def test_runtime_dispatch(self):
        compiler = shutil.which('cc')
        if not compiler:
            self.skipTest('C compiler unavailable')
        stub = r'''
#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <errno.h>
#define IS_ENABLED(x) x
#define CONFIG_ZMK_BEHAVIOR_METADATA TEST_METADATA
#define ARRAY_SIZE(a) (sizeof(a)/sizeof((a)[0]))
#define BUILD_ASSERT(c, msg) _Static_assert(c, msg)
#define DT_HAS_COMPAT_STATUS_OKAY(c) 1
#define CAT_(a,b) a##b
#define CAT(a,b) CAT_(a,b)
#define INSTANCES_roba_behavior_os_select(f) f(0) f(1)
#define INSTANCES_roba_behavior_host_os(f) f(0)
#define DT_INST_FOREACH_STATUS_OKAY(f) CAT(INSTANCES_,DT_DRV_COMPAT)(f)
#define DT_INST_PROP_LEN(n,p) 2
#define DT_INST_PHANDLE_BY_IDX(n,p,i) ((i) == 0 ? "linux" : "windows")
#define DEVICE_DT_NAME(node) (node)
#define BEHAVIOR_DT_INST_DEFINE(n,init,pm,d,c,level,prio,a) \
 static const struct device CAT(DT_DRV_COMPAT,n) = {.data=d,.config=c,.api=a}
#define BEHAVIOR_LOCALITY_CENTRAL 0
#define ZMK_BEHAVIOR_OPAQUE 0
#define BEHAVIOR_PARAMETER_VALUE_TYPE_VALUE 1
struct device { void *data; const void *config; const void *api; };
struct zmk_behavior_binding { const char *behavior_dev; uint32_t param1, param2; };
struct zmk_behavior_binding_event { int layer; uint32_t position; int64_t timestamp; uint8_t source; };
struct behavior_parameter_value_metadata { char *display_name; int type; uint32_t value; };
struct behavior_parameter_metadata_set {
 const struct behavior_parameter_value_metadata *param1_values; size_t param1_values_len;
};
struct behavior_parameter_metadata { const struct behavior_parameter_metadata_set *sets; size_t sets_len; };
struct behavior_driver_api {
 int locality;
 int (*binding_pressed)(struct zmk_behavior_binding *, struct zmk_behavior_binding_event);
 int (*binding_released)(struct zmk_behavior_binding *, struct zmk_behavior_binding_event);
 int (*get_parameter_metadata)(const struct device *, struct behavior_parameter_metadata *);
 const struct behavior_parameter_metadata *parameter_metadata;
};
const struct device *zmk_behavior_get_binding(const char *);
int zmk_behavior_invoke_binding(const struct zmk_behavior_binding *, struct zmk_behavior_binding_event, bool);
int zmk_behavior_get_empty_param_metadata(const struct device *, struct behavior_parameter_metadata *);
'''
        harness = r'''
#include <assert.h>
#include <string.h>
#include "behavior_host_os.c"
static const struct zmk_behavior_binding *last;
static struct zmk_behavior_binding_event last_event;
static bool last_pressed;
static int result;
const struct device *zmk_behavior_get_binding(const char *name) {
 return strcmp(name,"a") == 0 ? &roba_behavior_os_select0 : &roba_behavior_os_select1;
}
int zmk_behavior_invoke_binding(const struct zmk_behavior_binding *b,
                                struct zmk_behavior_binding_event e, bool p) {
 last=b; last_event=e; last_pressed=p; return result;
}
int zmk_behavior_get_empty_param_metadata(const struct device *d, struct behavior_parameter_metadata *m) { return 0; }
int main(void) {
 struct zmk_behavior_binding a={.behavior_dev="a"}, b={.behavior_dev="b"}, mode={0};
 struct zmk_behavior_binding_event e={.position=22,.timestamp=123,.source=1};
 assert(!windows_mode);
 assert(os_select_pressed(&a,e)==0 && !strcmp(last->behavior_dev,"linux") && last_pressed);
 assert(last_event.position==22 && last_event.timestamp==123 && last_event.source==1);
 assert(os_select_pressed(&a,e)==-EBUSY);
 mode.param1=ROBA_OS_WINDOWS;
 assert(host_os_pressed(&mode,e)==0 && windows_mode);
 assert(os_select_pressed(&b,e)==0 && !strcmp(last->behavior_dev,"windows"));
 assert(os_select_released(&a,e)==0 && !strcmp(last->behavior_dev,"linux") && !last_pressed);
 assert(os_select_released(&b,e)==0 && !strcmp(last->behavior_dev,"windows"));
 assert(os_select_released(&a,e)==-EINVAL);
 assert(host_os_released(&mode,e)==0 && windows_mode);
 mode.param1=ROBA_OS_TOGGLE;
 assert(host_os_pressed(&mode,e)==0 && !windows_mode);
 assert(host_os_released(&mode,e)==0 && !windows_mode);
 assert(host_os_pressed(&mode,e)==0 && windows_mode);
 mode.param1=ROBA_OS_LINUX;
 assert(host_os_pressed(&mode,e)==0 && !windows_mode);
 assert(host_os_pressed(&mode,e)==0 && !windows_mode);
 mode.param1=99;
 assert(host_os_pressed(&mode,e)==-EINVAL && !windows_mode);
 result=-EIO;
 assert(os_select_pressed(&a,e)==-EIO);
 result=0;
 assert(os_select_pressed(&a,e)==0); /* failed presses must not latch */
 assert(os_select_released(&a,e)==0);
 assert(roba_behavior_host_os0.api==&host_os_api);
 return 0;
}
'''
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            (temp/'stub.h').write_text(stub)
            for header in ['zephyr/device.h', 'drivers/behavior.h', 'zmk/behavior.h']:
                path = temp/header
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('#include "stub.h"\n')
            (temp/'main.c').write_text(harness)
            for metadata in [0, 1]:
                with self.subTest(metadata=metadata):
                    subprocess.run([compiler, '-std=c11', '-Wall', '-Wextra', '-Werror',
                                    '-Wno-unused-parameter', f'-DTEST_METADATA={metadata}',
                                    f'-I{temp}', f'-I{ROOT / "include"}', f'-I{ROOT / "src"}',
                                    str(temp/'main.c'), '-o', str(temp/'test')], check=True)
                    subprocess.run([str(temp/'test')], check=True)

    def test_macro_sequences_and_layer_positions(self):
        source = (ROOT/'config/roBa.keymap').read_text()
        windows = dict(re.findall(r'ac_(\w+)_windows: ac_\w+_windows \{(.*?)\n        \};', source, re.S))
        linux = dict(re.findall(r'ac_(\w+)_linux: ac_\w+_linux \{(.*?)\n        \};', source, re.S))
        self.assertEqual(len(windows), 29)
        self.assertEqual(windows.keys(), linux.keys())
        for name, body in windows.items():
            char = re.search(r'label = "(.*?)"', body)[1]
            digits = ''.join(re.findall(r'<&kp KP_NUMBER_(\d)>', body))
            self.assertEqual(digits, f'{char.encode("cp1252")[0]:04}', name)
            self.assertRegex(source, rf'ac_{name}: ac_{name} \{{\s+compatible = "roba,behavior-os-select";\s+#binding-cells = <0>;\s+bindings = <&ac_{name}_linux>, <&ac_{name}_windows>;')
        drawer = yaml.safe_load((ROOT/'keymap-drawer/roBa.yaml').read_text())
        service = source.split('        SERVICE {')[1].split('>;')[0]
        self.assertEqual(len(re.findall(r'&\w+', service)), 43)
        self.assertEqual(len(drawer['layers']['SERVICE']), 43)
        self.assertEqual(drawer['layers']['SERVICE'][2:5], [{'t': '▽', 'type': 'trans'}, {'t': '▽', 'type': 'trans'}, {'t': 'OS', 'h': 'toggle'}])
        self.assertEqual(re.findall(r'&host_os (\w+)', service), ['ROBA_OS_TOGGLE'])
        self.assertIn('CONFIG_PMW3610_MOVEMENT_THRESHOLD=2', (ROOT/'boards/shields/roBa/roBa_R.conf').read_text())

    def test_linux_compose(self):
        library = ctypes.util.find_library('xkbcommon')
        if not library:
            self.skipTest('libxkbcommon unavailable')
        lib = C.CDLL(library)
        def function(name, result, args):
            f = getattr(lib, name)
            f.restype, f.argtypes = result, args
            return f
        ptr, integer, string = C.c_void_p, C.c_int, C.c_char_p
        context = function('xkb_context_new', ptr, [integer])(0)
        table = function('xkb_compose_table_new_from_locale', ptr, [ptr, string, integer])(context, b'en_US.UTF-8', 0)
        if not table:
            self.skipTest('en_US.UTF-8 Compose table unavailable')
        state = function('xkb_compose_state_new', ptr, [ptr, integer])(table, 0)
        reset = function('xkb_compose_state_reset', None, [ptr])
        feed = function('xkb_compose_state_feed', integer, [ptr, C.c_uint])
        keysym = function('xkb_keysym_from_name', C.c_uint, [string, integer])
        status = function('xkb_compose_state_get_status', integer, [ptr])
        get = function('xkb_compose_state_get_utf8', integer, [ptr, ptr, C.c_size_t])
        aliases = {'K_APPLICATION': 'Multi_key', 'GRAVE': 'grave', 'SQT': 'apostrophe',
                   'CARET': 'asciicircum', 'COMMA': 'comma', 'DOUBLE_QUOTES': 'quotedbl', 'EQUAL': 'equal'}
        source = (ROOT/'config/roBa.keymap').read_text()
        macros = re.findall(r'ac_(\w+)_linux: ac_\w+_linux \{(.*?)\n        \};', source, re.S)
        self.assertEqual(len(macros), 29)
        for name, body in macros:
            reset(state)
            for code in re.findall(r'<&kp ([^>]+)>', body):
                symbol = aliases.get(code, code[3:-1] if code.startswith('LS(') else code.lower())
                key = keysym(symbol.encode(), 0)
                self.assertNotEqual(key, 0, code)
                feed(state, key)
            buf = C.create_string_buffer(32)
            get(state, buf, 32)
            self.assertEqual(status(state), 2, name)
            self.assertEqual(buf.value.decode(), re.search(r'label = "(.*?)"', body)[1], name)
        function('xkb_compose_state_unref', None, [ptr])(state)
        function('xkb_compose_table_unref', None, [ptr])(table)
        function('xkb_context_unref', None, [ptr])(context)


if __name__ == '__main__':
    unittest.main()
