#ifndef DEFINES_H_
#define DEFINES_H_

#include "ap_fixed.h"
#include "ap_int.h"
#include "nnet_utils/nnet_types.h"
#include <cstddef>
#include <cstdio>

// hls-fpga-machine-learning insert numbers
#define N_INPUT_1_1 75
#define N_LAYER_2 64
#define N_LAYER_2 64
#define N_LAYER_4 32
#define N_LAYER_4 32
#define N_LAYER_6 16
#define N_LAYER_6 16
#define N_LAYER_8 1
#define N_LAYER_8 1


// hls-fpga-machine-learning insert layer-precision
typedef ap_fixed<32,16> input_t;
typedef ap_fixed<32,18> hidden_1_accum_t;
typedef ap_fixed<32,18> layer2_t;
typedef ap_fixed<32,18> hidden_1_weight_t;
typedef ap_fixed<32,18> hidden_1_bias_t;
typedef ap_uint<1> layer2_index;
typedef ap_fixed<16,6> layer3_t;
typedef ap_fixed<18,8> hidden_1_relu_table_t;
typedef ap_fixed<32,18> hidden_2_accum_t;
typedef ap_fixed<32,18> layer4_t;
typedef ap_fixed<32,18> hidden_2_weight_t;
typedef ap_fixed<32,18> hidden_2_bias_t;
typedef ap_uint<1> layer4_index;
typedef ap_fixed<16,6> layer5_t;
typedef ap_fixed<18,8> hidden_2_relu_table_t;
typedef ap_fixed<32,18> hidden_3_accum_t;
typedef ap_fixed<32,18> layer6_t;
typedef ap_fixed<32,18> hidden_3_weight_t;
typedef ap_fixed<32,18> hidden_3_bias_t;
typedef ap_uint<1> layer6_index;
typedef ap_fixed<16,6> layer7_t;
typedef ap_fixed<18,8> hidden_3_relu_table_t;
typedef ap_fixed<32,18> output_accum_t;
typedef ap_fixed<32,18> layer8_t;
typedef ap_fixed<32,18> output_weight_t;
typedef ap_fixed<32,18> output_bias_t;
typedef ap_uint<1> layer8_index;
typedef ap_fixed<16,6> result_t;
typedef ap_fixed<18,8> output_sigmoid_table_t;


#endif
