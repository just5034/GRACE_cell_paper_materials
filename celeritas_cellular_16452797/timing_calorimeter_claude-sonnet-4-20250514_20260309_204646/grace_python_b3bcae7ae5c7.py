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
energies = sorted(glob.glob(os.path.join(base_dir, 'energy_*GeV')))

results = {
    'energy_resolution': {},
    'timing_resolution': {},
    'depth_radiation_lengths': 20.0  # 20 X₀ for LYSO, X₀=1.14cm
}

def gaussian(x, amp, mean, sigma):
    return amp * np.exp(-(x - mean)**2 / (2 * sigma**2))

fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

for i, edir in enumerate(energies):
    events_files = glob.glob(os.path.join(edir, 'lyso_calorimeter_em_events.parquet'))
    hits_files = glob.glob(os.path.join(edir, 'lyso_calorimeter_em_hits_data.parquet'))
    
    if not events_files or not hits_files:
        continue
        
    events_file = events_files[0]
    hits_file = hits_files[0]
    true_e = float(os.path.basename(edir).replace('energy_','').replace('GeV',''))
    
    # Energy resolution
    events = pd.read_parquet(events_file)
    mean_edep = events['totalEdep'].mean() / 1000.0  # MeV→GeV
    std_edep = events['totalEdep'].std() / 1000.0
    energy_resolution = std_edep / mean_edep if mean_edep > 0 else 0
    
    # Timing resolution from first hit times
    hits = pd.read_parquet(hits_file)
    first_hits = hits.groupby('eventID')['time'].min()
    
    # Remove outliers (>3σ)
    mean_time = first_hits.mean()
    std_time = first_hits.std()
    mask = np.abs(first_hits - mean_time) < 3 * std_time
    first_hits_clean = first_hits[mask]
    
    # Fit gaussian to get timing resolution
    hist, bins = np.histogram(first_hits_clean, bins=50)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    
    try:
        popt, _ = curve_fit(gaussian, bin_centers, hist, 
                           p0=[hist.max(), first_hits_clean.mean(), first_hits_clean.std()])
        timing_resolution_ns = abs(popt[2])
        timing_resolution_ps = timing_resolution_ns * 1000  # ns to ps
    except:
        timing_resolution_ps = first_hits_clean.std() * 1000
    
    results['energy_resolution'][f'{true_e}GeV'] = {
        'mean_edep_gev': mean_edep,
        'resolution': energy_resolution,
        'percent': energy_resolution * 100
    }
    
    results['timing_resolution'][f'{true_e}GeV'] = {
        'resolution_ps': timing_resolution_ps,
        'mean_first_hit_ns': first_hits_clean.mean(),
        'std_first_hit_ns': first_hits_clean.std()
    }
    
    # Plot first hit time distribution
    ax = axes[i*2]
    ax.hist(first_hits_clean, bins=50, alpha=0.7, density=True)
    if 'popt' in locals():
        x_fit = np.linspace(first_hits_clean.min(), first_hits_clean.max(), 100)
        ax.plot(x_fit, gaussian(x_fit, *popt)/np.sum(hist * (bins[1]-bins[0])), 'r-', lw=2)
    ax.set_xlabel('First Hit Time (ns)')
    ax.set_ylabel('Normalized Counts')
    ax.set_title(f'LYSO @ {true_e} GeV - σ_t = {timing_resolution_ps:.1f} ps')
    
    # Plot energy distribution
    ax = axes[i*2 + 1]
    ax.hist(events['totalEdep']/1000, bins=50, alpha=0.7)
    ax.axvline(mean_edep, color='r', linestyle='--', label=f'Mean = {mean_edep:.3f} GeV')
    ax.set_xlabel('Total Energy Deposited (GeV)')
    ax.set_ylabel('Events')
    ax.set_title(f'LYSO @ {true_e} GeV - σ_E/E = {energy_resolution*100:.1f}%')
    ax.legend()

plt.tight_layout()
plt.savefig(os.path.join(base_dir, 'lyso_timing_energy_analysis.png'), dpi=150)
plt.close()

results['plot'] = os.path.join(base_dir, 'lyso_timing_energy_analysis.png')

print(json.dumps(results))