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
import math

# Iron radiation length: 1.76 cm
# Scintillator radiation length: 41.3 cm (polystyrene)
# Target: 20 radiation lengths total

iron_X0 = 1.76  # cm
scintillator_X0 = 41.3  # cm

# Design parameters
target_X0 = 20
sampling_fraction = 0.05  # 5% sampling fraction typical for Fe-Scint

# Calculate layer thicknesses
# For iron-scintillator, use 1cm iron + 0.5cm scintillator layers
absorber_thickness = 1.0  # cm of iron
active_thickness = 0.5   # cm of scintillator

# Radiation lengths per layer
X0_per_layer = absorber_thickness/iron_X0 + active_thickness/scintillator_X0

# Number of layers needed
num_layers = int(math.ceil(target_X0 / X0_per_layer))

# Actual radiation lengths achieved
actual_X0 = num_layers * X0_per_layer

# Total depth
total_depth = num_layers * (absorber_thickness + active_thickness)

# Transverse size - use 5cm for budget option
transverse_size = 5.0

result = {
    "iron_scintillator_layer_structure": {
        "absorber_thickness": absorber_thickness,
        "active_thickness": active_thickness,
        "num_layers": num_layers,
        "total_depth_cm": total_depth,
        "transverse_size_cm": transverse_size,
        "radiation_lengths_per_layer": X0_per_layer,
        "total_radiation_lengths": actual_X0,
        "sampling_fraction": active_thickness / (absorber_thickness + active_thickness)
    }
}

print(json.dumps(result))