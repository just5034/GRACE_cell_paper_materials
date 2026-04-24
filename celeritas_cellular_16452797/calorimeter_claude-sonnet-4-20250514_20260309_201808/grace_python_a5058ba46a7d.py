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

# Design compensating calorimeter configuration with optimized steel-scintillator ratio
# Goal: achieve e/h ≈ 1 for improved linearity

# For compensation, we need to balance electromagnetic and hadronic responses
# Typical compensating ratios for steel:scintillator are around 4:1 to 5:1 by thickness

config = {
    "absorber_material": "G4_Fe",  # Steel absorber
    "absorber_thickness": 20.0,     # 20 mm steel plates
    "active_material": "G4_POLYSTYRENE",  # Plastic scintillator
    "active_thickness": 4.0,        # 4 mm scintillator (5:1 ratio)
    "num_layers": 40,               # 40 layers for good containment
    "transverse_size": 120.0,       # 120x120 mm^2 transverse size
    "compensation_ratio": 5.0,      # Steel:scintillator thickness ratio
    "detector_type": "compensating_calorimeter"
}

# Calculate derived quantities
layer_thickness = config["absorber_thickness"] + config["active_thickness"]
total_depth = config["num_layers"] * layer_thickness

# Nuclear interaction length for Fe: ~16.8 cm, for plastic: ~70 cm
# Radiation length for Fe: ~1.76 cm, for plastic: ~42.5 cm
lambda_Fe = 168.0  # mm
lambda_plastic = 700.0  # mm
X0_Fe = 17.6  # mm
X0_plastic = 425.0  # mm

# Calculate effective interaction length and radiation length
absorber_fraction = config["absorber_thickness"] / layer_thickness
active_fraction = config["active_thickness"] / layer_thickness

effective_lambda = 1.0 / (absorber_fraction/lambda_Fe + active_fraction/lambda_plastic)
effective_X0 = 1.0 / (absorber_fraction/X0_Fe + active_fraction/X0_plastic)

# Sampling fraction estimate (energy deposited in active / total energy)
# For compensating calorimeter, this is tuned to achieve e/h ≈ 1
sampling_fraction = 0.035  # Typical value for 5:1 steel:scintillator

# Add calculated values to config
config.update({
    "layer_thickness": layer_thickness,
    "total_depth": total_depth,
    "effective_lambda": effective_lambda,
    "effective_X0": effective_X0,
    "sampling_fraction": sampling_fraction,
    "containment_lambda": total_depth / effective_lambda,
    "containment_X0": total_depth / effective_X0,
    "e_h_ratio_target": 1.0
})

print(json.dumps(config))