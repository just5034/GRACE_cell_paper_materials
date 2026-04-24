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

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/crystal_ecal_claude-sonnet-4-20250514_20260309_204537'
energies = [1.0, 5.0, 20.0]
results = {
    "material": "CsI",
    "energy_resolution": {"data_points": {}},
    "shower_containment": {"data_points": {}},
    "moliere_radius": {"data_points": {}}
}

for energy in energies:
    energy_dir = os.path.join(base_dir, f'energy_{energy:.3f}GeV')
    
    # Find CsI files
    events_files = glob.glob(os.path.join(energy_dir, 'csi_*_events.parquet'))
    hits_files = glob.glob(os.path.join(energy_dir, 'csi_*_hits_data.parquet'))
    
    if not events_files or not hits_files:
        continue
        
    events = pd.read_parquet(events_files[0])
    hits = pd.read_parquet(hits_files[0])
    
    # Energy resolution
    mean_edep = events['totalEdep'].mean() / 1000.0  # MeV to GeV
    std_edep = events['totalEdep'].std() / 1000.0
    resolution = std_edep / mean_edep if mean_edep > 0 else 0
    n_events = len(events)
    
    results["energy_resolution"]["data_points"][f"{energy:.3f}"] = {
        "mean_edep_gev": mean_edep,
        "std_edep_gev": std_edep,
        "resolution": resolution,
        "n_events": n_events
    }
    
    # Shower containment
    containment_fraction = mean_edep / energy
    results["shower_containment"]["data_points"][f"{energy:.3f}"] = {
        "containment_fraction": containment_fraction,
        "true_energy_gev": energy,
        "mean_deposited_gev": mean_edep
    }
    
    # Moliere radius calculation
    r_values = np.sqrt(hits['x']**2 + hits['y']**2)
    edep_values = hits['edep']
    
    # Sort by radius
    sorted_indices = np.argsort(r_values)
    r_sorted = r_values.iloc[sorted_indices].values
    edep_sorted = edep_values.iloc[sorted_indices].values
    
    # Cumulative energy fraction
    cumsum_edep = np.cumsum(edep_sorted)
    total_edep = cumsum_edep[-1]
    
    if total_edep > 0:
        frac_contained = cumsum_edep / total_edep
        # Find radius containing 90% of energy
        idx_90 = np.searchsorted(frac_contained, 0.9)
        if idx_90 < len(r_sorted):
            r_90 = r_sorted[idx_90]
        else:
            r_90 = r_sorted[-1]
            
        # Estimate Moliere radius (simplified)
        moliere_radius = r_90 / 3.5  # Approximate scaling
        
        results["moliere_radius"]["data_points"][f"{energy:.3f}"] = {
            "moliere_radius_mm": moliere_radius,
            "r90_mm": r_90,
            "mean_shower_radius_mm": np.average(r_values, weights=edep_values)
        }

# Fit energy resolution
energies_fit = []
resolutions_fit = []
for e_str, data in results["energy_resolution"]["data_points"].items():
    energies_fit.append(float(e_str))
    resolutions_fit.append(data["resolution"])

if len(energies_fit) >= 2:
    energies_fit = np.array(energies_fit)
    resolutions_fit = np.array(resolutions_fit)
    
    def resolution_func(E, a, b, c):
        return np.sqrt((a/np.sqrt(E))**2 + b**2 + (c/E)**2)
    
    try:
        popt, _ = curve_fit(resolution_func, energies_fit, resolutions_fit, 
                           p0=[0.1, 0.01, 0.1], bounds=(0, [1, 0.1, 1]))
        results["energy_resolution"]["fit_parameters"] = {
            "stochastic_term": popt[0],
            "constant_term": popt[1],
            "noise_term": popt[2]
        }
    except:
        results["energy_resolution"]["fit_parameters"] = {
            "stochastic_term": 0.0,
            "constant_term": 0.0,
            "noise_term": 0.0
        }

# Create plots
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))

# Energy resolution plot
energies_plot = sorted([float(e) for e in results["energy_resolution"]["data_points"].keys()])
res_plot = [results["energy_resolution"]["data_points"][f"{e:.3f}"]["resolution"] for e in energies_plot]
ax1.plot(energies_plot, res_plot, 'bo-', label='CsI data')
ax1.set_xlabel('Energy (GeV)')
ax1.set_ylabel('σ/E')
ax1.set_title('CsI Energy Resolution')
ax1.grid(True)
ax1.legend()

# Shower containment plot
cont_plot = [results["shower_containment"]["data_points"][f"{e:.3f}"]["containment_fraction"] for e in energies_plot]
ax2.plot(energies_plot, cont_plot, 'ro-', label='CsI')
ax2.set_xlabel('Energy (GeV)')
ax2.set_ylabel('Containment Fraction')
ax2.set_title('CsI Shower Containment')
ax2.grid(True)
ax2.legend()

# Moliere radius plot
moliere_plot = [results["moliere_radius"]["data_points"][f"{e:.3f}"]["moliere_radius_mm"] for e in energies_plot]
ax3.plot(energies_plot, moliere_plot, 'go-', label='CsI')
ax3.set_xlabel('Energy (GeV)')
ax3.set_ylabel('Molière Radius (mm)')
ax3.set_title('CsI Molière Radius')
ax3.grid(True)
ax3.legend()

plt.tight_layout()
plot_path = os.path.join(base_dir, 'csi_analysis_plots.png')
plt.savefig(plot_path)
plt.close()

results["plots"] = [plot_path]

print(json.dumps(results))