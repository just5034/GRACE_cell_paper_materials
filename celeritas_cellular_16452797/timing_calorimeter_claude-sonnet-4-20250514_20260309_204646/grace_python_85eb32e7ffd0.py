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

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/timing_calorimeter_claude-sonnet-4-20250514_20260309_204646'
energies = [1.0, 5.0, 20.0]
detectors = ['lyso_calorimeter', 'plastic_calorimeter', 'detector_2']
detector_labels = {'lyso_calorimeter': 'LYSO Crystal', 'plastic_calorimeter': 'Plastic Scintillator', 'detector_2': 'W/Plastic Sampling'}

results = {}

for detector in detectors:
    results[detector] = {'energy_resolution': {}, 'timing_resolution': {}}
    
    for energy in energies:
        energy_dir = os.path.join(base_dir, f'energy_{energy:.3f}GeV')
        
        # Find events file
        events_files = glob.glob(os.path.join(energy_dir, f'{detector}_em_events.parquet'))
        if not events_files:
            continue
        events_file = events_files[0]
        
        # Find hits file
        hits_files = glob.glob(os.path.join(energy_dir, f'{detector}_em_hits_data.parquet'))
        if not hits_files:
            continue
        hits_file = hits_files[0]
        
        # Energy resolution
        events = pd.read_parquet(events_file)
        mean_edep = events['totalEdep'].mean()
        std_edep = events['totalEdep'].std()
        energy_res = std_edep / mean_edep if mean_edep > 0 else 0
        
        # Timing resolution from first hit times
        hits = pd.read_parquet(hits_file)
        first_hits = hits.groupby('eventID')['time'].min()
        
        # Remove outliers (>3 sigma)
        mean_time = first_hits.mean()
        std_time = first_hits.std()
        mask = np.abs(first_hits - mean_time) < 3 * std_time
        first_hits_clean = first_hits[mask]
        
        timing_res = first_hits_clean.std() * 1000  # ns to ps
        
        results[detector]['energy_resolution'][f'{energy}GeV'] = {
            'resolution': energy_res,
            'percent': energy_res * 100
        }
        results[detector]['timing_resolution'][f'{energy}GeV'] = {
            'resolution_ps': timing_res,
            'mean_time_ns': first_hits_clean.mean()
        }

# Create comparison plots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Energy resolution comparison
for detector in detectors:
    x = []
    y = []
    for energy in energies:
        key = f'{energy}GeV'
        if key in results[detector]['energy_resolution']:
            x.append(energy)
            y.append(results[detector]['energy_resolution'][key]['percent'])
    ax1.plot(x, y, 'o-', label=detector_labels[detector], linewidth=2, markersize=8)

ax1.set_xlabel('Beam Energy (GeV)', fontsize=12)
ax1.set_ylabel('Energy Resolution (%)', fontsize=12)
ax1.set_title('Energy Resolution Comparison', fontsize=14)
ax1.grid(True, alpha=0.3)
ax1.legend()
ax1.set_xscale('log')

# Timing resolution comparison
for detector in detectors:
    x = []
    y = []
    for energy in energies:
        key = f'{energy}GeV'
        if key in results[detector]['timing_resolution']:
            x.append(energy)
            y.append(results[detector]['timing_resolution'][key]['resolution_ps'])
    ax2.plot(x, y, 'o-', label=detector_labels[detector], linewidth=2, markersize=8)

ax2.set_xlabel('Beam Energy (GeV)', fontsize=12)
ax2.set_ylabel('Timing Resolution (ps)', fontsize=12)
ax2.set_title('Timing Resolution Comparison', fontsize=14)
ax2.grid(True, alpha=0.3)
ax2.legend()
ax2.set_xscale('log')
ax2.axhspan(10, 30, alpha=0.2, color='green', label='Target Range')

plt.tight_layout()
plot_path = os.path.join(base_dir, 'detector_comparison.png')
plt.savefig(plot_path, dpi=150)
plt.close()

# Determine best detector
best_detector = None
best_score = float('inf')

for detector in detectors:
    # Average timing resolution across energies
    timing_vals = [results[detector]['timing_resolution'][f'{e}GeV']['resolution_ps'] 
                   for e in energies if f'{e}GeV' in results[detector]['timing_resolution']]
    avg_timing = np.mean(timing_vals)
    
    # Check if in target range
    if 10 <= avg_timing <= 30:
        # Also consider energy resolution
        energy_vals = [results[detector]['energy_resolution'][f'{e}GeV']['percent'] 
                      for e in energies if f'{e}GeV' in results[detector]['energy_resolution']]
        avg_energy = np.mean(energy_vals)
        
        # Combined score (lower is better)
        score = avg_timing + avg_energy
        if score < best_score:
            best_score = score
            best_detector = detector

summary = {
    'detector_comparison': results,
    'best_detector': {
        'name': detector_labels.get(best_detector, best_detector) if best_detector else 'None meet criteria',
        'detector_key': best_detector,
        'reasoning': f'Best combined timing and energy resolution' if best_detector else 'No detector meets 10-30 ps timing requirement'
    },
    'plot': plot_path
}

print(json.dumps(summary))