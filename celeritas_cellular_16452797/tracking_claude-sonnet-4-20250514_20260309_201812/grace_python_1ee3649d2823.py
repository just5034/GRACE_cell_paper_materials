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
from scipy import stats

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/tracking_claude-sonnet-4-20250514_20260309_201812'
energies = ['1.000', '10.000', '30.000']
configs = ['baseline_tracker', 'detector_3', 'detector_4']

results = {}

# Material budget calculation (Si radiation length = 9.37 cm)
X0_Si = 9.37  # cm
layer_configs = {
    'baseline_tracker': {'n_layers': 4, 'thickness_um': 250, 'spacing_cm': 33.33},
    'detector_3': {'n_layers': 8, 'thickness_um': 200, 'spacing_cm': 14.29},
    'detector_4': {'n_layers': 4, 'thickness_um': 100, 'spacing_cm': 33.33}
}

for config in configs:
    results[config] = {
        'material_budget': {},
        'hit_efficiency': {},
        'energy_deposits': {},
        'momentum_resolution_proxy': {}
    }
    
    # Calculate material budget
    n_layers = layer_configs[config]['n_layers']
    thickness_cm = layer_configs[config]['thickness_um'] / 10000.0
    total_X0_percent = n_layers * thickness_cm / X0_Si * 100
    results[config]['material_budget'] = {
        'n_layers': n_layers,
        'thickness_um': layer_configs[config]['thickness_um'],
        'total_percent_X0': total_X0_percent
    }
    
    for energy in energies:
        energy_dir = os.path.join(base_dir, f'energy_{energy}GeV')
        
        # Find the correct parquet files
        events_pattern = os.path.join(energy_dir, f'{config}_mum_events.parquet')
        hits_pattern = os.path.join(energy_dir, f'{config}_mum_hits_data.parquet')
        
        events_files = glob.glob(events_pattern)
        hits_files = glob.glob(hits_pattern)
        
        if not events_files or not hits_files:
            continue
            
        events_df = pd.read_parquet(events_files[0])
        hits_df = pd.read_parquet(hits_files[0])
        
        true_e = float(energy)
        
        # Hit efficiency
        n_events = len(events_df)
        events_with_hits = len(events_df[events_df['nHits'] > 0])
        hit_efficiency = events_with_hits / n_events if n_events > 0 else 0
        
        # Energy deposits per layer (using z-position binning)
        if config == 'baseline_tracker':
            z_bins = np.linspace(-5, 1005, n_layers + 1)
        elif config == 'detector_3':
            z_bins = np.linspace(-5, 1005, n_layers + 1)
        else:  # detector_4
            z_bins = np.linspace(-5, 1005, n_layers + 1)
            
        hits_df['layer'] = pd.cut(hits_df['z'], bins=z_bins, labels=range(n_layers))
        layer_edep = hits_df.groupby('layer')['edep'].sum()
        
        # Momentum resolution proxy (RMS of hit positions in x,y)
        x_rms = hits_df.groupby('eventID')['x'].std().mean()
        y_rms = hits_df.groupby('eventID')['y'].std().mean()
        position_resolution = np.sqrt(x_rms**2 + y_rms**2)
        
        results[config]['hit_efficiency'][f'{true_e}GeV'] = hit_efficiency
        results[config]['energy_deposits'][f'{true_e}GeV'] = {
            'mean_edep_per_layer_MeV': layer_edep.mean() if len(layer_edep) > 0 else 0,
            'total_edep_MeV': layer_edep.sum()
        }
        results[config]['momentum_resolution_proxy'][f'{true_e}GeV'] = position_resolution

# Create comparison plots
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Material budget comparison
ax = axes[0, 0]
x_pos = np.arange(len(configs))
material_budgets = [results[c]['material_budget']['total_percent_X0'] for c in configs]
ax.bar(x_pos, material_budgets)
ax.set_xlabel('Configuration')
ax.set_ylabel('Material Budget (% X0)')
ax.set_title('Material Budget Comparison')
ax.set_xticks(x_pos)
ax.set_xticklabels(configs)

# Hit efficiency vs energy
ax = axes[0, 1]
for config in configs:
    energies_plot = []
    efficiencies = []
    for e in energies:
        if f'{float(e)}GeV' in results[config]['hit_efficiency']:
            energies_plot.append(float(e))
            efficiencies.append(results[config]['hit_efficiency'][f'{float(e)}GeV'])
    ax.plot(energies_plot, efficiencies, 'o-', label=config)
ax.set_xlabel('Energy (GeV)')
ax.set_ylabel('Hit Efficiency')
ax.set_title('Hit Efficiency vs Energy')
ax.set_xscale('log')
ax.legend()

# Position resolution proxy vs energy
ax = axes[1, 0]
for config in configs:
    energies_plot = []
    resolutions = []
    for e in energies:
        if f'{float(e)}GeV' in results[config]['momentum_resolution_proxy']:
            energies_plot.append(float(e))
            resolutions.append(results[config]['momentum_resolution_proxy'][f'{float(e)}GeV'])
    ax.plot(energies_plot, resolutions, 'o-', label=config)
ax.set_xlabel('Energy (GeV)')
ax.set_ylabel('Position Resolution (mm)')
ax.set_title('Position Resolution Proxy vs Energy')
ax.set_xscale('log')
ax.legend()

# Figure of merit: resolution/material_budget
ax = axes[1, 1]
for config in configs:
    energies_plot = []
    fom = []
    mat_budget = results[config]['material_budget']['total_percent_X0']
    for e in energies:
        if f'{float(e)}GeV' in results[config]['momentum_resolution_proxy']:
            energies_plot.append(float(e))
            res = results[config]['momentum_resolution_proxy'][f'{float(e)}GeV']
            fom.append(res / mat_budget if mat_budget > 0 else 0)
    ax.plot(energies_plot, fom, 'o-', label=config)
ax.set_xlabel('Energy (GeV)')
ax.set_ylabel('Resolution / Material Budget')
ax.set_title('Figure of Merit (lower is better)')
ax.set_xscale('log')
ax.legend()

plt.tight_layout()
plt.savefig('tracker_comparison.png', dpi=150)
plt.close()

results['plot'] = 'tracker_comparison.png'

print(json.dumps(results))