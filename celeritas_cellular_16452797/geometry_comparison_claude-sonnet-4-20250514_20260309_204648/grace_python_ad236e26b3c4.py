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
from scipy import stats

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/geometry_comparison_claude-sonnet-4-20250514_20260309_204648'
energy_dirs = sorted(glob.glob(os.path.join(base_dir, 'energy_*GeV')))

results = {
    'energy_resolution': {},
    'uniformity': {},
    'containment': {},
    'linearity': {'energies': [], 'mean_edep': [], 'response': []}
}

# Analyze each energy
for edir in energy_dirs:
    # Find box calorimeter files
    events_files = glob.glob(os.path.join(edir, 'box_calorimeter_2_em_events.parquet'))
    hits_files = glob.glob(os.path.join(edir, 'box_calorimeter_2_em_hits_data.parquet'))
    
    if not events_files or not hits_files:
        continue
        
    true_e = float(os.path.basename(edir).replace('energy_','').replace('GeV',''))
    
    # Load data
    events = pd.read_parquet(events_files[0])
    hits = pd.read_parquet(hits_files[0])
    
    # Energy resolution
    mean_edep = events['totalEdep'].mean()
    std_edep = events['totalEdep'].std()
    resolution = std_edep / mean_edep if mean_edep > 0 else 0
    results['energy_resolution'][f'{true_e}GeV'] = {
        'mean_edep_MeV': mean_edep,
        'std_edep_MeV': std_edep,
        'resolution': resolution
    }
    
    # Linearity
    results['linearity']['energies'].append(true_e)
    results['linearity']['mean_edep'].append(mean_edep / 1000.0)  # MeV to GeV
    results['linearity']['response'].append(mean_edep / (true_e * 1000.0))  # Response = measured/true
    
    # Uniformity analysis - divide detector into regions
    hits_with_edep = hits.merge(events[['eventID', 'totalEdep']], on='eventID')
    
    # Define regions (assuming detector centered at 0,0)
    n_bins = 5
    x_bins = np.linspace(-50, 50, n_bins+1)  # mm
    y_bins = np.linspace(-50, 50, n_bins+1)  # mm
    
    region_response = []
    for i in range(n_bins):
        for j in range(n_bins):
            mask = ((hits_with_edep['x'] >= x_bins[i]) & (hits_with_edep['x'] < x_bins[i+1]) &
                    (hits_with_edep['y'] >= y_bins[j]) & (hits_with_edep['y'] < y_bins[j+1]))
            
            region_hits = hits_with_edep[mask]
            if len(region_hits) > 0:
                region_events = region_hits.groupby('eventID')['edep'].sum()
                if len(region_events) > 0:
                    region_response.append(region_events.mean())
    
    if region_response:
        uniformity = np.std(region_response) / np.mean(region_response)
        results['uniformity'][f'{true_e}GeV'] = uniformity
    
    # Containment - fraction of energy within detector volume
    # Assuming detector is 200x200x300 mm centered at origin
    contained_mask = ((hits['x'].abs() <= 100) & 
                      (hits['y'].abs() <= 100) & 
                      (hits['z'] >= 0) & (hits['z'] <= 300))
    
    contained_edep = hits[contained_mask].groupby('eventID')['edep'].sum()
    total_edep = hits.groupby('eventID')['edep'].sum()
    
    containment_fractions = []
    for event_id in events['eventID']:
        if event_id in contained_edep.index and event_id in total_edep.index:
            frac = contained_edep[event_id] / total_edep[event_id]
            containment_fractions.append(frac)
    
    if containment_fractions:
        results['containment'][f'{true_e}GeV'] = {
            'mean_containment': np.mean(containment_fractions),
            'std_containment': np.std(containment_fractions)
        }

# Create plots
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

# Energy resolution vs energy
energies = [float(e.replace('GeV','')) for e in results['energy_resolution'].keys()]
resolutions = [results['energy_resolution'][e]['resolution'] for e in results['energy_resolution'].keys()]
ax1.plot(energies, resolutions, 'bo-')
ax1.set_xlabel('Beam Energy (GeV)')
ax1.set_ylabel('Energy Resolution (σ/E)')
ax1.set_title('Box Calorimeter Energy Resolution')
ax1.grid(True)

# Uniformity
if results['uniformity']:
    uniformity_energies = [float(e.replace('GeV','')) for e in results['uniformity'].keys()]
    uniformity_values = list(results['uniformity'].values())
    ax2.plot(uniformity_energies, uniformity_values, 'ro-')
    ax2.set_xlabel('Beam Energy (GeV)')
    ax2.set_ylabel('Non-uniformity (σ/μ)')
    ax2.set_title('Response Uniformity')
    ax2.grid(True)

# Containment
if results['containment']:
    cont_energies = [float(e.replace('GeV','')) for e in results['containment'].keys()]
    cont_values = [results['containment'][e]['mean_containment'] for e in results['containment'].keys()]
    ax3.plot(cont_energies, cont_values, 'go-')
    ax3.set_xlabel('Beam Energy (GeV)')
    ax3.set_ylabel('Containment Fraction')
    ax3.set_title('Shower Containment')
    ax3.grid(True)

# Linearity
if results['linearity']['energies']:
    ax4.plot(results['linearity']['energies'], results['linearity']['response'], 'mo-')
    ax4.axhline(y=1.0, color='k', linestyle='--', alpha=0.5)
    ax4.set_xlabel('True Energy (GeV)')
    ax4.set_ylabel('Response (Measured/True)')
    ax4.set_title('Calorimeter Linearity')
    ax4.grid(True)

plt.tight_layout()
plt.savefig('box_calorimeter_performance.png', dpi=150)
results['plots'] = ['box_calorimeter_performance.png']

# Calculate overall metrics
if resolutions:
    results['summary'] = {
        'mean_resolution': np.mean(resolutions),
        'resolution_at_5GeV': results['energy_resolution'].get('5.0GeV', {}).get('resolution', None),
        'mean_uniformity': np.mean(list(results['uniformity'].values())) if results['uniformity'] else None,
        'mean_containment': np.mean([v['mean_containment'] for v in results['containment'].values()]) if results['containment'] else None,
        'linearity_deviation': np.std(results['linearity']['response']) if results['linearity']['response'] else None
    }

print(json.dumps(results))