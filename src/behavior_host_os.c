/* SPDX-License-Identifier: MIT */

#include <errno.h>
#include <zephyr/device.h>
#include <drivers/behavior.h>
#include <zmk/behavior.h>
#include <dt-bindings/roba/host-os.h>

#if DT_HAS_COMPAT_STATUS_OKAY(roba_behavior_os_select) || \
    DT_HAS_COMPAT_STATUS_OKAY(roba_behavior_host_os)

/* Central-side state, shared by OS-dependent shortcuts and accents. Resets to Linux at boot. */
static bool windows_mode;

#define DT_DRV_COMPAT roba_behavior_os_select
#if DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT)

struct os_select_config {
    struct zmk_behavior_binding bindings[2];
};

struct os_select_data {
    const struct zmk_behavior_binding *pressed;
};

static int os_select_pressed(struct zmk_behavior_binding *binding,
                             struct zmk_behavior_binding_event event) {
    const struct device *dev = zmk_behavior_get_binding(binding->behavior_dev);
    const struct os_select_config *config = dev->config;
    struct os_select_data *data = dev->data;

    if (data->pressed != NULL) {
        return -EBUSY;
    }
    data->pressed = &config->bindings[windows_mode ? ROBA_OS_WINDOWS : ROBA_OS_LINUX];
    int err = zmk_behavior_invoke_binding(data->pressed, event, true);
    if (err < 0) {
        data->pressed = NULL;
    }
    return err;
}

static int os_select_released(struct zmk_behavior_binding *binding,
                              struct zmk_behavior_binding_event event) {
    const struct device *dev = zmk_behavior_get_binding(binding->behavior_dev);
    struct os_select_data *data = dev->data;
    const struct zmk_behavior_binding *pressed = data->pressed;

    if (pressed == NULL) {
        return -EINVAL;
    }
    /* A host switch between press and release must not release the other macro. */
    data->pressed = NULL;
    return zmk_behavior_invoke_binding(pressed, event, false);
}

static const struct behavior_driver_api os_select_api = {
    .locality = BEHAVIOR_LOCALITY_CENTRAL,
    .binding_pressed = os_select_pressed,
    .binding_released = os_select_released,
#if IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)
    .get_parameter_metadata = zmk_behavior_get_empty_param_metadata,
#endif
};

#define OS_BINDING(n, i) {.behavior_dev = DEVICE_DT_NAME(DT_INST_PHANDLE_BY_IDX(n, bindings, i))}
#define OS_SELECT_DEFINE(n)                                                                         \
    BUILD_ASSERT(DT_INST_PROP_LEN(n, bindings) == 2, "OS selector needs Linux and Windows");          \
    static const struct os_select_config os_config_##n = {                                          \
        .bindings = {OS_BINDING(n, 0), OS_BINDING(n, 1)},                                             \
    };                                                                                             \
    static struct os_select_data os_data_##n;                                                       \
    BEHAVIOR_DT_INST_DEFINE(n, NULL, NULL, &os_data_##n, &os_config_##n, POST_KERNEL,                  \
                            CONFIG_KERNEL_INIT_PRIORITY_DEFAULT, &os_select_api);

DT_INST_FOREACH_STATUS_OKAY(OS_SELECT_DEFINE)
#endif
#undef DT_DRV_COMPAT

#define DT_DRV_COMPAT roba_behavior_host_os
#if DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT)

static int host_os_pressed(struct zmk_behavior_binding *binding,
                           struct zmk_behavior_binding_event event) {
    switch (binding->param1) {
    case ROBA_OS_LINUX:
        windows_mode = false;
        break;
    case ROBA_OS_WINDOWS:
        windows_mode = true;
        break;
    case ROBA_OS_TOGGLE:
        windows_mode = !windows_mode;
        break;
    default:
        return -EINVAL;
    }
    return ZMK_BEHAVIOR_OPAQUE;
}

static int host_os_released(struct zmk_behavior_binding *binding,
                            struct zmk_behavior_binding_event event) {
    return ZMK_BEHAVIOR_OPAQUE;
}

#if IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)
static const struct behavior_parameter_value_metadata host_values[] = {
    {.display_name = "Linux", .type = BEHAVIOR_PARAMETER_VALUE_TYPE_VALUE, .value = ROBA_OS_LINUX},
    {.display_name = "Windows", .type = BEHAVIOR_PARAMETER_VALUE_TYPE_VALUE, .value = ROBA_OS_WINDOWS},
    {.display_name = "Toggle", .type = BEHAVIOR_PARAMETER_VALUE_TYPE_VALUE, .value = ROBA_OS_TOGGLE},
};
static const struct behavior_parameter_metadata_set host_metadata_set[] = {{
    .param1_values = host_values,
    .param1_values_len = ARRAY_SIZE(host_values),
}};
static const struct behavior_parameter_metadata host_metadata = {
    .sets = host_metadata_set,
    .sets_len = ARRAY_SIZE(host_metadata_set),
};
#endif

static const struct behavior_driver_api host_os_api = {
    .locality = BEHAVIOR_LOCALITY_CENTRAL,
    .binding_pressed = host_os_pressed,
    .binding_released = host_os_released,
#if IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)
    .parameter_metadata = &host_metadata,
#endif
};

#define HOST_OS_DEFINE(n)                                                                           \
    BEHAVIOR_DT_INST_DEFINE(n, NULL, NULL, NULL, NULL, POST_KERNEL,                                   \
                            CONFIG_KERNEL_INIT_PRIORITY_DEFAULT, &host_os_api);

DT_INST_FOREACH_STATUS_OKAY(HOST_OS_DEFINE)
#endif
#endif
