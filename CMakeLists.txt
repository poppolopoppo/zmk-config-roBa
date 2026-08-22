if(CONFIG_ZMK_BEHAVIOR_MOD_LAYER)
  zephyr_library()
  zephyr_library_sources(
    src/behaviors/behavior_mod_layer.c
  )
endif()
