import numpy as np
from scipy.optimize import curve_fit

# Data points
x_values = np.array([100, 120, 125, 175, 200])
y_values = np.array([
    8.053995935122172 + 6.011186643441518,
    10.978048129876455 + 8.245512060324351,
    11.185382628440856 + 8.520979837576548,
    8.614582137266796 + 38.750710519154865,
    7.766799648602803 + 42.81052504380544
])


def log_func(x, a, b):
    return a * np.log(x) + b


popt, pcov = curve_fit(log_func, x_values, y_values)


a, b = popt


x_fit = np.linspace(min(x_values), max(x_values), 200)


y_fit = log_func(x_fit, *popt)


residuals = y_values - log_func(x_values, *popt)


ss_res = np.sum(residuals**2)

ss_tot = np.sum((y_values - np.mean(y_values))**2)

r_squared = 1 - (ss_res / ss_tot)


print(f"The logarithmic model is: y = {a:.4f}ln(x) + {b:.4f}")
print(f"R-squared: {r_squared}")
