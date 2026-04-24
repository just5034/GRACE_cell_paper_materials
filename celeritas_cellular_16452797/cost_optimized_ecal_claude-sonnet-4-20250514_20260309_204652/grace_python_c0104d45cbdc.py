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

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/cost_optimized_ecal_claude-sonnet-4-20250514_20260309_204652'
energies = ['1.000', '5.000', '20.000']
results = {}

for energy in energies:
    energy_dir = os.path.join(base_dir, f'energy_{energy}GeV')
    
    # Find budget Fe-scintillator events file
    events_files = glob.glob(os.path.join(energy_dir, 'budget_fe_scintillator*_events.parquet'))
    
    if not events_files:
        continue
        
    events_file = events_files[0]
    true_e = float(energy)
    
    # Read events data
    events = pd.read_parquet(events_file)
    
    # Calculate energy resolution
    mean_edep = events['totalEdep'].mean() / 1000.0  # MeV to GeV
    std_edep = events['totalEdep'].std() / 1000.0   # MeV to GeV
    resolution = std_edep / mean_edep if mean_edep > 0 else 0
    containment = mean_edep / true_e if true_e > 0 else 0
    
    results[f'{true_e}GeV'] = {
        'mean_edep_gev': mean_edep,
        'std_edep_gev': std_edep,
        'resolution': resolution,
        'containment': containment,
        'true_energy_gev': true_e
    }

print(json.dumps(results))