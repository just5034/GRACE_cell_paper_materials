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
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/sampling_ecal_claude-sonnet-4-20250514_20260309_204620'

# Configuration 3 parameters
tungsten_thickness = 5.0  # mm
scintillator_thickness = 2.0  # mm
sampling_fraction = scintillator_thickness / (tungsten_thickness + scintillator_thickness)

# Analyze energy resolution for config3
energies_gev = []
resolutions = []
mean_edeps = []
containments = []

energy_dirs = sorted(glob.glob(os.path.join(base_dir, 'energy_*GeV')))

for edir in energy_dirs:
    # Find config3 events file
    events_files = glob.glob(os.path.join(edir, 'config3_calorimeter_em_events.parquet'))
    if not events_files:
        continue
    
    events_file = events_files[0]
    true_e = float(os.path.basename(edir).replace('energy_','').replace('GeV',''))
    
    events = pd.read_parquet(events_file)
    mean_edep = events['totalEdep'].mean() / 1000.0  # MeV to GeV
    std_edep = events['totalEdep'].std() / 1000.0
    resolution = std_edep / mean_edep if mean_edep > 0 else 0
    containment = mean_edep / true_e
    
    energies_gev.append(true_e)
    resolutions.append(resolution)
    mean_edeps.append(mean_edep)
    containments.append(containment)

# Fit resolution vs energy to extract stochastic term
def resolution_fit(E, a, b):
    return np.sqrt((a/np.sqrt(E))**2 + b**2)

energies_arr = np.array(energies_gev)
resolutions_arr = np.array(resolutions)

popt, pcov = curve_fit(resolution_fit, energies_arr, resolutions_arr)
stochastic_term = popt[0]
constant_term = popt[1]

# Create plot
plt.figure(figsize=(8, 6))
E_fit = np.linspace(0.5, 25, 100)
plt.scatter(energies_arr, resolutions_arr, s=100, label='Config3 Data', color='green')
plt.plot(E_fit, resolution_fit(E_fit, *popt), 'g-', 
         label=f'Fit: {stochastic_term:.1%}/√E ⊕ {constant_term:.1%}')
plt.xlabel('Beam Energy (GeV)')
plt.ylabel('Energy Resolution (σ/E)')
plt.title('Config3: Energy Resolution vs Beam Energy')
plt.legend()
plt.grid(True, alpha=0.3)
plt.xlim(0, 25)
plt.ylim(0, max(resolutions_arr) * 1.2)
plot_file = os.path.join(base_dir, 'config3_resolution_fit.png')
plt.savefig(plot_file, dpi=150, bbox_inches='tight')
plt.close()

# Prepare energy data dictionary
energy_data = {}
for i, e in enumerate(energies_gev):
    energy_data[f'{e}GeV'] = {
        'resolution': resolutions[i],
        'mean_edep_gev': mean_edeps[i],
        'containment': containments[i]
    }

result = {
    'config3_analysis': {
        'stochastic_term': stochastic_term,
        'constant_term': constant_term,
        'sampling_fraction': sampling_fraction,
        'energy_data': energy_data,
        'resolution_plot': plot_file
    }
}

print(json.dumps(result))