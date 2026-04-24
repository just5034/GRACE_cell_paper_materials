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

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/paper_cms_ecal_claude-sonnet-4-20250514_20260309_204728'

# Read extracted setup to get material info
with open(os.path.join(base_dir, 'extracted_setup.json'), 'r') as f:
    setup = json.load(f)

# Calculate derived properties with explicit depth_radiation_lengths
materials = setup['materials']
for mat in materials:
    if mat['name'] == 'PbWO4':
        mat['depth_radiation_lengths'] = 25.0  # 25 X₀ for good containment
        mat['depth_cm'] = mat['depth_radiation_lengths'] * mat['radiation_length_cm']

# Analyze baseline (detector_2) and improved (detector) performance
energies = ['1.000', '5.000', '20.000']
results = {
    'baseline': {},
    'improved': {},
    'comparison': {}
}

for energy in energies:
    energy_dir = os.path.join(base_dir, f'energy_{energy}GeV')
    true_e = float(energy)
    
    # Baseline analysis (detector_2)
    baseline_events = pd.read_parquet(os.path.join(energy_dir, 'detector_2_em_events.parquet'))
    baseline_mean = baseline_events['totalEdep'].mean() / 1000.0  # MeV to GeV
    baseline_std = baseline_events['totalEdep'].std() / 1000.0
    baseline_resolution = baseline_std / baseline_mean if baseline_mean > 0 else 0
    
    results['baseline'][f'{true_e}GeV'] = {
        'mean_edep_gev': baseline_mean,
        'resolution': baseline_resolution,
        'containment': baseline_mean / true_e
    }
    
    # Improved analysis (detector)
    improved_events = pd.read_parquet(os.path.join(energy_dir, 'detector_em_events.parquet'))
    improved_mean = improved_events['totalEdep'].mean() / 1000.0
    improved_std = improved_events['totalEdep'].std() / 1000.0
    improved_resolution = improved_std / improved_mean if improved_mean > 0 else 0
    
    results['improved'][f'{true_e}GeV'] = {
        'mean_edep_gev': improved_mean,
        'resolution': improved_resolution,
        'containment': improved_mean / true_e
    }
    
    # Calculate improvements
    results['comparison'][f'{true_e}GeV'] = {
        'resolution_improvement': (baseline_resolution - improved_resolution) / baseline_resolution * 100,
        'containment_improvement': (improved_mean - baseline_mean) / baseline_mean * 100
    }

# Create comparison plots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Resolution comparison
energies_float = [1.0, 5.0, 20.0]
baseline_res = [results['baseline'][f'{e}GeV']['resolution'] for e in energies_float]
improved_res = [results['improved'][f'{e}GeV']['resolution'] for e in energies_float]

ax1.plot(energies_float, baseline_res, 'o-', label='Baseline', markersize=8)
ax1.plot(energies_float, improved_res, 's-', label='Improved', markersize=8)
ax1.set_xlabel('Energy (GeV)')
ax1.set_ylabel('Energy Resolution (σ/E)')
ax1.set_title('Energy Resolution Comparison')
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.set_xscale('log')

# Containment comparison
baseline_cont = [results['baseline'][f'{e}GeV']['containment'] for e in energies_float]
improved_cont = [results['improved'][f'{e}GeV']['containment'] for e in energies_float]

ax2.plot(energies_float, baseline_cont, 'o-', label='Baseline', markersize=8)
ax2.plot(energies_float, improved_cont, 's-', label='Improved', markersize=8)
ax2.set_xlabel('Energy (GeV)')
ax2.set_ylabel('Energy Containment Fraction')
ax2.set_title('Energy Containment Comparison')
ax2.legend()
ax2.grid(True, alpha=0.3)
ax2.set_xscale('log')

plt.tight_layout()
plt.savefig('performance_comparison.png', dpi=150)

results['plots'] = ['performance_comparison.png']

# Summary statistics
avg_resolution_improvement = np.mean([results['comparison'][f'{e}GeV']['resolution_improvement'] for e in energies_float])
avg_containment_improvement = np.mean([results['comparison'][f'{e}GeV']['containment_improvement'] for e in energies_float])

results['summary'] = {
    'average_resolution_improvement_percent': avg_resolution_improvement,
    'average_containment_improvement_percent': avg_containment_improvement,
    'material_properties': materials
}

print(json.dumps(results))