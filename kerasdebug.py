import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
import joblib
import numpy as np

print("TF version:", tf.__version__)

def build_mlp_model(input_dim):
    """Build the neural network - 3 hidden layers with dropout to prevent overfitting."""
    print(f"\nBuilding MLP model with input dimension: {input_dim}")
    
    model = Sequential([
        Dense(64, activation='relu', input_dim=input_dim, name='hidden_1'),
        Dropout(0.3, name='dropout_1'),
        Dense(32, activation='relu', name='hidden_2'),
        Dropout(0.2, name='dropout_2'),
        Dense(16, activation='relu', name='hidden_3'),
        Dropout(0.2, name='dropout_3'),
        Dense(1, activation='sigmoid', name='output')
    ])
    
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model
results_file="results_2015.txt"
X_test = np.load("prepared/X_test.npy").astype("float32")
y_test = np.load("prepared/y_test.npy").astype("float32")
# 1) Rebuild the architecture with the SAME input_dim as original
INPUT_DIM = 75  # from batch_shape [None, 75]
model = build_mlp_model(INPUT_DIM)

# 2) Load weights from the H5 file
model.load_weights("mlp_vnq.h5")

# 3) Load the scaler
scaler = joblib.load("scaler_vnq.pkl")

# Choose to scale or not

X_scaled = scaler.transform(X_test)

# X_scaled = X_test

print("\nModel and scaler loaded successfully!")
model.summary()


# --- put this AFTER you've loaded `model`, `X_test`, `y_test` ---
import os, math, numpy as np
from tensorflow import keras
from qkeras import QDense
import hls4ml

# 1) Start from auto config
cfg = hls4ml.utils.config_from_keras_model(model, granularity='name')
cfg['Model']['ReuseFactor'] = 32  # default for any layer not overridden
cfg['LayerName']['hidden_1']['ReuseFactor'] = 32   # 1536/32 ≈ 48 parallel mult
cfg['LayerName']['hidden_2']['ReuseFactor'] = 32   # 2048/64 ≈ 32 parallel mult
cfg['Model']['Strategy'] = 'Resource'
# 2) IO tensor names
in_name  = model.input.name.split(':')[0]
out_name = model.output.name.split(':')[0]

print("Model expects:", model.input_shape)   # should print (None, 75)
print("X_test shape:", X_scaled.shape)

# 3) Check keras model
X_scaled = X_scaled.astype('float32')
y_true = y_test
y_pred_keras_raw = model.predict(X_scaled, verbose=0).reshape(-1)


y_pred_keras = (y_pred_keras_raw > 0.5).astype(int).flatten()  # convert to 0 or 1
mae = float(np.mean(np.abs(y_pred_keras - y_true)))
correct_mask = (y_pred_keras == y_true)          
num_correct = int(np.sum(correct_mask))     
total = len(y_true)                         
accuracy = num_correct / total              

print("Keras emu MAE:", mae)
print("y_keras min/max:", float(y_pred_keras_raw.min()), float(y_pred_keras_raw.max()))
print("Keras emu accuracy:", accuracy)

# with open(results_file, "w") as f:   # use "a" instead of "w" if you want to append
#     print("Keras emu MAE:", mae, file=f)
#     print("y_keras min/max:", float(y_pred_keras_raw.min()), float(y_pred_keras_raw.max()), file=f)
#     print("Keras emu accuracy:", accuracy, file=f)

# 4) Widen INPUT; keep OUTPUT reasonable (±32 is fine for y_max≈24)
cfg['LayerName'].setdefault(in_name, {}).setdefault('Precision', {})
cfg['LayerName'][in_name]['Precision']['result'] = "ap_fixed<32,16>"

cfg['LayerName'].setdefault(out_name, {}).setdefault('Precision', {})
cfg['LayerName'][out_name]['Precision']['result'] ="ap_fixed<32,20>"
# If you want a one-time sanity: use float and see MAE snap back
# cfg['LayerName'][out_name]['Precision']['result'] = 'float'

layer_precision_select ="ap_fixed<32,18>"
# 5) Prevent internal overflow: widen Dense accumulators + pre-activation result
dense_names = [l.name for l in model.layers
               if isinstance(l, QDense) or isinstance(l, keras.layers.Dense)]
for n in dense_names:
    cfg['LayerName'].setdefault(n, {}).setdefault('Precision', {})
    cfg['LayerName'][n]['Precision']['accum']  = layer_precision_select
    cfg['LayerName'][n]['Precision']['result'] = layer_precision_select
    cfg['LayerName'][n]['Precision']['bias'] = layer_precision_select
    cfg['LayerName'][n]['Precision']['weight'] = layer_precision_select

# 6) Convert, emulate, and check MAE
outdir = os.path.expanduser('~/senior_design_project_v3_housingbased/hls_project_resource')
os.makedirs(outdir, exist_ok=True)

hls_model = hls4ml.converters.convert_from_keras_model(
    model,
    hls_config=cfg,
    backend='Vitis',
    part='xc7z020clg400-1',
    clock_period=10,
    io_type='io_parallel',      # or 'io_stream' if you prefer
    output_dir=outdir
)

hls_model.compile()
y_hls = hls_model.predict(np.ascontiguousarray(X_scaled)).reshape(-1)
y_pred = (y_hls > 0.5).astype(int).flatten()  # convert to 0 or 1
mae = float(np.mean(np.abs(y_pred - y_true)))
correct_mask = (y_pred == y_true)          
num_correct = int(np.sum(correct_mask))     
total = len(y_true)                         
accuracy = num_correct / total              

print("HLS emu MAE:", mae)
print("y_hls min/max:", float(y_hls.min()), float(y_hls.max()))
print("HLS emu accuracy:", accuracy)

# with open(results_file, "a") as f:  # "a" = append, use "w" to overwrite
#     print("HLS emu MAE:", mae, file=f)
#     print("y_hls min/max:", float(y_hls.min()), float(y_hls.max()), file=f)
#     print("HLS emu accuracy:", accuracy, file=f)


# Save into .dat files for C/RTL co-simulation
# --- write tb_data for HLS cosim ---
import os, numpy as np
# N = 400  # how many samples to test

# X_test must be the *raw* features your model expects (same ones you use for emu).
# Xc = np.ascontiguousarray(X_scaled, dtype=np.float32)
# y_ref = model.predict(Xc, verbose=1).reshape(-1)  # same Keras model you converted
# y_ref_prediction = (y_ref > 0.5).astype(int).flatten()  # convert to 0 or 1

# tb_dir1 = os.path.join("hls_project", "tb_data")  # OUTDIR_NO_SPACES is your hls4ml_prj folder

# tb_dir2 = os.path.join("self_check", "tb_data_2015")  # OUTDIR_NO_SPACES is your hls4ml_prj folder
# os.makedirs(tb_dir1, exist_ok=True)
# os.makedirs(tb_dir2, exist_ok=True)

# np.savetxt(os.path.join(tb_dir1, "tb_input_features.dat"),  Xc,   fmt="%.10e")
# np.savetxt(os.path.join(tb_dir1, "tb_output_predictions.dat"), y_hls, fmt="%.10e")

# np.savetxt(os.path.join(tb_dir2, "tb_input_features.dat"),  Xc,   fmt="%.10e")
# np.savetxt(os.path.join(tb_dir2, "tb_output_features.dat"),  y_ref_prediction,   fmt="%.10e")


# print("Wrote tb_data to:", tb_dir1)
