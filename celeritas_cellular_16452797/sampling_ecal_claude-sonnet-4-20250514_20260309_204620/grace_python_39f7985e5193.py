import json as _json_orig
class _NumpySafeEncoder(_json_orig.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'tolist') and hasattr(obj, 'shape'):
            if getattr(obj, 'ndim', 0) > 0:
                return obj.tolist()
            return obj.item()
        if hasattr(obj, 'item'):
            return obj.item()
        return super().default(obj)
_orig_dumps = _json_orig.dumps
def _safe_dumps(*args, **kwargs):
    kwargs.setdefault('cls', _NumpySafeEncoder)
    return _orig_dumps(*args, **kwargs)
_json_orig.dumps = _safe_dumps
import matplotlib
matplotlib.use('Agg')
import pandas as pd
import numpy as np
import json
import glob
import os
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/sampling_ecal_claude-sonnet-4-20250514_20260309_204620'

# Get energy directories
energy_dirs = sorted(glob.glob(os.path.join(base_dir, 'energy_*GeV')))

# Analyze Config1
results = []
energies_gev = []
resolutions = []
sampling_fractions = []

for edir in energy_dirs:
    # Find config1 events file
    events_files = glob.glob(os.path.join(edir, 'config1_calorimeter_em_events.parquet'))
    if not events_files:
        continue
    
    events_file = events_files[0]
    true_e = float(os.path.basename(edir).replace('energy_','').replace('GeV',''))
    
    # Read events data
    events = pd.read_parquet(events_file)
    
    # Calculate energy resolution
    mean_edep = events['totalEdep'].mean() / 1000.0  # MeV to GeV
    std_edep = events['totalEdep'].std() / 1000.0
    resolution = std_edep / mean_edep if mean_edep > 0 else 0
    
    # Calculate sampling fraction
    sampling_fraction = mean_edep / true_e
    
    energies_gev.append(true_e)
    resolutions.append(resolution)
    sampling_fractions.append(sampling_fraction)
    
    results.append({
        'energy_gev': true_e,
        'mean_edep_gev': mean_edep,
        'std_edep_gev': std_edep,
        'resolution': resolution,
        'sampling_fraction': sampling_fraction
    })

# Fit resolution vs 1/sqrt(E) to extract stochastic term
def resolution_func(x, a, b, c):
    # σ/E = a/√E ⊕ b ⊕ c/E (quadrature sum)
    return np.sqrt(a**2 * x**2 + b**2 + c**2 * x**4)

x_data = 1.0 / np.sqrt(energies_gev)
y_data = np.array(resolutions)

# Initial guess: stochastic ~10%, constant ~1%, noise ~1%
p0 = [0.1, 0.01, 0.01]
popt, pcov = curve_fit(resolution_func, x_data, y_data, p0=p0)
stochastic_term = popt[0]
constant_term = popt[1]
noise_term = popt[2]

# Calculate shower containment from highest energy point
containment = np.mean(sampling_fractions)

# Create resolution plot
plt.figure(figsize=(8, 6))
plt.scatter(x_data, y_data, s=100, label='Data', color='blue')
x_fit = np.linspace(min(x_data)*0.9, max(x_data)*1.1, 100)
y_fit = resolution_func(x_fit, *popt)
plt.plot(x_fit, y_fit, 'r-', label=f'Fit: {stochastic_term:.3f}/√E ⊕ {constant_term:.3f} ⊕ {noise_term:.3f}/E')
plt.xlabel('1/√E (GeV^{-1/2})')
plt.ylabel('σ/E')
plt.title('Configuration 1: Energy Resolution vs 1/√E')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('config1_resolution_fit.png', dpi=150, bbox_inches='tight')
plt.close()

# Create sampling fraction plot
plt.figure(figsize=(8, 6))
plt.scatter(energies_gev, sampling_fractions, s=100, color='green')
plt.axhline(y=containment, color='red', linestyle='--', label=f'Mean: {containment:.3f}')
plt.xlabel('Beam Energy (GeV)')
plt.ylabel('Sampling Fraction')
plt.title('Configuration 1: Sampling Fraction vs Energy')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('config1_sampling_fraction.png', dpi=150, bbox_inches='tight')
plt.close()

# Calculate sampling fraction from geometry (2mm W + 3mm plastic)
geometric_sampling_fraction = 3.0 / (2.0 + 3.0)

result = {
    'config1_analysis': {
        'energy_resolution_data': results,
        'stochastic_term': stochastic_term,
        'constant_term': constant_term,
        'noise_term': noise_term,
        'mean_sampling_fraction': containment,
        'geometric_sampling_fraction': geometric_sampling_fraction,
        'shower_containment': containment / geometric_sampling_fraction,
        'plots': ['config1_resolution_fit.png', 'config1_sampling_fraction.png']
    }
}

print(json.dumps(result))