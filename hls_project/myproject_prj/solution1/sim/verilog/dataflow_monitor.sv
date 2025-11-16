
`include "dump_file_agent.svh"
`include "csv_file_dump.svh"
`include "sample_agent.svh"
`include "sample_manager.svh"
`include "nodf_module_interface.svh"
`include "nodf_module_monitor.svh"
`timescale 1ns/1ps

// top module for dataflow related monitors
module dataflow_monitor(
input logic clock,
input logic reset,
input logic finish
);




    nodf_module_intf module_intf_1(clock,reset);
    assign module_intf_1.ap_start = AESL_inst_myproject.ap_start;
    assign module_intf_1.ap_ready = AESL_inst_myproject.ap_ready;
    assign module_intf_1.ap_done = AESL_inst_myproject.ap_done;
    assign module_intf_1.ap_continue = 1'b1;
    assign module_intf_1.finish = finish;
    csv_file_dump mstatus_csv_dumper_1;
    nodf_module_monitor module_monitor_1;
    nodf_module_intf module_intf_2(clock,reset);
    assign module_intf_2.ap_start = AESL_inst_myproject.grp_dense_latency_ap_fixed_32_16_5_3_0_ap_fixed_32_18_5_3_0_config2_s_fu_57.ap_start;
    assign module_intf_2.ap_ready = AESL_inst_myproject.grp_dense_latency_ap_fixed_32_16_5_3_0_ap_fixed_32_18_5_3_0_config2_s_fu_57.ap_ready;
    assign module_intf_2.ap_done = AESL_inst_myproject.grp_dense_latency_ap_fixed_32_16_5_3_0_ap_fixed_32_18_5_3_0_config2_s_fu_57.ap_done;
    assign module_intf_2.ap_continue = 1'b1;
    assign module_intf_2.finish = finish;
    csv_file_dump mstatus_csv_dumper_2;
    nodf_module_monitor module_monitor_2;
    nodf_module_intf module_intf_3(clock,reset);
    assign module_intf_3.ap_start = 1'b0;
    assign module_intf_3.ap_ready = AESL_inst_myproject.call_ret2_relu_ap_fixed_32_18_5_3_0_ap_fixed_16_6_5_3_0_relu_config3_s_fu_63.ap_ready;
    assign module_intf_3.ap_done = 1'b0;
    assign module_intf_3.ap_continue = 1'b0;
    assign module_intf_3.finish = finish;
    csv_file_dump mstatus_csv_dumper_3;
    nodf_module_monitor module_monitor_3;
    nodf_module_intf module_intf_4(clock,reset);
    assign module_intf_4.ap_start = AESL_inst_myproject.grp_dense_latency_ap_fixed_16_6_5_3_0_ap_fixed_32_18_5_3_0_config4_s_fu_131.ap_start;
    assign module_intf_4.ap_ready = AESL_inst_myproject.grp_dense_latency_ap_fixed_16_6_5_3_0_ap_fixed_32_18_5_3_0_config4_s_fu_131.ap_ready;
    assign module_intf_4.ap_done = AESL_inst_myproject.grp_dense_latency_ap_fixed_16_6_5_3_0_ap_fixed_32_18_5_3_0_config4_s_fu_131.ap_done;
    assign module_intf_4.ap_continue = 1'b1;
    assign module_intf_4.finish = finish;
    csv_file_dump mstatus_csv_dumper_4;
    nodf_module_monitor module_monitor_4;
    nodf_module_intf module_intf_5(clock,reset);
    assign module_intf_5.ap_start = 1'b0;
    assign module_intf_5.ap_ready = AESL_inst_myproject.call_ret4_relu_ap_fixed_32_18_5_3_0_ap_fixed_16_6_5_3_0_relu_config5_s_fu_199.ap_ready;
    assign module_intf_5.ap_done = 1'b0;
    assign module_intf_5.ap_continue = 1'b0;
    assign module_intf_5.finish = finish;
    csv_file_dump mstatus_csv_dumper_5;
    nodf_module_monitor module_monitor_5;
    nodf_module_intf module_intf_6(clock,reset);
    assign module_intf_6.ap_start = AESL_inst_myproject.grp_dense_latency_ap_fixed_16_6_5_3_0_ap_fixed_32_18_5_3_0_config6_s_fu_235.ap_start;
    assign module_intf_6.ap_ready = AESL_inst_myproject.grp_dense_latency_ap_fixed_16_6_5_3_0_ap_fixed_32_18_5_3_0_config6_s_fu_235.ap_ready;
    assign module_intf_6.ap_done = AESL_inst_myproject.grp_dense_latency_ap_fixed_16_6_5_3_0_ap_fixed_32_18_5_3_0_config6_s_fu_235.ap_done;
    assign module_intf_6.ap_continue = 1'b1;
    assign module_intf_6.finish = finish;
    csv_file_dump mstatus_csv_dumper_6;
    nodf_module_monitor module_monitor_6;
    nodf_module_intf module_intf_7(clock,reset);
    assign module_intf_7.ap_start = 1'b0;
    assign module_intf_7.ap_ready = AESL_inst_myproject.call_ret6_relu_ap_fixed_32_18_5_3_0_ap_fixed_16_6_5_3_0_relu_config7_s_fu_271.ap_ready;
    assign module_intf_7.ap_done = 1'b0;
    assign module_intf_7.ap_continue = 1'b0;
    assign module_intf_7.finish = finish;
    csv_file_dump mstatus_csv_dumper_7;
    nodf_module_monitor module_monitor_7;
    nodf_module_intf module_intf_8(clock,reset);
    assign module_intf_8.ap_start = AESL_inst_myproject.grp_dense_latency_ap_fixed_16_6_5_3_0_ap_fixed_32_18_5_3_0_config8_s_fu_291.ap_start;
    assign module_intf_8.ap_ready = AESL_inst_myproject.grp_dense_latency_ap_fixed_16_6_5_3_0_ap_fixed_32_18_5_3_0_config8_s_fu_291.ap_ready;
    assign module_intf_8.ap_done = AESL_inst_myproject.grp_dense_latency_ap_fixed_16_6_5_3_0_ap_fixed_32_18_5_3_0_config8_s_fu_291.ap_done;
    assign module_intf_8.ap_continue = 1'b1;
    assign module_intf_8.finish = finish;
    csv_file_dump mstatus_csv_dumper_8;
    nodf_module_monitor module_monitor_8;
    nodf_module_intf module_intf_9(clock,reset);
    assign module_intf_9.ap_start = AESL_inst_myproject.grp_sigmoid_ap_fixed_32_18_5_3_0_ap_fixed_16_6_5_3_0_sigmoid_config9_s_fu_311.ap_start;
    assign module_intf_9.ap_ready = AESL_inst_myproject.grp_sigmoid_ap_fixed_32_18_5_3_0_ap_fixed_16_6_5_3_0_sigmoid_config9_s_fu_311.ap_ready;
    assign module_intf_9.ap_done = AESL_inst_myproject.grp_sigmoid_ap_fixed_32_18_5_3_0_ap_fixed_16_6_5_3_0_sigmoid_config9_s_fu_311.ap_done;
    assign module_intf_9.ap_continue = 1'b1;
    assign module_intf_9.finish = finish;
    csv_file_dump mstatus_csv_dumper_9;
    nodf_module_monitor module_monitor_9;


    sample_manager sample_manager_inst;

initial begin
    sample_manager_inst = new;



    mstatus_csv_dumper_1 = new("./module_status1.csv");
    module_monitor_1 = new(module_intf_1,mstatus_csv_dumper_1);
    mstatus_csv_dumper_2 = new("./module_status2.csv");
    module_monitor_2 = new(module_intf_2,mstatus_csv_dumper_2);
    mstatus_csv_dumper_3 = new("./module_status3.csv");
    module_monitor_3 = new(module_intf_3,mstatus_csv_dumper_3);
    mstatus_csv_dumper_4 = new("./module_status4.csv");
    module_monitor_4 = new(module_intf_4,mstatus_csv_dumper_4);
    mstatus_csv_dumper_5 = new("./module_status5.csv");
    module_monitor_5 = new(module_intf_5,mstatus_csv_dumper_5);
    mstatus_csv_dumper_6 = new("./module_status6.csv");
    module_monitor_6 = new(module_intf_6,mstatus_csv_dumper_6);
    mstatus_csv_dumper_7 = new("./module_status7.csv");
    module_monitor_7 = new(module_intf_7,mstatus_csv_dumper_7);
    mstatus_csv_dumper_8 = new("./module_status8.csv");
    module_monitor_8 = new(module_intf_8,mstatus_csv_dumper_8);
    mstatus_csv_dumper_9 = new("./module_status9.csv");
    module_monitor_9 = new(module_intf_9,mstatus_csv_dumper_9);





    sample_manager_inst.add_one_monitor(module_monitor_1);
    sample_manager_inst.add_one_monitor(module_monitor_2);
    sample_manager_inst.add_one_monitor(module_monitor_3);
    sample_manager_inst.add_one_monitor(module_monitor_4);
    sample_manager_inst.add_one_monitor(module_monitor_5);
    sample_manager_inst.add_one_monitor(module_monitor_6);
    sample_manager_inst.add_one_monitor(module_monitor_7);
    sample_manager_inst.add_one_monitor(module_monitor_8);
    sample_manager_inst.add_one_monitor(module_monitor_9);
    
    fork
        sample_manager_inst.start_monitor();
        last_transaction_done;
    join
    disable fork;

    sample_manager_inst.start_dump();
end

    task last_transaction_done();
        wait(reset == 0);
        while(1) begin
            if (finish == 1'b1) begin
                @(negedge clock);
                break;
            end
            else
                @(posedge clock);
        end
    endtask


endmodule
