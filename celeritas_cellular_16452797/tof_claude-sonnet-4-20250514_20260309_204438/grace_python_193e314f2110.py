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

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/tof_claude-sonnet-4-20250514_20260309_204438'
energies = [1.0, 2.0, 3.0]
detector_configs = {
    'homogeneous_slab': 'homogeneous_slab_tof_2',
    'segmented': 'detector',
    'multilayer': 'detector_2'
}

results = {}

# Analyze each detector configuration
for config_name, file_prefix in detector_configs.items():
    results[config_name] = {}
    
    for energy in energies:
        energy_dir = os.path.join(base_dir, f'energy_{energy:.3f}GeV')
        
        # Find events file
        events_pattern = os.path.join(energy_dir, f'{file_prefix}_pip_events.parquet')
        events_files = glob.glob(events_pattern)
        
        if not events_files:
            continue
            
        events = pd.read_parquet(events_files[0])
        
        # Calculate statistics
        mean_edep = events['totalEdep'].mean()
        std_edep = events['totalEdep'].std()
        resolution = std_edep / mean_edep if mean_edep > 0 else 0
        
        results[config_name][f'{energy}GeV'] = {
            'mean_edep_MeV': mean_edep,
            'std_edep_MeV': std_edep,
            'resolution': resolution,
            'n_events': len(events)
        }

# Create comparison plots
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Plot 1: Mean energy deposition vs beam energy
ax1 = axes[0, 0]
for config_name in detector_configs.keys():
    energies_plot = []
    mean_edeps = []
    for e in energies:
        key = f'{e}GeV'
        if key in results[config_name]:
            energies_plot.append(e)
            mean_edeps.append(results[config_name][key]['mean_edep_MeV'])
    ax1.plot(energies_plot, mean_edeps, 'o-', label=config_name, markersize=8)
ax1.set_xlabel('Beam Energy (GeV)')
ax1.set_ylabel('Mean Energy Deposition (MeV)')
ax1.set_title('Energy Deposition vs Beam Energy')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot 2: Energy resolution vs beam energy
ax2 = axes[0, 1]
for config_name in detector_configs.keys():
    energies_plot = []
    resolutions = []
    for e in energies:
        key = f'{e}GeV'
        if key in results[config_name]:
            energies_plot.append(e)
            resolutions.append(results[config_name][key]['resolution'] * 100)
    ax2.plot(energies_plot, resolutions, 'o-', label=config_name, markersize=8)
ax2.set_xlabel('Beam Energy (GeV)')
ax2.set_ylabel('Energy Resolution (%)')
ax2.set_title('Energy Resolution vs Beam Energy')
ax2.legend()
ax2.grid(True, alpha=0.3)

# Plot 3: Energy deposition distributions at 2 GeV
ax3 = axes[1, 0]
energy_dir = os.path.join(base_dir, 'energy_2.000GeV')
for config_name, file_prefix in detector_configs.items():
    events_file = os.path.join(energy_dir, f'{file_prefix}_pip_events.parquet')
    if os.path.exists(events_file):
        events = pd.read_parquet(events_file)
        ax3.hist(events['totalEdep'], bins=50, alpha=0.5, label=config_name, density=True)
ax3.set_xlabel('Total Energy Deposition (MeV)')
ax3.set_ylabel('Normalized Counts')
ax3.set_title('Energy Deposition Distribution at 2 GeV')
ax3.legend()
ax3.grid(True, alpha=0.3)

# Plot 4: Discrimination metric (coefficient of variation)
ax4 = axes[1, 1]
for config_name in detector_configs.keys():
    energies_plot = []
    cv_values = []
    for e in energies:
        key = f'{e}GeV'
        if key in results[config_name]:
            energies_plot.append(e)
            cv = results[config_name][key]['resolution']
            cv_values.append(cv)
    ax4.plot(energies_plot, cv_values, 'o-', label=config_name, markersize=8)
ax4.set_xlabel('Beam Energy (GeV)')
ax4.set_ylabel('Coefficient of Variation')
ax4.set_title('Energy Deposition Variability (Lower is Better for PID)')
ax4.legend()
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('particle_discrimination_analysis.png', dpi=150)

# Calculate discrimination metrics
discrimination_metrics = {}
for config_name in detector_configs.keys():
    # Average resolution across energies
    resolutions = []
    for e in energies:
        key = f'{e}GeV'
        if key in results[config_name]:
            resolutions.append(results[config_name][key]['resolution'])
    
    avg_resolution = np.mean(resolutions) if resolutions else 0
    
    # Energy linearity (correlation between beam and deposited energy)
    beam_energies = []
    deposited_energies = []
    for e in energies:
        key = f'{e}GeV'
        if key in results[config_name]:
            beam_energies.append(e * 1000)  # Convert to MeV
            deposited_energies.append(results[config_name][key]['mean_edep_MeV'])
    
    if len(beam_energies) > 1:
        correlation = np.corrcoef(beam_energies, deposited_energies)[0, 1]
    else:
        correlation = 0
    
    discrimination_metrics[config_name] = {
        'avg_resolution': avg_resolution,
        'energy_linearity': correlation,
        'discrimination_score': (1 - avg_resolution) * correlation if correlation > 0 else 0
    }

# Final results
output = {
    'detector_performance': results,
    'discrimination_metrics': discrimination_metrics,
    'best_detector': max(discrimination_metrics.items(), key=lambda x: x[1]['discrimination_score'])[0],
    'plot': 'particle_discrimination_analysis.png'
}

print(json.dumps(output))