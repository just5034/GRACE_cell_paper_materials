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

# Define materials and their properties
materials = {
    'pbwo4': {'name': 'PbWO4', 'X0': 0.89, 'RM': 2.0, 'density': 8.28},
    'bgo': {'name': 'BGO', 'X0': 1.12, 'RM': 2.3, 'density': 7.13},
    'csi': {'name': 'CsI', 'X0': 1.86, 'RM': 3.5, 'density': 4.51}
}

# Energy points
energies = [1.0, 5.0, 20.0]

# Collect all performance data
performance_data = {}

for mat_key, mat_info in materials.items():
    performance_data[mat_key] = {
        'name': mat_info['name'],
        'X0': mat_info['X0'],
        'RM': mat_info['RM'],
        'density': mat_info['density'],
        'energy_resolution': {},
        'shower_containment': {},
        'moliere_radius': {}
    }
    
    for energy in energies:
        energy_dir = os.path.join(base_dir, f'energy_{energy:.3f}GeV')
        
        # Find events file
        events_pattern = os.path.join(energy_dir, f'{mat_key}_projective_tower*_em_events.parquet')
        events_files = glob.glob(events_pattern)
        if not events_files:
            continue
        
        events = pd.read_parquet(events_files[0])
        
        # Energy resolution
        mean_edep = events['totalEdep'].mean() / 1000.0  # MeV to GeV
        std_edep = events['totalEdep'].std() / 1000.0
        resolution = std_edep / mean_edep if mean_edep > 0 else 0
        
        performance_data[mat_key]['energy_resolution'][energy] = {
            'mean_edep': mean_edep,
            'resolution': resolution,
            'containment': mean_edep / energy  # fraction of energy contained
        }
        
        # Find hits file for spatial analysis
        hits_pattern = os.path.join(energy_dir, f'{mat_key}_projective_tower*_em_hits_data.parquet')
        hits_files = glob.glob(hits_pattern)
        if hits_files:
            hits = pd.read_parquet(hits_files[0])
            
            # Calculate shower radius (90% containment)
            hits['r'] = np.sqrt(hits['x']**2 + hits['y']**2)
            hits_sorted = hits.sort_values('r')
            hits_sorted['cumulative_edep'] = hits_sorted['edep'].cumsum()
            total_edep = hits_sorted['edep'].sum()
            
            if total_edep > 0:
                r90_idx = (hits_sorted['cumulative_edep'] >= 0.9 * total_edep).idxmax()
                r90 = hits_sorted.loc[r90_idx, 'r']
                performance_data[mat_key]['moliere_radius'][energy] = r90 / 10.0  # mm to cm

# Fit energy resolution
def resolution_func(E, a, b):
    return np.sqrt((a/np.sqrt(E))**2 + b**2)

# Create comparison plots
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Plot 1: Energy Resolution vs Energy
ax1 = axes[0, 0]
for mat_key, data in performance_data.items():
    if data['energy_resolution']:
        E = np.array(sorted(data['energy_resolution'].keys()))
        res = np.array([data['energy_resolution'][e]['resolution'] for e in E])
        
        # Fit resolution
        try:
            popt, _ = curve_fit(resolution_func, E, res, p0=[0.1, 0.01])
            E_fit = np.linspace(0.5, 25, 100)
            res_fit = resolution_func(E_fit, *popt)
            
            ax1.plot(E, res*100, 'o', label=data['name'], markersize=8)
            ax1.plot(E_fit, res_fit*100, '--', alpha=0.7)
            
            data['resolution_fit'] = {'a': popt[0], 'b': popt[1]}
        except:
            ax1.plot(E, res*100, 'o-', label=data['name'], markersize=8)

ax1.set_xlabel('Energy (GeV)')
ax1.set_ylabel('Energy Resolution (%)')
ax1.set_title('Energy Resolution Comparison')
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.set_xlim(0, 25)

# Plot 2: Energy Containment
ax2 = axes[0, 1]
for mat_key, data in performance_data.items():
    if data['energy_resolution']:
        E = np.array(sorted(data['energy_resolution'].keys()))
        containment = np.array([data['energy_resolution'][e]['containment'] for e in E])
        ax2.plot(E, containment*100, 'o-', label=data['name'], markersize=8)

ax2.set_xlabel('Energy (GeV)')
ax2.set_ylabel('Energy Containment (%)')
ax2.set_title('Energy Containment vs Beam Energy')
ax2.legend()
ax2.grid(True, alpha=0.3)
ax2.set_ylim(95, 101)

# Plot 3: Moliere Radius
ax3 = axes[1, 0]
for mat_key, data in performance_data.items():
    if data['moliere_radius']:
        E = np.array(sorted(data['moliere_radius'].keys()))
        r90 = np.array([data['moliere_radius'][e] for e in E])
        ax3.plot(E, r90, 'o-', label=f"{data['name']} (RM={data['RM']} cm)", markersize=8)

ax3.set_xlabel('Energy (GeV)')
ax3.set_ylabel('90% Containment Radius (cm)')
ax3.set_title('Shower Lateral Containment')
ax3.legend()
ax3.grid(True, alpha=0.3)

# Plot 4: Material Properties Comparison
ax4 = axes[1, 1]
mat_names = [data['name'] for data in performance_data.values()]
X0_vals = [data['X0'] for data in performance_data.values()]
RM_vals = [data['RM'] for data in performance_data.values()]
density_vals = [data['density'] for data in performance_data.values()]

x = np.arange(len(mat_names))
width = 0.25

ax4.bar(x - width, X0_vals, width, label='X₀ (cm)', alpha=0.8)
ax4.bar(x, RM_vals, width, label='RM (cm)', alpha=0.8)
ax4.bar(x + width, density_vals, width, label='Density (g/cm³)', alpha=0.8)

ax4.set_ylabel('Value')
ax4.set_title('Material Properties')
ax4.set_xticks(x)
ax4.set_xticklabels(mat_names)
ax4.legend()
ax4.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('crystal_comparison.png', dpi=150)

# Determine optimal material
scores = {}
for mat_key, data in performance_data.items():
    # Resolution at 5 GeV (typical FCC-ee energy)
    res_5gev = data['energy_resolution'].get(5.0, {}).get('resolution', 1.0)
    
    # Average containment
    avg_containment = np.mean([v['containment'] for v in data['energy_resolution'].values()])
    
    # Compactness (smaller is better)
    avg_r90 = np.mean(list(data['moliere_radius'].values())) if data['moliere_radius'] else 10.0
    
    # Combined score (lower is better)
    # Weight: 50% resolution, 30% compactness, 20% containment
    score = 0.5 * res_5gev + 0.3 * (avg_r90/10.0) + 0.2 * (1.0 - avg_containment)
    
    scores[mat_key] = {
        'score': score,
        'resolution_5gev': res_5gev,
        'avg_containment': avg_containment,
        'avg_r90': avg_r90
    }

# Find best material
best_material = min(scores.keys(), key=lambda k: scores[k]['score'])

# Prepare final results
result = {
    'optimal_material': materials[best_material]['name'],
    'reasoning': {
        'resolution_comparison': {
            mat: {
                'resolution_5gev_percent': scores[mat]['resolution_5gev'] * 100,
                'fit_parameters': performance_data[mat].get('resolution_fit', {})
            }
            for mat in materials.keys()
        },
        'containment_comparison': {
            mat: scores[mat]['avg_containment'] * 100
            for mat in materials.keys()
        },
        'compactness_comparison': {
            mat: scores[mat]['avg_r90']
            for mat in materials.keys()
        }
    },
    'recommendation': f"{materials[best_material]['name']} provides the best overall performance for FCC-ee with {scores[best_material]['resolution_5gev']*100:.1f}% energy resolution at 5 GeV",
    'plots': ['crystal_comparison.png']
}

print(json.dumps(result))