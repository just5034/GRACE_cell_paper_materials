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

base_dir = '/work/nvme/bgde/jhill5/benchmarks/celeritas_cellular_16452797/geometry_comparison_claude-sonnet-4-20250514_20260309_204648'
energies = [1.0, 5.0, 20.0]
geometries = ['box_calorimeter_2', 'projective_tower_calorimeter', 'accordion_calorimeter']

results = {
    'energy_resolution': {},
    'response_uniformity': {},
    'linearity': {},
    'optimal_geometry': None,
    'summary': {}
}

# Analyze each geometry
for geom in geometries:
    geom_results = {
        'resolution': {},
        'mean_response': {},
        'uniformity': {}
    }
    
    for energy in energies:
        energy_dir = os.path.join(base_dir, f'energy_{energy:.3f}GeV')
        
        # Find events file
        events_files = glob.glob(os.path.join(energy_dir, f'{geom}_em_events.parquet'))
        if not events_files:
            continue
            
        # Load events data
        events = pd.read_parquet(events_files[0])
        
        # Calculate energy resolution
        mean_edep = events['totalEdep'].mean()
        std_edep = events['totalEdep'].std()
        resolution = std_edep / mean_edep if mean_edep > 0 else 0
        
        geom_results['resolution'][f'{energy}GeV'] = resolution
        geom_results['mean_response'][f'{energy}GeV'] = mean_edep / 1000.0  # MeV to GeV
        
        # Load hits data for uniformity analysis
        hits_files = glob.glob(os.path.join(energy_dir, f'{geom}_em_hits_data.parquet'))
        if hits_files:
            hits = pd.read_parquet(hits_files[0])
            
            # Calculate response uniformity (RMS of energy deposition in different regions)
            # Divide detector into regions and calculate response variation
            n_bins = 5
            x_bins = np.linspace(hits['x'].min(), hits['x'].max(), n_bins+1)
            y_bins = np.linspace(hits['y'].min(), hits['y'].max(), n_bins+1)
            
            region_responses = []
            for i in range(n_bins):
                for j in range(n_bins):
                    mask = ((hits['x'] >= x_bins[i]) & (hits['x'] < x_bins[i+1]) & 
                           (hits['y'] >= y_bins[j]) & (hits['y'] < y_bins[j+1]))
                    if mask.sum() > 0:
                        region_edep = hits[mask].groupby('eventID')['edep'].sum().mean()
                        region_responses.append(region_edep)
            
            if region_responses:
                uniformity = np.std(region_responses) / np.mean(region_responses)
                geom_results['uniformity'][f'{energy}GeV'] = uniformity
    
    results['energy_resolution'][geom] = geom_results['resolution']
    results['response_uniformity'][geom] = geom_results['uniformity']
    results['linearity'][geom] = geom_results['mean_response']

# Calculate linearity metric (deviation from linear response)
for geom in geometries:
    if geom in results['linearity'] and len(results['linearity'][geom]) >= 2:
        responses = []
        true_energies = []
        for e_str, resp in results['linearity'][geom].items():
            true_e = float(e_str.replace('GeV', ''))
            responses.append(resp)
            true_energies.append(true_e)
        
        if len(responses) >= 2:
            # Fit linear response
            coeffs = np.polyfit(true_energies, responses, 1)
            fitted = np.poly1d(coeffs)(true_energies)
            linearity_metric = np.sqrt(np.mean((np.array(responses) - fitted)**2)) / np.mean(responses)
            results['linearity'][geom] = {'metric': linearity_metric, 'slope': coeffs[0], 'intercept': coeffs[1]}

# Determine optimal geometry
scores = {}
for geom in geometries:
    # Lower is better for all metrics
    res_score = np.mean(list(results['energy_resolution'].get(geom, {}).values())) if geom in results['energy_resolution'] else 1.0
    unif_score = np.mean(list(results['response_uniformity'].get(geom, {}).values())) if geom in results['response_uniformity'] else 1.0
    lin_score = results['linearity'].get(geom, {}).get('metric', 1.0) if isinstance(results['linearity'].get(geom), dict) else 1.0
    
    # Combined score (equal weighting)
    scores[geom] = res_score + unif_score + lin_score

if scores:
    optimal = min(scores, key=scores.get)
    results['optimal_geometry'] = optimal
    results['scores'] = scores

# Create comparison plot
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

# Energy resolution vs energy
ax1.set_xlabel('Beam Energy (GeV)')
ax1.set_ylabel('Energy Resolution (σ/E)')
ax1.set_title('Energy Resolution Comparison')
ax1.grid(True, alpha=0.3)

for geom in geometries:
    if geom in results['energy_resolution']:
        x_vals = []
        y_vals = []
        for e_str, res in results['energy_resolution'][geom].items():
            x_vals.append(float(e_str.replace('GeV', '')))
            y_vals.append(res)
        if x_vals:
            ax1.plot(x_vals, y_vals, 'o-', label=geom.replace('_calorimeter', '').replace('_', ' '))

ax1.legend()
ax1.set_xscale('log')

# Response uniformity
ax2.set_xlabel('Beam Energy (GeV)')
ax2.set_ylabel('Response Non-uniformity')
ax2.set_title('Response Uniformity Comparison')
ax2.grid(True, alpha=0.3)

for geom in geometries:
    if geom in results['response_uniformity']:
        x_vals = []
        y_vals = []
        for e_str, unif in results['response_uniformity'][geom].items():
            x_vals.append(float(e_str.replace('GeV', '')))
            y_vals.append(unif)
        if x_vals:
            ax2.plot(x_vals, y_vals, 'o-', label=geom.replace('_calorimeter', '').replace('_', ' '))

ax2.legend()
ax2.set_xscale('log')

# Overall scores
if scores:
    geom_names = [g.replace('_calorimeter', '').replace('_', ' ') for g in scores.keys()]
    score_vals = list(scores.values())
    ax3.bar(geom_names, score_vals)
    ax3.set_ylabel('Combined Score (lower is better)')
    ax3.set_title('Overall Performance Score')
    ax3.grid(True, alpha=0.3, axis='y')

# Summary table
ax4.axis('off')
summary_text = f"Optimal Geometry: {results['optimal_geometry']}\n\n"
summary_text += "Average Energy Resolution (σ/E):\n"
for geom in geometries:
    if geom in results['energy_resolution'] and results['energy_resolution'][geom]:
        avg_res = np.mean(list(results['energy_resolution'][geom].values()))
        summary_text += f"  {geom.replace('_calorimeter', '')}: {avg_res:.3f}\n"

ax4.text(0.1, 0.9, summary_text, transform=ax4.transAxes, fontsize=10, 
         verticalalignment='top', fontfamily='monospace')

plt.tight_layout()
plt.savefig('geometry_comparison.png', dpi=150)

results['plot'] = 'geometry_comparison.png'

# Add summary statistics
for geom in geometries:
    summary = {}
    if geom in results['energy_resolution'] and results['energy_resolution'][geom]:
        summary['avg_resolution'] = np.mean(list(results['energy_resolution'][geom].values()))
    if geom in results['response_uniformity'] and results['response_uniformity'][geom]:
        summary['avg_uniformity'] = np.mean(list(results['response_uniformity'][geom].values()))
    if summary:
        results['summary'][geom] = summary

print(json.dumps(results))