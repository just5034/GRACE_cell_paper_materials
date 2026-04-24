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
from matplotlib.backends.backend_pdf import PdfPages

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/tof_claude-sonnet-4-20250514_20260309_204438'
energies = [1.0, 2.0, 3.0]
configs = {
    'homogeneous_slab': 'homogeneous_slab_tof_2_pip',
    'segmented': 'detector_pip',
    'multilayer': 'detector_2_pip'
}

fig, axes = plt.subplots(3, 3, figsize=(15, 12))
fig.suptitle('Energy Deposition Distributions for TOF Detector Configurations', fontsize=16)

colors = {'homogeneous_slab': 'blue', 'segmented': 'green', 'multilayer': 'red'}
results = {}

for i, energy in enumerate(energies):
    energy_dir = os.path.join(base_dir, f'energy_{energy:.3f}GeV')
    
    for j, (config_name, file_prefix) in enumerate(configs.items()):
        events_file = os.path.join(energy_dir, f'{file_prefix}_events.parquet')
        
        if os.path.exists(events_file):
            events = pd.read_parquet(events_file)
            edep_data = events['totalEdep'].values
            
            ax = axes[i, j]
            ax.hist(edep_data, bins=50, alpha=0.7, color=colors[config_name], edgecolor='black')
            ax.set_xlabel('Total Energy Deposit (MeV)')
            ax.set_ylabel('Events')
            ax.set_title(f'{config_name.replace("_", " ").title()} - {energy} GeV')
            ax.grid(True, alpha=0.3)
            
            mean_edep = np.mean(edep_data)
            std_edep = np.std(edep_data)
            ax.axvline(mean_edep, color='red', linestyle='--', label=f'Mean: {mean_edep:.2f} MeV')
            ax.axvline(mean_edep - std_edep, color='orange', linestyle=':', alpha=0.5)
            ax.axvline(mean_edep + std_edep, color='orange', linestyle=':', alpha=0.5)
            ax.legend()
            
            if config_name not in results:
                results[config_name] = {}
            results[config_name][f'{energy}GeV'] = {
                'mean_MeV': float(mean_edep),
                'std_MeV': float(std_edep),
                'resolution': float(std_edep/mean_edep) if mean_edep > 0 else 0
            }

plt.tight_layout()
plt.savefig('tof_energy_distributions.png', dpi=300, bbox_inches='tight')
plt.close()

# Particle separation analysis
fig2, axes2 = plt.subplots(1, 3, figsize=(15, 5))
fig2.suptitle('Energy Resolution vs Beam Energy', fontsize=16)

for i, (config_name, config_data) in enumerate(results.items()):
    ax = axes2[i]
    energies_plot = []
    resolutions = []
    
    for e_str, data in config_data.items():
        energies_plot.append(float(e_str.replace('GeV', '')))
        resolutions.append(data['resolution'])
    
    ax.plot(energies_plot, resolutions, 'o-', color=colors[config_name], linewidth=2, markersize=8)
    ax.set_xlabel('Beam Energy (GeV)')
    ax.set_ylabel('Energy Resolution (σ/E)')
    ax.set_title(f'{config_name.replace("_", " ").title()}')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, max(resolutions) * 1.2)

plt.tight_layout()
plt.savefig('tof_energy_resolution.png', dpi=300, bbox_inches='tight')
plt.close()

# Combined comparison plot
fig3, ax3 = plt.subplots(figsize=(10, 6))
fig3.suptitle('Energy Resolution Comparison Across Configurations', fontsize=16)

for config_name, config_data in results.items():
    energies_plot = []
    resolutions = []
    
    for e_str, data in config_data.items():
        energies_plot.append(float(e_str.replace('GeV', '')))
        resolutions.append(data['resolution'])
    
    ax3.plot(energies_plot, resolutions, 'o-', color=colors[config_name], 
             linewidth=2, markersize=8, label=config_name.replace('_', ' ').title())

ax3.set_xlabel('Beam Energy (GeV)')
ax3.set_ylabel('Energy Resolution (σ/E)')
ax3.grid(True, alpha=0.3)
ax3.legend()
ax3.set_ylim(0, 1.5)

plt.tight_layout()
plt.savefig('tof_resolution_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

# Mean energy deposit comparison
fig4, ax4 = plt.subplots(figsize=(10, 6))
fig4.suptitle('Mean Energy Deposition vs Beam Energy', fontsize=16)

for config_name, config_data in results.items():
    energies_plot = []
    mean_deps = []
    
    for e_str, data in config_data.items():
        energies_plot.append(float(e_str.replace('GeV', '')))
        mean_deps.append(data['mean_MeV'])
    
    ax4.plot(energies_plot, mean_deps, 'o-', color=colors[config_name], 
             linewidth=2, markersize=8, label=config_name.replace('_', ' ').title())

ax4.set_xlabel('Beam Energy (GeV)')
ax4.set_ylabel('Mean Energy Deposition (MeV)')
ax4.grid(True, alpha=0.3)
ax4.legend()

plt.tight_layout()
plt.savefig('tof_mean_energy_deposition.png', dpi=300, bbox_inches='tight')
plt.close()

output = {
    "success": True,
    "artifacts": [
        "tof_energy_distributions.png",
        "tof_energy_resolution.png",
        "tof_resolution_comparison.png",
        "tof_mean_energy_deposition.png"
    ],
    "analysis_results": results,
    "summary": {
        "best_resolution_config": min(results.keys(), 
                                     key=lambda x: np.mean([results[x][e]['resolution'] 
                                                          for e in results[x]])),
        "configurations_analyzed": list(results.keys()),
        "energies_analyzed_GeV": energies
    }
}

print(json.dumps(output))