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
energies = sorted(glob.glob(os.path.join(base_dir, 'energy_*GeV')))

results = {}

for edir in energies:
    # Look for budget_fe_scintillator files
    events_files = glob.glob(os.path.join(edir, 'budget_fe_scintillator*_events.parquet'))
    if not events_files:
        continue
    
    events_file = events_files[0]
    hits_files = glob.glob(os.path.join(edir, 'budget_fe_scintillator*_hits_data.parquet'))
    hits_file = hits_files[0] if hits_files else None
    
    true_e = float(os.path.basename(edir).replace('energy_','').replace('GeV',''))
    
    events = pd.read_parquet(events_file)
    mean_edep = events['totalEdep'].mean() / 1000.0  # MeV to GeV
    std_edep = events['totalEdep'].std() / 1000.0
    resolution = std_edep / mean_edep if mean_edep > 0 else 0
    containment = mean_edep / true_e
    
    result_entry = {
        'mean_edep_gev': mean_edep,
        'std_edep_gev': std_edep,
        'resolution': resolution,
        'containment': containment,
        'true_energy_gev': true_e
    }
    
    # Calculate shower containment using hits data if available
    if hits_file and os.path.exists(hits_file):
        hits = pd.read_parquet(hits_file)
        # Calculate radial containment
        hits['r'] = np.sqrt(hits['x']**2 + hits['y']**2)
        total_energy = hits['edep'].sum()
        if total_energy > 0:
            # 90% containment radius
            sorted_hits = hits.sort_values('r')
            sorted_hits['cumulative_edep'] = sorted_hits['edep'].cumsum()
            containment_90 = sorted_hits[sorted_hits['cumulative_edep'] <= 0.9 * total_energy]['r'].max()
            result_entry['r90_mm'] = containment_90
            
            # Longitudinal profile
            z_bins = np.linspace(hits['z'].min(), hits['z'].max(), 20)
            z_profile, _ = np.histogram(hits['z'], bins=z_bins, weights=hits['edep'])
            z_centers = (z_bins[:-1] + z_bins[1:]) / 2
            shower_max_z = z_centers[np.argmax(z_profile)]
            result_entry['shower_max_z_mm'] = shower_max_z
    
    results[f'{true_e}GeV'] = result_entry

print(json.dumps(results))