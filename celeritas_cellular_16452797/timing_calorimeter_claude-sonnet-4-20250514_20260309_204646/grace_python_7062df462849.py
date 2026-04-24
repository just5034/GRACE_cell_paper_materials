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

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/timing_calorimeter_claude-sonnet-4-20250514_20260309_204646'

# Define detector configurations with proper depth_radiation_lengths
detector_configs = {
    'LYSO': {
        'pattern': 'lyso_calorimeter_em',
        'label': 'LYSO Crystal',
        'color': 'blue',
        'depth_radiation_lengths': 20.0  # 20 X₀ for ~99% containment
    },
    'Plastic': {
        'pattern': 'plastic_calorimeter_em',
        'label': 'Plastic Scintillator',
        'color': 'green',
        'depth_radiation_lengths': 20.0
    },
    'Sampling': {
        'pattern': 'detector_2_em',
        'label': 'W/Plastic Sampling',
        'color': 'red',
        'depth_radiation_lengths': 20.0
    }
}

energies = [1.0, 5.0, 20.0]
results = {}

# Analyze each detector
for det_name, config in detector_configs.items():
    results[det_name] = {
        'energies': [],
        'timing_resolution': [],
        'energy_resolution': []
    }
    
    for energy in energies:
        energy_dir = os.path.join(base_dir, f'energy_{energy:.3f}GeV')
        
        # Find hits file
        hits_files = glob.glob(os.path.join(energy_dir, f'{config["pattern"]}_hits_data.parquet'))
        if not hits_files:
            continue
            
        # Find events file
        events_files = glob.glob(os.path.join(energy_dir, f'{config["pattern"]}_events.parquet'))
        if not events_files:
            continue
            
        # Read data
        hits = pd.read_parquet(hits_files[0])
        events = pd.read_parquet(events_files[0])
        
        # Calculate energy resolution
        mean_edep = events['totalEdep'].mean()
        std_edep = events['totalEdep'].std()
        energy_res = (std_edep / mean_edep * 100) if mean_edep > 0 else 0
        
        # Calculate timing resolution from first hit times
        first_hits = hits.groupby('eventID')['time'].min()
        timing_res = first_hits.std() * 1000  # ns to ps
        
        results[det_name]['energies'].append(energy)
        results[det_name]['timing_resolution'].append(timing_res)
        results[det_name]['energy_resolution'].append(energy_res)

# Create publication-quality plots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Plot 1: Timing resolution vs energy
for det_name, config in detector_configs.items():
    if results[det_name]['energies']:
        ax1.plot(results[det_name]['energies'], 
                results[det_name]['timing_resolution'],
                'o-', color=config['color'], label=config['label'],
                linewidth=2, markersize=8)

ax1.set_xlabel('Beam Energy (GeV)', fontsize=12)
ax1.set_ylabel('Timing Resolution (ps)', fontsize=12)
ax1.set_title('Timing Resolution vs Beam Energy', fontsize=14, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.legend(fontsize=11)
ax1.set_xscale('log')
ax1.set_xlim(0.8, 25)
ax1.set_ylim(0, 50)

# Plot 2: Energy resolution vs energy
for det_name, config in detector_configs.items():
    if results[det_name]['energies']:
        ax2.plot(results[det_name]['energies'], 
                results[det_name]['energy_resolution'],
                'o-', color=config['color'], label=config['label'],
                linewidth=2, markersize=8)

ax2.set_xlabel('Beam Energy (GeV)', fontsize=12)
ax2.set_ylabel('Energy Resolution (%)', fontsize=12)
ax2.set_title('Energy Resolution vs Beam Energy', fontsize=14, fontweight='bold')
ax2.grid(True, alpha=0.3)
ax2.legend(fontsize=11)
ax2.set_xscale('log')
ax2.set_xlim(0.8, 25)

plt.tight_layout()
plt.savefig(os.path.join(base_dir, 'detector_comparison.png'), dpi=300, bbox_inches='tight')

# Create time distribution example plot
fig2, axes = plt.subplots(1, 3, figsize=(15, 5))

for idx, (det_name, config) in enumerate(detector_configs.items()):
    ax = axes[idx]
    
    # Use 5 GeV data for example
    energy_dir = os.path.join(base_dir, 'energy_5.000GeV')
    hits_files = glob.glob(os.path.join(energy_dir, f'{config["pattern"]}_hits_data.parquet'))
    
    if hits_files:
        hits = pd.read_parquet(hits_files[0])
        first_hits = hits.groupby('eventID')['time'].min()
        
        ax.hist(first_hits * 1000, bins=50, alpha=0.7, color=config['color'], edgecolor='black')
        ax.set_xlabel('First Hit Time (ps)', fontsize=11)
        ax.set_ylabel('Events', fontsize=11)
        ax.set_title(f'{config["label"]} @ 5 GeV', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Add statistics
        mean_time = first_hits.mean() * 1000
        std_time = first_hits.std() * 1000
        ax.text(0.95, 0.95, f'σ = {std_time:.1f} ps', 
                transform=ax.transAxes, ha='right', va='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

plt.tight_layout()
plt.savefig(os.path.join(base_dir, 'time_distributions.png'), dpi=300, bbox_inches='tight')

# Prepare summary
summary = {
    'detector_comparison': results,
    'best_timing_detector': min(detector_configs.keys(), 
                               key=lambda x: np.mean(results[x]['timing_resolution']) if results[x]['timing_resolution'] else float('inf')),
    'plots': {
        'comparison': os.path.join(base_dir, 'detector_comparison.png'),
        'time_distributions': os.path.join(base_dir, 'time_distributions.png')
    }
}

print(json.dumps(summary))