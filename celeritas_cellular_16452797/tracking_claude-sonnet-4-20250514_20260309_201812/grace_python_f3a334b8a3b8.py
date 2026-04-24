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

# Silicon properties
X0_Si = 9.37  # radiation length in cm
rho_Si = 2.33  # density in g/cm^3

# Design parameters
n_layers = 4
detector_length = 100.0  # cm total length
min_layer_spacing = 15.0  # cm minimum spacing for pattern recognition

# Optimize layer positions for momentum resolution
# Equal spacing is near-optimal for momentum measurement
layer_spacing = detector_length / (n_layers - 1)
layer_positions = np.linspace(0, detector_length, n_layers)

# Silicon thickness optimization
# Balance between resolution (thinner is better) and signal (thicker is better)
# Typical pixel detectors use 200-300 microns
layer_thickness = 250e-4  # 250 microns in cm

# Calculate material budget
material_budget_per_layer = layer_thickness / X0_Si * 100  # in % X0
total_material_budget = n_layers * material_budget_per_layer

# Position resolution (typical for pixel detectors)
position_resolution = 10e-4  # 10 microns in cm

# Calculate expected momentum resolution contribution from multiple scattering
# sigma_p/p ~ 0.0136 * sqrt(x/X0) / (beta * p) for small angles
# For relativistic particles (beta ~ 1) at 1 GeV/c
p_test = 1.0  # GeV/c
ms_contribution = 0.0136 * np.sqrt(total_material_budget/100) / p_test

# Calculate measurement resolution contribution
# For helical tracks: sigma_p/p ~ sigma_x * p / (0.3 * B * L^2)
# Assuming B = 2 Tesla typical for trackers
B_field = 2.0  # Tesla
measurement_contribution = position_resolution * p_test / (0.3 * B_field * (detector_length/100)**2)

# Total momentum resolution
total_momentum_resolution = np.sqrt(ms_contribution**2 + measurement_contribution**2)

# Create visualization
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

# Layer layout
ax1.set_xlim(-10, 110)
ax1.set_ylim(-5, 5)
for i, pos in enumerate(layer_positions):
    ax1.add_patch(plt.Rectangle((pos-0.5, -2), 1, 4, 
                               facecolor='blue', alpha=0.6))
    ax1.text(pos, 3, f'L{i+1}', ha='center', fontsize=10)
ax1.set_xlabel('Z position (cm)')
ax1.set_ylabel('Detector view')
ax1.set_title('Silicon Pixel Tracker Layout')
ax1.grid(True, alpha=0.3)

# Material budget distribution
z_positions = np.linspace(0, detector_length, 1000)
material_accumulated = np.zeros_like(z_positions)
for i, z in enumerate(z_positions):
    n_layers_crossed = np.sum(z >= layer_positions)
    material_accumulated[i] = n_layers_crossed * material_budget_per_layer

ax2.plot(z_positions, material_accumulated, 'b-', linewidth=2)
ax2.set_xlabel('Z position (cm)')
ax2.set_ylabel('Accumulated material budget (% X0)')
ax2.set_title('Material Budget vs Position')
ax2.grid(True, alpha=0.3)
ax2.axhline(y=total_material_budget, color='r', linestyle='--', 
            label=f'Total: {total_material_budget:.2f}% X0')
ax2.legend()

plt.tight_layout()
plt.savefig('tracker_design.png', dpi=150)
plt.close()

# Compile results
result = {
    "detector_configuration": {
        "n_layers": n_layers,
        "layer_positions_cm": layer_positions.tolist(),
        "layer_spacing_cm": layer_spacing,
        "layer_thickness_microns": layer_thickness * 1e4,
        "detector_length_cm": detector_length
    },
    "material_budget": {
        "per_layer_percent_X0": material_budget_per_layer,
        "total_percent_X0": total_material_budget,
        "radiation_length_Si_cm": X0_Si
    },
    "expected_performance": {
        "position_resolution_microns": position_resolution * 1e4,
        "momentum_resolution_at_1GeV": total_momentum_resolution,
        "multiple_scattering_contribution": ms_contribution,
        "measurement_contribution": measurement_contribution
    },
    "design_rationale": {
        "spacing_optimized_for": "momentum measurement with equal spacing",
        "thickness_choice": "250 microns balances resolution and signal",
        "total_material_budget_assessment": "1.07% X0 is excellent for a 4-layer tracker"
    },
    "plots": ["tracker_design.png"]
}

print(json.dumps(result))