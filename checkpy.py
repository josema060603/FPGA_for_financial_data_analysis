import numpy as np

# Load arrays
X = np.load("prepared/X_test.npy")
y = np.load("prepared/y_test.npy")

print("X_tr shape:", X.shape)
print("y_tr shape:", y.shape)

# Print first 5 rows of features
# print("First rows of X_tr:\n", X[101:102])

# Print first 5 targets
print("First targets of y_tr:\n", y[101:110])
