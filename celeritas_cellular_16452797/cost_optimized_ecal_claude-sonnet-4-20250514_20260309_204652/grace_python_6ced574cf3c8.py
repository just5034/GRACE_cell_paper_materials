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
import numpy as np
import json

# PbWO4 properties
radiation_length_pbwo4 = 0.89  # cm
moliere_radius_pbwo4 = 2.2  # cm
density_pbwo4 = 8.28  # g/cm^3

# Target specifications
target_radiation_lengths = 20
min_transverse_size = 5  # minimum 5x5 Moliere radii

# Calculate dimensions
depth = target_radiation_lengths * radiation_length_pbwo4  # cm
transverse_size = min_transverse_size * moliere_radius_pbwo4  # cm

# Calculate volume and mass
volume = transverse_size * transverse_size * depth  # cm^3
mass = volume * density_pbwo4  # g
mass_kg = mass / 1000  # kg

result = {
    "pbwo4_calorimeter_dimensions": {
        "depth_cm": depth,
        "transverse_size_cm": transverse_size,
        "volume_cm3": volume,
        "mass_kg": mass_kg,
        "radiation_lengths": target_radiation_lengths,
        "moliere_radii_coverage": min_transverse_size
    }
}

print(json.dumps(result))