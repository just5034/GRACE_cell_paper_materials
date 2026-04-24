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

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/timing_calorimeter_claude-sonnet-4-20250514_20260309_204646'
energies = sorted(glob.glob(os.path.join(base_dir, 'energy_*GeV')))

results = {}

for edir in energies:
    # Find LYSO files
    events_files = glob.glob(os.path.join(edir, 'lyso_calorimeter_em_events.parquet'))
    hits_files = glob.glob(os.path.join(edir, 'lyso_calorimeter_em_hits_data.parquet'))
    
    if not events_files or not hits_files:
        continue
    
    events_file = events_files[0]
    hits_file = hits_files[0]
    
    true_e = float(os.path.basename(edir).replace('energy_','').replace('GeV',''))
    
    # Energy resolution
    events = pd.read_parquet(events_file)
    mean_edep = events['totalEdep'].mean() / 1000.0  # MeV→GeV
    std_edep = events['totalEdep'].std() / 1000.0
    energy_resolution = std_edep / mean_edep if mean_edep > 0 else 0
    
    # Timing resolution from first-hit times
    hits = pd.read_parquet(hits_file)
    
    # Get first hit time per event
    first_hit_times = hits.groupby('eventID')['time'].min()
    
    # Calculate timing resolution
    mean_time = first_hit_times.mean()
    std_time = first_hit_times.std()
    timing_resolution_ns = std_time
    timing_resolution_ps = std_time * 1000  # ns to ps
    
    results[f'{true_e}GeV'] = {
        'mean_edep_gev': mean_edep,
        'energy_resolution': energy_resolution,
        'timing_resolution_ns': timing_resolution_ns,
        'timing_resolution_ps': timing_resolution_ps,
        'mean_first_hit_time_ns': mean_time,
        'n_events': len(events)
    }

# Plot timing resolution vs energy
energies_gev = []
timing_res_ps = []
energy_res = []

for key in sorted(results.keys(), key=lambda x: float(x.replace('GeV',''))):
    energies_gev.append(float(key.replace('GeV','')))
    timing_res_ps.append(results[key]['timing_resolution_ps'])
    energy_res.append(results[key]['energy_resolution'])

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 10))

# Timing resolution plot
ax1.plot(energies_gev, timing_res_ps, 'bo-', linewidth=2, markersize=8)
ax1.set_xlabel('Beam Energy (GeV)', fontsize=12)
ax1.set_ylabel('Timing Resolution (ps)', fontsize=12)
ax1.set_title('LYSO Calorimeter Timing Resolution vs Energy', fontsize=14)
ax1.grid(True, alpha=0.3)
ax1.set_xscale('log')
ax1.axhline(y=30, color='r', linestyle='--', label='30 ps target')
ax1.axhline(y=10, color='g', linestyle='--', label='10 ps target')
ax1.legend()

# Energy resolution plot
ax2.plot(energies_gev, energy_res, 'ro-', linewidth=2, markersize=8)
ax2.set_xlabel('Beam Energy (GeV)', fontsize=12)
ax2.set_ylabel('Energy Resolution (σ/E)', fontsize=12)
ax2.set_title('LYSO Calorimeter Energy Resolution vs Energy', fontsize=14)
ax2.grid(True, alpha=0.3)
ax2.set_xscale('log')

plt.tight_layout()
plt.savefig('lyso_resolution_analysis.png', dpi=150)

# Add plot to results
results['plot'] = 'lyso_resolution_analysis.png'

# Summary statistics
timing_res_range = f"{min(timing_res_ps):.1f}-{max(timing_res_ps):.1f} ps"
energy_res_range = f"{min(energy_res)*100:.1f}-{max(energy_res)*100:.1f}%"

results['summary'] = {
    'timing_resolution_range': timing_res_range,
    'energy_resolution_range': energy_res_range,
    'meets_10ps_target': any(t < 10 for t in timing_res_ps),
    'meets_30ps_target': all(t < 30 for t in timing_res_ps)
}

print(json.dumps(results))