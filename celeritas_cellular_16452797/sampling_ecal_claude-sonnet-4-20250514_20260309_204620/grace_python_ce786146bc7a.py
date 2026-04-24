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

# Constants
tungsten_radiation_length = 0.35  # cm
total_tungsten_depth = 8.75  # cm (approximately 25 radiation lengths)

# Configuration thicknesses in cm
config1_thickness = 0.2  # 2mm
config2_thickness = 0.35  # 3.5mm
config3_thickness = 0.5  # 5mm

# Calculate number of layers for each configuration
n_layers_config1 = int(total_tungsten_depth / config1_thickness)
n_layers_config2 = int(total_tungsten_depth / config2_thickness)
n_layers_config3 = int(total_tungsten_depth / config3_thickness)

# Calculate actual tungsten depth and radiation lengths
actual_depth_config1 = n_layers_config1 * config1_thickness
actual_depth_config2 = n_layers_config2 * config2_thickness
actual_depth_config3 = n_layers_config3 * config3_thickness

actual_rad_lengths_config1 = actual_depth_config1 / tungsten_radiation_length
actual_rad_lengths_config2 = actual_depth_config2 / tungsten_radiation_length
actual_rad_lengths_config3 = actual_depth_config3 / tungsten_radiation_length

result = {
    "config1": {
        "tungsten_layer_thickness_mm": 2,
        "number_of_layers": n_layers_config1,
        "total_tungsten_depth_cm": actual_depth_config1,
        "radiation_lengths": actual_rad_lengths_config1
    },
    "config2": {
        "tungsten_layer_thickness_mm": 3.5,
        "number_of_layers": n_layers_config2,
        "total_tungsten_depth_cm": actual_depth_config2,
        "radiation_lengths": actual_rad_lengths_config2
    },
    "config3": {
        "tungsten_layer_thickness_mm": 5,
        "number_of_layers": n_layers_config3,
        "total_tungsten_depth_cm": actual_depth_config3,
        "radiation_lengths": actual_rad_lengths_config3
    }
}

print(json.dumps(result))