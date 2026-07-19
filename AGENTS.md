# RoBa ZMK Config

This repository is the ZMK firmware configuration for **RoBa** (pOpPolLoPpoBa), a DIY split ergonomic keyboard with an integrated PMW3610 optical trackball. It defines the complete hardware abstraction (shields, pin mappings, matrix), firmware behavior (keymap, layers, home row mods, combos, macros), trackball configuration (AutoMouse, Snipe, Scroll modes), and the CI/build pipeline (GitHub Actions, keymap-drawer visualization).

---

# RoBa (pOpPolLoPpoBa) — ZMK Config Reference

## Project Identity

- **Keyboard name:** `"pOpPolLoPpoBa"` (set in `roBa_R.conf`)
- **Shield name:** `roBa` (left half: `roBa_L`, right half: `roBa_R`)
- **MCU:** nRF52840 (Seeed Studio XIAO BLE)
- **Type:** DIY split column-stagger keyboard with integrated PMW3610 optical trackball

---

## Hardware

| Half   | MCU                        | Role     | Peripherals                              |
|--------|----------------------------|----------|------------------------------------------|
| Right  | Seeed XIAO BLE (nRF52840) | Central  | PMW3610 trackball (SPI0)                 |
| Left   | Seeed XIAO BLE (nRF52840) | Peripheral | EC11 rotary encoder                     |

- **Matrix:** 4 rows × 11 columns, diode `col2row`, GPIO `ACTIVE_HIGH | PULL_DOWN`
- **Physical keys:** 42 keys (10 per row × 4 rows + 2 thumb cluster keys per side)
- **Left column GPIOs:** `xiao_d 10,9,8,7, gpio0 10, gpio0 9` (6 columns)
- **Right column GPIOs:** `xiao_d 10,9,8,7, gpio0 10` (5 columns, offset +6)
- **Row GPIOs:** `xiao_d 1,2,3,6`
- **Left encoder:** EC11 on `xiao_d 5` (A), `xiao_d 0` (B), 12 steps
- **Trackball:** PMW3610 on SPI0, SCK=0.5, MOSI=0.4, MISO=0.4, CS=gpio0.9, IRQ=gpio0.2, `snipe-layers = <7>`, 2MHz

---

## Firmware Stack

| Component | Source |
|-----------|--------|
| ZMK | `zmkfirmware/zmk` — `v0.3-branch` |
| PMW3610 Driver | `kumamuk-git/zmk-pmw3610-driver` — `main` |
| ZMK Studio | Enabled, unlocked (`CONFIG_ZMK_STUDIO_LOCKING=n`) |
| Build system | Zephyr module via `zephyr/module.yml`, `config/west.yml` |

---

## Build Targets (build.yaml)

```yaml
- board: seeeduino_xiao_ble
  shield: roBa_R
  snippet: studio-rpc-usb-uart
- board: seeeduino_xiao_ble
  shield: roBa_L
- board: seeeduino_xiao_ble
  shield: settings_reset
```

---

## File Map

| File | Purpose |
|------|---------|
| `config/roBa.keymap` | **ACTIVE keymap** — edit this file |
| `config/roBa.json` | Layout definition for keymap-drawer (44 keys, 2 encoders) |
| `config/west.yml` | West manifest (ZMK version, custom driver remotes) |
| `build.yaml` | CI build matrix |
| `boards/shields/roBa/roBa.dtsi` | Common hardware definitions (matrix, encoder, trackball, physical layout, transform) |
| `boards/shields/roBa/roBa_L.overlay` | Left half pin assignments (6 columns, enable encoder) |
| `boards/shields/roBa/roBa_R.overlay` | Right half pin assignments (5 columns, enable trackball, SPI0 pinctrl) |
| `boards/shields/roBa/roBa_L.conf` | Left configuration (EC11, battery, pointing) |
| `boards/shields/roBa/roBa_R.conf` | Right configuration (trackball CPI/modes, SPI, BLE, ZMK Studio, battery) |
| `boards/shields/roBa/Kconfig.defconfig` | Split roles: `roBa_R` = central, `roBa_L` = peripheral |
| `boards/shields/roBa/Kconfig.shield` | Shield detection |
| `boards/shields/roBa/roBa.zmk.yml` | Shield metadata (requires `seeeduino_xiao_ble`, features: keys, pointing, sensors) |
| `zephyr/module.yml` | Zephyr module definition |
| `keymap-drawer/config.yaml` | SVG draw configuration (key sizes, colors, glyphs, modifier names) |
| `keymap-drawer/roBa.yaml` | Parsed keymap for SVG generation |
| `keymap-drawer/roBa.svg` | Generated keymap visualization |
| `.github/workflows/build.yml` | GitHub Actions: build firmware on push/PR |
| `.github/workflows/draw.yml` | GitHub Actions: regenerate SVG on keymap/config changes |

### Variant / Reference Files

| File | Purpose |
|------|---------|
| `main_keymap.txt` | Older keymap variant (fewer HRM variants, shorter terms, no `lt_scroll`, mod-morph accents) |
| `main_keymap_raw.txt` | Identical to `main_keymap.txt` |
| `zmk_update_keymap_raw.txt` | **Experimental future version** — input processors, conditional layers, mod-morph accents, `zip_*_transform`, `hold-preferred` on `lt_to_layer_0` |

---

## Active Keymap Architecture (`config/roBa.keymap`)

### Layer Index (10 layers)

| # | Name | Access | Purpose |
|---|------|--------|---------|
| 0 | `default_layer` | Base | QWERTY + home row mods + layer access |
| 1 | `FUNCTION` | `&lt 1` on ENTER | F1–F13 |
| 2 | `NUM` | `&mo 2` on thumb | Number pad (left) + symbol pairs (right) |
| 3 | `ARROW` | `&lt_to_layer_0_space` on SPACE | Navigation + IDE shortcuts |
| 4 | `MOUSE` | AutoMouse (trackball movement) | Mouse buttons (MB1–MB5), AutoMouse with 700ms timeout |
| 5 | `SCROLL` | `&lt_scroll` on I | Trackball becomes scroll wheel |
| 6 | `SERVICE` | `&mo 6` on thumb | Media, Bluetooth, system keys, bootloader |
| 7 | `SNIPE` | `&lt_to_layer_0` on DEL | Low-CPI precision aiming (300 CPI), same buttons as MOUSE |
| 8 | `GAMING` | Combo `Gaming` (toggle) | WASD layout, no home row mods, plain keys |
| 9 | `ACCENTS` | `&lt_to_layer_0` on `;` | French/Portuguese accented characters (Alt+code macros) |

### Custom Behaviors

#### Home Row Mods

| Alias | Tapping Term | Flavor | Quick Tap | Require Idle | Hold-Trigger Positions | Hold-Trigger-on-Release |
|-------|-------------|--------|-----------|-------------|----------------------|:---:|
| `hm_l` | 280ms | balanced | 175ms | 175ms | Right hand + right thumb (positions 5–9, 16–21, 28–33, 40–42) | Yes |
| `hm_r` | 280ms | balanced | 175ms | 175ms | Left hand + left thumb (positions 0–4, 10–16, 22–28, 34–39) | Yes |
| `hm_shift_l` | 175ms | balanced | 175ms | — | Right hand positions (same as `hm_l`) | Yes |
| `hm_shift_r` | 175ms | balanced | 175ms | — | Left hand positions (same as `hm_r`) | Yes |

- `hm_l` applied to: A (`LCTRL`), S (`LSHIFT`), D (`LALT`), F (`LGUI`)
- `hm_r` applied to: J (`RCTRL`), K (none), L (`RALT`)
- `hm_shift_l` applied to: Z (`LSHIFT`)
- `hm_shift_r` applied to: `/` (`RSHIFT`)

#### Layer-Tap Behaviors

| Alias | Tapping Term | Flavor | Behavior |
|-------|-------------|--------|----------|
| `lt_to_layer_0` | 200ms | tap-preferred | Hold = `&mo`, Tap = `&to_layer_0` (macro: go to layer 0 + send key) |
| `lt_to_layer_0_space` | 150ms | tap-preferred | Same as above, used for SPACE |
| `lt_scroll` | 175ms | balanced | Hold = `&mo`, Tap = passed key (I) |
| `msl` | 200ms | tap-preferred | Hold = `&mo`, Tap = `&sl` (sticky layer) |
| `msk` | 200ms | tap-preferred | Hold = `&mo`, Tap = `&sk` (sticky key) |

#### Global Hold-Tap / Layer-Tap Defaults

| Behavior | Tapping Term | Flavor | Quick Tap | Require Idle |
|----------|-------------|--------|-----------|-------------|
| `&mt` | 200ms | balanced | 150ms | 150ms |
| `&lt` | 200ms | tap-preferred | 150ms | 100ms |
| `&sl` | — | — | (quick-release, 2000ms timeout) | — |
| `&sk` | — | — | (quick-release, 2000ms timeout) | — |

### Combos (6)

| Combo | Keys | Binding | Timeout | Require Idle | Layers |
|-------|------|---------|---------|-------------|--------|
| tab | 11, 12 | `TAB` | 40ms | 175ms | 0 |
| shift_tab | 12, 13 | `LS(TAB)` | 40ms | 175ms | 0 |
| double_quotation | 20, 21 | `DOUBLE_QUOTES` | 40ms | 175ms | All |
| eq | 24, 25 | `EQUAL` | 40ms | — | 0, 2 |
| ctrl+alt+del | 34, 42 | `LC(LA(DELETE))` | 40ms | 175ms | All |
| Gaming | 0, 1, 8, 9 | `&tog 8` (GAMING toggle) | 40ms | 175ms | All |

### Macros (18)

#### Accent Characters (12) — Windows Alt+Keypad codes

| Macro | Char | Alt+Code | Lowercase | Uppercase | Macro | Char | Alt+Code |
|-------|------|----------|-----------|-----------|-------|------|----------|
| `ac_agrv_l` | à | Alt+0224 | ✓ | | `ac_agrv_u` | À | Alt+0192 |
| `ac_egrv_l` | è | Alt+0232 | ✓ | | `ac_egrv_u` | È | Alt+0200 |
| `ac_eacu_l` | é | Alt+0233 | ✓ | | `ac_eacu_u` | É | Alt+0201 |
| `ac_ugrv_l` | ù | Alt+0249 | ✓ | | `ac_ugrv_u` | Ù | Alt+0217 |
| `ac_ocir_l` | ô | Alt+0244 | ✓ | | `ac_ocir_u` | Ô | Alt+0212 |
| `ac_ccdi_l` | ç | Alt+0231 | ✓ | | `ac_ccdi_u` | Ç | Alt+0199 |

#### Productivity Macros (10)

| Macro | Action |
|-------|--------|
| `mc_find` | Ctrl+F |
| `mc_selall` | Ctrl+A |
| `mc_undo` | Ctrl+Z |
| `mc_copy` | Ctrl+C |
| `mc_cut` | Ctrl+X |
| `mc_paste` | Ctrl+V |
| `mc_save` | Ctrl+S |
| `mc_save_esc` | Ctrl+S → Esc |
| `mc_save_all` | Ctrl+Shift+S |
| `mc_seln` | Home → Shift+End |

#### Special

| Macro | Type | Purpose |
|-------|------|---------|
| `to_layer_0` | `zmk,behavior-macro-one-param` | `&to 0` then `&macro_param_1to1 &kp` — used by `lt_to_layer_0` and `lt_to_layer_0_space` |

---

## Trackball Configuration

### Physical Settings (`roBa_R.conf`)

| Setting | Value | Effect |
|---------|-------|--------|
| `CPI` | 800 | Normal cursor speed |
| `CPI_DIVIDOR` | 1 | Effective CPI = 800 / 1 = 800 |
| `SNIPE_CPI` | 1200 | CPI used when snipe layer active |
| `SNIPE_CPI_DIVIDOR` | 4 | Effective snipe CPI = 1200 / 4 = 300 |
| `ORIENTATION_180` | y | Trackball rotated 180° |
| `INVERT_X` | n | Normal X axis |
| `INVERT_SCROLL_X` | y | Invert scroll X |
| `SCROLL_TICK` | 16 | Scroll sensitivity (lower = faster) |
| `AUTOMOUSE_TIMEOUT_MS` | 700 | AutoMouse layer timeout after movement |
| `MOVEMENT_THRESHOLD` | 0 | Detect all motion |
| `POLLING_RATE_125_SW` | y | 125 Hz software polling |
| `SMART_ALGORITHM` | y | Improved tracking |
| `RUN_DOWNSHIFT_TIME_MS` | 3264 | Power-saving downshift delay |
| `REST1_SAMPLE_TIME_MS` | 20 | Sampling in REST1 mode |

### Trackball Layers

| Layer # | Name | Trigger | Effect |
|---------|------|---------|--------|
| 4 | MOUSE | Auto-detect (movement) | MB1–MB5 buttons |
| 5 | SCROLL | `&lt_scroll` on I hold | XY → scroll wheel |
| 7 | SNIPE | `&lt_to_layer_0` on DEL hold | 300 CPI precision aiming, same buttons as MOUSE |

The `snipe-layers = <7>` property in `roBa_R.overlay` tells the PMW3610 driver to enter low-CPI mode when layer 7 is active.

---

## Encoder Bindings

| Layer | Binding |
|-------|---------|
| `default_layer` (0) | `C_VOLUME_UP` / `C_VOLUME_DOWN` |
| `FUNCTION` (1) | `TAB` / `LS(TAB)` |
| `NUM` (2) | `F3` / `LS(F3)` |
| `ARROW` (3) | `LC(RIGHT_ARROW)` / `LC(LEFT_ARROW)` (browser tab switching) |
| `GAMING` (8) | `C_VOLUME_UP` / `C_VOLUME_DOWN` |

---

## Keymap Drawer Integration

- **Trigger:** Auto-regenerates SVG on push to `config/roBa.keymap`, `keymap-drawer/config.yaml`, or `config/roBa.dtsi`
- **Config:** `keymap-drawer/config.yaml` — visual settings, glyph sizes (tap=14, hold=12, shifted=10), modifier abbreviations
- **Parsed YAML:** `keymap-drawer/roBa.yaml` — must be kept in sync with `config/roBa.keymap` (auto-regenerated by CI via `.github/workflows/draw.yml`)
- **Output:** `keymap-drawer/roBa.svg`

When editing `roBa.keymap`, also update `keymap-drawer/roBa.yaml` to keep the visualizer in sync (or push and let CI regenerate it).

---

## Experimental / Future Features (`zmk_update_keymap_raw.txt`)

This file contains an experimental evolution of the keymap with:

- **Conditional Layers** — `snipe_scroll` layer 9 activates when both SCROLL (5) and SNIPE (7) are active
- **Input Processors** — Per-layer input processing chains on the `trackball_listener`:
  - Default: `temp_layer` (auto-layer-4 for 600ms on movement) + `zip_xy_transform` (swap + invert X)
  - SCROLL layer (5): `custom_scroll_mapper` (REL_X→WHEEL, REL_Y→HWHEEL) + `zip_scroll_transform` (invert X+Y) + scaler 1:4
  - SNIPE layer (7): scaler 3:8 + `zip_xy_transform`
  - SNIPE_SCROLL layer (9): scroll mapper + `zip_scroll_transform` + scaler 1:8
- **Mod-Morph Accents** — `ac_agrv`, `ac_egrv`, etc. combine lower/upper with Shift
- **`hold-preferred`** on `lt_to_layer_0` — only 1 behavioral diff from active keymap
- **No `lt_scroll`** — uses plain `&lt 5 I` instead
- **No `lt_to_layer_0_space`** — uses `&lt_to_layer_0 3 SPACE` with `hold-preferred`
- **Unified `hm_shift`** — single shift variant at 200ms (vs active's 175ms left/right split)

---

## Typical Tasks & Agent Guidelines

1. **The active keymap file is `config/roBa.keymap`** — always edit this, not the `.txt` variants.
2. **Keep `keymap-drawer/roBa.yaml` in sync** when changing keymap bindings (or rely on CI to regenerate, but local sync is preferred for consistency).
3. **The `.conf` files use Japanese-style comments** with detailed explanations — preserve this style when adding new config options.
4. **Home row mod key positions** are 0-indexed GPIO matrix positions, not physical positions. Refer to `roBa.dtsi` for the `RC(row,col)` → position mapping.
5. **When adding new behaviors**, use the same naming conventions: `hm_*` for hold-tap home row mods, `lt_*` for layer-tap, `mc_*` for macros, `ac_*` for accent characters.
6. **Trackball config lives in `roBa_R.conf`** — the PMW3610 driver's Kconfig options are documented at `kumamuk-git/zmk-pmw3610-driver`.
7. **ZMK Studio** is enabled and unlocked — this allows runtime keymap changes. The `studio-rpc-usb-uart` snippet is used for the right half.
8. **Split roles** are defined in `Kconfig.defconfig`: right (`roBa_R`) = central (connected to computer), left (`roBa_L`) = peripheral.

### Key Positions Reference

Position mapping from matrix coordinates:
```
RC(0,0)  RC(0,1)  RC(0,2)  RC(0,3)  RC(0,4)                RC(0,6)  RC(0,7)  RC(0,8)  RC(0,9)  RC(0,10)     ← row 0
 0         1         2         3         4          5     6     7         8         9        10         11    ← positions

RC(1,0)  RC(1,1)  RC(1,2)  RC(1,3)  RC(1,4)  RC(1,5)    RC(3,6)  RC(1,6)  RC(1,7)  RC(1,8)  RC(1,9)  RC(1,10)  ← row 1
12        13        14        15        16        17      18        19        20        21        22        23

RC(2,0)  RC(2,1)  RC(2,2)  RC(2,3)  RC(2,4)  RC(2,5)    RC(3,7)  RC(2,6)  RC(2,7)  RC(2,8)  RC(2,9)  RC(2,10)  ← row 2
24        25        26        27        28        29      30        31        32        33        34        35

RC(3,0)  RC(3,1)  RC(3,2)  RC(3,3)  RC(3,4)  RC(3,5)    RC(3,8)  RC(3,9)                      RC(3,10)   ← row 3
36        37        38      (39)      (40)      (41)       42        43                                     44
```
Parenthesized positions (39–41) are the left thumb cluster. 42–43 are right thumb inner. 44 is the right thumb outer key.
