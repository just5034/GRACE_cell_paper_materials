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
depth_radiation_lengths = 25.0  # X₀ for calorimeter depth

results = {}

fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

for edir in energy_dirs:
    energy_str = os.path.basename(edir)
    true_energy = float(energy_str.replace('energy_', '').replace('GeV', ''))
    
    hits_file = os.path.join(edir, 'pbwo4_calorimeter_em_hits_data.parquet')
    events_file = os.path.join(edir, 'pbwo4_calorimeter_em_events.parquet')
    
    if not os.path.exists(hits_file) or not os.path.exists(events_file):
        continue
    
    hits = pd.read_parquet(hits_file)
    events = pd.read_parquet(events_file)
    
    # Convert z to radiation lengths
    hits['z_X0'] = hits['z'] / 10.0 / X0_pbwo4  # mm to cm, then to X₀
    
    # Longitudinal profile
    z_bins = np.linspace(0, depth_radiation_lengths, 50)
    z_hist, _ = np.histogram(hits['z_X0'], bins=z_bins, weights=hits['edep'])
    z_centers = (z_bins[:-1] + z_bins[1:]) / 2
    z_profile = z_hist / events.shape[0]  # Average per event
    
    # Find shower maximum
    shower_max_idx = np.argmax(z_profile)
    shower_max_z = z_centers[shower_max_idx]
    
    # Transverse profile
    hits['r'] = np.sqrt(hits['x']**2 + hits['y']**2)  # mm
    r_bins = np.linspace(0, 100, 50)  # mm
    r_hist, _ = np.histogram(hits['r'], bins=r_bins, weights=hits['edep'])
    r_centers = (r_bins[:-1] + r_bins[1:]) / 2
    r_profile = r_hist / events.shape[0]
    
    # Calculate containment radius (90% energy)
    r_cumsum = np.cumsum(r_profile)
    r_total = r_cumsum[-1]
    r90_idx = np.where(r_cumsum >= 0.9 * r_total)[0]
    r90 = r_centers[r90_idx[0]] if len(r90_idx) > 0 else r_centers[-1]
    
    # Calculate Moliere radius
    r_moliere_idx = np.where(r_cumsum >= 0.9 * r_total)[0]
    r_moliere = r_centers[r_moliere_idx[0]] / 10.0 / X0_pbwo4 if len(r_moliere_idx) > 0 else 0
    
    results[f'{true_energy}GeV'] = {
        'shower_max_X0': float(shower_max_z),
        'containment_radius_90_mm': float(r90),
        'moliere_radius_X0': float(r_moliere),
        'total_edep_MeV': float(events['totalEdep'].mean())
    }
    
    # Plot profiles
    ax1.plot(z_centers, z_profile, label=f'{true_energy} GeV', marker='o', markersize=3)
    ax2.plot(r_centers, r_profile, label=f'{true_energy} GeV', marker='o', markersize=3)

ax1.set_xlabel('Depth (X₀)')
ax1.set_ylabel('Energy deposition (MeV/event)')
ax1.set_title('Longitudinal shower profile')
ax1.legend()
ax1.grid(True, alpha=0.3)

ax2.set_xlabel('Radius (mm)')
ax2.set_ylabel('Energy deposition (MeV/event)')
ax2.set_title('Transverse shower profile')
ax2.legend()
ax2.grid(True, alpha=0.3)

# Extract energies and shower max positions for scaling plots
energies = []
shower_maxs = []
r90s = []
for key, val in results.items():
    energies.append(float(key.replace('GeV', '')))
    shower_maxs.append(val['shower_max_X0'])
    r90s.append(val['containment_radius_90_mm'])

energies = np.array(energies)
shower_maxs = np.array(shower_maxs)
r90s = np.array(r90s)

# Fit logarithmic scaling for shower maximum
log_e = np.log(energies)
fit_coeffs = np.polyfit(log_e, shower_maxs, 1)
fit_line = fit_coeffs[0] * log_e + fit_coeffs[1]

ax3.scatter(energies, shower_maxs, s=100, color='blue', label='Data')
ax3.plot(energies, fit_line, 'r--', label=f'Fit: {fit_coeffs[0]:.2f}·ln(E) + {fit_coeffs[1]:.2f}')
ax3.set_xlabel('Energy (GeV)')
ax3.set_ylabel('Shower maximum (X₀)')
ax3.set_title('Shower maximum vs energy')
ax3.set_xscale('log')
ax3.legend()
ax3.grid(True, alpha=0.3)

# Transverse containment scaling
ax4.scatter(energies, r90s, s=100, color='green')
ax4.set_xlabel('Energy (GeV)')
ax4.set_ylabel('90% containment radius (mm)')
ax4.set_title('Transverse containment vs energy')
ax4.set_xscale('log')
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('shower_profiles_analysis.png', dpi=150)

results['plots'] = ['shower_profiles_analysis.png']
results['scaling'] = {
    'shower_max_fit': {
        'slope': float(fit_coeffs[0]),
        'intercept': float(fit_coeffs[1]),
        'formula': f'shower_max = {fit_coeffs[0]:.2f}·ln(E) + {fit_coeffs[1]:.2f}'
    }
}

print(json.dumps(results))