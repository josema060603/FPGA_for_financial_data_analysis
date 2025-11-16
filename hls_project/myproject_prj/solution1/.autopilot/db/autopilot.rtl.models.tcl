set SynModuleInfo {
  {SRCNAME {dense_latency<ap_fixed<32, 16, 5, 3, 0>, ap_fixed<32, 18, 5, 3, 0>, config2>} MODELNAME dense_latency_ap_fixed_32_16_5_3_0_ap_fixed_32_18_5_3_0_config2_s RTLNAME myproject_dense_latency_ap_fixed_32_16_5_3_0_ap_fixed_32_18_5_3_0_config2_s
    SUBMODULES {
      {MODELNAME myproject_mul_32s_14s_45_1_1 RTLNAME myproject_mul_32s_14s_45_1_1 BINDTYPE op TYPE mul IMPL auto LATENCY 0 ALLOW_PRAGMA 1}
    }
  }
  {SRCNAME {relu<ap_fixed<32, 18, 5, 3, 0>, ap_fixed<16, 6, 5, 3, 0>, relu_config3>} MODELNAME relu_ap_fixed_32_18_5_3_0_ap_fixed_16_6_5_3_0_relu_config3_s RTLNAME myproject_relu_ap_fixed_32_18_5_3_0_ap_fixed_16_6_5_3_0_relu_config3_s}
  {SRCNAME {dense_latency<ap_fixed<16, 6, 5, 3, 0>, ap_fixed<32, 18, 5, 3, 0>, config4>} MODELNAME dense_latency_ap_fixed_16_6_5_3_0_ap_fixed_32_18_5_3_0_config4_s RTLNAME myproject_dense_latency_ap_fixed_16_6_5_3_0_ap_fixed_32_18_5_3_0_config4_s
    SUBMODULES {
      {MODELNAME myproject_mul_16s_14s_29_1_1 RTLNAME myproject_mul_16s_14s_29_1_1 BINDTYPE op TYPE mul IMPL auto LATENCY 0 ALLOW_PRAGMA 1}
      {MODELNAME myproject_mul_16s_14s_30_1_1 RTLNAME myproject_mul_16s_14s_30_1_1 BINDTYPE op TYPE mul IMPL auto LATENCY 0 ALLOW_PRAGMA 1}
      {MODELNAME myproject_mul_16s_15s_30_1_1 RTLNAME myproject_mul_16s_15s_30_1_1 BINDTYPE op TYPE mul IMPL auto LATENCY 0 ALLOW_PRAGMA 1}
    }
  }
  {SRCNAME {relu<ap_fixed<32, 18, 5, 3, 0>, ap_fixed<16, 6, 5, 3, 0>, relu_config5>} MODELNAME relu_ap_fixed_32_18_5_3_0_ap_fixed_16_6_5_3_0_relu_config5_s RTLNAME myproject_relu_ap_fixed_32_18_5_3_0_ap_fixed_16_6_5_3_0_relu_config5_s}
  {SRCNAME {dense_latency<ap_fixed<16, 6, 5, 3, 0>, ap_fixed<32, 18, 5, 3, 0>, config6>} MODELNAME dense_latency_ap_fixed_16_6_5_3_0_ap_fixed_32_18_5_3_0_config6_s RTLNAME myproject_dense_latency_ap_fixed_16_6_5_3_0_ap_fixed_32_18_5_3_0_config6_s}
  {SRCNAME {relu<ap_fixed<32, 18, 5, 3, 0>, ap_fixed<16, 6, 5, 3, 0>, relu_config7>} MODELNAME relu_ap_fixed_32_18_5_3_0_ap_fixed_16_6_5_3_0_relu_config7_s RTLNAME myproject_relu_ap_fixed_32_18_5_3_0_ap_fixed_16_6_5_3_0_relu_config7_s}
  {SRCNAME {dense_latency<ap_fixed<16, 6, 5, 3, 0>, ap_fixed<32, 18, 5, 3, 0>, config8>} MODELNAME dense_latency_ap_fixed_16_6_5_3_0_ap_fixed_32_18_5_3_0_config8_s RTLNAME myproject_dense_latency_ap_fixed_16_6_5_3_0_ap_fixed_32_18_5_3_0_config8_s}
  {SRCNAME {sigmoid<ap_fixed<32, 18, 5, 3, 0>, ap_fixed<16, 6, 5, 3, 0>, sigmoid_config9>} MODELNAME sigmoid_ap_fixed_32_18_5_3_0_ap_fixed_16_6_5_3_0_sigmoid_config9_s RTLNAME myproject_sigmoid_ap_fixed_32_18_5_3_0_ap_fixed_16_6_5_3_0_sigmoid_config9_s
    SUBMODULES {
      {MODELNAME myproject_sigmoid_ap_fixed_32_18_5_3_0_ap_fixed_16_6_5_3_0_sigmoid_config9_s_sigmoid_tabkb RTLNAME myproject_sigmoid_ap_fixed_32_18_5_3_0_ap_fixed_16_6_5_3_0_sigmoid_config9_s_sigmoid_tabkb BINDTYPE storage TYPE rom IMPL auto LATENCY 2 ALLOW_PRAGMA 1}
    }
  }
  {SRCNAME myproject MODELNAME myproject RTLNAME myproject IS_TOP 1}
}
