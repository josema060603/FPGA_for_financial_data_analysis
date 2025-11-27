#!/usr/bin/env python3
import sys

# Fixed-point type: ap_fixed<32,16>
W = 32          # total bits
I = 16          # integer bits (including sign)
F = W - I       # fractional bits
SCALE = 1 << F  # 2^F

N_FEATURES = 75


def float_to_fixed32(x: float) -> int:
    """Quantize float x to signed 32-bit 2's complement with F fractional bits."""
    q = int(round(x * SCALE))  # quantized integer

    # Saturate to signed 32-bit range just in case
    min_q = -(1 << (W - 1))
    max_q = (1 << (W - 1)) - 1
    if q < min_q:
        q = min_q
    elif q > max_q:
        q = max_q

    # Return as unsigned 32-bit 2's complement
    return q & ((1 << W) - 1)


def pack_features_to_bus(features):
    """
    Pack N_FEATURES fixed-point words (32-bit each) into a 2400-bit bus:
    feature i -> bits [32*i +: 32]
    """
    bus = 0
    for i, x in enumerate(features):
        word = float_to_fixed32(x)
        bus |= int(word) << (W * i)
    return bus


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} tb_input_features.dat > stimuli.vh", file=sys.stderr)
        sys.exit(1)

    infile = sys.argv[1]

    with open(infile, "r") as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue

            # Parse floats on this line
            parts = line.split()
            vals = [float(x) for x in parts]

            if len(vals) != N_FEATURES:
                print(
                    f"Warning: line {idx} has {len(vals)} values, expected {N_FEATURES}",
                    file=sys.stderr,
                )

            bus = pack_features_to_bus(vals)

            # 2400 bits = 600 hex digits; pad with leading zeros
            hex_str = f"{bus:0600X}"

            # Print as localparam literal
            print(f"localparam [2399:0] VEC{idx} = 2400'h{hex_str};")


if __name__ == "__main__":
    main()
