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
    
    # Look for Fe-scintillator (budget) calorimeter files
    events_files = glob.glob(os.path.join(energy_dir, 'budget_fe_scintillator_*_em_events.parquet'))
    hits_files = glob.glob(os.path.join(energy_dir, 'budget_fe_scintillator_*_em_hits_data.parquet'))
    
    if not events_files:
        continue
        
    events_file = events_files[0]
    hits_file = hits_files[0] if hits_files else None
    
    true_e = float(energy)
    
    # Read events data
    events = pd.read_parquet(events_file)
    
    # Calculate energy resolution
    mean_edep = events['totalEdep'].mean() / 1000.0  # MeV to GeV
    std_edep = events['totalEdep'].std() / 1000.0
    resolution = std_edep / mean_edep if mean_edep > 0 else 0
    
    # Calculate shower containment (fraction of beam energy deposited)
    containment = mean_edep / true_e
    
    # Store results
    results[f'{true_e}GeV'] = {
        'mean_edep_gev': mean_edep,
        'std_edep_gev': std_edep,
        'resolution': resolution,
        'containment': containment,
        'true_energy_gev': true_e
    }
    
    # If hits file exists, calculate shower profile metrics
    if hits_file and os.path.exists(hits_file):
        hits = pd.read_parquet(hits_file)
        
        # Calculate mean shower depth (z position weighted by energy)
        mean_z = (hits['z'] * hits['edep']).sum() / hits['edep'].sum()
        
        # Calculate RMS of shower in z
        z_rms = np.sqrt(((hits['z'] - mean_z)**2 * hits['edep']).sum() / hits['edep'].sum())
        
        # Calculate transverse shower size
        r_squared = hits['x']**2 + hits['y']**2
        mean_r = np.sqrt((r_squared * hits['edep']).sum() / hits['edep'].sum())
        
        results[f'{true_e}GeV']['mean_shower_depth_mm'] = mean_z
        results[f'{true_e}GeV']['shower_depth_rms_mm'] = z_rms
        results[f'{true_e}GeV']['mean_transverse_size_mm'] = mean_r

print(json.dumps(results))