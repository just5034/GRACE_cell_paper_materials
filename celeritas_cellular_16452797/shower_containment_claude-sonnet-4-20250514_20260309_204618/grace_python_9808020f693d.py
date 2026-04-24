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
import matplotlib.pyplot as plt
import json
import os
import glob

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/shower_containment_claude-sonnet-4-20250514_20260309_204618'

# Define depths and energies
depths = [16, 20, 25]  # X0
energies = [1.0, 5.0, 20.0]  # GeV

# Collect containment data
containment_data = {}

for depth in depths:
    containment_data[depth] = {}
    
    for energy in energies:
        energy_dir = os.path.join(base_dir, f'energy_{energy:.3f}GeV')
        events_file = os.path.join(energy_dir, f'pbwo4_{depth}x0_em_events.parquet')
        
        if os.path.exists(events_file):
            events = pd.read_parquet(events_file)
            mean_edep = events['totalEdep'].mean()  # MeV
            containment_fraction = mean_edep / (energy * 1000)  # Convert GeV to MeV
            containment_data[depth][energy] = containment_fraction

# Create containment vs depth plot for each energy
plt.figure(figsize=(10, 8))

for energy in energies:
    depths_list = []
    containment_list = []
    
    for depth in depths:
        if energy in containment_data[depth]:
            depths_list.append(depth)
            containment_list.append(containment_data[depth][energy])
    
    plt.plot(depths_list, containment_list, 'o-', label=f'{energy} GeV', markersize=8, linewidth=2)

plt.xlabel('Calorimeter Depth (X₀)', fontsize=12)
plt.ylabel('Energy Containment Fraction', fontsize=12)
plt.title('Energy Containment vs Calorimeter Depth', fontsize=14)
plt.grid(True, alpha=0.3)
plt.legend(fontsize=11)
plt.ylim(0.9, 1.0)

# Add 99% containment line
plt.axhline(y=0.99, color='red', linestyle='--', alpha=0.5, label='99% containment')

plt.tight_layout()
plt.savefig('containment_vs_depth.png', dpi=150)
plt.close()

# Determine minimum depth for <1% leakage at 20 GeV
leakage_20gev = {}
for depth in depths:
    if 20.0 in containment_data[depth]:
        leakage_20gev[depth] = 1.0 - containment_data[depth][20.0]

# Find minimum depth for <1% leakage
min_depth_for_1pct = None
for depth in sorted(depths):
    if depth in leakage_20gev and leakage_20gev[depth] < 0.01:
        min_depth_for_1pct = depth
        break

# If no depth achieves <1% leakage, extrapolate
if min_depth_for_1pct is None:
    # Fit exponential to leakage data
    depths_fit = [d for d in depths if d in leakage_20gev]
    leakages_fit = [leakage_20gev[d] for d in depths_fit]
    
    if len(depths_fit) >= 2:
        # Log-linear fit: log(leakage) = a + b*depth
        log_leakages = np.log(leakages_fit)
        coeffs = np.polyfit(depths_fit, log_leakages, 1)
        
        # Find depth where leakage = 0.01
        target_log_leakage = np.log(0.01)
        min_depth_for_1pct = (target_log_leakage - coeffs[1]) / coeffs[0]

# Create leakage vs depth plot for 20 GeV
plt.figure(figsize=(8, 6))

depths_20gev = sorted([d for d in depths if d in leakage_20gev])
leakages_20gev = [leakage_20gev[d] * 100 for d in depths_20gev]  # Convert to percentage

plt.semilogy(depths_20gev, leakages_20gev, 'bo-', markersize=8, linewidth=2, label='20 GeV data')

# Add 1% leakage line
plt.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='1% leakage target')

# Add extrapolation if needed
if min_depth_for_1pct and min_depth_for_1pct > max(depths):
    depth_range = np.linspace(min(depths), min_depth_for_1pct * 1.1, 100)
    leakage_fit = np.exp(coeffs[0] * depth_range + coeffs[1]) * 100
    plt.plot(depth_range, leakage_fit, 'g--', alpha=0.5, label='Exponential fit')
    plt.axvline(x=min_depth_for_1pct, color='green', linestyle=':', alpha=0.5, label=f'Min depth: {min_depth_for_1pct:.1f} X₀')

plt.xlabel('Calorimeter Depth (X₀)', fontsize=12)
plt.ylabel('Energy Leakage (%)', fontsize=12)
plt.title('Energy Leakage vs Depth at 20 GeV', fontsize=14)
plt.grid(True, alpha=0.3)
plt.legend(fontsize=11)
plt.ylim(0.1, 10)

plt.tight_layout()
plt.savefig('leakage_vs_depth_20gev.png', dpi=150)
plt.close()

result = {
    "containment_data": containment_data,
    "leakage_20gev": leakage_20gev,
    "minimum_depth_for_1pct_leakage_at_20gev": min_depth_for_1pct,
    "plots": ["containment_vs_depth.png", "leakage_vs_depth_20gev.png"]
}

print(json.dumps(result))