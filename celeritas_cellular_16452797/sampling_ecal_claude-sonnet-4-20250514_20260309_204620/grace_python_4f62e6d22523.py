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
energies = sorted(glob.glob(os.path.join(base_dir, 'energy_*GeV')))

# Analyze Config 2
config2_results = {}
energy_points = []
resolution_points = []
mean_edep_points = []

for edir in energies:
    events_files = glob.glob(os.path.join(edir, 'config2_calorimeter_em_events.parquet'))
    if not events_files:
        continue
    
    events_file = events_files[0]
    true_e = float(os.path.basename(edir).replace('energy_','').replace('GeV',''))
    events = pd.read_parquet(events_file)
    
    mean_edep = events['totalEdep'].mean() / 1000.0  # MeV→GeV
    std_edep = events['totalEdep'].std() / 1000.0
    resolution = std_edep / mean_edep if mean_edep > 0 else 0
    containment = mean_edep / true_e
    
    config2_results[f'{true_e}GeV'] = {
        'resolution': resolution,
        'mean_edep_gev': mean_edep,
        'containment': containment
    }
    
    energy_points.append(true_e)
    resolution_points.append(resolution)
    mean_edep_points.append(mean_edep)

# Fit resolution vs energy to extract stochastic term
def resolution_func(E, a, b):
    return np.sqrt((a/np.sqrt(E))**2 + b**2)

energy_points = np.array(energy_points)
resolution_points = np.array(resolution_points)

popt, pcov = curve_fit(resolution_func, energy_points, resolution_points)
stochastic_term = popt[0]
constant_term = popt[1]

# Calculate sampling fraction for Config 2
# Config 2: 3.5mm W + 2mm plastic = 5.5mm per layer
sampling_fraction = 2.0 / 5.5

# Create resolution plot
plt.figure(figsize=(8, 6))
plt.scatter(energy_points, resolution_points, s=100, label='Config 2 Data', color='red')
E_fit = np.linspace(0.5, 25, 100)
plt.plot(E_fit, resolution_func(E_fit, *popt), 'r--', 
         label=f'Fit: {stochastic_term:.1%}/√E ⊕ {constant_term:.1%}')
plt.xlabel('Beam Energy (GeV)')
plt.ylabel('Energy Resolution (σ/E)')
plt.title('Config 2: Energy Resolution vs Beam Energy')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig(os.path.join(base_dir, 'config2_resolution.png'), dpi=150, bbox_inches='tight')
plt.close()

result = {
    "config2_analysis": {
        "stochastic_term": stochastic_term,
        "constant_term": constant_term,
        "sampling_fraction": sampling_fraction,
        "energy_data": config2_results,
        "resolution_plot": "config2_resolution.png"
    }
}

print(json.dumps(result))