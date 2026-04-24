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
    edir = os.path.join(base_dir, f'energy_{energy}GeV')
    
    # Look for budget_fe_scintillator files
    events_files = glob.glob(os.path.join(edir, 'budget_fe_scintillator*_events.parquet'))
    hits_files = glob.glob(os.path.join(edir, 'budget_fe_scintillator*_hits_data.parquet'))
    
    if not events_files:
        continue
        
    events_file = events_files[0]
    hits_file = hits_files[0] if hits_files else None
    
    true_e = float(energy)
    
    # Read events data
    events = pd.read_parquet(events_file)
    mean_edep = events['totalEdep'].mean() / 1000.0  # MeV to GeV
    std_edep = events['totalEdep'].std() / 1000.0
    resolution = std_edep / mean_edep if mean_edep > 0 else 0
    containment = mean_edep / true_e
    
    # Calculate shower containment using hits data if available
    if hits_file and os.path.exists(hits_file):
        hits = pd.read_parquet(hits_file)
        # Group by event and calculate total energy per event
        event_totals = hits.groupby('eventID')['edep'].sum() / 1000.0  # MeV to GeV
        # Shower containment from hits should match events file
        containment_check = event_totals.mean() / true_e
    
    results[f'{true_e}GeV'] = {
        'mean_edep_gev': mean_edep,
        'std_edep_gev': std_edep,
        'resolution': resolution,
        'containment': containment,
        'true_energy_gev': true_e
    }

print(json.dumps(results))