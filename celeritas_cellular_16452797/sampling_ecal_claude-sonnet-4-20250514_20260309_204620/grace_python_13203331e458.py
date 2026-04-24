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

# Get all energy directories
energy_dirs = sorted(glob.glob(os.path.join(base_dir, 'energy_*GeV')))

# Extract energy resolution data for config1
energies = []
resolutions = []
mean_edeps = []

for edir in energy_dirs:
    # Find config1 events file
    events_files = glob.glob(os.path.join(edir, 'config1_calorimeter_em_events.parquet'))
    if not events_files:
        continue
    
    # Extract true energy from directory name
    true_e = float(os.path.basename(edir).replace('energy_','').replace('GeV',''))
    
    # Read events data
    events = pd.read_parquet(events_files[0])
    
    # Calculate mean and std of deposited energy
    mean_edep = events['totalEdep'].mean() / 1000.0  # MeV to GeV
    std_edep = events['totalEdep'].std() / 1000.0
    
    # Calculate resolution
    resolution = std_edep / mean_edep if mean_edep > 0 else 0
    
    energies.append(true_e)
    resolutions.append(resolution)
    mean_edeps.append(mean_edep)

# Convert to numpy arrays
energies = np.array(energies)
resolutions = np.array(resolutions)

# Fit resolution vs 1/sqrt(E) to extract stochastic term
# σ/E = a/√E ⊕ b where a is stochastic term, b is constant term
def resolution_func(E, a, b):
    return np.sqrt((a/np.sqrt(E))**2 + b**2)

# Perform fit
popt, pcov = curve_fit(resolution_func, energies, resolutions)
stochastic_term = popt[0]
constant_term = popt[1]

# Calculate sampling fraction
# For config1: 2mm W / 5mm scintillator
sampling_fraction = 5.0 / (2.0 + 5.0)  # scintillator/(W+scintillator)

# Calculate shower containment (fraction of beam energy deposited)
containments = []
for i, true_e in enumerate(energies):
    containment = mean_edeps[i] / true_e if true_e > 0 else 0
    containments.append(containment)

# Create resolution plot
plt.figure(figsize=(8, 6))
x_fit = 1/np.sqrt(energies)
y_fit = resolutions
plt.scatter(x_fit, y_fit, s=100, label='Data')

# Plot fit
x_smooth = np.linspace(min(x_fit), max(x_fit), 100)
E_smooth = 1/x_smooth**2
y_smooth = resolution_func(E_smooth, *popt)
plt.plot(x_smooth, y_smooth, 'r-', label=f'Fit: a={stochastic_term:.3f}, b={constant_term:.3f}')

plt.xlabel('1/√E [GeV^(-1/2)]')
plt.ylabel('σ/E')
plt.title('Config1: Energy Resolution vs 1/√E')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('config1_resolution_fit.png', dpi=150, bbox_inches='tight')
plt.close()

# Create containment plot
plt.figure(figsize=(8, 6))
plt.scatter(energies, containments, s=100)
plt.xlabel('Beam Energy [GeV]')
plt.ylabel('Energy Containment (E_dep/E_beam)')
plt.title('Config1: Shower Containment vs Energy')
plt.grid(True, alpha=0.3)
plt.savefig('config1_containment.png', dpi=150, bbox_inches='tight')
plt.close()

result = {
    "config1_analysis": {
        "stochastic_term": float(stochastic_term),
        "constant_term": float(constant_term),
        "sampling_fraction": float(sampling_fraction),
        "energy_data": {
            f"{e:.1f}GeV": {
                "resolution": float(resolutions[i]),
                "mean_edep_gev": float(mean_edeps[i]),
                "containment": float(containments[i])
            } for i, e in enumerate(energies)
        },
        "plots": ["config1_resolution_fit.png", "config1_containment.png"]
    }
}

print(json.dumps(result))