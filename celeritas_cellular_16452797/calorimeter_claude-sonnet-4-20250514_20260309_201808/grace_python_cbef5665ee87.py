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
# Typical compensating ratios for Fe:scintillator are around 4:1 to 5:1 by thickness

config = {
    "absorber_material": "G4_Fe",
    "absorber_thickness": 20.0,  # mm - thicker absorber for compensation
    "active_material": "G4_POLYSTYRENE", 
    "active_thickness": 4.0,  # mm - ratio of 5:1 Fe:scintillator
    "num_layers": 50,  # More layers for better sampling
    "compensation_ratio": 5.0,  # Fe:scintillator thickness ratio
    "transverse_size": 150.0,  # mm - larger for better containment
    "detector_type": "compensating_calorimeter"
}

# Calculate derived parameters
layer_thickness = config["absorber_thickness"] + config["active_thickness"]
total_depth = config["num_layers"] * layer_thickness

# Nuclear interaction length for Fe: ~16.8 cm
# Radiation length for Fe: ~1.76 cm
lambda_Fe = 168.0  # mm
X0_Fe = 17.6  # mm

# For polystyrene: lambda ~ 79 cm, X0 ~ 42.5 cm
lambda_PS = 790.0  # mm
X0_PS = 425.0  # mm

# Calculate effective interaction length and radiation length
absorber_fraction = config["absorber_thickness"] / layer_thickness
active_fraction = config["active_thickness"] / layer_thickness

effective_lambda = 1.0 / (absorber_fraction/lambda_Fe + active_fraction/lambda_PS)
effective_X0 = 1.0 / (absorber_fraction/X0_Fe + active_fraction/X0_PS)

# Sampling fraction estimate
density_Fe = 7.874  # g/cm^3
density_PS = 1.06   # g/cm^3
sampling_fraction = (config["active_thickness"] * density_PS) / (config["absorber_thickness"] * density_Fe + config["active_thickness"] * density_PS)

# Add calculated parameters to config
config.update({
    "layer_thickness": layer_thickness,
    "total_depth": total_depth,
    "effective_lambda": effective_lambda,
    "effective_X0": effective_X0,
    "sampling_fraction": sampling_fraction,
    "containment_lambda": total_depth / effective_lambda,
    "e_h_ratio_target": 1.0,  # Target for compensation
    "description": "Compensating calorimeter with 5:1 Fe:scintillator ratio for e/h≈1"
})

print(json.dumps(config))