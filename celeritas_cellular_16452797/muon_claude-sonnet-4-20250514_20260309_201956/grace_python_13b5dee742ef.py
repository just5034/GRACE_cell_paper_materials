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

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/muon_claude-sonnet-4-20250514_20260309_201956'
energies = [5.0, 20.0, 50.0]
configs = ['iron_spectrometer_3', 'aluminum_spectrometer']

results = {}

# Analyze each configuration
for config in configs:
    results[config] = {
        'muon_efficiency': {},
        'pion_rejection': {},
        'energy_resolution': {},
        'mean_edep_fraction': {}
    }
    
    for energy in energies:
        energy_dir = os.path.join(base_dir, f'energy_{energy:.3f}GeV')
        
        # Load muon data
        muon_events_file = os.path.join(energy_dir, f'{config}_mum_events.parquet')
        muon_hits_file = os.path.join(energy_dir, f'{config}_mum_hits_data.parquet')
        
        # Load pion data
        pion_events_file = os.path.join(energy_dir, f'{config}_pim_events.parquet')
        pion_hits_file = os.path.join(energy_dir, f'{config}_pim_hits_data.parquet')
        
        if os.path.exists(muon_events_file) and os.path.exists(pion_events_file):
            muon_events = pd.read_parquet(muon_events_file)
            pion_events = pd.read_parquet(pion_events_file)
            
            # Muon efficiency: fraction with significant energy deposition
            muon_eff = (muon_events['totalEdep'] > 0.1).mean()
            results[config]['muon_efficiency'][f'{energy}GeV'] = muon_eff
            
            # Pion rejection: fraction with very low energy deposition
            pion_rej = (pion_events['totalEdep'] < 0.1).mean()
            results[config]['pion_rejection'][f'{energy}GeV'] = pion_rej
            
            # Energy resolution for muons
            muon_edep_gev = muon_events['totalEdep'] / 1000.0
            if muon_edep_gev.mean() > 0:
                resolution = muon_edep_gev.std() / muon_edep_gev.mean()
            else:
                resolution = 0
            results[config]['energy_resolution'][f'{energy}GeV'] = resolution
            
            # Mean energy deposition fraction
            results[config]['mean_edep_fraction'][f'{energy}GeV'] = muon_edep_gev.mean() / energy

# Create publication-quality plots
plt.style.use('default')
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Plot 1: Muon Efficiency vs Energy
ax = axes[0, 0]
for config in configs:
    x = [5.0, 20.0, 50.0]
    y = [results[config]['muon_efficiency'].get(f'{e}GeV', 0) for e in x]
    label = 'Iron' if 'iron' in config else 'Aluminum'
    ax.plot(x, y, 'o-', linewidth=2, markersize=8, label=label)
ax.set_xlabel('Beam Energy (GeV)', fontsize=12)
ax.set_ylabel('Muon Efficiency', fontsize=12)
ax.set_title('Muon Detection Efficiency', fontsize=14, fontweight='bold')
ax.set_xscale('log')
ax.grid(True, alpha=0.3)
ax.legend(fontsize=11)

# Plot 2: Pion Rejection vs Energy
ax = axes[0, 1]
for config in configs:
    x = [5.0, 20.0, 50.0]
    y = [results[config]['pion_rejection'].get(f'{e}GeV', 0) for e in x]
    label = 'Iron' if 'iron' in config else 'Aluminum'
    ax.plot(x, y, 's-', linewidth=2, markersize=8, label=label)
ax.set_xlabel('Beam Energy (GeV)', fontsize=12)
ax.set_ylabel('Pion Rejection', fontsize=12)
ax.set_title('Pion Rejection Efficiency', fontsize=14, fontweight='bold')
ax.set_xscale('log')
ax.grid(True, alpha=0.3)
ax.legend(fontsize=11)

# Plot 3: Energy Resolution vs Energy
ax = axes[1, 0]
for config in configs:
    x = [5.0, 20.0, 50.0]
    y = [results[config]['energy_resolution'].get(f'{e}GeV', 0) for e in x]
    label = 'Iron' if 'iron' in config else 'Aluminum'
    ax.plot(x, y, '^-', linewidth=2, markersize=8, label=label)
ax.set_xlabel('Beam Energy (GeV)', fontsize=12)
ax.set_ylabel('Energy Resolution (σ/E)', fontsize=12)
ax.set_title('Energy Resolution', fontsize=14, fontweight='bold')
ax.set_xscale('log')
ax.grid(True, alpha=0.3)
ax.legend(fontsize=11)

# Plot 4: Energy deposition profiles
ax = axes[1, 1]
energy_dir = os.path.join(base_dir, 'energy_20.000GeV')
for config, color in zip(configs, ['blue', 'red']):
    muon_hits_file = os.path.join(energy_dir, f'{config}_mum_hits_data.parquet')
    if os.path.exists(muon_hits_file):
        hits = pd.read_parquet(muon_hits_file)
        # Create longitudinal profile
        z_bins = np.linspace(hits['z'].min(), hits['z'].max(), 50)
        z_hist, _ = np.histogram(hits['z'], bins=z_bins, weights=hits['edep'])
        z_centers = (z_bins[:-1] + z_bins[1:]) / 2
        label = 'Iron' if 'iron' in config else 'Aluminum'
        ax.plot(z_centers/10, z_hist/z_hist.sum(), linewidth=2, label=f'{label} (20 GeV μ)', color=color)

ax.set_xlabel('Longitudinal Position (cm)', fontsize=12)
ax.set_ylabel('Normalized Energy Deposition', fontsize=12)
ax.set_title('Longitudinal Shower Profile', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.legend(fontsize=11)

plt.tight_layout()
plt.savefig('muon_spectrometer_performance.png', dpi=300, bbox_inches='tight')

# Summary table plot
fig2, ax = plt.subplots(figsize=(10, 6))
ax.axis('tight')
ax.axis('off')

# Create summary data
summary_data = []
for config in configs:
    material = 'Iron' if 'iron' in config else 'Aluminum'
    muon_eff_20 = results[config]['muon_efficiency'].get('20.0GeV', 0)
    pion_rej_20 = results[config]['pion_rejection'].get('20.0GeV', 0)
    energy_res_20 = results[config]['energy_resolution'].get('20.0GeV', 0)
    summary_data.append([material, f'{muon_eff_20:.2%}', f'{pion_rej_20:.2%}', f'{energy_res_20:.3f}'])

col_labels = ['Material', 'Muon Eff. (20 GeV)', 'Pion Rej. (20 GeV)', 'Energy Res. (σ/E)']
table = ax.table(cellText=summary_data, colLabels=col_labels, loc='center', cellLoc='center')
table.auto_set_font_size(False)
table.set_fontsize(12)
table.scale(1.2, 1.5)

for i in range(len(col_labels)):
    table[(0, i)].set_facecolor('#4CAF50')
    table[(0, i)].set_text_props(weight='bold', color='white')

ax.set_title('Muon Spectrometer Performance Summary', fontsize=16, fontweight='bold', pad=20)
plt.savefig('performance_summary_table.png', dpi=300, bbox_inches='tight')

output = {
    'performance_metrics': results,
    'plots': ['muon_spectrometer_performance.png', 'performance_summary_table.png']
}

print(json.dumps(output))