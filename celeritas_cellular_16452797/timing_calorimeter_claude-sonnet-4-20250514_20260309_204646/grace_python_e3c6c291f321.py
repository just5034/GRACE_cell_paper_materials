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
from scipy.optimize import curve_fit

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/timing_calorimeter_claude-sonnet-4-20250514_20260309_204646'
energies = [1.0, 5.0, 20.0]
detectors = ['lyso_calorimeter', 'plastic_calorimeter', 'detector_2']
detector_names = {'lyso_calorimeter': 'LYSO', 'plastic_calorimeter': 'Plastic', 'detector_2': 'Sampling'}

results = {}

def gaussian(x, a, mu, sigma):
    return a * np.exp(-(x - mu)**2 / (2 * sigma**2))

for detector in detectors:
    detector_results = {'timing_resolution': {}, 'energy_resolution': {}}
    
    for energy in energies:
        energy_dir = os.path.join(base_dir, f'energy_{energy:.3f}GeV')
        
        # Energy resolution from events file
        events_files = glob.glob(os.path.join(energy_dir, f'{detector}_em_events.parquet'))
        if events_files:
            events = pd.read_parquet(events_files[0])
            mean_edep = events['totalEdep'].mean()
            std_edep = events['totalEdep'].std()
            energy_res = std_edep / mean_edep if mean_edep > 0 else 0
            detector_results['energy_resolution'][f'{energy}GeV'] = energy_res * 100  # percent
        
        # Timing resolution from hits file
        hits_files = glob.glob(os.path.join(energy_dir, f'{detector}_em_hits_data.parquet'))
        if hits_files:
            hits = pd.read_parquet(hits_files[0])
            # Get first hit time per event
            first_hits = hits.groupby('eventID')['time'].min()
            
            # Fit gaussian to first hit times
            hist, bins = np.histogram(first_hits, bins=50)
            bin_centers = (bins[:-1] + bins[1:]) / 2
            
            try:
                # Initial guess: peak at mode, height from max count
                p0 = [hist.max(), bin_centers[hist.argmax()], first_hits.std()]
                popt, _ = curve_fit(gaussian, bin_centers, hist, p0=p0)
                timing_res = popt[2] * 1000  # ns to ps
                detector_results['timing_resolution'][f'{energy}GeV'] = timing_res
            except:
                detector_results['timing_resolution'][f'{energy}GeV'] = None
    
    results[detector_names[detector]] = detector_results

# Create comparison plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Timing resolution plot
for detector_name, detector_data in results.items():
    energies_plot = []
    timing_res = []
    for e in energies:
        if f'{e}GeV' in detector_data['timing_resolution'] and detector_data['timing_resolution'][f'{e}GeV'] is not None:
            energies_plot.append(e)
            timing_res.append(detector_data['timing_resolution'][f'{e}GeV'])
    if energies_plot:
        ax1.plot(energies_plot, timing_res, 'o-', label=detector_name, markersize=8)

ax1.axhspan(10, 30, alpha=0.2, color='green', label='Target range')
ax1.set_xlabel('Beam Energy (GeV)')
ax1.set_ylabel('Timing Resolution (ps)')
ax1.set_title('Timing Resolution Comparison')
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.set_xscale('log')

# Energy resolution plot
for detector_name, detector_data in results.items():
    energies_plot = []
    energy_res = []
    for e in energies:
        if f'{e}GeV' in detector_data['energy_resolution']:
            energies_plot.append(e)
            energy_res.append(detector_data['energy_resolution'][f'{e}GeV'])
    if energies_plot:
        ax2.plot(energies_plot, energy_res, 'o-', label=detector_name, markersize=8)

ax2.set_xlabel('Beam Energy (GeV)')
ax2.set_ylabel('Energy Resolution (%)')
ax2.set_title('Energy Resolution Comparison')
ax2.legend()
ax2.grid(True, alpha=0.3)
ax2.set_xscale('log')

plt.tight_layout()
plot_path = os.path.join(base_dir, 'detector_comparison.png')
plt.savefig(plot_path, dpi=150)
plt.close()

# Determine best detector
best_detector = None
best_score = float('inf')

for detector_name, detector_data in results.items():
    # Check if timing is in target range and has good energy resolution
    timing_vals = [v for v in detector_data['timing_resolution'].values() if v is not None]
    energy_vals = list(detector_data['energy_resolution'].values())
    
    if timing_vals:
        avg_timing = np.mean(timing_vals)
        avg_energy = np.mean(energy_vals)
        
        # Score based on timing in target range and energy resolution
        timing_penalty = 0 if 10 <= avg_timing <= 30 else min(abs(avg_timing - 10), abs(avg_timing - 30))
        score = timing_penalty + avg_energy  # Lower is better
        
        if score < best_score:
            best_score = score
            best_detector = detector_name

results['best_detector'] = best_detector
results['plot'] = plot_path
results['summary'] = {
    'best_for_timing': best_detector,
    'meets_timing_target': any(10 <= v <= 30 for d in results.values() if isinstance(d, dict) for v in d.get('timing_resolution', {}).values() if v is not None)
}

print(json.dumps(results))