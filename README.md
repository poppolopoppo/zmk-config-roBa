# zmk-config-roBa

<img src="keymap-drawer/roBa.svg" >

## Accent layer on Linux (KDE/Wayland)

The ACCENTS layer defaults to Linux Compose sequences. Use a standard **US
QWERTY** host layout. In KDE System Settings → Keyboard → Key Bindings
(or Advanced on older Plasma), enable **Configure keyboard options**, then
set **Position of Compose key → Menu** and apply. This corresponds to the
XKB option `compose:menu`. The firmware sends Menu inside each accent macro;
no physical Compose key is needed. NumLock is irrelevant in Linux mode.

Hold the existing ACCENTS layer key and tap an accent key as before. Hold Shift
for uppercase. For example, é sends Menu, apostrophe, E; É sends Menu,
apostrophe, Shift+E. The same layer positions and displayed characters are kept.
Compose support depends on the application; test in a KDE editor and your
usual applications after flashing. Caps Lock and other held modifiers can
change the sequence; use Shift for uppercase.

## Switch host mode at runtime

Use the existing SERVICE layer (hold the SERVICE thumb key):

| Keys | Host mode |
| --- | --- |
| SERVICE + T | Toggle Linux / Windows |

Linux is selected at boot. The selection is global across USB and Bluetooth
profiles and lasts until changed or the central half restarts; it is not saved
to flash and does not follow Bluetooth profile selection. Each SERVICE + T press
switches to the other mode. The same firmware contains both modes.
Windows needs **NumLock on**; SERVICE + the inner Minus key toggles NumLock.
No additional Windows software is required. The selected mode also controls these shortcuts:

| Binding | Linux (KDE) | Windows |
| --- | --- | --- |
| ARROW-layer Redo | Ctrl+Shift+Z | Ctrl+Y |
| SERVICE + Q | Meta+Esc (System Monitor) | Ctrl+Shift+Esc (Task Manager) |
| SERVICE taskbar gestures (positions 22–27) | Meta+1–6 | Meta+Shift+1–6 |
| Existing screenshot key (position 15) | Meta+Shift+PrintScreen (region capture) | Meta+Shift+S |

The ARROW-layer encoder switches browser tabs in either mode: clockwise sends
Ctrl+PageDown (next tab), counterclockwise sends Ctrl+PageUp (previous tab).
Other bindings do not change with the host mode.

The runtime selector is a local ZMK behavior in `src/behavior_host_os.c`,
compiled through this repository's Zephyr module. Its native tests can be run
with `python3 -m unittest discover -s tests` (requires a C compiler and PyYAML;
Linux Compose checks also use libxkbcommon).

## Clipboard shortcuts

| Keys | Action | Output |
| --- | --- | --- |
| ARROW + Copy | Desktop copy | Ctrl+C |
| Shift + ARROW + Copy | Terminal copy | Ctrl+Shift+C |
| ARROW + Paste | Desktop paste | Ctrl+V |
| Shift + ARROW + Paste | Terminal paste | Ctrl+Shift+V |
| SERVICE + K | Clipboard history | Meta+V |

Hold Shift while tapping the existing ARROW-layer Copy/Paste keys to use
terminal clipboard shortcuts. The macros preserve held Shift; no separate
terminal bindings are needed. Cut remains Ctrl+X. SERVICE+H/J are transparent
again. These shortcuts send the same keys in both host modes. Clipboard history requires the host's history
feature to be enabled (Klipper on KDE or clipboard history on Windows).
The screenshot key stays at its existing position; SERVICE+T selects its
Linux or Windows sequence. The Linux sequence uses Spectacle's configured
region-capture action. No KRunner binding is added.
