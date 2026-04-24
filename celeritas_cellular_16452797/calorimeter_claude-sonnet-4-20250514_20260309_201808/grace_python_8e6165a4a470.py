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
import math

# Design baseline sampling calorimeter configuration
# Target: 95% shower containment at 50 GeV

# Material properties
steel_density = 7.87  # g/cm^3
steel_X0 = 1.757  # cm (radiation length)
steel_lambda = 16.77  # cm (nuclear interaction length)

plastic_density = 1.032  # g/cm^3
plastic_X0 = 42.4  # cm
plastic_lambda = 79.36  # cm

# Design parameters for hadronic calorimeter
# Typical sampling fraction for steel/plastic: 4-5% 
# Absorber thickness: ~1 lambda for good sampling
# Active thickness: ~5-10 mm for light collection

# Calculate optimal configuration
absorber_thickness = 2.0  # cm (about 0.12 lambda)
active_thickness = 0.5  # cm (5 mm plastic scintillator)
layer_thickness = absorber_thickness + active_thickness

# For 95% containment at 50 GeV, need ~5-6 lambda total
# Rule of thumb: 95% containment requires 4.5 + 0.08*ln(E/GeV) lambda
containment_lambda = 4.5 + 0.08 * math.log(50)
total_depth_needed = containment_lambda * steel_lambda  # cm

# Calculate number of layers
num_layers = int(np.ceil(total_depth_needed / layer_thickness))
total_depth = num_layers * layer_thickness

# Calculate effective lambda and X0
steel_fraction = absorber_thickness / layer_thickness
plastic_fraction = active_thickness / layer_thickness
effective_lambda = 1.0 / (steel_fraction/steel_lambda + plastic_fraction/plastic_lambda)
effective_X0 = 1.0 / (steel_fraction/steel_X0 + plastic_fraction/plastic_X0)

# Sampling fraction estimation
mip_dedx_steel = 1.45  # MeV cm^2/g
mip_dedx_plastic = 2.0  # MeV cm^2/g
energy_steel = mip_dedx_steel * steel_density * absorber_thickness
energy_plastic = mip_dedx_plastic * plastic_density * active_thickness
sampling_fraction = energy_plastic / (energy_steel + energy_plastic)

# Transverse size for shower containment
# Moliere radius approximation
moliere_radius = effective_X0 * 21.2 / 7.0  # MeV
transverse_size = 100.0  # cm (sufficient for shower containment)

result = {
    "absorber_material": "G4_Fe",
    "absorber_thickness": absorber_thickness,
    "active_material": "G4_POLYSTYRENE", 
    "active_thickness": active_thickness,
    "num_layers": num_layers,
    "total_depth": total_depth,
    "transverse_size": transverse_size,
    "layer_thickness": layer_thickness,
    "effective_lambda": effective_lambda,
    "effective_X0": effective_X0,
    "sampling_fraction": sampling_fraction,
    "containment_lambda": containment_lambda,
    "total_lambda": total_depth / effective_lambda
}

print(json.dumps(result))