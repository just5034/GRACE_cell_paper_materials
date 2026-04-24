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

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/muon_claude-sonnet-4-20250514_20260309_201956'
energies = [5.0, 20.0, 50.0]
configurations = ['iron_spectrometer_3', 'aluminum_spectrometer']

results = {}

for config in configurations:
    results[config] = {
        'muon_efficiency': {},
        'pion_rejection': {},
        'energy_resolution': {},
        'mean_edep_fraction': {}
    }
    
    for energy in energies:
        energy_dir = os.path.join(base_dir, f'energy_{energy:.3f}GeV')
        
        # Muon data
        muon_events_file = os.path.join(energy_dir, f'{config}_mum_events.parquet')
        muon_hits_file = os.path.join(energy_dir, f'{config}_mum_hits_data.parquet')
        
        # Pion data
        pion_events_file = os.path.join(energy_dir, f'{config}_pim_events.parquet')
        pion_hits_file = os.path.join(energy_dir, f'{config}_pim_hits_data.parquet')
        
        if os.path.exists(muon_events_file) and os.path.exists(pion_events_file):
            # Read muon events
            muon_events = pd.read_parquet(muon_events_file)
            muon_hits = pd.read_parquet(muon_hits_file)
            
            # Read pion events
            pion_events = pd.read_parquet(pion_events_file)
            pion_hits = pd.read_parquet(pion_hits_file)
            
            # Calculate muon efficiency (fraction with significant energy deposition)
            muon_threshold = 0.1 * energy * 1000  # 10% of beam energy in MeV
            muon_detected = (muon_events['totalEdep'] > muon_threshold).sum()
            muon_efficiency = muon_detected / len(muon_events)
            
            # Calculate pion rejection (fraction stopped/absorbed)
            pion_threshold = 0.1 * energy * 1000  # 10% of beam energy in MeV
            pion_detected = (pion_events['totalEdep'] > pion_threshold).sum()
            pion_rejection = 1.0 - (pion_detected / len(pion_events))
            
            # Energy resolution for muons
            muon_mean_edep = muon_events['totalEdep'].mean()
            muon_std_edep = muon_events['totalEdep'].std()
            energy_resolution = muon_std_edep / muon_mean_edep if muon_mean_edep > 0 else 0
            
            # Mean energy deposition fraction
            mean_edep_fraction = muon_mean_edep / (energy * 1000)  # Convert GeV to MeV
            
            results[config]['muon_efficiency'][f'{energy}GeV'] = muon_efficiency
            results[config]['pion_rejection'][f'{energy}GeV'] = pion_rejection
            results[config]['energy_resolution'][f'{energy}GeV'] = energy_resolution
            results[config]['mean_edep_fraction'][f'{energy}GeV'] = mean_edep_fraction

# Create energy deposition profile plots
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
fig.suptitle('Energy Deposition Profiles', fontsize=16)

for i, config in enumerate(configurations):
    for j, energy in enumerate(energies):
        ax = axes[i, j]
        energy_dir = os.path.join(base_dir, f'energy_{energy:.3f}GeV')
        
        muon_hits_file = os.path.join(energy_dir, f'{config}_mum_hits_data.parquet')
        pion_hits_file = os.path.join(energy_dir, f'{config}_pim_hits_data.parquet')
        
        if os.path.exists(muon_hits_file) and os.path.exists(pion_hits_file):
            muon_hits = pd.read_parquet(muon_hits_file)
            pion_hits = pd.read_parquet(pion_hits_file)
            
            # Z-profile of energy deposition
            z_bins = np.linspace(muon_hits['z'].min(), muon_hits['z'].max(), 50)
            
            muon_z_profile, _ = np.histogram(muon_hits['z'], bins=z_bins, weights=muon_hits['edep'])
            pion_z_profile, _ = np.histogram(pion_hits['z'], bins=z_bins, weights=pion_hits['edep'])
            
            z_centers = (z_bins[:-1] + z_bins[1:]) / 2
            
            ax.plot(z_centers, muon_z_profile, 'b-', label='Muons', linewidth=2)
            ax.plot(z_centers, pion_z_profile, 'r--', label='Pions', linewidth=2)
            ax.set_xlabel('Z position (mm)')
            ax.set_ylabel('Energy deposition (MeV)')
            ax.set_title(f'{config.replace("_", " ").title()} - {energy} GeV')
            ax.legend()
            ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('energy_deposition_profiles.png', dpi=150)
plt.close()

# Create performance summary plots
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
fig.suptitle('Spectrometer Performance Summary', fontsize=16)

# Muon efficiency vs energy
ax1.set_title('Muon Detection Efficiency')
for config in configurations:
    efficiencies = [results[config]['muon_efficiency'][f'{e}GeV'] for e in energies]
    ax1.plot(energies, efficiencies, 'o-', label=config.replace('_', ' ').title(), linewidth=2, markersize=8)
ax1.set_xlabel('Energy (GeV)')
ax1.set_ylabel('Efficiency')
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.set_xscale('log')

# Pion rejection vs energy
ax2.set_title('Pion Rejection Rate')
for config in configurations:
    rejections = [results[config]['pion_rejection'][f'{e}GeV'] for e in energies]
    ax2.plot(energies, rejections, 'o-', label=config.replace('_', ' ').title(), linewidth=2, markersize=8)
ax2.set_xlabel('Energy (GeV)')
ax2.set_ylabel('Rejection Rate')
ax2.legend()
ax2.grid(True, alpha=0.3)
ax2.set_xscale('log')

# Energy resolution vs energy
ax3.set_title('Energy Resolution (σ/E)')
for config in configurations:
    resolutions = [results[config]['energy_resolution'][f'{e}GeV'] for e in energies]
    ax3.plot(energies, resolutions, 'o-', label=config.replace('_', ' ').title(), linewidth=2, markersize=8)
ax3.set_xlabel('Energy (GeV)')
ax3.set_ylabel('σ/E')
ax3.legend()
ax3.grid(True, alpha=0.3)
ax3.set_xscale('log')

# Mean energy deposition fraction
ax4.set_title('Mean Energy Deposition Fraction')
for config in configurations:
    fractions = [results[config]['mean_edep_fraction'][f'{e}GeV'] for e in energies]
    ax4.plot(energies, fractions, 'o-', label=config.replace('_', ' ').title(), linewidth=2, markersize=8)
ax4.set_xlabel('Energy (GeV)')
ax4.set_ylabel('Edep/E_beam')
ax4.legend()
ax4.grid(True, alpha=0.3)
ax4.set_xscale('log')

plt.tight_layout()
plt.savefig('performance_summary.png', dpi=150)
plt.close()

# Calculate figure of merit for each configuration
for config in configurations:
    fom_values = []
    for energy in energies:
        muon_eff = results[config]['muon_efficiency'][f'{energy}GeV']
        pion_rej = results[config]['pion_rejection'][f'{energy}GeV']
        fom = muon_eff * pion_rej
        fom_values.append(fom)
    results[config]['figure_of_merit'] = {
        f'{e}GeV': fom for e, fom in zip(energies, fom_values)
    }
    results[config]['average_fom'] = np.mean(fom_values)

# Add plot filenames to results
results['plots'] = ['energy_deposition_profiles.png', 'performance_summary.png']

# Summary statistics
results['summary'] = {
    'best_overall': max(configurations, key=lambda c: results[c]['average_fom']),
    'best_muon_efficiency': {},
    'best_pion_rejection': {}
}

for energy in energies:
    energy_key = f'{energy}GeV'
    results['summary']['best_muon_efficiency'][energy_key] = max(
        configurations, 
        key=lambda c: results[c]['muon_efficiency'][energy_key]
    )
    results['summary']['best_pion_rejection'][energy_key] = max(
        configurations, 
        key=lambda c: results[c]['pion_rejection'][energy_key]
    )

print(json.dumps(results))