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
# Typical sampling fraction for iron-scintillator: 2-5% scintillator by radiation length
# Target: 20 radiation lengths total

iron_X0 = 1.76  # cm
target_X0 = 20
sampling_fraction = 0.04  # 4% sampling fraction (typical for iron-scintillator)

# Calculate layer structure
# For iron-scintillator, typical configuration uses thin iron absorber with thin scintillator
# Common ratio is ~10:1 iron to scintillator by thickness

iron_thickness = 1.0  # cm per layer
scintillator_thickness = 0.3  # cm per layer
layer_thickness = iron_thickness + scintillator_thickness

# Calculate radiation lengths per layer
X0_per_layer = iron_thickness / iron_X0  # scintillator contributes negligibly to X0

# Number of layers needed
num_layers = int(math.ceil(target_X0 / X0_per_layer))

# Adjust iron thickness to hit exactly 20 X0
iron_thickness = (target_X0 * iron_X0) / num_layers

# Recalculate total thickness
layer_thickness = iron_thickness + scintillator_thickness
total_depth = num_layers * layer_thickness

# Transverse size - use 5 cm (matching midrange design)
transverse_size = 5.0

# Calculate actual radiation lengths and sampling fraction
actual_X0 = num_layers * (iron_thickness / iron_X0)
actual_sampling_fraction = scintillator_thickness / layer_thickness

result = {
    "iron_scintillator_layer_structure": {
        "absorber_thickness": iron_thickness,
        "active_thickness": scintillator_thickness,
        "num_layers": num_layers,
        "total_thickness_per_layer_cm": layer_thickness,
        "total_depth_cm": total_depth,
        "transverse_size_cm": transverse_size,
        "radiation_lengths_per_layer": iron_thickness / iron_X0,
        "total_radiation_lengths": actual_X0,
        "sampling_fraction": actual_sampling_fraction,
        "iron_density_g_cm3": 7.874,
        "scintillator_density_g_cm3": 1.032
    }
}

print(json.dumps(result))