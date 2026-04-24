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
energies = ['1.000', '5.000', '20.000']
results = {}

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

for energy in energies:
    energy_dir = os.path.join(base_dir, f'energy_{energy}GeV')
    
    # Find detector_2 files (sampling calorimeter)
    events_files = glob.glob(os.path.join(energy_dir, 'detector_2_em_events.parquet'))
    hits_files = glob.glob(os.path.join(energy_dir, 'detector_2_em_hits_data.parquet'))
    
    if not events_files or not hits_files:
        continue
        
    events = pd.read_parquet(events_files[0])
    hits = pd.read_parquet(hits_files[0])
    
    true_e = float(energy)
    
    # Energy resolution
    mean_edep = events['totalEdep'].mean() / 1000.0  # MeV to GeV
    std_edep = events['totalEdep'].std() / 1000.0
    energy_resolution = std_edep / mean_edep if mean_edep > 0 else 0
    
    # Timing resolution from first hit times
    first_hit_times = []
    for event_id in events['eventID'].unique():
        event_hits = hits[hits['eventID'] == event_id]
        if len(event_hits) > 0:
            first_hit_time = event_hits['time'].min()
            first_hit_times.append(first_hit_time)
    
    first_hit_times = np.array(first_hit_times)
    mean_time = np.mean(first_hit_times)
    std_time = np.std(first_hit_times)
    timing_resolution_ps = std_time * 1000  # ns to ps
    
    results[f'{true_e}GeV'] = {
        'mean_edep_gev': mean_edep,
        'energy_resolution': energy_resolution,
        'timing_resolution_ns': std_time,
        'timing_resolution_ps': timing_resolution_ps,
        'mean_first_hit_time_ns': mean_time,
        'n_events': len(events)
    }
    
    # Plot first hit time distribution
    ax1.hist(first_hit_times, bins=50, alpha=0.7, label=f'{true_e} GeV')

ax1.set_xlabel('First Hit Time (ns)')
ax1.set_ylabel('Events')
ax1.set_title('Sampling Calorimeter First Hit Time Distribution')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot timing resolution vs energy
if results:
    energies_plot = [float(k.replace('GeV', '')) for k in results.keys()]
    timing_res = [results[k]['timing_resolution_ps'] for k in results.keys()]
    
    ax2.plot(energies_plot, timing_res, 'o-', markersize=8)
    ax2.set_xlabel('Beam Energy (GeV)')
    ax2.set_ylabel('Timing Resolution (ps)')
    ax2.set_title('Sampling Calorimeter Timing Resolution vs Energy')
    ax2.grid(True, alpha=0.3)
    ax2.set_xscale('log')

plt.tight_layout()
plot_path = os.path.join(base_dir, 'sampling_timing_analysis.png')
plt.savefig(plot_path, dpi=150)
plt.close()

results['plot'] = plot_path
print(json.dumps(results))