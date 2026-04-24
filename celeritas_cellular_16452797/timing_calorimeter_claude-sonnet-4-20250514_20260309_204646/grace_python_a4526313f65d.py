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
    
    # Get first hit time per event
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
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Timing resolution plot
    ax1.plot(energies_list, timing_res_list, 'bo-', linewidth=2, markersize=8)
    ax1.set_xlabel('Beam Energy (GeV)')
    ax1.set_ylabel('Timing Resolution (ps)')
    ax1.set_title('Plastic Scintillator Timing Resolution')
    ax1.grid(True, alpha=0.3)
    ax1.set_xscale('log')
    
    # Energy resolution plot
    ax2.plot(energies_list, energy_res_list, 'ro-', linewidth=2, markersize=8)
    ax2.set_xlabel('Beam Energy (GeV)')
    ax2.set_ylabel('Energy Resolution (σ/E)')
    ax2.set_title('Plastic Scintillator Energy Resolution')
    ax2.grid(True, alpha=0.3)
    ax2.set_xscale('log')
    
    plt.tight_layout()
    plot_file = os.path.join(base_dir, 'plastic_resolution_analysis.png')
    plt.savefig(plot_file, dpi=150)
    plt.close()
    
    results['plot'] = plot_file

print(json.dumps(results))