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
import matplotlib
matplotlib.use('Agg')
import pandas as pd
import numpy as np
import json
import glob
import os
import matplotlib.pyplot as plt

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/timing_calorimeter_claude-sonnet-4-20250514_20260309_204646'
energies = ['1.000', '5.000', '20.000']
detectors = ['lyso_calorimeter', 'plastic_calorimeter', 'detector_2']
detector_names = {'lyso_calorimeter': 'LYSO Crystal', 'plastic_calorimeter': 'Plastic Scintillator', 'detector_2': 'W/Plastic Sampling'}

results = {}

for detector in detectors:
    results[detector] = {
        'energy_resolution': {},
        'timing_resolution_ps': {},
        'mean_first_hit_time_ns': {},
        'depth_radiation_lengths': None
    }
    
    # Set radiation lengths based on detector type
    if detector == 'lyso_calorimeter':
        # LYSO X0 = 1.14 cm, detector depth = 30 cm
        results[detector]['depth_radiation_lengths'] = 30.0 / 1.14
    elif detector == 'plastic_calorimeter':
        # Plastic X0 ~ 42 cm, detector depth = 30 cm  
        results[detector]['depth_radiation_lengths'] = 30.0 / 42.0
    else:  # sampling calorimeter
        # W X0 = 0.35 cm, 20 layers of 2mm W = 4 cm W total
        results[detector]['depth_radiation_lengths'] = 4.0 / 0.35
    
    for energy in energies:
        energy_dir = os.path.join(base_dir, f'energy_{energy}GeV')
        
        # Find events file
        events_pattern = os.path.join(energy_dir, f'{detector}_em_events.parquet')
        events_files = glob.glob(events_pattern)
        if not events_files:
            continue
            
        # Find hits file
        hits_pattern = os.path.join(energy_dir, f'{detector}_em_hits_data.parquet')
        hits_files = glob.glob(hits_pattern)
        if not hits_files:
            continue
            
        # Read data
        events = pd.read_parquet(events_files[0])
        hits = pd.read_parquet(hits_files[0])
        
        # Energy resolution
        true_e = float(energy)
        mean_edep = events['totalEdep'].mean() / 1000.0  # MeV to GeV
        std_edep = events['totalEdep'].std() / 1000.0
        energy_res = std_edep / mean_edep if mean_edep > 0 else 0
        results[detector]['energy_resolution'][f'{true_e}GeV'] = energy_res
        
        # Timing resolution - first hit time per event
        first_hits = hits.groupby('eventID')['time'].min()
        mean_time = first_hits.mean()
        std_time = first_hits.std()
        timing_res_ps = std_time * 1000  # ns to ps
        
        results[detector]['timing_resolution_ps'][f'{true_e}GeV'] = timing_res_ps
        results[detector]['mean_first_hit_time_ns'][f'{true_e}GeV'] = mean_time

# Create comparison plots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Timing resolution plot
for detector in detectors:
    energies_gev = []
    timing_ps = []
    for e in ['1.0', '5.0', '20.0']:
        key = f'{e}GeV'
        if key in results[detector]['timing_resolution_ps']:
            energies_gev.append(float(e))
            timing_ps.append(results[detector]['timing_resolution_ps'][key])
    if energies_gev:
        ax1.plot(energies_gev, timing_ps, 'o-', label=detector_names[detector], markersize=8)

ax1.axhspan(10, 30, alpha=0.2, color='green', label='Target: 10-30 ps')
ax1.set_xlabel('Beam Energy (GeV)')
ax1.set_ylabel('Timing Resolution (ps)')
ax1.set_title('Timing Resolution Comparison')
ax1.set_xscale('log')
ax1.set_yscale('log')
ax1.grid(True, alpha=0.3)
ax1.legend()

# Energy resolution plot
for detector in detectors:
    energies_gev = []
    energy_res = []
    for e in ['1.0', '5.0', '20.0']:
        key = f'{e}GeV'
        if key in results[detector]['energy_resolution']:
            energies_gev.append(float(e))
            energy_res.append(results[detector]['energy_resolution'][key] * 100)  # to percent
    if energies_gev:
        ax2.plot(energies_gev, energy_res, 'o-', label=detector_names[detector], markersize=8)

ax2.set_xlabel('Beam Energy (GeV)')
ax2.set_ylabel('Energy Resolution (%)')
ax2.set_title('Energy Resolution Comparison')
ax2.set_xscale('log')
ax2.grid(True, alpha=0.3)
ax2.legend()

plt.tight_layout()
plot_file = os.path.join(base_dir, 'detector_comparison.png')
plt.savefig(plot_file, dpi=150)
plt.close()

# Summary table
summary = {
    'best_timing_detector': None,
    'best_timing_resolution_ps': float('inf'),
    'detector_performance': {}
}

for detector in detectors:
    avg_timing = np.mean(list(results[detector]['timing_resolution_ps'].values()))
    avg_energy = np.mean(list(results[detector]['energy_resolution'].values())) * 100
    
    summary['detector_performance'][detector_names[detector]] = {
        'avg_timing_resolution_ps': round(avg_timing, 2),
        'avg_energy_resolution_percent': round(avg_energy, 2),
        'radiation_lengths': round(results[detector]['depth_radiation_lengths'], 1),
        'meets_timing_target': 10 <= avg_timing <= 30
    }
    
    if avg_timing < summary['best_timing_resolution_ps']:
        summary['best_timing_resolution_ps'] = avg_timing
        summary['best_timing_detector'] = detector_names[detector]

summary['plot'] = plot_file
summary['recommendation'] = f"The {summary['best_timing_detector']} provides the best timing resolution at {summary['best_timing_resolution_ps']:.1f} ps"

print(json.dumps(summary))