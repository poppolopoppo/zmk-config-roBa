/*
 * Copyright (c) 2026 The ZMK Contributors
 *
 * SPDX-License-Identifier: MIT
 */

#define DT_DRV_COMPAT zmk_behavior_mod_layer

#include <zephyr/device.h>
#include <drivers/behavior.h>
#include <zephyr/logging/log.h>

#include <zmk/behavior.h>
#include <zmk/keymap.h>

LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

#if DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT)

struct behavior_mod_layer_config {
    struct zmk_behavior_binding layer_binding;
    struct zmk_behavior_binding mod_binding;
};

struct behavior_mod_layer_data {
#if IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)
    struct behavior_parameter_metadata_set set;
#endif // IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)
};

static int on_mod_layer_binding_pressed(struct zmk_behavior_binding *binding,
                                        struct zmk_behavior_binding_event event) {
    const struct device *dev = zmk_behavior_get_binding(binding->behavior_dev);
    const struct behavior_mod_layer_config *cfg = dev->config;

    // Press the modifier first so any following key event already sees it,
    // then activate the layer. Both invocations are synchronous within this
    // single key-event listener call, so no other event can interleave.
    struct zmk_behavior_binding mod_binding = {
        .behavior_dev = cfg->mod_binding.behavior_dev,
        .param1 = binding->param2,
    };
    int ret = zmk_behavior_invoke_binding(&mod_binding, event, true);

    struct zmk_behavior_binding layer_binding = {
        .behavior_dev = cfg->layer_binding.behavior_dev,
        .param1 = binding->param1,
    };
    int layer_ret = zmk_behavior_invoke_binding(&layer_binding, event, true);

    return ret < 0 ? ret : layer_ret;
}

static int on_mod_layer_binding_released(struct zmk_behavior_binding *binding,
                                         struct zmk_behavior_binding_event event) {
    const struct device *dev = zmk_behavior_get_binding(binding->behavior_dev);
    const struct behavior_mod_layer_config *cfg = dev->config;

    // Deactivate the layer first, then release the modifier.
    struct zmk_behavior_binding layer_binding = {
        .behavior_dev = cfg->layer_binding.behavior_dev,
        .param1 = binding->param1,
    };
    int ret = zmk_behavior_invoke_binding(&layer_binding, event, false);

    struct zmk_behavior_binding mod_binding = {
        .behavior_dev = cfg->mod_binding.behavior_dev,
        .param1 = binding->param2,
    };
    int mod_ret = zmk_behavior_invoke_binding(&mod_binding, event, false);

    return ret < 0 ? ret : mod_ret;
}

#if IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)

// Minimal ZMK Studio support: param1 domain comes from the layer child (&mo),
// param2 domain from the modifier child (&kp). Same aggregation pattern as
// upstream behavior_hold_tap.c.
static int mod_layer_parameter_metadata(const struct device *dev,
                                        struct behavior_parameter_metadata *param_metadata) {
    const struct behavior_mod_layer_config *cfg = dev->config;
    struct behavior_mod_layer_data *data = dev->data;
    struct behavior_parameter_metadata child_meta;
    int err;

    err = behavior_get_parameter_metadata(zmk_behavior_get_binding(cfg->layer_binding.behavior_dev),
                                          &child_meta);
    if (err < 0) {
        LOG_WRN("Failed to get the layer behavior parameter metadata: %d", err);
        return err;
    }

    if (child_meta.sets_len > 0) {
        data->set.param1_values = child_meta.sets[0].param1_values;
        data->set.param1_values_len = child_meta.sets[0].param1_values_len;
    }

    err = behavior_get_parameter_metadata(zmk_behavior_get_binding(cfg->mod_binding.behavior_dev),
                                          &child_meta);
    if (err < 0) {
        LOG_WRN("Failed to get the modifier behavior parameter metadata: %d", err);
        return err;
    }

    if (child_meta.sets_len > 0) {
        data->set.param2_values = child_meta.sets[0].param1_values;
        data->set.param2_values_len = child_meta.sets[0].param1_values_len;
    }

    param_metadata->sets = &data->set;
    param_metadata->sets_len = 1;

    return 0;
}

#endif // IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)

static const struct behavior_driver_api behavior_mod_layer_driver_api = {
    .binding_pressed = on_mod_layer_binding_pressed,
    .binding_released = on_mod_layer_binding_released,
#if IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)
    .get_parameter_metadata = mod_layer_parameter_metadata,
#endif // IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)
};

#define ML_INST(n)                                                                                 \
    static struct behavior_mod_layer_data behavior_mod_layer_data_##n = {};                        \
    static const struct behavior_mod_layer_config behavior_mod_layer_config_##n = {                \
        .layer_binding = ZMK_KEYMAP_EXTRACT_BINDING(0, DT_DRV_INST(n)),                            \
        .mod_binding = ZMK_KEYMAP_EXTRACT_BINDING(1, DT_DRV_INST(n)),                              \
    };                                                                                             \
    BEHAVIOR_DT_INST_DEFINE(n, NULL, NULL, &behavior_mod_layer_data_##n,                           \
                            &behavior_mod_layer_config_##n, POST_KERNEL,                           \
                            CONFIG_KERNEL_INIT_PRIORITY_DEFAULT,                                   \
                            &behavior_mod_layer_driver_api);

DT_INST_FOREACH_STATUS_OKAY(ML_INST)

#endif // DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT)
