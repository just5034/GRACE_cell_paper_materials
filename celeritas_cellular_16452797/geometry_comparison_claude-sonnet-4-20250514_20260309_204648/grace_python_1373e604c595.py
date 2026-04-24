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
import glob
import os

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/geometry_comparison_claude-sonnet-4-20250514_20260309_204648'
energies = [1.0, 5.0, 20.0]
geometries = ['box_calorimeter_2', 'projective_tower_calorimeter', 'accordion_calorimeter']

# Collect data for all geometries
results = {}
for geom in geometries:
    results[geom] = {
        'energies': [],
        'resolutions': [],
        'mean_responses': [],
        'uniformity': []
    }
    
    for energy in energies:
        edir = os.path.join(base_dir, f'energy_{energy:.3f}GeV')
        events_files = glob.glob(os.path.join(edir, f'{geom}_em_events.parquet'))
        
        if events_files:
            events = pd.read_parquet(events_files[0])
            mean_edep = events['totalEdep'].mean()
            std_edep = events['totalEdep'].std()
            resolution = std_edep / mean_edep if mean_edep > 0 else 0
            
            results[geom]['energies'].append(energy)
            results[geom]['resolutions'].append(resolution)
            results[geom]['mean_responses'].append(mean_edep / 1000.0)  # MeV to GeV
            
            # Calculate uniformity from hits data
            hits_files = glob.glob(os.path.join(edir, f'{geom}_em_hits_data.parquet'))
            if hits_files:
                hits = pd.read_parquet(hits_files[0])
                # Group by event and calculate RMS of hit positions
                event_groups = hits.groupby('eventID')
                x_rms = event_groups['x'].std().mean()
                y_rms = event_groups['y'].std().mean()
                uniformity = np.sqrt(x_rms**2 + y_rms**2)
                results[geom]['uniformity'].append(uniformity)
            else:
                results[geom]['uniformity'].append(0)

# Create publication-quality plots
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

# Plot 1: Energy Resolution vs Energy
for geom in geometries:
    if results[geom]['energies']:
        ax1.plot(results[geom]['energies'], np.array(results[geom]['resolutions'])*100, 
                'o-', label=geom.replace('_calorimeter', '').replace('_', ' ').title(), 
                linewidth=2, markersize=8)
ax1.set_xlabel('Beam Energy (GeV)', fontsize=12)
ax1.set_ylabel('Energy Resolution σ/E (%)', fontsize=12)
ax1.set_xscale('log')
ax1.grid(True, alpha=0.3)
ax1.legend(fontsize=10)
ax1.set_title('Energy Resolution Comparison', fontsize=14)

# Plot 2: Response Linearity
for geom in geometries:
    if results[geom]['energies']:
        response_ratio = np.array(results[geom]['mean_responses']) / np.array(results[geom]['energies'])
        ax2.plot(results[geom]['energies'], response_ratio, 
                'o-', label=geom.replace('_calorimeter', '').replace('_', ' ').title(),
                linewidth=2, markersize=8)
ax2.set_xlabel('Beam Energy (GeV)', fontsize=12)
ax2.set_ylabel('Response / True Energy', fontsize=12)
ax2.set_xscale('log')
ax2.axhline(y=1.0, color='k', linestyle='--', alpha=0.5)
ax2.grid(True, alpha=0.3)
ax2.legend(fontsize=10)
ax2.set_title('Response Linearity', fontsize=14)

# Plot 3: Response Uniformity
for geom in geometries:
    if results[geom]['energies'] and any(results[geom]['uniformity']):
        ax3.plot(results[geom]['energies'], results[geom]['uniformity'], 
                'o-', label=geom.replace('_calorimeter', '').replace('_', ' ').title(),
                linewidth=2, markersize=8)
ax3.set_xlabel('Beam Energy (GeV)', fontsize=12)
ax3.set_ylabel('Spatial RMS (mm)', fontsize=12)
ax3.set_xscale('log')
ax3.grid(True, alpha=0.3)
ax3.legend(fontsize=10)
ax3.set_title('Response Uniformity', fontsize=14)

# Plot 4: Resolution scaling
for geom in geometries:
    if results[geom]['energies']:
        # Fit resolution = a/sqrt(E) + b
        E = np.array(results[geom]['energies'])
        res = np.array(results[geom]['resolutions'])
        if len(E) > 1:
            ax4.plot(1/np.sqrt(E), res*100, 'o', label=geom.replace('_calorimeter', '').replace('_', ' ').title(),
                    markersize=8)
ax4.set_xlabel('1/√E (GeV^-1/2)', fontsize=12)
ax4.set_ylabel('Energy Resolution σ/E (%)', fontsize=12)
ax4.grid(True, alpha=0.3)
ax4.legend(fontsize=10)
ax4.set_title('Resolution Scaling', fontsize=14)

plt.tight_layout()
plt.savefig(os.path.join(base_dir, 'geometry_comparison_plots.png'), dpi=300, bbox_inches='tight')

# Summary statistics
summary = {
    'best_resolution_geometry': '',
    'best_uniformity_geometry': '',
    'resolution_comparison': {},
    'uniformity_comparison': {},
    'linearity_comparison': {},
    'plot_file': 'geometry_comparison_plots.png'
}

# Find best performers
avg_resolutions = {}
avg_uniformity = {}
for geom in geometries:
    if results[geom]['resolutions']:
        avg_resolutions[geom] = np.mean(results[geom]['resolutions'])
    if results[geom]['uniformity'] and any(results[geom]['uniformity']):
        avg_uniformity[geom] = np.mean([u for u in results[geom]['uniformity'] if u > 0])

if avg_resolutions:
    summary['best_resolution_geometry'] = min(avg_resolutions, key=avg_resolutions.get)
if avg_uniformity:
    summary['best_uniformity_geometry'] = min(avg_uniformity, key=avg_uniformity.get)

# Detailed comparisons
for geom in geometries:
    if results[geom]['energies']:
        summary['resolution_comparison'][geom] = {
            f'{e}GeV': f'{r*100:.2f}%' 
            for e, r in zip(results[geom]['energies'], results[geom]['resolutions'])
        }
        summary['uniformity_comparison'][geom] = {
            f'{e}GeV': f'{u:.2f}mm' 
            for e, u in zip(results[geom]['energies'], results[geom]['uniformity'])
        }
        response_ratio = np.array(results[geom]['mean_responses']) / np.array(results[geom]['energies'])
        summary['linearity_comparison'][geom] = {
            f'{e}GeV': f'{r:.3f}' 
            for e, r in zip(results[geom]['energies'], response_ratio)
        }

print(json.dumps(summary))