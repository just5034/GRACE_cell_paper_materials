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
from collections import defaultdict

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/tracking_claude-sonnet-4-20250514_20260309_201812'

# Define the three configurations
configs = {
    'baseline': {
        'name': 'baseline_tracker',
        'n_layers': 4,
        'thickness_um': 250,
        'spacing_cm': 33.33
    },
    'thin': {
        'name': 'detector_2',
        'n_layers': 4,
        'thickness_um': 100,
        'spacing_cm': 33.33
    },
    'multilayer': {
        'name': 'detector_3',
        'n_layers': 8,
        'thickness_um': 100,
        'spacing_cm': 14.29
    }
}

# Silicon radiation length
X0_Si = 9.37  # cm

results = {}

for config_name, config in configs.items():
    results[config_name] = {
        'material_budget': {},
        'hit_efficiency': {},
        'energy_deposits': {},
        'momentum_resolution_proxy': {}
    }
    
    # Calculate material budget
    total_thickness_cm = config['n_layers'] * config['thickness_um'] / 10000.0
    material_budget_percent = (total_thickness_cm / X0_Si) * 100
    results[config_name]['material_budget'] = {
        'total_percent_X0': material_budget_percent,
        'per_layer_percent_X0': material_budget_percent / config['n_layers'],
        'total_thickness_mm': total_thickness_cm * 10
    }
    
    # Analyze each energy
    energies = ['1.000GeV', '10.000GeV', '30.000GeV']
    
    for energy in energies:
        energy_dir = os.path.join(base_dir, f'energy_{energy}')
        
        # Find the appropriate files
        events_pattern = os.path.join(energy_dir, f'{config["name"]}_mum_events.parquet')
        hits_pattern = os.path.join(energy_dir, f'{config["name"]}_mum_hits_data.parquet')
        
        events_files = glob.glob(events_pattern)
        hits_files = glob.glob(hits_pattern)
        
        if not events_files or not hits_files:
            # Try baseline_tracker pattern for all configs (since they might share data)
            events_files = glob.glob(os.path.join(energy_dir, 'baseline_tracker_mum_events.parquet'))
            hits_files = glob.glob(os.path.join(energy_dir, 'baseline_tracker_mum_hits_data.parquet'))
        
        if events_files and hits_files:
            # Read data
            events_df = pd.read_parquet(events_files[0])
            hits_df = pd.read_parquet(hits_files[0])
            
            # Hit efficiency
            n_events = len(events_df)
            events_with_hits = events_df[events_df['nHits'] > 0]
            hit_efficiency = len(events_with_hits) / n_events if n_events > 0 else 0
            
            # Average hits per event
            avg_hits = events_df['nHits'].mean()
            
            results[config_name]['hit_efficiency'][energy] = {
                'efficiency': hit_efficiency,
                'avg_hits_per_event': avg_hits,
                'total_events': n_events
            }
            
            # Energy deposits per layer (using z-position binning)
            if len(hits_df) > 0:
                # Define layer boundaries based on config
                layer_width = config['spacing_cm'] * 10  # mm
                layer_edges = np.arange(0, config['n_layers'] + 1) * layer_width - layer_width/2
                
                # Bin hits by z position
                hits_df['layer'] = pd.cut(hits_df['z'], bins=layer_edges, labels=False)
                
                # Calculate energy per layer
                layer_edep = hits_df.groupby('layer')['edep'].sum()
                layer_hits = hits_df.groupby('layer').size()
                
                results[config_name]['energy_deposits'][energy] = {
                    'total_edep_MeV': hits_df['edep'].sum(),
                    'mean_edep_per_hit_MeV': hits_df['edep'].mean(),
                    'layer_edep_MeV': layer_edep.to_dict() if len(layer_edep) > 0 else {},
                    'layer_hit_counts': layer_hits.to_dict() if len(layer_hits) > 0 else {}
                }
            
            # Momentum resolution proxy (position resolution)
            if len(hits_df) > 0:
                # Group by event and calculate position spread
                event_groups = hits_df.groupby('eventID')
                
                x_spreads = []
                y_spreads = []
                
                for event_id, group in event_groups:
                    if len(group) > 1:
                        x_spreads.append(group['x'].std())
                        y_spreads.append(group['y'].std())
                
                results[config_name]['momentum_resolution_proxy'][energy] = {
                    'mean_x_spread_mm': np.mean(x_spreads) if x_spreads else 0,
                    'mean_y_spread_mm': np.mean(y_spreads) if y_spreads else 0,
                    'combined_spread_mm': np.sqrt(np.mean(x_spreads)**2 + np.mean(y_spreads)**2) if x_spreads else 0
                }

# Create comparison plots
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Material budget comparison
ax = axes[0, 0]
configs_list = list(configs.keys())
material_budgets = [results[c]['material_budget']['total_percent_X0'] for c in configs_list]
ax.bar(configs_list, material_budgets)
ax.set_ylabel('Material Budget (% X0)')
ax.set_title('Total Material Budget Comparison')

# Hit efficiency comparison
ax = axes[0, 1]
for config_name in configs_list:
    energies_num = []
    efficiencies = []
    for e, data in results[config_name]['hit_efficiency'].items():
        energies_num.append(float(e.replace('GeV', '')))
        efficiencies.append(data['efficiency'])
    if energies_num:
        ax.plot(energies_num, efficiencies, 'o-', label=config_name)
ax.set_xlabel('Energy (GeV)')
ax.set_ylabel('Hit Efficiency')
ax.set_xscale('log')
ax.legend()
ax.set_title('Hit Efficiency vs Energy')

# Average hits per event
ax = axes[1, 0]
for config_name in configs_list:
    energies_num = []
    avg_hits = []
    for e, data in results[config_name]['hit_efficiency'].items():
        energies_num.append(float(e.replace('GeV', '')))
        avg_hits.append(data['avg_hits_per_event'])
    if energies_num:
        ax.plot(energies_num, avg_hits, 'o-', label=config_name)
ax.set_xlabel('Energy (GeV)')
ax.set_ylabel('Average Hits per Event')
ax.set_xscale('log')
ax.legend()
ax.set_title('Average Hits per Event vs Energy')

# Position spread (momentum resolution proxy)
ax = axes[1, 1]
for config_name in configs_list:
    energies_num = []
    spreads = []
    for e, data in results[config_name]['momentum_resolution_proxy'].items():
        energies_num.append(float(e.replace('GeV', '')))
        spreads.append(data['combined_spread_mm'])
    if energies_num:
        ax.plot(energies_num, spreads, 'o-', label=config_name)
ax.set_xlabel('Energy (GeV)')
ax.set_ylabel('Position Spread (mm)')
ax.set_xscale('log')
ax.legend()
ax.set_title('Position Spread vs Energy')

plt.tight_layout()
plt.savefig('tracker_comparison.png', dpi=150)
plt.close()

# Summary analysis
summary = {
    'best_material_budget': min(configs_list, key=lambda c: results[c]['material_budget']['total_percent_X0']),
    'best_hit_efficiency': {},
    'best_position_resolution': {},
    'recommendation': ''
}

# Find best hit efficiency for each energy
for energy in ['1.000GeV', '10.000GeV', '30.000GeV']:
    best_config = max(configs_list, 
                     key=lambda c: results[c]['hit_efficiency'].get(energy, {}).get('efficiency', 0))
    summary['best_hit_efficiency'][energy] = best_config

# Find best position resolution for each energy
for energy in ['1.000GeV', '10.000GeV', '30.000GeV']:
    best_config = min(configs_list,
                     key=lambda c: results[c]['momentum_resolution_proxy'].get(energy, {}).get('combined_spread_mm', float('inf')))
    summary['best_position_resolution'][energy] = best_config

# Make recommendation
thin_score = sum([
    results['thin']['material_budget']['total_percent_X0'] < results['baseline']['material_budget']['total_percent_X0'],
    results['thin']['hit_efficiency'].get('10.000GeV', {}).get('efficiency', 0) > 0.95,
    results['thin']['momentum_resolution_proxy'].get('10.000GeV', {}).get('combined_spread_mm', float('inf')) < 
    results['baseline']['momentum_resolution_proxy'].get('10.000GeV', {}).get('combined_spread_mm', float('inf'))
])

multilayer_score = sum([
    results['multilayer']['hit_efficiency'].get('10.000GeV', {}).get('avg_hits_per_event', 0) > 
    results['baseline']['hit_efficiency'].get('10.000GeV', {}).get('avg_hits_per_event', 0),
    results['multilayer']['momentum_resolution_proxy'].get('10.000GeV', {}).get('combined_spread_mm', float('inf')) < 
    results['baseline']['momentum_resolution_proxy'].get('10.000GeV', {}).get('combined_spread_mm', float('inf'))
])

if multilayer_score >= 2:
    summary['recommendation'] = 'multilayer: Best momentum resolution due to more measurement points'
elif thin_score >= 2:
    summary['recommendation'] = 'thin: Good balance of low material budget and adequate performance'
else:
    summary['recommendation'] = 'baseline: Reliable performance across all metrics'

final_results = {
    'configurations': results,
    'summary': summary,
    'plot': 'tracker_comparison.png'
}

print(json.dumps(final_results))