import numpy as np

# Given empirical x and y data points
x_data = np.array([10, 20, 30, 40, 50, 60])
y_data = np.array([0.25, 0.45, 0.8, 1.5, 2, 2.8])


a, b, c = coefficients

p = np.poly1d(coefficients)


y_pred = p(x_data)


y_mean = np.mean(y_data)


ss_tot = np.sum((y_data - y_mean)**2)


ss_res = np.sum((y_data - y_pred)**2)


r_squared = 1 - (ss_res / ss_tot)

print(f"Derived coefficients:\na = {a}\nb = {b}\nc = {c}\n")
print(f"R-squared value: {r_squared}")
