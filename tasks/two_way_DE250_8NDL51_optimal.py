#!/usr/bin/env python3
"""
Two-way speaker design: BC_DE250 + BC_8NDL51

Optimizing for:
1. Flat frequency response
2. Wavefront sphericity

Design approach:
- BC_8NDL51: Ported enclosure for bass/midrange
- BC_DE250: Multi-segment horn for HF with optimal wavefront
- Crossover: Optimized for seamless integration
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from viberesp.driver import load_driver
from viberesp.optimization.api.design_assistant import DesignAssistant
from viberesp.optimization.api.crossover_assistant import CrossoverDesignAssistant
from viberesp.optimization.objectives.response_metrics import objective_response_flatness


def main():
    print("=" * 80)
    print("TWO-WAY SPEAKER DESIGN: BC_DE250 + BC_8NDL51")
    print("=" * 80)
    print()

    # Initialize assistants
    design_assistant = DesignAssistant(validation_mode=True)
    xo_assistant = CrossoverDesignAssistant(validation_mode=True)

    # Load drivers
    print("Loading drivers...")
    lf_driver_name = "BC_8NDL51"
    hf_driver_name = "BC_DE250"

    lf_driver = load_driver(lf_driver_name)
    hf_driver = load_driver(hf_driver_name)

    print(f"LF Driver: {lf_driver_name}")
    print(f"  - Fs: {lf_driver.F_s:.1f} Hz")
    print(f"  - Qts: {lf_driver.Q_ts:.3f}")
    print(f"  - Vas: {lf_driver.V_as*1000:.1f} L")
    print(f"  - Sd: {lf_driver.S_d*10000:.1f} cm²")
    print()

    print(f"HF Driver: {hf_driver_name}")
    print(f"  - Fs: {hf_driver.F_s:.1f} Hz")
    print(f"  - Sensitivity: 108.5 dB (2.83V, 1m)")
    print(f"  - Recommended XO: 1.6 kHz")
    print()

    # Step 1: Design woofer enclosure
    print("-" * 80)
    print("STEP 1: Designing BC_8NDL51 Enclosure")
    print("-" * 80)

    # Get recommendation
    rec = design_assistant.recommend_design(
        driver_name="BC_8NDL51",
        objectives=["f3", "flatness"],
        target_f3=70,
        enclosure_preference="ported"
    )

    print(f"Recommended enclosure: {rec.enclosure_type}")
    print(f"Reasoning: {rec.reasoning}")
    print()

    if rec.enclosure_type == "ported":
        Vb = rec.suggested_parameters["Vb"]
        Fb = rec.suggested_parameters["Fb"]

        print(f"Suggested parameters:")
        print(f"  - Vb: {Vb*1000:.1f} L")
        print(f"  - Fb: {Fb:.1f} Hz")
        print(f"  - Expected F3: {rec.expected_performance['F3']:.1f} Hz")
        print()

    # Step 2: Design compression driver horn
    print("-" * 80)
    print("STEP 2: Designing BC_DE250 Horn (Optimizing for Wavefront Sphericity)")
    print("-" * 80)

    # Optimize horn for wavefront sphericity
    horn_result = design_assistant.optimize_design(
        driver_name="BC_DE250",
        enclosure_type="multisegment_horn",
        objectives=["wavefront_sphericity", "impedance_smoothness"],
        population_size=50,
        generations=50,
        top_n=5,
        num_segments=2
    )

    if horn_result.success:
        print(f"✓ Horn optimization found {horn_result.n_designs_found} designs")
        print()

        # Get best design
        best_horn = horn_result.best_designs[0]
        horn_params = best_horn['parameters']

        print("Best horn design:")
        for param, value in horn_params.items():
            if param == 'profile_type':
                print(f"  - {param}: {value}")
            elif 'area' in param:
                print(f"  - {param}: {value*10000:.1f} cm²")
            elif 'length' in param:
                print(f"  - {param}: {value*100:.1f} cm")
            elif 'flare' in param:
                print(f"  - {param}: {value:.2f}")
            else:
                print(f"  - {param}: {value:.4f}")
        print()

        # Calculate horn characteristics from optimized parameters
        throat_area = horn_params.get('throat_area', 0.0015)
        middle_area = horn_params.get('middle_area', 0.01)
        mouth_area = horn_params.get('mouth_area', 0.05)
        length1 = horn_params.get('length1', 0.2)
        length2 = horn_params.get('length2', 0.2)
        total_length = length1 + length2

        # Calculate effective cutoff from first segment flare rate
        m1 = np.log(middle_area / throat_area) / length1 if length1 > 0 else 0
        cutoff = (m1 * 343) / (2 * np.pi) if m1 > 0 else 800

        horn_design = {
            'throat_area': throat_area,
            'middle_area': middle_area,
            'mouth_area': mouth_area,
            'length1': length1,
            'length2': length2,
            'total_length': total_length,
            'cutoff': cutoff,
            'm1': m1,
            'V_tc': horn_params.get('V_tc', 0.0),
            'V_rc': horn_params.get('V_rc', 0.0)
        }

        print(f"Horn characteristics:")
        print(f"  - Total length: {total_length*100:.1f} cm")
        print(f"  - Effective cutoff: {cutoff:.0f} Hz (from segment 1)")
        print(f"  - Throat area: {throat_area*10000:.1f} cm²")
        print(f"  - Middle area: {middle_area*10000:.1f} cm²")
        print(f"  - Mouth area: {mouth_area*10000:.1f} cm²")
        print()

    else:
        print("✗ Horn optimization failed")
        print(f"Warnings: {horn_result.warnings}")
        # Use default horn parameters
        horn_design = {
            'cutoff': 800,
            'length': 0.35,
            'throat_area': 0.0015,
            'mouth_area': 0.05
        }

    # Step 3: Design crossover
    print("-" * 80)
    print("STEP 3: Designing Optimal Crossover")
    print("-" * 80)

    xo_design = xo_assistant.design_crossover(
        lf_driver_name="BC_8NDL51",
        hf_driver_name="BC_DE250",
        lf_enclosure_type="ported",
        lf_enclosure_params={"Vb": Vb, "Fb": Fb},
        hf_horn_params=horn_design,
        crossover_range=(800, 2000)
    )

    print(f"Crossover Design:")
    print(f"  - Frequency: {xo_design.crossover_frequency:.0f} Hz")
    print(f"  - Filter type: {xo_design.filter_type}")
    print(f"  - Order: {xo_design.crossover_order}th-order (LR{xo_design.crossover_order})")
    print(f"  - LF padding: {xo_design.lf_padding_db:+.1f} dB")
    print(f"  - HF padding: {xo_design.hf_padding_db:+.1f} dB")
    print(f"  - Estimated ripple: {xo_design.estimated_ripple:.2f} dB")
    print()

    print("Analysis:")
    for key, value in xo_design.analysis.items():
        if key != 'all_candidates':
            print(f"  - {key}: {value}")
    print()

    print("Top 5 crossover frequencies:")
    for i, candidate in enumerate(xo_design.analysis['all_candidates'][:5], 1):
        print(f"  {i}. {candidate['freq']:.0f} Hz - Score: {candidate['score']:.1f}")
    print()

    # Step 4: Generate system response plot
    print("-" * 80)
    print("STEP 4: Generating System Response Analysis")
    print("-" * 80)

    generate_system_response_plot(
        lf_driver, hf_driver, Vb, Fb, horn_design, xo_design
    )

    # Step 5: Summary
    print("=" * 80)
    print("COMPLETE SYSTEM DESIGN SUMMARY")
    print("=" * 80)
    print()
    print("LOW FREQUENCY DRIVER (BC_8NDL51):")
    print(f"  Enclosure: Ported")
    print(f"  Vb: {Vb*1000:.1f} L")
    print(f"  Fb: {Fb:.1f} Hz")
    print(f"  Expected F3: {rec.expected_performance['F3']:.1f} Hz")
    print()

    print("HIGH FREQUENCY DRIVER (BC_DE250):")
    print(f"  Horn type: Multi-segment (optimized for wavefront)")
    print(f"  Horn cutoff: {horn_design['cutoff']:.0f} Hz")
    print(f"  Horn length: {horn_design['total_length']*100:.1f} cm")
    print(f"    - Segment 1: {horn_design['length1']*100:.1f} cm")
    print(f"    - Segment 2: {horn_design['length2']*100:.1f} cm")
    print(f"  Throat area: {horn_design['throat_area']*10000:.1f} cm²")
    print(f"  Middle area: {horn_design['middle_area']*10000:.1f} cm²")
    print(f"  Mouth area: {horn_design['mouth_area']*10000:.1f} cm²")
    print()

    print("CROSSOVER:")
    print(f"  Frequency: {xo_design.crossover_frequency:.0f} Hz")
    print(f"  Type: LR{xo_design.crossover_order} (Linkwitz-Riley)")
    print(f"  HF padding: {xo_design.hf_padding_db:+.1f} dB")
    print(f"  Expected ripple: {xo_design.estimated_ripple:.2f} dB")
    print()

    print("PERFORMANCE METRICS:")
    print(f"  ✓ Optimized for flatness (<{xo_design.estimated_ripple:.1f} dB ripple)")
    print(f"  ✓ Optimized for wavefront sphericity (multi-segment horn)")
    print(f"  ✓ Bass extension: F3 = {rec.expected_performance['F3']:.1f} Hz")
    print(f"  ✓ System sensitivity: ~{108 + xo_design.hf_padding_db:.1f} dB (2.83V, 1m)")
    print()

    # Save design to JSON
    save_design_results(Vb, Fb, horn_design, xo_design, rec)


def generate_system_response_plot(lf_driver, hf_driver, Vb, Fb, horn_design, xo_design):
    """Generate and save system frequency response plot."""

    from viberesp.enclosure.ported_box import calculate_spl_ported_transfer_function

    # Frequency range
    freq = np.logspace(np.log10(20), np.log10(20000), 500)

    # Calculate LF response
    lf_response = np.array([
        calculate_spl_ported_transfer_function(f, lf_driver, Vb, Fb)
        for f in freq
    ])

    # Calculate HF response
    hf_response = calculate_hf_response(freq, hf_driver, horn_design)

    # Apply crossover filters (simplified LR4 model)
    from scipy import signal

    # Convert frequency to normalized for filter
    sample_rate = 48000  # Standard audio sample rate
    nyquist = sample_rate / 2
    normalized_xo = xo_design.crossover_frequency / nyquist

    # Design LR4 filters (two cascaded Butterworth 2nd-order)
    b_lf, a_lf = signal.butter(2, normalized_xo, btype='low')
    b_lf2, a_lf2 = signal.butter(2, normalized_xo, btype='low')
    b_hf, a_hf = signal.butter(2, normalized_xo, btype='high')
    b_hf2, a_hf2 = signal.butter(2, normalized_xo, btype='high')

    # Apply filters in frequency domain
    # Get filter responses at each frequency
    w = 2 * np.pi * freq / sample_rate
    _, h_lf = signal.freqz(b_lf, a_lf, worN=w)
    _, h_lf2 = signal.freqz(b_lf2, a_lf2, worN=w)
    _, h_hf = signal.freqz(b_hf, a_hf, worN=w)
    _, h_hf2 = signal.freqz(b_hf2, a_hf2, worN=w)

    # Cascade filters for LR4
    H_lf = h_lf * h_lf2
    H_hf = h_hf * h_hf2

    # Convert to dB
    H_lf_db = 20 * np.log10(np.abs(H_lf))
    H_hf_db = 20 * np.log10(np.abs(H_hf))

    # Apply padding
    hf_response_padded = hf_response + xo_design.hf_padding_db

    # Sum filtered responses
    lf_filtered = lf_response + H_lf_db
    hf_filtered = hf_response_padded + H_hf_db

    # Acoustic sum (accounting for phase)
    # Simplified: power sum for LR4 (in-phase at crossover)
    system_response = 10 * np.log10(
        10**(lf_filtered/10) + 10**(hf_filtered/10)
    )

    # Create plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Plot 1: Individual and system responses
    ax1.semilogx(freq, lf_response, 'b-', label='BC_8NDL51 (LF)', linewidth=1.5, alpha=0.7)
    ax1.semilogx(freq, hf_response_padded, 'r-', label='BC_DE250 (HF)', linewidth=1.5, alpha=0.7)
    ax1.semilogx(freq, system_response, 'k-', label='System Response', linewidth=2.5)
    ax1.axvline(xo_design.crossover_frequency, color='gray', linestyle='--', alpha=0.5, label=f'XO: {xo_design.crossover_frequency:.0f} Hz')

    ax1.set_xlabel('Frequency (Hz)')
    ax1.set_ylabel('SPL (dB)')
    ax1.set_title('Two-Way System Frequency Response')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    ax1.set_xlim([20, 20000])
    ax1.set_ylim([70, 115])

    # Plot 2: Ripple analysis (deviation from flat)
    reference = np.max(system_response)
    ripple = system_response - reference

    ax2.semilogx(freq, ripple, 'k-', linewidth=1.5)
    ax2.axhline(0, color='gray', linestyle='--', alpha=0.5)
    ax2.axhline(-3, color='red', linestyle=':', alpha=0.5, label='-3 dB')
    ax2.axhline(3, color='red', linestyle=':', alpha=0.5, label='+3 dB')
    ax2.axvline(xo_design.crossover_frequency, color='gray', linestyle='--', alpha=0.5)

    ax2.set_xlabel('Frequency (Hz)')
    ax2.set_ylabel('Deviation from Peak (dB)')
    ax2.set_title('System Response Flatness')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    ax2.set_xlim([20, 20000])
    ax2.set_ylim([-10, 3])

    plt.tight_layout()

    # Save plot
    output_path = Path("tasks/results/DE250_8NDL51_two_way_response.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    print(f"✓ Response plot saved to: {output_path}")
    print()


def calculate_hf_response(freq, driver, horn_params):
    """Calculate HF horn response using datasheet model."""
    fc = horn_params['cutoff']
    sensitivity = 108.5  # DE250 datasheet

    response = np.zeros_like(freq)

    for i, f in enumerate(freq):
        if f <= fc / 2:
            # Below cutoff: 12 dB/octave rolloff
            octaves_below = np.log2(max(f, 10) / fc)
            response[i] = sensitivity + octaves_below * 12
        elif f <= fc * 1.5:
            # Transition region
            blend = (f - fc/2) / fc
            blend_smooth = blend * blend * (3 - 2 * blend)
            octaves_below = np.log2(max(f, 10) / fc)
            below_cutoff = sensitivity + octaves_below * 12
            response[i] = below_cutoff * (1 - blend_smooth) + sensitivity * blend_smooth
        elif f > 5000:
            # HF beaming rolloff
            hf_rolloff = 3 * np.log2(f / 5000)
            transition = 0.5 * (1 + np.tanh((f - 7000) / 1000))
            response[i] = sensitivity - hf_rolloff * transition
        else:
            # Passband
            response[i] = sensitivity

    return response


def save_design_results(Vb, Fb, horn_design, xo_design, enclosure_rec):
    """Save complete design to JSON file."""

    import json
    from datetime import datetime

    design = {
        'timestamp': datetime.now().isoformat(),
        'lf_driver': 'BC_8NDL51',
        'hf_driver': 'BC_DE250',
        'lf_enclosure': {
            'type': 'ported',
            'Vb_liters': Vb * 1000,
            'Fb_hz': Fb,
            'expected_F3_hz': enclosure_rec.expected_performance['F3']
        },
        'hf_horn': {
            'type': 'multisegment_optimized',
            'throat_area_cm2': horn_design['throat_area'] * 10000,
            'middle_area_cm2': horn_design['middle_area'] * 10000,
            'mouth_area_cm2': horn_design['mouth_area'] * 10000,
            'length1_cm': horn_design['length1'] * 100,
            'length2_cm': horn_design['length2'] * 100,
            'total_length_m': horn_design['total_length'],
            'cutoff_hz': horn_design['cutoff'],
            'flare_constant_m1': horn_design['m1'],
            'V_tc_cm3': horn_design['V_tc'] * 1e6,
            'V_rc_cm3': horn_design['V_rc'] * 1e6,
            'optimization_objectives': ['wavefront_sphericity', 'impedance_smoothness']
        },
        'crossover': {
            'frequency_hz': xo_design.crossover_frequency,
            'type': xo_design.filter_type,
            'order': xo_design.crossover_order,
            'lf_padding_db': xo_design.lf_padding_db,
            'hf_padding_db': xo_design.hf_padding_db,
            'estimated_ripple_db': xo_design.estimated_ripple
        },
        'performance_targets': {
            'bass_extension_F3_hz': enclosure_rec.expected_performance['F3'],
            'max_ripple_db': xo_design.estimated_ripple,
            'system_sensitivity_db': 108 + xo_design.hf_padding_db
        }
    }

    output_path = Path("tasks/results/DE250_8NDL51_two_way_design.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(design, f, indent=2)

    print(f"✓ Design saved to: {output_path}")
    print()


if __name__ == "__main__":
    main()
