#!/usr/bin/env python3
"""
Validate Viberesp against synthetic Hornresp test cases.

This script runs validation on all 4 synthetic test cases and tracks
the improvements from Phase 1 enhancements.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import numpy as np
import matplotlib.pyplot as plt
from viberesp.core.models import ThieleSmallParameters, EnclosureParameters
from viberesp.enclosures.horns import ExponentialHorn, FrontLoadedHorn
from viberesp.validation import parse_hornresp_output, compare_responses
from viberesp.validation.metrics import calculate_validation_metrics


def create_idealized_driver() -> ThieleSmallParameters:
    """Create idealized 18" driver for cases 1-3."""
    return ThieleSmallParameters(
        fs=30.0,
        qes=0.25,
        qms=5.0,
        sd=0.121,
        re=6.0,
        bl=35.0,
        mms=300.0,
        cms=8.24e-5,
        rms=15.0,
        le=3.5,
        xmax=15.0,
        pe=100.0,
        vas=200.0,
        manufacturer="Idealized",
        model_number="18inch_Test",
    )


def create_bc18ds115_driver() -> ThieleSmallParameters:
    """Create B&C 18DS115 driver for case 4."""
    return ThieleSmallParameters(
        fs=32.0,
        qes=0.38,
        qms=6.52,
        sd=0.121,
        re=5.0,
        bl=39.0,
        mms=330.0,
        cms=8.24e-5,
        rms=14.72,
        le=3.85,
        xmax=16.5,
        pe=500.0,
        vas=158.0,
        manufacturer="B&C",
        model_number="18DS115",
    )


def validate_case1():
    """Case 1: Straight Exponential Horn (No Chambers)"""
    print("\n" + "="*70)
    print("CASE 1: Straight Exponential Horn - No Chambers")
    print("="*70)

    # Load Hornresp simulation
    sim_path = Path(__file__).parent / "hornresp" / "synthetic" / "case1_sim.txt"
    hornresp_data = parse_hornresp_output(sim_path)

    # Create Viberesp simulation
    driver = create_idealized_driver()
    params = EnclosureParameters(
        enclosure_type='exponential_horn',
        vb=100,
        throat_area_cm2=600,
        mouth_area_cm2=4800,
        horn_length_cm=200,
        cutoff_frequency=35,
        rear_chamber_volume=0,
        front_chamber_volume=0,
        front_chamber_modes=3,
        radiation_model='beranek',
    )

    enclosure = ExponentialHorn(driver, params)
    frequencies = np.logspace(1, 3, 600)
    spl_db, phase_degrees = enclosure.calculate_frequency_response(frequencies)

    # Compare
    comparison = compare_responses(
        viberesp_freq=frequencies,
        viberesp_spl=spl_db,
        viberesp_phase=phase_degrees,
        hornresp_freq=hornresp_data.frequencies,
        hornresp_spl=hornresp_data.spl,
        hornresp_phase=hornresp_data.phase if hasattr(hornresp_data, 'phase') else None,
    )

    # Calculate metrics
    metrics = calculate_validation_metrics(comparison)

    # Print results
    print(f"RMSE: {metrics.rmse:.2f} dB (target: < 3 dB)")
    print(f"MAE: {metrics.mae:.2f} dB")
    print(f"F3 Error: {metrics.f3_error:.1f} Hz (Vib: {metrics.f3_viberesp:.1f}, HR: {metrics.f3_hornresp:.1f})")
    print(f"Max Error: {metrics.max_error:.2f} dB @ {metrics.max_error_freq:.1f} Hz")
    print(f"Correlation: {metrics.correlation:.3f} (target: > 0.98)")
    print(f"Bass RMSE (20-200 Hz): {metrics.bass_rmse:.2f} dB")

    return metrics


def validate_case2():
    """Case 2: Horn + Rear Chamber"""
    print("\n" + "="*70)
    print("CASE 2: Horn + Rear Chamber (100L)")
    print("="*70)

    # Load Hornresp simulation
    sim_path = Path(__file__).parent / "hornresp" / "synthetic" / "case2_sim.txt"
    hornresp_data = parse_hornresp_output(sim_path)

    # Create Viberesp simulation
    driver = create_idealized_driver()
    params = EnclosureParameters(
        enclosure_type='exponential_horn',
        vb=100,
        throat_area_cm2=600,
        mouth_area_cm2=4800,
        horn_length_cm=200,
        cutoff_frequency=35,
        rear_chamber_volume=100,
        front_chamber_volume=0,
        front_chamber_modes=3,
        radiation_model='beranek',
    )

    enclosure = ExponentialHorn(driver, params)
    frequencies = np.logspace(1, 3, 600)
    spl_db, phase_degrees = enclosure.calculate_frequency_response(frequencies)

    # Compare
    comparison = compare_responses(
        viberesp_freq=frequencies,
        viberesp_spl=spl_db,
        viberesp_phase=phase_degrees,
        hornresp_freq=hornresp_data.frequencies,
        hornresp_spl=hornresp_data.spl,
        hornresp_phase=hornresp_data.phase if hasattr(hornresp_data, 'phase') else None,
    )

    # Calculate metrics
    metrics = calculate_validation_metrics(comparison)

    # Print results
    print(f"RMSE: {metrics.rmse:.2f} dB (target: < 3 dB)")
    print(f"MAE: {metrics.mae:.2f} dB")
    print(f"F3 Error: {metrics.f3_error:.1f} Hz (Vib: {metrics.f3_viberesp:.1f}, HR: {metrics.f3_hornresp:.1f})")
    print(f"Max Error: {metrics.max_error:.2f} dB @ {metrics.max_error_freq:.1f} Hz")
    print(f"Correlation: {metrics.correlation:.3f} (target: > 0.98)")
    print(f"Bass RMSE (20-200 Hz): {metrics.bass_rmse:.2f} dB")

    return metrics


def validate_case3():
    """Case 3: Horn + Front Chamber"""
    print("\n" + "="*70)
    print("CASE 3: Horn + Front Chamber (6L)")
    print("="*70)

    # Load Hornresp simulation
    sim_path = Path(__file__).parent / "hornresp" / "synthetic" / "case3_sim.txt"
    hornresp_data = parse_hornresp_output(sim_path)

    # Create Viberesp simulation
    # Note: FrontLoadedHorn requires rear_chamber_volume, using minimal value
    driver = create_idealized_driver()
    params = EnclosureParameters(
        enclosure_type='front_loaded_horn',
        vb=100,
        throat_area_cm2=600,
        mouth_area_cm2=4800,
        horn_length_cm=200,
        cutoff_frequency=35,
        rear_chamber_volume=1.0,  # Minimal to satisfy constraint (Hornresp: 0.00)
        front_chamber_volume=6,
        front_chamber_area_cm2=600,
        rear_chamber_length_cm=15,
        front_chamber_modes=3,
        radiation_model='beranek',
    )

    enclosure = FrontLoadedHorn(driver, params)
    frequencies = np.logspace(1, 3, 600)
    spl_db, phase_degrees = enclosure.calculate_frequency_response(frequencies)

    # Compare
    comparison = compare_responses(
        viberesp_freq=frequencies,
        viberesp_spl=spl_db,
        viberesp_phase=phase_degrees,
        hornresp_freq=hornresp_data.frequencies,
        hornresp_spl=hornresp_data.spl,
        hornresp_phase=hornresp_data.phase if hasattr(hornresp_data, 'phase') else None,
    )

    # Calculate metrics
    metrics = calculate_validation_metrics(comparison)

    # Print results
    print(f"RMSE: {metrics.rmse:.2f} dB (target: < 3 dB)")
    print(f"MAE: {metrics.mae:.2f} dB")
    print(f"F3 Error: {metrics.f3_error:.1f} Hz (Vib: {metrics.f3_viberesp:.1f}, HR: {metrics.f3_hornresp:.1f})")
    print(f"Max Error: {metrics.max_error:.2f} dB @ {metrics.max_error_freq:.1f} Hz")
    print(f"Correlation: {metrics.correlation:.3f} (target: > 0.98)")
    print(f"Bass RMSE (20-200 Hz): {metrics.bass_rmse:.2f} dB")

    return metrics


def validate_case4():
    """Case 4: Complete System (F118 Style)"""
    print("\n" + "="*70)
    print("CASE 4: Complete System - B&C 18DS115 F118 Style")
    print("="*70)

    # Load Hornresp simulation
    sim_path = Path(__file__).parent / "hornresp" / "synthetic" / "case4_sim.txt"
    hornresp_data = parse_hornresp_output(sim_path)

    # Create Viberesp simulation
    driver = create_bc18ds115_driver()
    params = EnclosureParameters(
        enclosure_type='front_loaded_horn',
        vb=100,
        throat_area_cm2=600,
        mouth_area_cm2=4800,
        horn_length_cm=200,
        cutoff_frequency=35,
        rear_chamber_volume=100,
        front_chamber_volume=6,
        front_chamber_area_cm2=600,
        rear_chamber_length_cm=15,
        front_chamber_modes=3,
        radiation_model='beranek',
    )

    enclosure = FrontLoadedHorn(driver, params)
    frequencies = np.logspace(1, 3, 600)
    spl_db, phase_degrees = enclosure.calculate_frequency_response(frequencies)

    # Compare
    comparison = compare_responses(
        viberesp_freq=frequencies,
        viberesp_spl=spl_db,
        viberesp_phase=phase_degrees,
        hornresp_freq=hornresp_data.frequencies,
        hornresp_spl=hornresp_data.spl,
        hornresp_phase=hornresp_data.phase if hasattr(hornresp_data, 'phase') else None,
    )

    # Calculate metrics
    metrics = calculate_validation_metrics(comparison)

    # Print results
    print(f"RMSE: {metrics.rmse:.2f} dB (target: < 5 dB for Phase 1)")
    print(f"MAE: {metrics.mae:.2f} dB")
    print(f"F3 Error: {metrics.f3_error:.1f} Hz (Vib: {metrics.f3_viberesp:.1f}, HR: {metrics.f3_hornresp:.1f})")
    print(f"Max Error: {metrics.max_error:.2f} dB @ {metrics.max_error_freq:.1f} Hz")
    print(f"Correlation: {metrics.correlation:.3f} (target: > 0.90)")
    print(f"Bass RMSE (20-200 Hz): {metrics.bass_rmse:.2f} dB")

    return metrics


def main():
    """Run validation on all 4 synthetic test cases."""
    print("\n" + "#"*70)
    print("# SYNTHETIC TEST CASE VALIDATION - PHASE 1 RESULTS")
    print("#"*70)

    metrics1 = validate_case1()
    metrics2 = validate_case2()
    metrics3 = validate_case3()
    metrics4 = validate_case4()

    # Summary
    print("\n" + "="*70)
    print("SUMMARY OF ALL CASES")
    print("="*70)
    print(f"{'Case':<6} {'RMSE':>8} {'MAE':>8} {'F3 Err':>10} {'Max Err':>10} {'Corr':>8}")
    print("-"*70)
    print(f"{'Case 1':<6} {metrics1.rmse:>8.2f} {metrics1.mae:>8.2f} {metrics1.f3_error:>10.1f} {metrics1.max_error:>10.2f} {metrics1.correlation:>8.3f}")
    print(f"{'Case 2':<6} {metrics2.rmse:>8.2f} {metrics2.mae:>8.2f} {metrics2.f3_error:>10.1f} {metrics2.max_error:>10.2f} {metrics2.correlation:>8.3f}")
    print(f"{'Case 3':<6} {metrics3.rmse:>8.2f} {metrics3.mae:>8.2f} {metrics3.f3_error:>10.1f} {metrics3.max_error:>10.2f} {metrics3.correlation:>8.3f}")
    print(f"{'Case 4':<6} {metrics4.rmse:>8.2f} {metrics4.mae:>8.2f} {metrics4.f3_error:>10.1f} {metrics4.max_error:>10.2f} {metrics4.correlation:>8.3f}")

    # Average
    avg_rmse = (metrics1.rmse + metrics2.rmse + metrics3.rmse + metrics4.rmse) / 4
    avg_mae = (metrics1.mae + metrics2.mae + metrics3.mae + metrics4.mae) / 4
    avg_f3_err = abs(metrics1.f3_error) + abs(metrics2.f3_error) + abs(metrics3.f3_error) + abs(metrics4.f3_error) / 4
    avg_corr = (metrics1.correlation + metrics2.correlation + metrics3.correlation + metrics4.correlation) / 4

    print("-"*70)
    print(f"{'AVG':<6} {avg_rmse:>8.2f} {avg_mae:>8.2f} {avg_f3_err:>10.1f} {'':>10} {avg_corr:>8.3f}")

    print("\n" + "="*70)
    print("PHASE 1 TARGETS")
    print("="*70)
    print(f"RMSE: < 5.0 dB (current: {avg_rmse:.2f} dB)")
    print(f"F3 Error: < 8.0 Hz (current: {avg_f3_err:.1f} Hz)")
    print(f"Correlation: > 0.90 (current: {avg_corr:.3f})")

    # Assessment
    print("\n" + "="*70)
    if avg_rmse < 5.0 and avg_f3_err < 8.0 and avg_corr > 0.90:
        print("✓ PHASE 1 TARGETS MET!")
    else:
        print("✗ Phase 1 targets not yet met")
        if avg_rmse >= 5.0:
            print(f"  - RMSE needs improvement: {avg_rmse:.2f} → < 5.0 dB")
        if avg_f3_err >= 8.0:
            print(f"  - F3 error needs improvement: {avg_f3_err:.1f} → < 8.0 Hz")
        if avg_corr <= 0.90:
            print(f"  - Correlation needs improvement: {avg_corr:.3f} → > 0.90")
    print("="*70)


if __name__ == "__main__":
    main()
