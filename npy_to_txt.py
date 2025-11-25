import numpy as np

FRAC_BITS = 16
SCALE = 1 << FRAC_BITS  # 2^16
INT_MIN = -2**31
INT_MAX =  2**31 - 1

def float_to_ap_fixed_32_16(x: float) -> int:
    """
    Convert Python float to ap_fixed<32,16> stored as signed 32-bit int.
    """
    q = int(round(x * SCALE))

    # Saturate to signed 32-bit range
    if q < INT_MIN:
        q = INT_MIN
    elif q > INT_MAX:
        q = INT_MAX

    return q

def ap_fixed_32_16_to_hex(x: float) -> str:
    """
    Convert Python float to 8-hex-digit two's-complement string.
    """
    q = float_to_ap_fixed_32_16(x)
    u = q & 0xFFFFFFFF         # unsigned view for hex
    return f"{u:08X}"
# 1) Load your data
X = np.load("prepared/X_test.npy")   # shape: (N, 75) expected

print("Shape of X:", X.shape)

# 2) Convert each sample to one 2400-bit Verilog literal
with open("stimuli_2400bit.txt", "w") as f:
    for sample in X:
        # sample: shape (75,)
        assert sample.shape[0] == 75, "Expected 75 features per sample"

        # Convert each feature to hex word (feature[0] .. feature[74])
        words = [ap_fixed_32_16_to_hex(float(v)) for v in sample]

        # HLS flattens as:
        # feature[0] -> bits [31:0]
        # feature[1] -> bits [63:32]
        # ...
        # feature[74] -> bits [2399:2368]
        #
        # In a single literal, the *leftmost* hex is the MSB,
        # so we put feature[74] first, feature[0] last:
        bus_hex = ''.join(reversed(words))

        verilog_literal = f"2400'h{bus_hex}"
        f.write(verilog_literal + "\n")
        
with open("stimuli_words.txt", "w") as f:
    for sample in X:
        words = [ap_fixed_32_16_to_hex(float(v)) for v in sample]
        f.write(' '.join(words) + "\n")
