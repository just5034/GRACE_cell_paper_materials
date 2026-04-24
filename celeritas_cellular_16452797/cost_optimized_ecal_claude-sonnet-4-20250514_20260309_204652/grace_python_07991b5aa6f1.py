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
import json
import numpy as np

# Material properties
lead_radiation_length = 0.56  # cm
lead_density = 11.34  # g/cm³
scintillator_radiation_length = 42.0  # cm (polystyrene)
scintillator_density = 1.06  # g/cm³

# Design parameters
target_radiation_lengths = 20
sampling_fraction = 0.05  # 5% sampling fraction typical for Pb-scintillator

# Calculate layer thicknesses
# For sampling calorimeter: X_eff = X_absorber / f_absorber + X_scintillator / f_scintillator
# where f_absorber + f_scintillator = 1
f_lead = 1 - sampling_fraction
f_scint = sampling_fraction

# Typical layer structure: 2mm Pb + 4mm scintillator
lead_layer_thickness = 0.2  # cm
scint_layer_thickness = 0.4  # cm
layer_thickness = lead_layer_thickness + scint_layer_thickness

# Radiation lengths per layer
x0_per_layer = (lead_layer_thickness / lead_radiation_length) + (scint_layer_thickness / scintillator_radiation_length)

# Number of layers needed
n_layers = int(np.ceil(target_radiation_lengths / x0_per_layer))

# Total depth
total_depth = n_layers * layer_thickness

# Actual radiation lengths
actual_x0 = n_layers * x0_per_layer

# Transverse size (typical tower size)
transverse_size = 5.0  # cm (typical tower size for sampling calorimeter)

# Calculate masses
lead_volume_per_layer = transverse_size * transverse_size * lead_layer_thickness
scint_volume_per_layer = transverse_size * transverse_size * scint_layer_thickness

total_lead_volume = lead_volume_per_layer * n_layers
total_scint_volume = scint_volume_per_layer * n_layers

lead_mass = total_lead_volume * lead_density / 1000  # kg
scint_mass = total_scint_volume * scintillator_density / 1000  # kg
total_mass = lead_mass + scint_mass

# Moliere radius for lead
lead_moliere_radius = 1.6  # cm
tower_coverage = transverse_size / lead_moliere_radius

result = {
    "lead_scintillator_layer_structure": {
        "lead_thickness_per_layer_cm": lead_layer_thickness,
        "scintillator_thickness_per_layer_cm": scint_layer_thickness,
        "total_thickness_per_layer_cm": layer_thickness,
        "number_of_layers": n_layers,
        "total_depth_cm": total_depth,
        "transverse_size_cm": transverse_size,
        "radiation_lengths_per_layer": round(x0_per_layer, 4),
        "total_radiation_lengths": round(actual_x0, 2),
        "sampling_fraction": sampling_fraction,
        "lead_mass_kg": round(lead_mass, 3),
        "scintillator_mass_kg": round(scint_mass, 3),
        "total_mass_kg": round(total_mass, 3),
        "moliere_radii_coverage": round(tower_coverage, 2)
    }
}

print(json.dumps(result))