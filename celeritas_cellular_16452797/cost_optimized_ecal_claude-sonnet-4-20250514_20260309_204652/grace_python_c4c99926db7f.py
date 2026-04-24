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

# Iron properties
iron_radiation_length = 1.76  # cm
iron_density = 7.874  # g/cm³

# Scintillator properties  
scintillator_radiation_length = 41.3  # cm (polystyrene)
scintillator_density = 1.032  # g/cm³

# Target: 20 radiation lengths total
target_X0 = 20

# Design parameters
# Use 3mm iron + 5mm scintillator per layer (common configuration)
iron_thickness_per_layer = 0.3  # cm
scintillator_thickness_per_layer = 0.5  # cm

# Calculate radiation lengths per layer
X0_iron_per_layer = iron_thickness_per_layer / iron_radiation_length
X0_scint_per_layer = scintillator_thickness_per_layer / scintillator_radiation_length
X0_per_layer = X0_iron_per_layer + X0_scint_per_layer

# Number of layers needed
n_layers = int(np.ceil(target_X0 / X0_per_layer))

# Total radiation lengths achieved
total_X0 = n_layers * X0_per_layer

# Total thickness
total_thickness_per_layer = iron_thickness_per_layer + scintillator_thickness_per_layer
total_depth = n_layers * total_thickness_per_layer

# Transverse size - use 10cm x 10cm modules
transverse_size = 10.0  # cm

# Calculate sampling fraction
sampling_fraction = scintillator_thickness_per_layer / total_thickness_per_layer

# Calculate masses
iron_volume_per_layer = iron_thickness_per_layer * transverse_size * transverse_size
scint_volume_per_layer = scintillator_thickness_per_layer * transverse_size * transverse_size

total_iron_mass = n_layers * iron_volume_per_layer * iron_density / 1000  # kg
total_scint_mass = n_layers * scint_volume_per_layer * scintillator_density / 1000  # kg

result = {
    "iron_scintillator_layer_structure": {
        "iron_thickness_per_layer_cm": iron_thickness_per_layer,
        "scintillator_thickness_per_layer_cm": scintillator_thickness_per_layer,
        "total_thickness_per_layer_cm": total_thickness_per_layer,
        "number_of_layers": n_layers,
        "total_depth_cm": total_depth,
        "transverse_size_cm": transverse_size,
        "radiation_lengths_per_layer": round(X0_per_layer, 4),
        "total_radiation_lengths": round(total_X0, 2),
        "sampling_fraction": round(sampling_fraction, 3),
        "total_iron_mass_kg": round(total_iron_mass, 2),
        "total_scintillator_mass_kg": round(total_scint_mass, 2)
    }
}

print(json.dumps(result))