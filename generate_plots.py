"""Generate publication-quality plots for GRACE Paper 2."""

import matplotlib.pyplot as plt
import matplotlib
import numpy as np

matplotlib.rcParams.update({
    'font.size': 11,
    'font.family': 'serif',
    'axes.labelsize': 13,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 9,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'axes.linewidth': 0.8,
})

OUT = "paper_figures"
C_MONO = "#A0522D"
C_CELL = "#2980B9"
C_CELL_DARK = "#1B4F72"
C_FAIL = "#CB4335"
C_GRAY = "#999999"
C_ORANGE = "#E67E22"


def fig1_token_comparison():
    fig, ax = plt.subplots(figsize=(5.5, 4))
    configs = ["Monolithic\n(Paper 1)", "Cellular v27\n(1K events)", "Cellular Final\n(10K events)"]
    vals = [750, 362, 488]
    colors = [C_MONO, C_CELL, C_CELL_DARK]
    bars = ax.bar(configs, vals, color=colors, width=0.5, edgecolor="white", linewidth=1.2)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 15,
                f"{val}K", ha='center', va='bottom', fontsize=12, fontweight='bold')
    ax.set_ylabel("Tokens per Benchmark (thousands)")
    ax.set_ylim(0, 870)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='x', length=0)
    plt.tight_layout()
    plt.savefig(f"{OUT}/fig1_token_comparison.png")
    plt.savefig(f"{OUT}/fig1_token_comparison.pdf")
    plt.close()
    print("Saved fig1_token_comparison")


def fig2_pass_rate_progression():
    fig, ax = plt.subplots(figsize=(7, 4.5))
    versions = ["Paper 1\nMonolithic", "Cellular\nBaseline", "Cellular\nPre-fix (v24)",
                "Cellular +\nQuality Eng.", "Cellular\n10K Focused"]
    pass_rates = [100, 56, 23, 62, 100]
    labels = ["4/4", "7/13", "3/13", "8/13", "2/2"]
    colors = [C_MONO, C_GRAY, C_FAIL, C_CELL, C_CELL_DARK]
    bars = ax.bar(versions, pass_rates, color=colors, width=0.6, edgecolor="white", linewidth=1.2)
    for bar, lbl in zip(bars, labels):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
                lbl, ha='center', va='bottom', fontsize=11, fontweight='bold')
    ax.set_ylabel("Pass Rate (%)")
    ax.set_ylim(0, 115)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='x', length=0)
    plt.tight_layout()
    plt.savefig(f"{OUT}/fig2_pass_rate_progression.png")
    plt.savefig(f"{OUT}/fig2_pass_rate_progression.pdf")
    plt.close()
    print("Saved fig2_pass_rate_progression")


def fig3_cost_per_valid():
    fig, ax = plt.subplots(figsize=(5.5, 4.2))
    configs = ["Monolithic\nSonnet", "Hybrid\nOpus+Sonnet", "Cellular\nBaseline",
               "Cellular +\nQuality Eng."]
    vals = [5.85, 10.28, 5.29, 4.63]
    colors = [C_MONO, C_FAIL, C_GRAY, C_CELL]
    bars = ax.bar(configs, vals, color=colors, width=0.5, edgecolor="white", linewidth=1.2)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                f"${val:.2f}", ha='center', va='bottom', fontsize=11, fontweight='bold')
    ax.set_ylabel("Cost per Valid Benchmark ($)")
    ax.set_ylim(0, 12.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='x', length=0)
    plt.tight_layout()
    plt.savefig(f"{OUT}/fig3_cost_per_valid_benchmark.png")
    plt.savefig(f"{OUT}/fig3_cost_per_valid_benchmark.pdf")
    plt.close()
    print("Saved fig3_cost_per_valid_benchmark")


def fig4_input_token_breakdown():
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    labels = ["ExtractParams\n(LLM)", "CalculateDerived\n(pure code)", "SelectTool\n(LLM)",
              "AssembleSchema\n(LLM)"]
    mono = [9000, 0, 0, 0]
    cell = [1329, 0, 84, 50]
    x = np.arange(len(labels))
    w = 0.32
    ax.bar(x - w/2, mono, w, label='Monolithic (single call)', color=C_MONO, edgecolor='white', linewidth=1)
    ax.bar(x + w/2, cell, w, label='Cellular (3 focused calls)', color=C_CELL, edgecolor='white', linewidth=1)
    ax.set_ylabel("Input Tokens per Step")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(0, 10500)
    ax.legend(loc='upper right', framealpha=0.95, fontsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig(f"{OUT}/fig4_input_token_breakdown.png")
    plt.savefig(f"{OUT}/fig4_input_token_breakdown.pdf")
    plt.close()
    print("Saved fig4_input_token_breakdown")


def fig5_emcal_physics_progression():
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    e_p1 = np.array([0.5, 1.0, 2.0, 5.0, 10.0])
    r_p1 = np.sqrt((1.62 / np.sqrt(e_p1))**2 + 0.87**2)
    e_cell = np.array([0.5, 1.0, 2.0, 5.0, 10.0, 20.0])
    r_csi = np.sqrt((1.11 / np.sqrt(e_cell))**2 + 0.64**2)
    r_pbwo4 = np.sqrt((0.68 / np.sqrt(e_cell))**2 + 0.78**2)

    ax.plot(e_p1, r_p1, 's-', color=C_MONO, markersize=7, linewidth=1.8,
            label=r'Paper 1: PbWO$_4$ (1K)')
    ax.plot(e_cell, r_pbwo4, 'D-', color=C_ORANGE, markersize=5, linewidth=1.5,
            label=r'Cellular: PbWO$_4$ box (10K)')
    ax.plot(e_cell, r_csi, 'o-', color=C_CELL, markersize=6, linewidth=2,
            label=r'Cellular: CsI box (10K, R$^2$=0.96)')

    ax.set_xlabel("Beam Energy (GeV)")
    ax.set_ylabel(r"Energy Resolution $\sigma_E/E$ (%)")
    ax.set_xscale('log')
    ax.set_xlim(0.35, 25)
    ax.set_ylim(0, 3.2)
    ax.legend(loc='upper right', framealpha=0.95)
    ax.grid(True, alpha=0.15, linewidth=0.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig(f"{OUT}/fig5_emcal_resolution.png")
    plt.savefig(f"{OUT}/fig5_emcal_resolution.pdf")
    plt.close()
    print("Saved fig5_emcal_resolution")


def fig6_muon_physics():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4), sharey=True)
    energies = [5, 20, 50]

    # Before
    ax1.plot(energies, [0, 5.3, 5.4], 'o--', color=C_FAIL, markersize=8, linewidth=2, label='Iron')
    ax1.plot(energies, [100, 96.4, 95.1], 's--', color='#5DADE2', markersize=8, linewidth=2, label='Aluminum')
    ax1.set_xlabel("Beam Energy (GeV)")
    ax1.set_ylabel("Pion Stopping Probability (%)")
    ax1.set_title("Before (1K events)", fontsize=11)
    ax1.set_ylim(-5, 115)
    ax1.set_xticks(energies)
    ax1.legend(loc='center left', fontsize=9)
    ax1.grid(True, alpha=0.15, linewidth=0.5)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)

    # After
    ax2.plot(energies, [90.7, 89.9, 89.9], 'o-', color=C_CELL, markersize=8, linewidth=2, label='Iron')
    ax2.plot(energies, [25.9, 7.8, 1.4], 's-', color=C_ORANGE, markersize=8, linewidth=2, label='Aluminum')
    ax2.set_xlabel("Beam Energy (GeV)")
    ax2.set_title("After (10K events + quality eng.)", fontsize=11)
    ax2.set_xticks(energies)
    ax2.legend(loc='center right', fontsize=9)
    ax2.grid(True, alpha=0.15, linewidth=0.5)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)

    plt.tight_layout(w_pad=1.5)
    plt.savefig(f"{OUT}/fig6_muon_pion_rejection.png")
    plt.savefig(f"{OUT}/fig6_muon_pion_rejection.pdf")
    plt.close()
    print("Saved fig6_muon_pion_rejection")


def fig7_fix_impact():
    fig, ax = plt.subplots(figsize=(7.5, 4))
    fixes = [
        "Terminal-name whitelist",
        "Percent-key exclusion",
        "R\u00b2 severity \u2192 WARN",
        "Particle-prefix exclusion",
        "Containment-aware scaling",
        "Honest-fit handling + dedup",
        "Reference detector KG",
        "Crystal topology routing",
    ]
    impact = [2, 1, 2, 2, 1, 1, 1, 1]
    y = np.arange(len(fixes))
    colors = plt.cm.YlGnBu(np.linspace(0.25, 0.85, len(fixes)))
    ax.barh(y, impact, color=colors, edgecolor='white', linewidth=1, height=0.65)
    ax.set_yticks(y)
    ax.set_yticklabels(fixes, fontsize=9)
    ax.set_xlabel("Benchmarks Recovered", fontsize=12)
    ax.set_xlim(0, 3)
    ax.set_xticks([0, 1, 2])
    ax.invert_yaxis()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig(f"{OUT}/fig7_fix_impact.png")
    plt.savefig(f"{OUT}/fig7_fix_impact.pdf")
    plt.close()
    print("Saved fig7_fix_impact")


if __name__ == "__main__":
    fig1_token_comparison()
    fig2_pass_rate_progression()
    fig3_cost_per_valid()
    fig4_input_token_breakdown()
    fig5_emcal_physics_progression()
    fig6_muon_physics()
    fig7_fix_impact()
    print(f"\nAll figures saved to {OUT}/")
