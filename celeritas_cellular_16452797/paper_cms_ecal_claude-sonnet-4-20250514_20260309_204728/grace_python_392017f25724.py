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
from pathlib import Path

# Read the extracted setup parameters
with open('/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/paper_cms_ecal_claude-sonnet-4-20250514_20260309_204728/extracted_setup.json', 'r') as f:
    setup = json.load(f)

# Extract crystal parameters
crystal_params = setup['detector']['crystal_parameters']
barrel_params = setup['detector']['barrel']
endcap_params = setup['detector']['endcap']

# Crystal dimensions (convert mm to cm for Geant4)
crystal_length = crystal_params['length'] / 10.0  # 230 mm -> 23 cm
crystal_front = crystal_params['front_face_area'] / 10.0  # 22 mm -> 2.2 cm
crystal_rear = crystal_params['rear_face_area'] / 10.0  # 26 mm -> 2.6 cm

# Calculate taper angle for trapezoidal crystal
taper = (crystal_rear - crystal_front) / (2 * crystal_length)

# Barrel parameters
barrel_inner_radius = barrel_params['inner_radius'] / 10.0  # 1290 mm -> 129 cm
barrel_crystals = barrel_params['crystals']
barrel_eta_coverage = barrel_params['eta_coverage']

# Create simplified GDML geometry
gdml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<gdml xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://service-spi.web.cern.ch/service-spi/app/releases/GDML/schema/gdml.xsd">

  <define>
    <constant name="world_size" value="10000"/>
    <constant name="crystal_length" value="{crystal_length}"/>
    <constant name="crystal_front" value="{crystal_front}"/>
    <constant name="crystal_rear" value="{crystal_rear}"/>
    <constant name="barrel_inner_radius" value="{barrel_inner_radius}"/>
    <constant name="n_phi" value="360"/>
    <constant name="n_eta" value="85"/>
  </define>

  <materials>
    <material name="PbWO4" state="solid">
      <D value="8.28" unit="g/cm3"/>
      <composite n="1" ref="Pb"/>
      <composite n="1" ref="W"/>
      <composite n="4" ref="O"/>
    </material>
    <element name="Pb" formula="Pb" Z="82">
      <atom value="207.2"/>
    </element>
    <element name="W" formula="W" Z="74">
      <atom value="183.84"/>
    </element>
    <element name="O" formula="O" Z="8">
      <atom value="15.999"/>
    </element>
    <material name="Air" state="gas">
      <D value="0.001293" unit="g/cm3"/>
      <fraction n="0.7" ref="N"/>
      <fraction n="0.3" ref="O"/>
    </material>
    <element name="N" formula="N" Z="7">
      <atom value="14.007"/>
    </element>
  </materials>

  <solids>
    <box name="world_solid" x="world_size" y="world_size" z="world_size" lunit="cm"/>
    
    <trd name="crystal_solid" 
         x1="crystal_front" y1="crystal_front" 
         x2="crystal_rear" y2="crystal_rear" 
         z="crystal_length" lunit="cm"/>
    
    <tube name="barrel_solid" 
          rmin="barrel_inner_radius" 
          rmax="barrel_inner_radius + crystal_length + 5" 
          z="600" 
          deltaphi="360" 
          aunit="deg" lunit="cm"/>
  </solids>

  <structure>
    <volume name="crystal_vol">
      <materialref ref="PbWO4"/>
      <solidref ref="crystal_solid"/>
    </volume>
    
    <volume name="barrel_vol">
      <materialref ref="Air"/>
      <solidref ref="barrel_solid"/>
      
      <!-- Place crystals in a simplified grid pattern -->
      <loop for="iphi" from="0" to="n_phi-1" step="1">
        <loop for="ieta" from="-n_eta/2" to="n_eta/2" step="1">
          <physvol>
            <volumeref ref="crystal_vol"/>
            <position name="crystal_pos_{{iphi}}_{{ieta}}" 
                      x="(barrel_inner_radius + crystal_length/2) * cos(iphi*360/n_phi*3.14159/180)" 
                      y="(barrel_inner_radius + crystal_length/2) * sin(iphi*360/n_phi*3.14159/180)" 
                      z="ieta * crystal_front * 1.1" 
                      unit="cm"/>
            <rotation name="crystal_rot_{{iphi}}_{{ieta}}" 
                      x="0" 
                      y="0" 
                      z="iphi*360/n_phi" 
                      unit="deg"/>
          </physvol>
        </loop>
      </loop>
    </volume>
    
    <volume name="world_vol">
      <materialref ref="Air"/>
      <solidref ref="world_solid"/>
      <physvol>
        <volumeref ref="barrel_vol"/>
      </physvol>
    </volume>
  </structure>

  <setup name="Default" version="1.0">
    <world ref="world_vol"/>
  </setup>

</gdml>"""

# Write GDML file
output_path = Path('/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/paper_cms_ecal_claude-sonnet-4-20250514_20260309_204728/baseline_detector.gdml')
with open(output_path, 'w') as f:
    f.write(gdml_content)

# Create Geant4 macro for running simulations
macro_content = """# Geant4 macro for CMS ECAL baseline simulation

/run/initialize

# Set physics list
/physics_list/em/GammaToMuons true
/physics_list/em/PositronToMuons true
/physics_list/em/PositronToHadrons true

# Primary particle generator
/gun/particle e-
/gun/energy 10 GeV
/gun/position 0 0 -200 cm
/gun/direction 0 0 1

# Visualization (optional)
#/vis/open OGL
#/vis/drawVolume
#/vis/viewer/set/viewpointThetaPhi 90 90
#/vis/scene/add/trajectories smooth

# Run simulation
/run/beamOn 1000
"""

macro_path = Path('/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/paper_cms_ecal_claude-sonnet-4-20250514_20260309_204728/baseline_run.mac')
with open(macro_path, 'w') as f:
    f.write(macro_content)

result = {
    "success": True,
    "gdml_file": str(output_path),
    "macro_file": str(macro_path),
    "geometry_parameters": {
        "crystal_length_cm": crystal_length,
        "crystal_front_face_cm": crystal_front,
        "crystal_rear_face_cm": crystal_rear,
        "barrel_inner_radius_cm": barrel_inner_radius,
        "n_crystals_phi": 360,
        "n_crystals_eta": 85,
        "total_crystals": 360 * 85
    },
    "material": "PbWO4",
    "density_g_cm3": 8.28
}

print(json.dumps(result))