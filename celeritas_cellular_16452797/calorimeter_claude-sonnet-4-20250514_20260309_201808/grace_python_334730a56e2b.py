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
import json
import matplotlib.pyplot as plt

# Nuclear interaction length for steel (Fe) in cm
lambda_I_steel = 16.77
# Radiation length for steel in cm
X0_steel = 1.757

# Typical sampling fraction for steel/plastic scintillator
sampling_fraction = 0.05

# Calculate required depth for 95% containment at 50 GeV
# For hadronic showers: 95% containment ~ 4.5 lambda_I + 2.5 lambda_I * log(E/1GeV)
E_max = 50  # GeV
depth_95 = 4.5 * lambda_I_steel + 2.5 * lambda_I_steel * np.log(E_max)

# Design parameters
n_layers = 40
total_depth = depth_95
layer_thickness = total_depth / n_layers

# Optimize absorber/scintillator ratio for sampling fraction
# sampling_fraction = t_scint / (t_absorber + t_scint)
# Typical plastic scintillator thickness: 3-5 mm
t_scint = 0.5  # cm (5 mm)
t_absorber = t_scint * (1 - sampling_fraction) / sampling_fraction

# Adjust to match total depth
scale_factor = layer_thickness / (t_absorber + t_scint)
t_absorber_final = t_absorber * scale_factor
t_scint_final = t_scint * scale_factor

# Calculate actual sampling fraction
actual_sampling_fraction = t_scint_final / (t_absorber_final + t_scint_final)

# Energy resolution estimation
# For hadronic calorimeters: sigma/E ~ a/sqrt(E) + b
# Typical values for steel/scintillator: a ~ 50-80%, b ~ 3-5%
a_resolution = 65  # %
b_resolution = 4   # %

# Calculate resolution at different energies
energies = np.array([5, 10, 20, 30, 40, 50])  # GeV
resolutions = a_resolution / np.sqrt(energies) + b_resolution

# Create visualization
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Plot 1: Calorimeter structure
layer_positions = np.arange(n_layers) * layer_thickness
ax1.barh(layer_positions, np.ones(n_layers) * t_absorber_final, 
         height=t_absorber_final, color='gray', alpha=0.7, label='Steel absorber')
ax1.barh(layer_positions + t_absorber_final, np.ones(n_layers) * t_scint_final, 
         height=t_scint_final, color='blue', alpha=0.7, label='Plastic scintillator')
ax1.set_xlabel('Depth (cm)')
ax1.set_ylabel('Position (cm)')
ax1.set_title('Hadronic Calorimeter Structure')
ax1.legend()
ax1.set_xlim(0, layer_thickness * 1.2)

# Plot 2: Expected energy resolution
ax2.plot(energies, resolutions, 'o-', linewidth=2, markersize=8)
ax2.set_xlabel('Energy (GeV)')
ax2.set_ylabel('Energy Resolution σ/E (%)')
ax2.set_title('Expected Energy Resolution')
ax2.grid(True, alpha=0.3)
ax2.set_ylim(0, max(resolutions) * 1.2)

plt.tight_layout()
plt.savefig('hadronic_calorimeter_design.png', dpi=150)
plt.close()

# Shower containment calculation
containment_fractions = {}
for E in [10, 20, 30, 40, 50]:
    # Longitudinal shower profile: dE/dt ~ t^a * exp(-b*t)
    # where t is depth in lambda_I units
    a = 0.2 * np.log(E) + 0.7
    b = 0.5
    t_max = a / b  # shower maximum position
    
    # Calculate containment fraction
    t_cal = total_depth / lambda_I_steel
    # Approximate integral of shower profile
    containment = 1 - np.exp(-b * t_cal) * (1 + b * t_cal)
    containment_fractions[f"{E}GeV"] = round(containment * 100, 1)

result = {
    "calorimeter_design": {
        "total_depth_cm": round(total_depth, 1),
        "total_depth_lambda_I": round(total_depth / lambda_I_steel, 2),
        "n_layers": n_layers,
        "absorber_thickness_cm": round(t_absorber_final, 3),
        "scintillator_thickness_cm": round(t_scint_final, 3),
        "layer_thickness_cm": round(layer_thickness, 2),
        "sampling_fraction": round(actual_sampling_fraction, 3)
    },
    "material_properties": {
        "absorber": "Steel (Fe)",
        "active": "Plastic scintillator",
        "steel_lambda_I_cm": lambda_I_steel,
        "steel_X0_cm": X0_steel
    },
    "expected_performance": {
        "energy_resolution_stochastic_term": f"{a_resolution}%",
        "energy_resolution_constant_term": f"{b_resolution}%",
        "resolution_at_50GeV": f"{round(resolutions[-1], 1)}%",
        "shower_containment": containment_fractions
    },
    "plots": ["hadronic_calorimeter_design.png"]
}

print(json.dumps(result))