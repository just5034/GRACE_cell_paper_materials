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

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/calorimeter_claude-sonnet-4-20250514_20260309_201808'

# Define the three configurations
configs = {
    'baseline': 'baseline_calorimeter',
    'projective': 'detector_4',  
    'compensating': 'detector_8'
}

# Energy directories
energy_dirs = ['energy_10.000GeV', 'energy_30.000GeV', 'energy_50.000GeV']
energies_gev = [10.0, 30.0, 50.0]

# Storage for results
results = {}

# Process each configuration
for config_name, detector_prefix in configs.items():
    energies = []
    mean_edeps = []
    resolutions = []
    responses = []
    
    for edir, true_e in zip(energy_dirs, energies_gev):
        # Find events file for this configuration
        events_pattern = os.path.join(base_dir, edir, f'{detector_prefix}*_events.parquet')
        events_files = glob.glob(events_pattern)
        
        if not events_files:
            # Try baseline_calorimeter pattern for all configs (since they all seem to use it)
            events_pattern = os.path.join(base_dir, edir, 'baseline_calorimeter*_events.parquet')
            events_files = glob.glob(events_pattern)
        
        if events_files:
            events = pd.read_parquet(events_files[0])
            mean_edep = events['totalEdep'].mean() / 1000.0  # MeV to GeV
            std_edep = events['totalEdep'].std() / 1000.0
            resolution = std_edep / mean_edep if mean_edep > 0 else 0
            response = mean_edep / true_e
            
            energies.append(true_e)
            mean_edeps.append(mean_edep)
            resolutions.append(resolution)
            responses.append(response)
    
    results[config_name] = {
        'energies': energies,
        'mean_edep': mean_edeps,
        'resolution': resolutions,
        'response': responses
    }

# Create plots
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))

# Plot 1: Energy Resolution vs Energy
for config_name in ['baseline', 'projective', 'compensating']:
    if results[config_name]['energies']:
        ax1.plot(results[config_name]['energies'], 
                np.array(results[config_name]['resolution']) * 100,
                'o-', label=config_name, markersize=8)
ax1.set_xlabel('Beam Energy [GeV]')
ax1.set_ylabel('Energy Resolution σ/E [%]')
ax1.set_title('Energy Resolution vs Beam Energy')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot 2: Response Linearity
for config_name in ['baseline', 'projective', 'compensating']:
    if results[config_name]['energies']:
        ax2.plot(results[config_name]['energies'], 
                results[config_name]['response'],
                'o-', label=config_name, markersize=8)
ax2.set_xlabel('Beam Energy [GeV]')
ax2.set_ylabel('Response (E_meas/E_true)')
ax2.set_title('Calorimeter Response Linearity')
ax2.axhline(y=1.0, color='k', linestyle='--', alpha=0.5)
ax2.legend()
ax2.grid(True, alpha=0.3)

# Plot 3: Shower Profile (longitudinal) for 30 GeV
ax3_data = {}
for config_name, detector_prefix in configs.items():
    hits_pattern = os.path.join(base_dir, 'energy_30.000GeV', f'{detector_prefix}*_hits_data.parquet')
    hits_files = glob.glob(hits_pattern)
    
    if not hits_files:
        hits_pattern = os.path.join(base_dir, 'energy_30.000GeV', 'baseline_calorimeter*_hits_data.parquet')
        hits_files = glob.glob(hits_pattern)
    
    if hits_files:
        hits = pd.read_parquet(hits_files[0])
        # Create longitudinal profile (z-binning)
        z_bins = np.linspace(0, 1200, 50)
        hist, edges = np.histogram(hits['z'], bins=z_bins, weights=hits['edep'])
        z_centers = (edges[:-1] + edges[1:]) / 2
        ax3_data[config_name] = (z_centers, hist)

for config_name in ['baseline', 'projective', 'compensating']:
    if config_name in ax3_data:
        z_centers, hist = ax3_data[config_name]
        ax3.plot(z_centers, hist, '-', label=config_name, linewidth=2)

ax3.set_xlabel('Depth [mm]')
ax3.set_ylabel('Energy Deposition [MeV]')
ax3.set_title('Longitudinal Shower Profile (30 GeV π+)')
ax3.legend()
ax3.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('calorimeter_performance_comparison.png', dpi=150)

# Prepare output
output = {
    'performance_metrics': results,
    'plots': ['calorimeter_performance_comparison.png']
}

print(json.dumps(output))