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
results = {
    'material': 'BGO',
    'energy_resolution': {'data_points': {}},
    'shower_containment': {},
    'moliere_radius': {}
}

# Energy resolution analysis
for energy in energies:
    edir = os.path.join(base_dir, f'energy_{energy}GeV')
    events_file = os.path.join(edir, 'bgo_projective_tower_em_events.parquet')
    
    if os.path.exists(events_file):
        events = pd.read_parquet(events_file)
        true_e = float(energy)
        mean_edep = events['totalEdep'].mean() / 1000.0  # MeV to GeV
        std_edep = events['totalEdep'].std() / 1000.0
        resolution = std_edep / mean_edep if mean_edep > 0 else 0
        
        results['energy_resolution']['data_points'][energy] = {
            'mean_edep_gev': mean_edep,
            'std_edep_gev': std_edep,
            'resolution': resolution,
            'n_events': len(events)
        }

# Fit energy resolution: sigma/E = a/sqrt(E) + b
if len(results['energy_resolution']['data_points']) >= 2:
    e_vals = []
    res_vals = []
    for e_str, data in results['energy_resolution']['data_points'].items():
        e_vals.append(float(e_str))
        res_vals.append(data['resolution'])
    
    e_vals = np.array(e_vals)
    res_vals = np.array(res_vals)
    
    def res_func(E, a, b):
        return a / np.sqrt(E) + b
    
    try:
        popt, _ = curve_fit(res_func, e_vals, res_vals)
        results['energy_resolution']['fit_parameters'] = {
            'stochastic_term': float(popt[0]),
            'constant_term': float(popt[1])
        }
    except:
        results['energy_resolution']['fit_parameters'] = {
            'stochastic_term': None,
            'constant_term': None
        }

# Shower containment and Moliere radius analysis
for energy in energies:
    edir = os.path.join(base_dir, f'energy_{energy}GeV')
    hits_file = os.path.join(edir, 'bgo_projective_tower_em_hits_data.parquet')
    
    if os.path.exists(hits_file):
        hits = pd.read_parquet(hits_file)
        
        # Longitudinal containment
        total_edep = hits.groupby('eventID')['edep'].sum()
        z_bins = np.linspace(0, 300, 31)  # 0-300mm in 10mm bins
        z_profile = []
        for i in range(len(z_bins)-1):
            mask = (hits['z'] >= z_bins[i]) & (hits['z'] < z_bins[i+1])
            z_profile.append(hits[mask]['edep'].sum())
        
        z_profile = np.array(z_profile)
        cumsum = np.cumsum(z_profile)
        total = cumsum[-1]
        if total > 0:
            containment_95 = z_bins[np.where(cumsum >= 0.95 * total)[0][0]] if np.any(cumsum >= 0.95 * total) else 300
            containment_99 = z_bins[np.where(cumsum >= 0.99 * total)[0][0]] if np.any(cumsum >= 0.99 * total) else 300
        else:
            containment_95 = containment_99 = 0
        
        results['shower_containment'][f'{energy}GeV'] = {
            'longitudinal_95_percent_mm': float(containment_95),
            'longitudinal_99_percent_mm': float(containment_99)
        }
        
        # Moliere radius calculation
        hits['r'] = np.sqrt(hits['x']**2 + hits['y']**2)
        r_bins = np.linspace(0, 100, 101)
        r_hist, _ = np.histogram(hits['r'], bins=r_bins, weights=hits['edep'])
        r_cumsum = np.cumsum(r_hist)
        r_total = r_cumsum[-1]
        
        if r_total > 0:
            moliere_radius = r_bins[np.where(r_cumsum >= 0.9 * r_total)[0][0]] if np.any(r_cumsum >= 0.9 * r_total) else 100
        else:
            moliere_radius = 0
        
        results['moliere_radius'][f'{energy}GeV'] = float(moliere_radius)

# Create energy resolution plot
if len(results['energy_resolution']['data_points']) > 0:
    plt.figure(figsize=(8, 6))
    e_plot = []
    res_plot = []
    for e_str, data in sorted(results['energy_resolution']['data_points'].items()):
        e_plot.append(float(e_str))
        res_plot.append(data['resolution'] * 100)  # Convert to percentage
    
    plt.scatter(e_plot, res_plot, s=100, label='BGO data')
    
    if 'fit_parameters' in results['energy_resolution'] and results['energy_resolution']['fit_parameters']['stochastic_term'] is not None:
        e_fit = np.logspace(np.log10(min(e_plot)), np.log10(max(e_plot)), 100)
        a = results['energy_resolution']['fit_parameters']['stochastic_term']
        b = results['energy_resolution']['fit_parameters']['constant_term']
        res_fit = (a / np.sqrt(e_fit) + b) * 100
        plt.plot(e_fit, res_fit, 'r-', label=f'Fit: {a*100:.1f}%/√E ⊕ {b*100:.1f}%')
    
    plt.xlabel('Energy (GeV)')
    plt.ylabel('Energy Resolution σ/E (%)')
    plt.xscale('log')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.title('BGO Energy Resolution')
    plt.tight_layout()
    plt.savefig('/tmp/bgo_energy_resolution.png', dpi=150)
    plt.close()
    results['plots'] = {'energy_resolution': '/tmp/bgo_energy_resolution.png'}

print(json.dumps(results))