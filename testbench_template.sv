// timescale nonsense
`timescale 1ps/1ps
// translate clock period to ps from ns
// macro shit maybe
// 1ns = 1000ps
// #1 = 1ns

module testbench ();

    clock,


    // module instantiation -- has to be generated

    // testing: might be able to
    // 1. run input, get "correct output" (no bitflip)
    // 2.
    //      a. sample in python, pass output of samples to testbench
    //      b. read in sample data, use to index, bitflip, time, etc.
    // 3. compare results, timing data whatever
    // 4. output in some reasonable way, or aggregate and output aggregations, counters of correct vs. timing masked vs whatever the fuck else


endmodule