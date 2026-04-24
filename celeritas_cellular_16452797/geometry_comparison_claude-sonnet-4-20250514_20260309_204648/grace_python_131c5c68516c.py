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

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/geometry_comparison_claude-sonnet-4-20250514_20260309_204648'

# Find projective tower data files
energies = sorted(glob.glob(os.path.join(base_dir, 'energy_*GeV')))
projective_data = {}

for edir in energies:
    # Look for projective tower files
    events_files = glob.glob(os.path.join(edir, 'projective_tower_calorimeter_*_events.parquet'))
    if not events_files:
        continue
    
    events_file = events_files[0]
    hits_files = glob.glob(os.path.join(edir, 'projective_tower_calorimeter_*_hits_data.parquet'))
    if not hits_files:
        continue
    hits_file = hits_files[0]
    
    true_e = float(os.path.basename(edir).replace('energy_','').replace('GeV',''))
    
    # Read events data
    events = pd.read_parquet(events_file)
    
    # Calculate energy resolution
    mean_edep = events['totalEdep'].mean()
    std_edep = events['totalEdep'].std()
    resolution = std_edep / mean_edep if mean_edep > 0 else 0
    
    # Read hits data for spatial analysis
    hits = pd.read_parquet(hits_file)
    
    # Merge hits with events to get per-event hit data
    hits_with_total = hits.merge(events[['eventID', 'totalEdep']], on='eventID')
    
    # Calculate radial distance from beam axis (assuming beam along z)
    hits_with_total['r'] = np.sqrt(hits_with_total['x']**2 + hits_with_total['y']**2)
    
    # Analyze response uniformity - compare energy deposition in different radial regions
    r_bins = [0, 10, 20, 30, 40, 50]  # mm
    hits_with_total['r_bin'] = pd.cut(hits_with_total['r'], bins=r_bins)
    
    # Calculate mean energy per event in each radial bin
    radial_response = []
    for i in range(len(r_bins)-1):
        bin_mask = (hits_with_total['r'] >= r_bins[i]) & (hits_with_total['r'] < r_bins[i+1])
        bin_hits = hits_with_total[bin_mask]
        if len(bin_hits) > 0:
            # Sum energy per event in this radial bin
            bin_energy_per_event = bin_hits.groupby('eventID')['edep'].sum()
            mean_bin_energy = bin_energy_per_event.mean()
            radial_response.append({
                'r_min': r_bins[i],
                'r_max': r_bins[i+1],
                'mean_edep_MeV': mean_bin_energy,
                'fraction_of_total': mean_bin_energy / mean_edep if mean_edep > 0 else 0
            })
    
    # Analyze longitudinal shower profile
    z_bins = np.linspace(hits['z'].min(), hits['z'].max(), 21)
    hits_with_total['z_bin'] = pd.cut(hits_with_total['z'], bins=z_bins)
    
    longitudinal_profile = []
    for i in range(len(z_bins)-1):
        bin_mask = (hits_with_total['z'] >= z_bins[i]) & (hits_with_total['z'] < z_bins[i+1])
        bin_hits = hits_with_total[bin_mask]
        if len(bin_hits) > 0:
            bin_energy = bin_hits['edep'].sum()
            longitudinal_profile.append({
                'z_center': (z_bins[i] + z_bins[i+1])/2,
                'edep_MeV': bin_energy,
                'fraction': bin_energy / hits['edep'].sum()
            })
    
    # Calculate shower containment (fraction of energy within certain radius)
    containment_radii = [20, 40, 60, 80, 100]  # mm
    containment = {}
    for radius in containment_radii:
        contained_hits = hits_with_total[hits_with_total['r'] <= radius]
        contained_energy = contained_hits['edep'].sum()
        total_energy = hits['edep'].sum()
        containment[f'r_{radius}mm'] = contained_energy / total_energy if total_energy > 0 else 0
    
    projective_data[f'{true_e}GeV'] = {
        'mean_edep_MeV': mean_edep,
        'std_edep_MeV': std_edep,
        'resolution': resolution,
        'radial_uniformity': radial_response,
        'longitudinal_profile': longitudinal_profile,
        'shower_containment': containment,
        'n_events': len(events)
    }

# Create summary plots
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Plot 1: Energy resolution vs beam energy
if projective_data:
    energies_gev = []
    resolutions = []
    for key in sorted(projective_data.keys(), key=lambda x: float(x.replace('GeV',''))):
        energies_gev.append(float(key.replace('GeV','')))
        resolutions.append(projective_data[key]['resolution'])
    
    axes[0,0].plot(energies_gev, resolutions, 'bo-', linewidth=2, markersize=8)
    axes[0,0].set_xlabel('Beam Energy (GeV)')
    axes[0,0].set_ylabel('Energy Resolution (σ/E)')
    axes[0,0].set_title('Projective Tower: Energy Resolution')
    axes[0,0].grid(True, alpha=0.3)
    axes[0,0].set_xscale('log')

# Plot 2: Response linearity
if projective_data:
    measured_energies = []
    for key in sorted(projective_data.keys(), key=lambda x: float(x.replace('GeV',''))):
        true_e = float(key.replace('GeV',''))
        measured_e = projective_data[key]['mean_edep_MeV'] / 1000.0  # Convert to GeV
        measured_energies.append(measured_e)
    
    axes[0,1].plot(energies_gev, measured_energies, 'ro-', linewidth=2, markersize=8, label='Measured')
    axes[0,1].plot(energies_gev, energies_gev, 'k--', linewidth=1, label='Ideal')
    axes[0,1].set_xlabel('True Energy (GeV)')
    axes[0,1].set_ylabel('Measured Energy (GeV)')
    axes[0,1].set_title('Projective Tower: Linearity')
    axes[0,1].legend()
    axes[0,1].grid(True, alpha=0.3)

# Plot 3: Radial uniformity for highest energy
if '20.0GeV' in projective_data and projective_data['20.0GeV']['radial_uniformity']:
    radial_data = projective_data['20.0GeV']['radial_uniformity']
    r_centers = [(d['r_min'] + d['r_max'])/2 for d in radial_data]
    fractions = [d['fraction_of_total'] for d in radial_data]
    
    axes[1,0].bar(r_centers, fractions, width=[d['r_max']-d['r_min'] for d in radial_data], 
                  alpha=0.7, edgecolor='black')
    axes[1,0].set_xlabel('Radial Distance (mm)')
    axes[1,0].set_ylabel('Fraction of Total Energy')
    axes[1,0].set_title('Projective Tower: Radial Energy Distribution (20 GeV)')
    axes[1,0].grid(True, alpha=0.3)

# Plot 4: Shower containment
if projective_data:
    containment_data = {}
    for energy_key in projective_data:
        if 'shower_containment' in projective_data[energy_key]:
            for radius_key, value in projective_data[energy_key]['shower_containment'].items():
                radius = int(radius_key.split('_')[1].replace('mm',''))
                if radius not in containment_data:
                    containment_data[radius] = {}
                containment_data[radius][float(energy_key.replace('GeV',''))] = value
    
    for radius in sorted(containment_data.keys()):
        energies = sorted(containment_data[radius].keys())
        values = [containment_data[radius][e] for e in energies]
        axes[1,1].plot(energies, values, 'o-', label=f'{radius} mm', linewidth=2, markersize=6)
    
    axes[1,1].set_xlabel('Beam Energy (GeV)')
    axes[1,1].set_ylabel('Containment Fraction')
    axes[1,1].set_title('Projective Tower: Shower Containment')
    axes[1,1].legend()
    axes[1,1].grid(True, alpha=0.3)
    axes[1,1].set_xscale('log')

plt.tight_layout()
plt.savefig('projective_tower_performance.png', dpi=150)

# Calculate performance metrics summary
summary = {
    'geometry': 'projective_tower',
    'energy_resolution': {},
    'response_linearity': {},
    'uniformity_metrics': {},
    'shower_containment_95pct_radius': {}
}

for energy_key in projective_data:
    energy_gev = float(energy_key.replace('GeV',''))
    data = projective_data[energy_key]
    
    # Energy resolution
    summary['energy_resolution'][energy_key] = {
        'resolution': data['resolution'],
        'mean_response_GeV': data['mean_edep_MeV'] / 1000.0
    }
    
    # Linearity
    summary['response_linearity'][energy_key] = {
        'true_energy_GeV': energy_gev,
        'measured_energy_GeV': data['mean_edep_MeV'] / 1000.0,
        'deviation_percent': 100 * (data['mean_edep_MeV'] / 1000.0 - energy_gev) / energy_gev
    }
    
    # Find radius containing 95% of energy
    if 'shower_containment' in data:
        for radius_key, containment in sorted(data['shower_containment'].items()):
            if containment >= 0.95:
                summary['shower_containment_95pct_radius'][energy_key] = radius_key
                break

# Add plot to artifacts
summary['plot'] = 'projective_tower_performance.png'
summary['detailed_data'] = projective_data

print(json.dumps(summary))