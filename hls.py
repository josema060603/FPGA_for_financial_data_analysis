import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import load_model
import hls4ml

# --- load your test set (same preprocessing as training) ---
X_test = np.load("prepared/X_test.npy").astype("float32")
y_test = np.load("prepared/y_test.npy").astype("float32")

# --- load the trained model ---
model = load_model('mlp_vnq.h5')

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
cfg['Model']['Strategy'] = 'Latency'
# 2) IO tensor names
in_name  = model.input.name.split(':')[0]
out_name = model.output.name.split(':')[0]

# 3) Measure ranges (for sane fixed-point choices)
X_test = X_test.astype('float32')
y_true = y_test.reshape(-1).astype('float32')
y_pred_keras = model.predict(X_test, verbose=0).reshape(-1)
x_max = float(np.max(np.abs(X_test))) + 1e-9
y_max = float(np.max(np.abs(y_pred_keras))) + 1e-9
print("x_max:", x_max, "y_max:", y_max)

# 4) Widen INPUT; keep OUTPUT reasonable (±32 is fine for y_max≈24)
cfg['LayerName'].setdefault(in_name, {}).setdefault('Precision', {})
cfg['LayerName'][in_name]['Precision']['result'] = 'ap_fixed<16,12>'

cfg['LayerName'].setdefault(out_name, {}).setdefault('Precision', {})
cfg['LayerName'][out_name]['Precision']['result'] = 'ap_fixed<16,6>'
# If you want a one-time sanity: use float and see MAE snap back
# cfg['LayerName'][out_name]['Precision']['result'] = 'float'

# 5) Prevent internal overflow: widen Dense accumulators + pre-activation result
dense_names = [l.name for l in model.layers
               if isinstance(l, QDense) or isinstance(l, keras.layers.Dense)]
for n in dense_names:
    cfg['LayerName'].setdefault(n, {}).setdefault('Precision', {})
    cfg['LayerName'][n]['Precision']['accum']  = 'ap_fixed<24,16>'
    cfg['LayerName'][n]['Precision']['result'] = 'ap_fixed<24,16>'

# 6) Convert, emulate, and check MAE
outdir = os.path.expanduser('~/senior_design_project_v3_housingbased/hls_project')
os.makedirs(outdir, exist_ok=True)

hls_model = hls4ml.converters.convert_from_keras_model(
    model,
    hls_config=cfg,
    backend='Vitis',
    part='xc7z020clg400-1',
    clock_period=100,
    io_type='io_parallel',      # or 'io_stream' if you prefer
    output_dir=outdir
)

hls_model.compile()
y_hls = hls_model.predict(np.ascontiguousarray(X_test)).reshape(-1)
mae = float(np.mean(np.abs(y_hls - y_true)))
print("HLS emu MAE:", mae)
print("y_hls min/max:", float(y_hls.min()), float(y_hls.max()))


# Save into .dat files for C/RTL co-simulation
# --- write tb_data for HLS cosim ---
import os, numpy as np
N = 480  # how many samples to test

# X_test must be the *raw* features your model expects (same ones you use for emu).
Xc = np.ascontiguousarray(X_test[:N], dtype=np.float32)
y_ref = model.predict(Xc, verbose=0).reshape(-1)  # same Keras model you converted

tb_dir = os.path.join("hls4ml_prj", "tb_data")  # OUTDIR_NO_SPACES is your hls4ml_prj folder
os.makedirs(tb_dir, exist_ok=True)

np.savetxt(os.path.join(tb_dir, "tb_input_features.dat"),  Xc,   fmt="%.10e")
np.savetxt(os.path.join(tb_dir, "tb_output_predictions.dat"), y_ref, fmt="%.10e")

print("Wrote tb_data to:", tb_dir)