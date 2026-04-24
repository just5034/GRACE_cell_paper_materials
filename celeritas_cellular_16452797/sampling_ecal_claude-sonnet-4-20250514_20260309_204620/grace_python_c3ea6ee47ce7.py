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
import xml.etree.ElementTree as ET

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/sampling_ecal_claude-sonnet-4-20250514_20260309_204620'

# Parse GDML to get layer thicknesses
gdml_file = os.path.join(base_dir, 'config1_calorimeter.gdml')
tree = ET.parse(gdml_file)
root = tree.getroot()

# Extract layer thicknesses from GDML
tungsten_thickness = None
scintillator_thickness = None
for solid in root.findall(".//{http://cern.ch/2001/Schemas/GDML}box"):
    name = solid.get('name')
    if 'Tungsten' in name:
        tungsten_thickness = float(solid.get('z')) / 10.0  # mm to cm
    elif 'Scintillator' in name:
        scintillator_thickness = float(solid.get('z')) / 10.0  # mm to cm

# Calculate sampling fraction
sampling_fraction = scintillator_thickness / (tungsten_thickness + scintillator_thickness)

# Analyze energy resolution for all energies
energy_dirs = sorted(glob.glob(os.path.join(base_dir, 'energy_*GeV')))
energies = []
resolutions = []
mean_edeps = []

for edir in energy_dirs:
    events_files = glob.glob(os.path.join(edir, 'config1_calorimeter_em_events.parquet'))
    if not events_files:
        continue
    
    events_file = events_files[0]
    true_e = float(os.path.basename(edir).replace('energy_','').replace('GeV',''))
    
    events = pd.read_parquet(events_file)
    mean_edep = events['totalEdep'].mean() / 1000.0  # MeV to GeV
    std_edep = events['totalEdep'].std() / 1000.0
    resolution = std_edep / mean_edep if mean_edep > 0 else 0
    
    energies.append(true_e)
    resolutions.append(resolution)
    mean_edeps.append(mean_edep)

# Fit σ/E vs 1/√E to extract stochastic term
def resolution_fit(x, a, b, c):
    return np.sqrt(a**2 / x + b**2 + c**2 * x)

x_data = np.array(energies)
y_data = np.array(resolutions)

# Initial guess for a (stochastic), b (constant), c (noise)
p0 = [0.1, 0.01, 0.001]
popt, pcov = curve_fit(resolution_fit, x_data, y_data, p0=p0)
stochastic_term = popt[0]
constant_term = popt[1]
noise_term = popt[2]

# Calculate shower containment (fraction of beam energy deposited)
containment = [mean_edeps[i] / energies[i] for i in range(len(energies))]

# Create resolution plot
plt.figure(figsize=(10, 6))
x_fit = np.linspace(0.5, 25, 100)
y_fit = resolution_fit(x_fit, *popt)

plt.scatter(1/np.sqrt(energies), resolutions, s=100, label='Data', color='blue')
plt.plot(1/np.sqrt(x_fit), y_fit, 'r-', label=f'Fit: a={stochastic_term:.3f}, b={constant_term:.3f}, c={noise_term:.3f}')
plt.xlabel('1/√E [GeV^(-1/2)]')
plt.ylabel('σ/E')
plt.title('Configuration 1: Energy Resolution vs 1/√E')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig(os.path.join(base_dir, 'config1_resolution_fit.png'), dpi=150, bbox_inches='tight')
plt.close()

# Create containment plot
plt.figure(figsize=(10, 6))
plt.plot(energies, containment, 'bo-', markersize=10, linewidth=2)
plt.xlabel('Beam Energy [GeV]')
plt.ylabel('Energy Containment Fraction')
plt.title('Configuration 1: Shower Containment vs Beam Energy')
plt.grid(True, alpha=0.3)
plt.ylim(0, 1.1)
plt.savefig(os.path.join(base_dir, 'config1_containment.png'), dpi=150, bbox_inches='tight')
plt.close()

result = {
    "config1_analysis": {
        "tungsten_thickness_cm": tungsten_thickness,
        "scintillator_thickness_cm": scintillator_thickness,
        "sampling_fraction": sampling_fraction,
        "stochastic_term": stochastic_term,
        "constant_term": constant_term,
        "noise_term": noise_term,
        "energy_resolution_data": {
            f"{e:.1f}GeV": {
                "resolution": resolutions[i],
                "mean_edep_gev": mean_edeps[i],
                "containment": containment[i]
            } for i, e in enumerate(energies)
        },
        "plots": [
            os.path.join(base_dir, "config1_resolution_fit.png"),
            os.path.join(base_dir, "config1_containment.png")
        ]
    }
}

print(json.dumps(result))