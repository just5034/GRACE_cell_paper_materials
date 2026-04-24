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

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/crystal_ecal_claude-sonnet-4-20250514_20260309_204537'
energies = sorted(glob.glob(os.path.join(base_dir, 'energy_*GeV')))

results = {
    "material": "CsI",
    "energy_resolution": {"data_points": {}},
    "shower_containment": {"data_points": {}},
    "moliere_radius": {"data_points": {}}
}

for edir in energies:
    events_files = glob.glob(os.path.join(edir, 'csi_projective_tower_em_events.parquet'))
    hits_files = glob.glob(os.path.join(edir, 'csi_projective_tower_em_hits_data.parquet'))
    
    if not events_files or not hits_files:
        continue
        
    true_e = float(os.path.basename(edir).replace('energy_','').replace('GeV',''))
    
    # Energy resolution
    events = pd.read_parquet(events_files[0])
    mean_edep = events['totalEdep'].mean() / 1000.0  # MeV to GeV
    std_edep = events['totalEdep'].std() / 1000.0
    resolution = std_edep / mean_edep if mean_edep > 0 else 0
    
    results["energy_resolution"]["data_points"][str(true_e)] = {
        "mean_edep_gev": mean_edep,
        "std_edep_gev": std_edep,
        "resolution": resolution,
        "n_events": len(events)
    }
    
    # Shower containment
    containment = mean_edep / true_e if true_e > 0 else 0
    results["shower_containment"]["data_points"][str(true_e)] = {
        "containment_fraction": containment,
        "energy_loss_fraction": 1 - containment
    }
    
    # Moliere radius
    hits = pd.read_parquet(hits_files[0])
    hits['r'] = np.sqrt(hits['x']**2 + hits['y']**2)
    
    # Calculate energy-weighted radial profile
    r_bins = np.linspace(0, 100, 101)
    hist, edges = np.histogram(hits['r'], bins=r_bins, weights=hits['edep'])
    r_centers = 0.5 * (edges[:-1] + edges[1:])
    
    # Cumulative distribution
    cumsum = np.cumsum(hist)
    total_edep = cumsum[-1]
    if total_edep > 0:
        frac = cumsum / total_edep
        # Find 90% containment radius
        idx_90 = np.argmax(frac >= 0.90)
        r_90 = r_centers[idx_90] if idx_90 < len(r_centers) else r_centers[-1]
        
        # Estimate Moliere radius (contains ~90% of shower)
        moliere_radius = r_90
        
        results["moliere_radius"]["data_points"][str(true_e)] = {
            "moliere_radius_mm": moliere_radius,
            "r_90_mm": r_90
        }

# Fit energy resolution
if len(results["energy_resolution"]["data_points"]) > 0:
    energies_fit = []
    resolutions_fit = []
    for e_str, data in results["energy_resolution"]["data_points"].items():
        energies_fit.append(float(e_str))
        resolutions_fit.append(data["resolution"])
    
    energies_fit = np.array(energies_fit)
    resolutions_fit = np.array(resolutions_fit)
    
    def res_func(E, a, b, c):
        return np.sqrt((a/np.sqrt(E))**2 + b**2 + (c/E)**2)
    
    try:
        popt, _ = curve_fit(res_func, energies_fit, resolutions_fit, p0=[0.1, 0.01, 0.1])
        results["energy_resolution"]["fit_parameters"] = {
            "stochastic_term": float(popt[0]),
            "constant_term": float(popt[1]),
            "noise_term": float(popt[2])
        }
        results["energy_resolution"]["fit_formula"] = "sigma/E = sqrt((a/sqrt(E))^2 + b^2 + (c/E)^2)"
    except:
        pass

# Average shower containment
containments = [d["containment_fraction"] for d in results["shower_containment"]["data_points"].values()]
results["shower_containment"]["average_containment"] = float(np.mean(containments))

# Average Moliere radius
moliere_radii = [d["moliere_radius_mm"] for d in results["moliere_radius"]["data_points"].values()]
results["moliere_radius"]["average_mm"] = float(np.mean(moliere_radii))

# Create plots
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Energy resolution vs energy
ax = axes[0, 0]
energies_plot = sorted([float(e) for e in results["energy_resolution"]["data_points"].keys()])
resolutions_plot = [results["energy_resolution"]["data_points"][str(e)]["resolution"] for e in energies_plot]
ax.scatter(energies_plot, resolutions_plot, s=100, label='Data')
if "fit_parameters" in results["energy_resolution"]:
    e_fit = np.logspace(np.log10(0.5), np.log10(30), 100)
    res_fit = res_func(e_fit, *popt)
    ax.plot(e_fit, res_fit, 'r-', label='Fit')
ax.set_xlabel('Energy (GeV)')
ax.set_ylabel('Energy Resolution (σ/E)')
ax.set_xscale('log')
ax.set_title('CsI Energy Resolution')
ax.grid(True, alpha=0.3)
ax.legend()

# Shower containment vs energy
ax = axes[0, 1]
containments_plot = [results["shower_containment"]["data_points"][str(e)]["containment_fraction"] for e in energies_plot]
ax.scatter(energies_plot, containments_plot, s=100)
ax.set_xlabel('Energy (GeV)')
ax.set_ylabel('Containment Fraction')
ax.set_xscale('log')
ax.set_title('CsI Shower Containment')
ax.grid(True, alpha=0.3)

# Moliere radius vs energy
ax = axes[1, 0]
moliere_plot = [results["moliere_radius"]["data_points"][str(e)]["moliere_radius_mm"] for e in energies_plot]
ax.scatter(energies_plot, moliere_plot, s=100)
ax.set_xlabel('Energy (GeV)')
ax.set_ylabel('Molière Radius (mm)')
ax.set_xscale('log')
ax.set_title('CsI Molière Radius')
ax.grid(True, alpha=0.3)

# Summary text
ax = axes[1, 1]
ax.axis('off')
summary_text = f"CsI Performance Summary\n\n"
summary_text += f"Average Containment: {results['shower_containment']['average_containment']:.3f}\n"
summary_text += f"Average Molière Radius: {results['moliere_radius']['average_mm']:.1f} mm\n\n"
if "fit_parameters" in results["energy_resolution"]:
    summary_text += f"Energy Resolution Fit:\n"
    summary_text += f"Stochastic: {results['energy_resolution']['fit_parameters']['stochastic_term']:.3f}\n"
    summary_text += f"Constant: {results['energy_resolution']['fit_parameters']['constant_term']:.3f}\n"
    summary_text += f"Noise: {results['energy_resolution']['fit_parameters']['noise_term']:.3f}"
ax.text(0.1, 0.5, summary_text, transform=ax.transAxes, fontsize=12, verticalalignment='center')

plt.tight_layout()
plot_path = os.path.join(base_dir, 'csi_performance_analysis.png')
plt.savefig(plot_path, dpi=150)
plt.close()

results["plots"] = [plot_path]

print(json.dumps(results))