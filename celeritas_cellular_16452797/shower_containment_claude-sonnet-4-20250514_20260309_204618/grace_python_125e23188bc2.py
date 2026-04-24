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

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/shower_containment_claude-sonnet-4-20250514_20260309_204618'
energies = [1.0, 5.0, 20.0]
depths = [16, 20, 25]
X0_pbwo4 = 0.89  # cm

results = {
    'containment_analysis': {},
    'resolution_analysis': {},
    'shower_max_analysis': {},
    'leakage_at_20GeV': {}
}

for depth in depths:
    for energy in energies:
        energy_dir = os.path.join(base_dir, f'energy_{energy:.3f}GeV')
        
        # Read events data
        events_file = os.path.join(energy_dir, f'pbwo4_{depth}x0_em_events.parquet')
        if not os.path.exists(events_file):
            continue
            
        events = pd.read_parquet(events_file)
        
        # Calculate containment fraction and resolution
        mean_edep = events['totalEdep'].mean()  # MeV
        std_edep = events['totalEdep'].std()    # MeV
        containment_fraction = mean_edep / (energy * 1000)  # Convert GeV to MeV
        resolution = std_edep / mean_edep if mean_edep > 0 else 0
        
        # Store results
        key = f'{depth}X0_{energy}GeV'
        results['containment_analysis'][key] = {
            'containment_fraction': containment_fraction,
            'mean_edep_MeV': mean_edep,
            'true_energy_MeV': energy * 1000
        }
        results['resolution_analysis'][key] = {
            'resolution': resolution,
            'sigma_MeV': std_edep
        }
        
        # Calculate shower maximum from hits data
        hits_file = os.path.join(energy_dir, f'pbwo4_{depth}x0_em_hits_data.parquet')
        if os.path.exists(hits_file):
            hits = pd.read_parquet(hits_file)
            
            # Group by z-position bins to find shower maximum
            z_bins = np.linspace(0, depth * X0_pbwo4 * 10, 50)  # mm
            z_profile = []
            for i in range(len(z_bins)-1):
                mask = (hits['z'] >= z_bins[i]) & (hits['z'] < z_bins[i+1])
                z_profile.append(hits[mask]['edep'].sum())
            
            if len(z_profile) > 0 and max(z_profile) > 0:
                shower_max_idx = np.argmax(z_profile)
                shower_max_z = (z_bins[shower_max_idx] + z_bins[shower_max_idx+1]) / 2
                shower_max_X0 = shower_max_z / (X0_pbwo4 * 10)  # Convert mm to X0
                
                results['shower_max_analysis'][key] = {
                    'shower_max_z_mm': shower_max_z,
                    'shower_max_X0': shower_max_X0
                }
        
        # Calculate leakage at 20 GeV
        if energy == 20.0:
            leakage_fraction = 1.0 - containment_fraction
            results['leakage_at_20GeV'][f'{depth}X0'] = {
                'leakage_percent': leakage_fraction * 100,
                'containment_percent': containment_fraction * 100
            }

# Create containment vs depth plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Plot 1: Containment fraction vs depth for different energies
for energy in energies:
    containment_values = []
    depth_values = []
    for depth in depths:
        key = f'{depth}X0_{energy}GeV'
        if key in results['containment_analysis']:
            containment_values.append(results['containment_analysis'][key]['containment_fraction'])
            depth_values.append(depth)
    if containment_values:
        ax1.plot(depth_values, containment_values, 'o-', label=f'{energy} GeV')

ax1.set_xlabel('Calorimeter Depth (X₀)')
ax1.set_ylabel('Energy Containment Fraction')
ax1.set_title('Energy Containment vs Calorimeter Depth')
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.axhline(y=0.99, color='r', linestyle='--', alpha=0.5, label='99% containment')

# Plot 2: Resolution vs depth
for energy in energies:
    resolution_values = []
    depth_values = []
    for depth in depths:
        key = f'{depth}X0_{energy}GeV'
        if key in results['resolution_analysis']:
            resolution_values.append(results['resolution_analysis'][key]['resolution'] * 100)
            depth_values.append(depth)
    if resolution_values:
        ax2.plot(depth_values, resolution_values, 'o-', label=f'{energy} GeV')

ax2.set_xlabel('Calorimeter Depth (X₀)')
ax2.set_ylabel('Energy Resolution (%)')
ax2.set_title('Energy Resolution vs Calorimeter Depth')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('containment_analysis.png', dpi=150)
plt.close()

# Determine minimum depth for <1% leakage at 20 GeV
min_depth_for_target = None
for depth in sorted(depths):
    key = f'{depth}X0'
    if key in results['leakage_at_20GeV']:
        if results['leakage_at_20GeV'][key]['leakage_percent'] < 1.0:
            min_depth_for_target = depth
            break

results['minimum_depth_analysis'] = {
    'target_leakage_percent': 1.0,
    'target_energy_GeV': 20.0,
    'minimum_depth_X0': min_depth_for_target,
    'minimum_depth_cm': min_depth_for_target * X0_pbwo4 if min_depth_for_target else None
}

results['plot'] = 'containment_analysis.png'

print(json.dumps(results))