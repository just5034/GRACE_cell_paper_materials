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

# Design compensating calorimeter configuration with optimized steel-scintillator ratio
# The goal is to achieve e/h ≈ 1 for improved linearity

# For compensating calorimeters, typical steel:scintillator ratios range from 3:1 to 5:1
# We'll use 4:1 ratio which is commonly used for e/h compensation

config = {
    "absorber_material": "G4_Fe",  # Steel absorber
    "absorber_thickness": 20.0,     # 20 mm steel plates
    "active_material": "G4_POLYSTYRENE",  # Plastic scintillator
    "active_thickness": 5.0,        # 5 mm scintillator (4:1 ratio)
    "num_layers": 40,               # 40 layers for good containment
    "transverse_size": 150.0,       # 150x150 mm^2 transverse size
    "segmentation": "5x5"           # 5x5 tower segmentation
}

# Calculate derived parameters
layer_thickness = config["absorber_thickness"] + config["active_thickness"]
total_depth = config["num_layers"] * layer_thickness

# Add calculated parameters
config["layer_thickness"] = layer_thickness
config["total_depth"] = total_depth
config["sampling_fraction"] = config["active_thickness"] / layer_thickness

# Estimate interaction lengths (approximate values for Fe and plastic)
lambda_Fe = 168.0  # mm
lambda_plastic = 790.0  # mm
X0_Fe = 17.6  # mm
X0_plastic = 424.0  # mm

# Calculate effective interaction length and radiation length
f_abs = config["absorber_thickness"] / layer_thickness
f_act = config["active_thickness"] / layer_thickness
effective_lambda = 1.0 / (f_abs/lambda_Fe + f_act/lambda_plastic)
effective_X0 = 1.0 / (f_abs/X0_Fe + f_act/X0_plastic)

config["effective_lambda"] = effective_lambda
config["effective_X0"] = effective_X0
config["containment_lambda"] = total_depth / effective_lambda

# Add compensation-specific parameters
config["compensation_ratio"] = config["absorber_thickness"] / config["active_thickness"]
config["detector_type"] = "compensating_calorimeter"
config["description"] = "Compensating hadronic calorimeter with 4:1 Fe:scintillator ratio for e/h≈1"

print(json.dumps(config))