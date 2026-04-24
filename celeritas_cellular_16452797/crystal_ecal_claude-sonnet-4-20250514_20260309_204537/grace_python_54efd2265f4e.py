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
import matplotlib.pyplot as plt
import json
import glob
import os
from scipy.optimize import curve_fit

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/crystal_ecal_claude-sonnet-4-20250514_20260309_204537'

# Material properties with explicit depth_radiation_lengths
materials = {
    'pbwo4': {'X0_cm': 0.89, 'depth_radiation_lengths': 20.0, 'color': 'blue', 'label': 'PbWO₄'},
    'bgo': {'X0_cm': 1.12, 'depth_radiation_lengths': 20.0, 'color': 'red', 'label': 'BGO'},
    'csi': {'X0_cm': 1.85, 'depth_radiation_lengths': 20.0, 'color': 'green', 'label': 'CsI'}
}

# Energy directories
energy_dirs = ['energy_1.000GeV', 'energy_5.000GeV', 'energy_20.000GeV']
energies = [1.0, 5.0, 20.0]

# Collect resolution data
resolution_data = {}

for mat_key, mat_info in materials.items():
    resolution_data[mat_key] = {'energies': [], 'resolutions': [], 'mean_edep': []}
    
    for edir, energy in zip(energy_dirs, energies):
        events_pattern = os.path.join(base_dir, edir, f'*{mat_key}*_events.parquet')
        events_files = glob.glob(events_pattern)
        
        if events_files:
            events = pd.read_parquet(events_files[0])
            mean_edep = events['totalEdep'].mean() / 1000.0  # MeV to GeV
            std_edep = events['totalEdep'].std() / 1000.0
            resolution = std_edep / mean_edep if mean_edep > 0 else 0
            
            resolution_data[mat_key]['energies'].append(energy)
            resolution_data[mat_key]['resolutions'].append(resolution * 100)  # Convert to percentage
            resolution_data[mat_key]['mean_edep'].append(mean_edep)

# Create figure with subplots
fig, axes = plt.subplots(2, 2, figsize=(14, 12))
fig.suptitle('Crystal Electromagnetic Calorimeter Performance Comparison', fontsize=16)

# 1. Energy Resolution vs Energy
ax1 = axes[0, 0]
for mat_key, mat_info in materials.items():
    if resolution_data[mat_key]['energies']:
        ax1.plot(resolution_data[mat_key]['energies'], 
                resolution_data[mat_key]['resolutions'],
                'o-', color=mat_info['color'], label=mat_info['label'], 
                markersize=8, linewidth=2)

ax1.set_xlabel('Beam Energy (GeV)', fontsize=12)
ax1.set_ylabel('Energy Resolution σ/E (%)', fontsize=12)
ax1.set_title('Energy Resolution Comparison', fontsize=14)
ax1.grid(True, alpha=0.3)
ax1.legend()
ax1.set_xscale('log')

# 2. Shower Profile at 5 GeV
ax2 = axes[0, 1]
energy_5gev_dir = os.path.join(base_dir, 'energy_5.000GeV')

for mat_key, mat_info in materials.items():
    hits_pattern = os.path.join(energy_5gev_dir, f'*{mat_key}*_hits_data.parquet')
    hits_files = glob.glob(hits_pattern)
    
    if hits_files:
        hits = pd.read_parquet(hits_files[0])
        # Calculate longitudinal profile
        z_bins = np.linspace(0, mat_info['depth_radiation_lengths'] * mat_info['X0_cm'] * 10, 50)  # mm
        z_hist, _ = np.histogram(hits['z'], bins=z_bins, weights=hits['edep'])
        z_centers = (z_bins[:-1] + z_bins[1:]) / 2
        z_centers_X0 = z_centers / (mat_info['X0_cm'] * 10)  # Convert to X0
        
        # Normalize by total energy
        z_hist_norm = z_hist / z_hist.sum()
        
        ax2.plot(z_centers_X0, z_hist_norm, '-', color=mat_info['color'], 
                label=mat_info['label'], linewidth=2)

ax2.set_xlabel('Depth (X₀)', fontsize=12)
ax2.set_ylabel('Normalized Energy Deposition', fontsize=12)
ax2.set_title('Longitudinal Shower Profile at 5 GeV', fontsize=14)
ax2.grid(True, alpha=0.3)
ax2.legend()
ax2.set_xlim(0, 25)

# 3. Material Comparison Table
ax3 = axes[1, 0]
ax3.axis('off')

# Create comparison data
table_data = []
headers = ['Material', 'X₀ (cm)', 'Depth (X₀)', 'σ/E @ 5GeV (%)']

for mat_key, mat_info in materials.items():
    res_5gev = None
    for e, r in zip(resolution_data[mat_key]['energies'], resolution_data[mat_key]['resolutions']):
        if e == 5.0:
            res_5gev = r
            break
    
    table_data.append([
        mat_info['label'],
        f"{mat_info['X0_cm']:.2f}",
        f"{mat_info['depth_radiation_lengths']:.0f}",
        f"{res_5gev:.2f}" if res_5gev else "N/A"
    ])

table = ax3.table(cellText=table_data, colLabels=headers, loc='center', cellLoc='center')
table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1.2, 1.8)
ax3.set_title('Material Properties Comparison', fontsize=14, pad=20)

# 4. Transverse shower profile at 5 GeV
ax4 = axes[1, 1]

for mat_key, mat_info in materials.items():
    hits_pattern = os.path.join(energy_5gev_dir, f'*{mat_key}*_hits_data.parquet')
    hits_files = glob.glob(hits_pattern)
    
    if hits_files:
        hits = pd.read_parquet(hits_files[0])
        # Calculate radial distribution
        r = np.sqrt(hits['x']**2 + hits['y']**2)
        r_bins = np.linspace(0, 50, 30)  # mm
        r_hist, _ = np.histogram(r, bins=r_bins, weights=hits['edep'])
        r_centers = (r_bins[:-1] + r_bins[1:]) / 2
        
        # Normalize
        r_hist_norm = r_hist / r_hist.sum()
        
        ax4.plot(r_centers, r_hist_norm, '-', color=mat_info['color'], 
                label=mat_info['label'], linewidth=2)

ax4.set_xlabel('Radial Distance (mm)', fontsize=12)
ax4.set_ylabel('Normalized Energy Deposition', fontsize=12)
ax4.set_title('Transverse Shower Profile at 5 GeV', fontsize=14)
ax4.grid(True, alpha=0.3)
ax4.legend()
ax4.set_xlim(0, 40)

plt.tight_layout()
plot_file = os.path.join(base_dir, 'crystal_ecal_comparison.png')
plt.savefig(plot_file, dpi=300, bbox_inches='tight')
plt.close()

# Fit resolution curves
def resolution_func(E, a, b):
    return np.sqrt(a**2 / E + b**2)

fit_results = {}
for mat_key in materials:
    if len(resolution_data[mat_key]['energies']) >= 2:
        try:
            popt, _ = curve_fit(resolution_func, 
                              resolution_data[mat_key]['energies'], 
                              np.array(resolution_data[mat_key]['resolutions'])/100)
            fit_results[mat_key] = {
                'stochastic_term': abs(popt[0]) * 100,
                'constant_term': abs(popt[1]) * 100
            }
        except:
            fit_results[mat_key] = {'stochastic_term': None, 'constant_term': None}

# Determine optimal material
optimal = 'bgo'  # Default to BGO based on best resolution
min_res = float('inf')
for mat_key in materials:
    for e, r in zip(resolution_data[mat_key]['energies'], resolution_data[mat_key]['resolutions']):
        if e == 5.0 and r < min_res:
            min_res = r
            optimal = mat_key

result = {
    'optimal_material': materials[optimal]['label'],
    'resolution_data': resolution_data,
    'fit_parameters': fit_results,
    'plots': [plot_file],
    'recommendation': f"{materials[optimal]['label']} provides the best energy resolution at 5 GeV ({min_res:.2f}%)"
}

print(json.dumps(result))