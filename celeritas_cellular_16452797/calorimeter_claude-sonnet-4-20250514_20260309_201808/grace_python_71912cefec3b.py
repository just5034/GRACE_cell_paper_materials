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

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/calorimeter_claude-sonnet-4-20250514_20260309_201808'
energies = [10.0, 30.0, 50.0]
configurations = ['baseline_calorimeter', 'detector_4', 'detector_8']

results = {}

for config in configurations:
    results[config] = {
        'energies': [],
        'mean_edep': [],
        'resolution': [],
        'response': [],
        'containment': []
    }
    
    for energy in energies:
        energy_dir = os.path.join(base_dir, f'energy_{energy:.3f}GeV')
        
        # Find events file
        events_files = glob.glob(os.path.join(energy_dir, f'{config}_*_events.parquet'))
        if not events_files:
            events_files = glob.glob(os.path.join(energy_dir, '*_events.parquet'))
        
        if events_files:
            events_file = events_files[0]
            events = pd.read_parquet(events_file)
            
            mean_edep = events['totalEdep'].mean() / 1000.0  # MeV to GeV
            std_edep = events['totalEdep'].std() / 1000.0
            resolution = std_edep / mean_edep if mean_edep > 0 else 0
            response = mean_edep / energy
            
            # Calculate containment from hits file
            hits_files = glob.glob(os.path.join(energy_dir, f'{config}_*_hits_data.parquet'))
            if not hits_files:
                hits_files = glob.glob(os.path.join(energy_dir, '*_hits_data.parquet'))
            
            containment = 1.0  # default
            if hits_files:
                hits_file = hits_files[0]
                hits = pd.read_parquet(hits_file)
                
                # Calculate shower containment based on z position
                max_z = hits['z'].max()
                detector_depth = 1200.0 if config == 'detector_8' else 82.5
                containment = len(hits[hits['z'] < detector_depth * 0.95]) / len(hits)
            
            results[config]['energies'].append(energy)
            results[config]['mean_edep'].append(mean_edep)
            results[config]['resolution'].append(resolution)
            results[config]['response'].append(response)
            results[config]['containment'].append(containment)

# Create plots
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

# Energy resolution vs energy
ax1.set_xlabel('Beam Energy [GeV]')
ax1.set_ylabel('Energy Resolution (σ/E)')
ax1.set_title('Energy Resolution')
for config in configurations:
    if results[config]['energies']:
        ax1.plot(results[config]['energies'], results[config]['resolution'], 
                'o-', label=config.replace('_', ' '))
ax1.legend()
ax1.grid(True)

# Response linearity
ax2.set_xlabel('Beam Energy [GeV]')
ax2.set_ylabel('Response (E_meas/E_true)')
ax2.set_title('Response Linearity')
for config in configurations:
    if results[config]['energies']:
        ax2.plot(results[config]['energies'], results[config]['response'], 
                'o-', label=config.replace('_', ' '))
ax2.axhline(y=1.0, color='k', linestyle='--', alpha=0.5)
ax2.legend()
ax2.grid(True)

# Shower containment
ax3.set_xlabel('Beam Energy [GeV]')
ax3.set_ylabel('Shower Containment')
ax3.set_title('Shower Containment')
for config in configurations:
    if results[config]['energies']:
        ax3.plot(results[config]['energies'], results[config]['containment'], 
                'o-', label=config.replace('_', ' '))
ax3.legend()
ax3.grid(True)

# Resolution comparison bar chart
ax4.set_xlabel('Configuration')
ax4.set_ylabel('Average Energy Resolution')
ax4.set_title('Average Resolution Comparison')
avg_resolutions = []
config_labels = []
for config in configurations:
    if results[config]['resolution']:
        avg_resolutions.append(np.mean(results[config]['resolution']))
        config_labels.append(config.replace('_', ' '))
ax4.bar(config_labels, avg_resolutions)
ax4.grid(True, axis='y')

plt.tight_layout()
plt.savefig('calorimeter_performance_analysis.png', dpi=150)

# Summary statistics
summary = {}
for config in configurations:
    if results[config]['energies']:
        summary[config] = {
            'avg_resolution': np.mean(results[config]['resolution']),
            'resolution_at_30GeV': results[config]['resolution'][results[config]['energies'].index(30.0)] if 30.0 in results[config]['energies'] else None,
            'avg_response': np.mean(results[config]['response']),
            'response_variation': np.std(results[config]['response']),
            'avg_containment': np.mean(results[config]['containment']),
            'data_points': len(results[config]['energies'])
        }

output = {
    'raw_results': results,
    'summary': summary,
    'plot': 'calorimeter_performance_analysis.png'
}

print(json.dumps(output))