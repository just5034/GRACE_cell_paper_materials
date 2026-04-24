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
timing_data = {}
energy_data = {}

for edir in energies:
    # Look for sampling calorimeter files (detector_2)
    events_files = glob.glob(os.path.join(edir, 'detector_2_em_events.parquet'))
    hits_files = glob.glob(os.path.join(edir, 'detector_2_em_hits_data.parquet'))
    
    if not events_files or not hits_files:
        continue
        
    events_file = events_files[0]
    hits_file = hits_files[0]
    
    true_e = float(os.path.basename(edir).replace('energy_','').replace('GeV',''))
    
    # Energy resolution analysis
    events = pd.read_parquet(events_file)
    mean_edep = events['totalEdep'].mean() / 1000.0  # MeV to GeV
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
    
    timing_data[true_e] = timing_resolution_ps
    energy_data[true_e] = energy_resolution

# Create plots
if timing_data:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Timing resolution plot
    energies_list = sorted(timing_data.keys())
    timing_values = [timing_data[e] for e in energies_list]
    
    ax1.plot(energies_list, timing_values, 'bo-', linewidth=2, markersize=8)
    ax1.set_xlabel('Beam Energy (GeV)', fontsize=12)
    ax1.set_ylabel('Timing Resolution (ps)', fontsize=12)
    ax1.set_title('Sampling Calorimeter Timing Resolution', fontsize=14)
    ax1.grid(True, alpha=0.3)
    ax1.set_xscale('log')
    
    # Add 10-30 ps target region
    ax1.axhspan(10, 30, alpha=0.2, color='green', label='Target: 10-30 ps')
    ax1.legend()
    
    # Energy resolution plot
    energy_values = [energy_data[e] for e in energies_list]
    
    ax2.plot(energies_list, energy_values, 'ro-', linewidth=2, markersize=8)
    ax2.set_xlabel('Beam Energy (GeV)', fontsize=12)
    ax2.set_ylabel('Energy Resolution (σ/E)', fontsize=12)
    ax2.set_title('Sampling Calorimeter Energy Resolution', fontsize=14)
    ax2.grid(True, alpha=0.3)
    ax2.set_xscale('log')
    
    plt.tight_layout()
    plot_path = os.path.join(base_dir, 'sampling_calorimeter_performance.png')
    plt.savefig(plot_path, dpi=150)
    plt.close()
    
    results['plot'] = plot_path

print(json.dumps(results))