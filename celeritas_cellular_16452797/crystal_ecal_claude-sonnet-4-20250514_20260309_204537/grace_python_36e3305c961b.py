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
energies = ['1.000', '5.000', '20.000']
results = {}

# Energy resolution analysis
energy_resolution = {}
for e in energies:
    edir = os.path.join(base_dir, f'energy_{e}GeV')
    events_file = os.path.join(edir, 'pbwo4_projective_tower_2_em_events.parquet')
    
    if os.path.exists(events_file):
        events = pd.read_parquet(events_file)
        true_e = float(e)
        mean_edep = events['totalEdep'].mean() / 1000.0  # MeV to GeV
        std_edep = events['totalEdep'].std() / 1000.0
        resolution = std_edep / mean_edep if mean_edep > 0 else 0
        
        energy_resolution[true_e] = {
            'mean_edep_gev': mean_edep,
            'std_edep_gev': std_edep,
            'resolution': resolution,
            'n_events': len(events)
        }

# Fit energy resolution to stochastic term: sigma/E = a/sqrt(E) + b
energies_gev = np.array(list(energy_resolution.keys()))
resolutions = np.array([energy_resolution[e]['resolution'] for e in energies_gev])

def res_func(E, a, b):
    return a / np.sqrt(E) + b

popt, pcov = curve_fit(res_func, energies_gev, resolutions)
stochastic_term = popt[0]
constant_term = popt[1]

# Shower containment analysis
shower_containment = {}
for e in energies:
    edir = os.path.join(base_dir, f'energy_{e}GeV')
    events_file = os.path.join(edir, 'pbwo4_projective_tower_2_em_events.parquet')
    
    if os.path.exists(events_file):
        events = pd.read_parquet(events_file)
        true_e = float(e)
        mean_fraction = events['totalEdep'].mean() / (true_e * 1000.0)  # fraction of true energy
        shower_containment[true_e] = mean_fraction

# Moliere radius analysis - analyze transverse shower profile
moliere_radius = {}
for e in energies:
    edir = os.path.join(base_dir, f'energy_{e}GeV')
    hits_file = os.path.join(edir, 'pbwo4_projective_tower_2_em_hits_data.parquet')
    
    if os.path.exists(hits_file):
        hits = pd.read_parquet(hits_file)
        true_e = float(e)
        
        # Calculate radial distance from beam axis (assumed at x=0, y=0)
        hits['r'] = np.sqrt(hits['x']**2 + hits['y']**2)
        
        # Group by event and calculate energy-weighted mean radius
        event_groups = hits.groupby('eventID')
        
        # Calculate 90% containment radius for each event
        r90_values = []
        for event_id, group in event_groups:
            sorted_hits = group.sort_values('r')
            sorted_hits['cumsum_edep'] = sorted_hits['edep'].cumsum()
            total_edep = sorted_hits['edep'].sum()
            if total_edep > 0:
                r90_idx = (sorted_hits['cumsum_edep'] >= 0.9 * total_edep).idxmax()
                r90_values.append(sorted_hits.loc[r90_idx, 'r'])
        
        if r90_values:
            moliere_radius[true_e] = {
                'mean_r90_mm': np.mean(r90_values),
                'std_r90_mm': np.std(r90_values)
            }

# Create plots
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))

# Energy resolution plot
ax1.scatter(energies_gev, resolutions, s=100, label='Data')
e_fit = np.linspace(0.5, 25, 100)
ax1.plot(e_fit, res_func(e_fit, *popt), 'r-', 
         label=f'Fit: {stochastic_term:.1f}%/√E ⊕ {constant_term:.1f}%')
ax1.set_xlabel('Energy (GeV)')
ax1.set_ylabel('σ/E')
ax1.set_title('PbWO4 Energy Resolution')
ax1.legend()
ax1.grid(True)

# Shower containment plot
e_cont = list(shower_containment.keys())
cont_values = list(shower_containment.values())
ax2.scatter(e_cont, cont_values, s=100)
ax2.set_xlabel('Energy (GeV)')
ax2.set_ylabel('Energy Containment Fraction')
ax2.set_title('PbWO4 Shower Containment')
ax2.grid(True)
ax2.set_ylim(0.9, 1.0)

# Moliere radius plot
e_mol = list(moliere_radius.keys())
r90_values = [moliere_radius[e]['mean_r90_mm'] for e in e_mol]
r90_errors = [moliere_radius[e]['std_r90_mm'] for e in e_mol]
ax3.errorbar(e_mol, r90_values, yerr=r90_errors, fmt='o', markersize=8)
ax3.set_xlabel('Energy (GeV)')
ax3.set_ylabel('90% Containment Radius (mm)')
ax3.set_title('PbWO4 Transverse Shower Size')
ax3.grid(True)

plt.tight_layout()
plt.savefig('pbwo4_analysis.png', dpi=150)
plt.close()

result = {
    'material': 'PbWO4',
    'energy_resolution': {
        'data_points': energy_resolution,
        'stochastic_term_percent': stochastic_term * 100,
        'constant_term_percent': constant_term * 100
    },
    'shower_containment': shower_containment,
    'moliere_radius': moliere_radius,
    'plot': 'pbwo4_analysis.png'
}

print(json.dumps(result))