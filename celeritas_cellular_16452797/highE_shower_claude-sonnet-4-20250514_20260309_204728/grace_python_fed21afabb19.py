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

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/highE_shower_claude-sonnet-4-20250514_20260309_204728'
energy_dirs = sorted(glob.glob(os.path.join(base_dir, 'energy_*GeV')))

X0_pbwo4 = 0.89  # cm
depth_radiation_lengths = 25.0  # X₀
calorimeter_depth = depth_radiation_lengths * X0_pbwo4 * 10  # cm to mm

results = {}

for edir in energy_dirs:
    energy_str = os.path.basename(edir)
    true_energy = float(energy_str.replace('energy_', '').replace('GeV', ''))
    
    hits_file = os.path.join(edir, 'pbwo4_calorimeter_em_hits_data.parquet')
    events_file = os.path.join(edir, 'pbwo4_calorimeter_em_events.parquet')
    
    if not os.path.exists(hits_file) or not os.path.exists(events_file):
        continue
    
    hits = pd.read_parquet(hits_file)
    events = pd.read_parquet(events_file)
    
    # Longitudinal profile
    z_bins = np.linspace(0, calorimeter_depth, 51)
    z_centers = (z_bins[:-1] + z_bins[1:]) / 2
    z_profile = []
    
    for event_id in hits['eventID'].unique()[:100]:  # Sample 100 events
        event_hits = hits[hits['eventID'] == event_id]
        hist, _ = np.histogram(event_hits['z'], bins=z_bins, weights=event_hits['edep'])
        z_profile.append(hist)
    
    z_profile = np.mean(z_profile, axis=0)
    z_profile_norm = z_profile / np.sum(z_profile)
    
    # Shower maximum position
    shower_max_idx = np.argmax(z_profile_norm)
    shower_max_z = z_centers[shower_max_idx]
    shower_max_X0 = shower_max_z / 10 / X0_pbwo4
    
    # Transverse profile
    r_bins = np.linspace(0, 50, 26)  # mm
    r_centers = (r_bins[:-1] + r_bins[1:]) / 2
    r_profile = []
    
    for event_id in hits['eventID'].unique()[:100]:
        event_hits = hits[hits['eventID'] == event_id]
        r = np.sqrt(event_hits['x']**2 + event_hits['y']**2)
        hist, _ = np.histogram(r, bins=r_bins, weights=event_hits['edep'])
        r_profile.append(hist)
    
    r_profile = np.mean(r_profile, axis=0)
    r_cumulative = np.cumsum(r_profile) / np.sum(r_profile)
    
    # Containment radii
    r90_idx = np.argmax(r_cumulative >= 0.90)
    r95_idx = np.argmax(r_cumulative >= 0.95)
    r99_idx = np.argmax(r_cumulative >= 0.99)
    
    r90 = r_centers[r90_idx]
    r95 = r_centers[r95_idx]
    r99 = r_centers[r99_idx]
    
    # Moliere radius
    moliere_radius = 2.19 * X0_pbwo4 * 10  # mm
    
    results[f'{true_energy}GeV'] = {
        'shower_max_z_mm': float(shower_max_z),
        'shower_max_X0': float(shower_max_X0),
        'r90_mm': float(r90),
        'r95_mm': float(r95),
        'r99_mm': float(r99),
        'r90_moliere': float(r90 / moliere_radius),
        'r95_moliere': float(r95 / moliere_radius),
        'r99_moliere': float(r99 / moliere_radius)
    }

# Scaling plots
energies = [10.0, 50.0, 100.0]
shower_max_X0 = [results[f'{e}GeV']['shower_max_X0'] for e in energies]
r90_moliere = [results[f'{e}GeV']['r90_moliere'] for e in energies]
r95_moliere = [results[f'{e}GeV']['r95_moliere'] for e in energies]
r99_moliere = [results[f'{e}GeV']['r99_moliere'] for e in energies]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Shower maximum scaling
ax1.semilogx(energies, shower_max_X0, 'o-', markersize=8)
ax1.set_xlabel('Energy (GeV)')
ax1.set_ylabel('Shower Maximum (X₀)')
ax1.set_title('Shower Maximum vs Energy')
ax1.grid(True, alpha=0.3)

# Transverse containment scaling
ax2.semilogx(energies, r90_moliere, 'o-', label='90% containment', markersize=8)
ax2.semilogx(energies, r95_moliere, 's-', label='95% containment', markersize=8)
ax2.semilogx(energies, r99_moliere, '^-', label='99% containment', markersize=8)
ax2.set_xlabel('Energy (GeV)')
ax2.set_ylabel('Radius (Moliere radii)')
ax2.set_title('Transverse Containment vs Energy')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('shower_scaling.png', dpi=150)
plt.close()

results['plots'] = ['shower_scaling.png']
results['metadata'] = {
    'X0_pbwo4_cm': X0_pbwo4,
    'depth_radiation_lengths': depth_radiation_lengths,
    'moliere_radius_mm': moliere_radius / 10
}

print(json.dumps(results))