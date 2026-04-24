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
    # Find plastic calorimeter files
    events_files = glob.glob(os.path.join(edir, 'plastic_calorimeter_em_events.parquet'))
    hits_files = glob.glob(os.path.join(edir, 'plastic_calorimeter_em_hits_data.parquet'))
    
    if not events_files or not hits_files:
        continue
    
    events_file = events_files[0]
    hits_file = hits_files[0]
    
    true_e = float(os.path.basename(edir).replace('energy_','').replace('GeV',''))
    
    # Energy resolution analysis
    events = pd.read_parquet(events_file)
    mean_edep = events['totalEdep'].mean() / 1000.0  # MeV→GeV
    std_edep = events['totalEdep'].std() / 1000.0
    energy_resolution = std_edep / mean_edep if mean_edep > 0 else 0
    
    # Timing resolution analysis
    hits = pd.read_parquet(hits_file)
    
    # Get first hit time for each event
    first_hit_times = hits.groupby('eventID')['time'].min()
    
    # Calculate timing resolution
    mean_time = first_hit_times.mean()
    std_time = first_hit_times.std()
    timing_resolution_ns = std_time
    timing_resolution_ps = timing_resolution_ns * 1000  # ns to ps
    
    results[f'{true_e}GeV'] = {
        'mean_edep_gev': mean_edep,
        'energy_resolution': energy_resolution,
        'timing_resolution_ns': timing_resolution_ns,
        'timing_resolution_ps': timing_resolution_ps,
        'mean_first_hit_time_ns': mean_time,
        'n_events': len(events)
    }

# Create timing resolution plot
if results:
    energies_list = []
    timing_res_list = []
    energy_res_list = []
    
    for key in sorted(results.keys(), key=lambda x: float(x.replace('GeV',''))):
        energies_list.append(float(key.replace('GeV','')))
        timing_res_list.append(results[key]['timing_resolution_ps'])
        energy_res_list.append(results[key]['energy_resolution'])
    
    # Timing resolution plot
    plt.figure(figsize=(8, 6))
    plt.plot(energies_list, timing_res_list, 'bo-', linewidth=2, markersize=8)
    plt.xlabel('Beam Energy (GeV)', fontsize=12)
    plt.ylabel('Timing Resolution (ps)', fontsize=12)
    plt.title('Plastic Scintillator Timing Resolution vs Energy', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.xscale('log')
    plt.savefig(os.path.join(base_dir, 'plastic_timing_resolution.png'), dpi=150, bbox_inches='tight')
    plt.close()
    
    # Energy resolution plot
    plt.figure(figsize=(8, 6))
    plt.plot(energies_list, energy_res_list, 'ro-', linewidth=2, markersize=8)
    plt.xlabel('Beam Energy (GeV)', fontsize=12)
    plt.ylabel('Energy Resolution (σ/E)', fontsize=12)
    plt.title('Plastic Scintillator Energy Resolution vs Energy', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.xscale('log')
    plt.savefig(os.path.join(base_dir, 'plastic_energy_resolution.png'), dpi=150, bbox_inches='tight')
    plt.close()
    
    results['plots'] = [
        os.path.join(base_dir, 'plastic_timing_resolution.png'),
        os.path.join(base_dir, 'plastic_energy_resolution.png')
    ]

print(json.dumps(results))