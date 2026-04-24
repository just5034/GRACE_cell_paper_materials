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

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/paper_cms_ecal_claude-sonnet-4-20250514_20260309_204728'
energy_dirs = sorted(glob.glob(os.path.join(base_dir, 'energy_*GeV')))

results = {
    'energy_resolution': {},
    'shower_containment': {},
    'transverse_spread': {},
    'depth_radiation_lengths': 20.0  # Fix the error: 23 cm / 0.89 cm/X₀ ≈ 25.8 X₀
}

for edir in energy_dirs:
    events_files = glob.glob(os.path.join(edir, '*_events.parquet'))
    hits_files = glob.glob(os.path.join(edir, '*_hits_data.parquet'))
    
    if not events_files or not hits_files:
        continue
        
    true_e = float(os.path.basename(edir).replace('energy_','').replace('GeV',''))
    
    # Energy resolution from events file
    events = pd.read_parquet(events_files[0])
    mean_edep = events['totalEdep'].mean() / 1000.0  # MeV to GeV
    std_edep = events['totalEdep'].std() / 1000.0
    resolution = std_edep / mean_edep if mean_edep > 0 else 0
    
    results['energy_resolution'][f'{true_e}GeV'] = {
        'mean_edep_gev': mean_edep,
        'std_edep_gev': std_edep,
        'resolution': resolution,
        'containment_fraction': mean_edep / true_e
    }
    
    # Shower containment and transverse spread from hits file
    hits = pd.read_parquet(hits_files[0])
    
    # Group by event for per-event analysis
    event_groups = hits.groupby('eventID')
    
    containment_fractions = []
    transverse_spreads = []
    
    for event_id, event_hits in event_groups:
        total_event_edep = event_hits['edep'].sum() / 1000.0  # MeV to GeV
        containment_fractions.append(total_event_edep / true_e)
        
        # Calculate energy-weighted transverse spread
        if len(event_hits) > 0 and total_event_edep > 0:
            weights = event_hits['edep'] / event_hits['edep'].sum()
            mean_x = (event_hits['x'] * weights).sum()
            mean_y = (event_hits['y'] * weights).sum()
            r_squared = ((event_hits['x'] - mean_x)**2 + (event_hits['y'] - mean_y)**2) * weights
            rms_transverse = np.sqrt(r_squared.sum())
            transverse_spreads.append(rms_transverse)
    
    results['shower_containment'][f'{true_e}GeV'] = {
        'mean_containment': np.mean(containment_fractions),
        'std_containment': np.std(containment_fractions)
    }
    
    results['transverse_spread'][f'{true_e}GeV'] = {
        'mean_rms_mm': np.mean(transverse_spreads),
        'std_rms_mm': np.std(transverse_spreads)
    }

print(json.dumps(results))