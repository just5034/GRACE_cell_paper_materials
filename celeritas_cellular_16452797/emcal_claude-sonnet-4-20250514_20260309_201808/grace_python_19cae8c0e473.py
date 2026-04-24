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
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json

# Material properties for common calorimeter crystals
materials = {
    'CsI': {
        'X0': 1.86,  # radiation length in cm
        'RM': 3.8,   # Molière radius in cm
        'density': 4.51,  # g/cm³
        'Z': 54.0    # effective atomic number
    },
    'LYSO': {
        'X0': 1.14,  # radiation length in cm
        'RM': 2.3,   # Molière radius in cm
        'density': 7.1,  # g/cm³
        'Z': 66.0    # effective atomic number
    },
    'PWO': {
        'X0': 0.89,  # radiation length in cm
        'RM': 2.2,   # Molière radius in cm
        'density': 8.28,  # g/cm³
        'Z': 73.0    # effective atomic number
    }
}

# Calculate critical energy for each material
def critical_energy(Z):
    return 610.0 / (Z + 1.24)  # MeV

# Calculate shower maximum depth
def shower_max_depth(E0, Ec, X0):
    return X0 * np.log(E0/Ec) / np.log(2)

# Calculate 95% longitudinal containment depth
def longitudinal_containment_95(E0, Ec, X0):
    t_max = shower_max_depth(E0, Ec, X0)
    return t_max + 3.0 * X0 * np.sqrt(np.log(E0/Ec))

# Calculate 95% transverse containment radius
def transverse_containment_95(RM):
    return 3.5 * RM  # ~95% containment within 3.5 Molière radii

results = {}
E0 = 5000  # 5 GeV in MeV

for mat_name, props in materials.items():
    Ec = critical_energy(props['Z'])
    
    # Longitudinal dimension for 95% containment
    depth_95 = longitudinal_containment_95(E0, Ec, props['X0'])
    
    # Transverse dimension for 95% containment
    radius_95 = transverse_containment_95(props['RM'])
    
    # Round up to practical dimensions
    depth_cm = np.ceil(depth_95 * 10) / 10
    width_cm = np.ceil(2 * radius_95 * 10) / 10  # full width
    
    results[mat_name] = {
        'radiation_length_cm': props['X0'],
        'moliere_radius_cm': props['RM'],
        'critical_energy_MeV': round(Ec, 2),
        'shower_max_depth_cm': round(shower_max_depth(E0, Ec, props['X0']), 2),
        'min_depth_95_percent_cm': round(depth_cm, 1),
        'min_width_95_percent_cm': round(width_cm, 1),
        'depth_in_X0': round(depth_cm / props['X0'], 1),
        'width_in_RM': round(width_cm / (2 * props['RM']), 1),
        'volume_cm3': round(depth_cm * width_cm * width_cm, 1),
        'mass_kg': round(depth_cm * width_cm * width_cm * props['density'] / 1000, 2)
    }

# Create comparison plots
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

# Plot 1: Minimum dimensions
materials_list = list(results.keys())
depths = [results[m]['min_depth_95_percent_cm'] for m in materials_list]
widths = [results[m]['min_width_95_percent_cm'] for m in materials_list]

x = np.arange(len(materials_list))
width = 0.35

ax1.bar(x - width/2, depths, width, label='Depth', color='steelblue')
ax1.bar(x + width/2, widths, width, label='Width', color='darkorange')
ax1.set_xlabel('Material')
ax1.set_ylabel('Dimension (cm)')
ax1.set_title('Minimum Calorimeter Dimensions for 95% Containment at 5 GeV')
ax1.set_xticks(x)
ax1.set_xticklabels(materials_list)
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot 2: Dimensions in natural units
depths_X0 = [results[m]['depth_in_X0'] for m in materials_list]
widths_RM = [results[m]['width_in_RM'] for m in materials_list]

ax2.bar(x - width/2, depths_X0, width, label='Depth (X₀)', color='steelblue')
ax2.bar(x + width/2, widths_RM, width, label='Width (R_M)', color='darkorange')
ax2.set_xlabel('Material')
ax2.set_ylabel('Dimension (natural units)')
ax2.set_title('Calorimeter Dimensions in Natural Units')
ax2.set_xticks(x)
ax2.set_xticklabels(materials_list)
ax2.legend()
ax2.grid(True, alpha=0.3)

# Plot 3: Volume and mass
volumes = [results[m]['volume_cm3'] for m in materials_list]
masses = [results[m]['mass_kg'] for m in materials_list]

ax3.bar(materials_list, volumes, color='green', alpha=0.7)
ax3.set_xlabel('Material')
ax3.set_ylabel('Volume (cm³)')
ax3.set_title('Calorimeter Volume')
ax3.grid(True, alpha=0.3)

ax4.bar(materials_list, masses, color='red', alpha=0.7)
ax4.set_xlabel('Material')
ax4.set_ylabel('Mass (kg)')
ax4.set_title('Calorimeter Mass')
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('calorimeter_dimensions_comparison.png', dpi=150, bbox_inches='tight')
plt.close()

# Create shower profile plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Longitudinal shower profile
z = np.linspace(0, 30, 300)
for mat_name, props in materials.items():
    Ec = critical_energy(props['Z'])
    t_max = shower_max_depth(E0, Ec, props['X0'])
    profile = (z/props['X0'])**((z/props['X0'])/np.e) * np.exp(-(z/props['X0']))
    profile = profile / np.max(profile)
    ax1.plot(z, profile, label=mat_name, linewidth=2)
    ax1.axvline(results[mat_name]['min_depth_95_percent_cm'], 
                color='gray', linestyle='--', alpha=0.5)

ax1.set_xlabel('Depth (cm)')
ax1.set_ylabel('Normalized Energy Deposition')
ax1.set_title('Longitudinal Shower Profile at 5 GeV')
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.set_xlim(0, 30)

# Transverse shower profile
r = np.linspace(0, 20, 200)
for mat_name, props in materials.items():
    profile = np.exp(-r/props['RM']) / props['RM']
    profile = profile / profile[0]
    ax2.plot(r, profile, label=mat_name, linewidth=2)
    ax2.axvline(results[mat_name]['min_width_95_percent_cm']/2, 
                color='gray', linestyle='--', alpha=0.5)

ax2.set_xlabel('Radius (cm)')
ax2.set_ylabel('Normalized Energy Density')
ax2.set_title('Transverse Shower Profile')
ax2.legend()
ax2.grid(True, alpha=0.3)
ax2.set_xlim(0, 20)
ax2.set_ylim(0, 1.1)

plt.tight_layout()
plt.savefig('shower_profiles.png', dpi=150, bbox_inches='tight')
plt.close()

# Add plot filenames to results
results['plots'] = ['calorimeter_dimensions_comparison.png', 'shower_profiles.png']

# Summary recommendations
results['recommendations'] = {
    'most_compact': 'PWO',
    'lightest': 'CsI',
    'best_sampling': 'PWO',
    'optimal_5GeV': {
        'material': 'PWO',
        'dimensions_cm': {
            'depth': results['PWO']['min_depth_95_percent_cm'],
            'width': results['PWO']['min_width_95_percent_cm'],
            'height': results['PWO']['min_width_95_percent_cm']
        },
        'reasoning': 'Shortest radiation length provides most compact design with best sampling'
    }
}

print(json.dumps(results))