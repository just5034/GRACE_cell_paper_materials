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
import pandas as pd
import numpy as np
import json
import glob
import os

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/timing_calorimeter_claude-sonnet-4-20250514_20260309_204646'
energies = ['1.000GeV', '5.000GeV', '20.000GeV']
results = {}

for energy in energies:
    edir = os.path.join(base_dir, f'energy_{energy}')
    
    # Find plastic calorimeter files
    events_files = glob.glob(os.path.join(edir, 'plastic_calorimeter_em_events.parquet'))
    hits_files = glob.glob(os.path.join(edir, 'plastic_calorimeter_em_hits_data.parquet'))
    
    if not events_files or not hits_files:
        continue
        
    events_file = events_files[0]
    hits_file = hits_files[0]
    
    true_e = float(energy.replace('GeV', ''))
    
    # Read events for energy resolution
    events = pd.read_parquet(events_file)
    mean_edep = events['totalEdep'].mean() / 1000.0  # MeV to GeV
    std_edep = events['totalEdep'].std() / 1000.0
    energy_resolution = std_edep / mean_edep if mean_edep > 0 else 0
    
    # Read hits for timing resolution
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

print(json.dumps(results))