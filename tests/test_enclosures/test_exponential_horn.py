"""Unit tests for exponential horn implementation."""

import pytest
import numpy as np
import warnings
from viberesp.core.models import ThieleSmallParameters, EnclosureParameters
from viberesp.enclosures.horns import ExponentialHorn


@pytest.fixture
def horn_driver():
    """Create a sample driver suitable for horn loading."""
    return ThieleSmallParameters(
        manufacturer="Test",
        model_number="HornDriver",
        fs=35.0,
        vas=50.0,
        qes=0.35,
        qms=3.5,
        sd=0.035,  # 350 cm²
        re=6.5,
        bl=12.0,
        xmax=10.0,
        pe=300.0
    )


@pytest.fixture
def exponential_horn_params():
    """Create exponential horn parameters."""
    return EnclosureParameters(
        enclosure_type="tapped_horn",  # Will use enum value
        vb=0.0,  # Not used for horns
        throat_area_cm2=50.0,
        mouth_area_cm2=1000.0,
        horn_length_cm=120.0,
        flare_rate=4.0,  # ~75 Hz cutoff
        cutoff_frequency=None
    )


class TestExponentialHorn:
    """Test suite for ExponentialHorn class."""

    def test_initialization(self, horn_driver, exponential_horn_params):
        """Test horn initialization with required parameters."""
        horn = ExponentialHorn(horn_driver, exponential_horn_params)

        assert horn.throat_area == pytest.approx(50.0 * 1e-4, rel=1e-3)
        assert horn.mouth_area == pytest.approx(1000.0 * 1e-4, rel=1e-3)
        assert horn.horn_length == pytest.approx(120.0 * 0.01, rel=1e-3)

    def test_initialization_requires_throat_area(self, horn_driver):
        """Test that throat_area_cm2 is required."""
        params = EnclosureParameters(
            enclosure_type="tapped_horn",
            vb=0.0,
            mouth_area_cm2=1000.0,
            horn_length_cm=120.0
        )

        with pytest.raises(ValueError, match="throat_area_cm2"):
            ExponentialHorn(horn_driver, params)

    def test_initialization_requires_mouth_area(self, horn_driver):
        """Test that mouth_area_cm2 is required."""
        params = EnclosureParameters(
            enclosure_type="tapped_horn",
            vb=0.0,
            throat_area_cm2=50.0,
            horn_length_cm=120.0
        )

        with pytest.raises(ValueError, match="mouth_area_cm2"):
            ExponentialHorn(horn_driver, params)

    def test_initialization_requires_horn_length(self, horn_driver):
        """Test that horn_length_cm is required."""
        params = EnclosureParameters(
            enclosure_type="tapped_horn",
            vb=0.0,
            throat_area_cm2=50.0,
            mouth_area_cm2=1000.0
        )

        with pytest.raises(ValueError, match="horn_length_cm"):
            ExponentialHorn(horn_driver, params)

    def test_calculate_cutoff_frequency_from_flare_rate(
        self, horn_driver, exponential_horn_params
    ):
        """Test cutoff frequency calculation from flare rate."""
        horn = ExponentialHorn(horn_driver, exponential_horn_params)

        # fc = (m * c) / (4π)
        # For m=4.0, c=346.1 m/s
        # fc ≈ (4.0 * 346.1) / (4π) ≈ 110.2 Hz
        fc = horn.calculate_cutoff_frequency()

        expected_fc = (4.0 * 346.1) / (4 * np.pi)
        assert fc == pytest.approx(expected_fc, rel=0.01)

    def test_calculate_cutoff_frequency_from_parameter(self, horn_driver):
        """Test cutoff frequency when explicitly provided."""
        params = EnclosureParameters(
            enclosure_type="tapped_horn",
            vb=0.0,
            throat_area_cm2=50.0,
            mouth_area_cm2=1000.0,
            horn_length_cm=120.0,
            cutoff_frequency=75.0  # Explicit cutoff
        )

        horn = ExponentialHorn(horn_driver, params)
        fc = horn.calculate_cutoff_frequency()

        assert fc == pytest.approx(75.0, rel=0.01)

    def test_calculate_cutoff_frequency_raises_without_flare_or_cutoff(
        self, horn_driver
    ):
        """Test that cutoff calculation raises error when flare_rate not provided."""
        params = EnclosureParameters(
            enclosure_type="tapped_horn",
            vb=0.0,
            throat_area_cm2=50.0,
            mouth_area_cm2=1000.0,
            horn_length_cm=120.0,
            flare_rate=None,
            cutoff_frequency=None
        )

        horn = ExponentialHorn(horn_driver, params)

        with pytest.raises(ValueError, match="Cutoff frequency"):
            horn.calculate_cutoff_frequency()

    def test_calculate_horn_gain(self, horn_driver, exponential_horn_params):
        """Test horn gain calculation."""
        horn = ExponentialHorn(horn_driver, exponential_horn_params)

        # Horn gain = 10 * log10(mouth_area / throat_area)
        # gain = 10 * log10(1000 / 50) = 10 * log10(20) ≈ 13.0 dB
        gain_db = horn.calculate_horn_gain()

        expected_gain = 10 * np.log10(1000.0 / 50.0)
        assert gain_db == pytest.approx(expected_gain, rel=0.01)

    def test_calculate_loaded_parameters(self, horn_driver, exponential_horn_params):
        """Test horn loading effect on driver parameters."""
        horn = ExponentialHorn(horn_driver, exponential_horn_params)

        loaded = horn.calculate_loaded_parameters()

        # Fs should increase due to horn loading
        assert loaded['fs_loaded'] > horn_driver.fs

        # Without rear chamber, Vas should stay the same
        assert loaded['vas_loaded'] == pytest.approx(horn_driver.vas, rel=0.01)

    def test_calculate_loaded_parameters_with_rear_chamber(self, horn_driver):
        """Test horn loading with rear chamber."""
        params = EnclosureParameters(
            enclosure_type="tapped_horn",
            vb=0.0,
            throat_area_cm2=50.0,
            mouth_area_cm2=1000.0,
            horn_length_cm=120.0,
            flare_rate=4.0,
            rear_chamber_volume=20.0
        )

        horn = ExponentialHorn(horn_driver, params)
        loaded = horn.calculate_loaded_parameters()

        # With rear chamber, Vas should be reduced
        assert loaded['vas_loaded'] < horn_driver.vas

        # Calculate expected Vas_loaded
        # Vas_loaded = Vas / (alpha + 1) where alpha = Vas / Vb
        alpha = horn_driver.vas / params.rear_chamber_volume
        expected_vas_loaded = horn_driver.vas / (alpha + 1)

        assert loaded['vas_loaded'] == pytest.approx(expected_vas_loaded, rel=0.01)

    def test_calculate_frequency_response(self, horn_driver, exponential_horn_params):
        """Test frequency response calculation."""
        horn = ExponentialHorn(horn_driver, exponential_horn_params)

        frequencies = np.logspace(1, 3, 100)  # 10 Hz - 1 kHz
        spl_db, phase_deg = horn.calculate_frequency_response(frequencies)

        # Check return shapes
        assert len(spl_db) == len(frequencies)
        assert len(phase_deg) == len(frequencies)

        # Check that SPL increases with frequency (high-pass characteristic)
        # Find SPL at 50 Hz vs 500 Hz
        idx_50 = np.argmin(np.abs(frequencies - 50))
        idx_500 = np.argmin(np.abs(frequencies - 500))

        assert spl_db[idx_500] > spl_db[idx_50]

        # Check phase is in reasonable range [-180, 180]
        assert np.all(phase_deg >= -180)
        assert np.all(phase_deg <= 180)

    def test_calculate_system_q(self, horn_driver, exponential_horn_params):
        """Test system Q calculation."""
        horn = ExponentialHorn(horn_driver, exponential_horn_params)

        q_system = horn.calculate_system_q()

        # System Q should be different from driver Qts due to loading
        # Typically lower due to increased Fs
        assert q_system != horn_driver.qts

        # Check approximate relationship
        loaded = horn.calculate_loaded_parameters()
        expected_q = horn_driver.qts * (horn_driver.fs / loaded['fs_loaded'])
        assert q_system == pytest.approx(expected_q, rel=0.01)

    def test_calculate_f3(self, horn_driver, exponential_horn_params):
        """Test F3 calculation."""
        horn = ExponentialHorn(horn_driver, exponential_horn_params)

        f3 = horn.calculate_f3()

        # F3 should be positive and in reasonable range
        # With high cutoff (~110 Hz) and small mouth, F3 will be higher
        assert f3 > 0

    def test_calculate_f10(self, horn_driver, exponential_horn_params):
        """Test F10 calculation."""
        horn = ExponentialHorn(horn_driver, exponential_horn_params)

        f10 = horn.calculate_f10()

        # F10 should be positive
        assert f10 > 0

        # F10 should be <= F3 (they may be equal at the frequency range limit)
        f3 = horn.calculate_f3()
        assert f10 <= f3

    def test_validate_compatibility_high_qts_warning(self, horn_driver):
        """Test warning for high Qts driver."""
        # Create driver with high Qts
        high_qts_driver = ThieleSmallParameters(
            manufacturer="Test",
            model_number="HighQts",
            fs=35.0,
            vas=50.0,
            qes=0.6,  # High Qes → High Qts
            qms=3.5,
            sd=0.035,
            re=6.5,
            bl=8.0,
        )

        params = EnclosureParameters(
            enclosure_type="tapped_horn",
            vb=0.0,
            throat_area_cm2=50.0,
            mouth_area_cm2=1000.0,
            horn_length_cm=120.0
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ExponentialHorn(high_qts_driver, params)

            # Should have warning about Qts > 0.4
            assert len(w) > 0
            assert any("Qts" in str(warning.message) for warning in w)

    def test_validate_compatibility_high_fs_warning(self, horn_driver):
        """Test warning for high Fs driver."""
        # Create driver with high Fs
        high_fs_driver = ThieleSmallParameters(
            manufacturer="Test",
            model_number="HighFs",
            fs=100.0,  # High Fs
            vas=50.0,
            qes=0.35,
            qms=3.5,
            sd=0.035,
            re=6.5,
            bl=12.0,
        )

        params = EnclosureParameters(
            enclosure_type="tapped_horn",
            vb=0.0,
            throat_area_cm2=50.0,
            mouth_area_cm2=1000.0,
            horn_length_cm=120.0
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ExponentialHorn(high_fs_driver, params)

            # Should have warning about Fs > 80
            assert len(w) > 0
            assert any("Fs" in str(warning.message) for warning in w)

    def test_validate_mouth_size_adequate(self, horn_driver):
        """Test mouth size validation with adequate mouth."""
        # Use a very large mouth to ensure it's adequate for the cutoff
        # For flare_rate=4.0, fc≈110 Hz, we need mouth >= ~3848 cm² for k_rm>=0.7
        params = EnclosureParameters(
            enclosure_type="tapped_horn",
            vb=0.0,
            throat_area_cm2=50.0,
            mouth_area_cm2=5000.0,  # Very large mouth
            horn_length_cm=120.0,
            flare_rate=4.0
        )

        # Should not warn with adequate mouth size
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            horn = ExponentialHorn(horn_driver, params)

            # Check mouth size
            is_adequate = horn._check_mouth_size()

            # Very large mouth should be adequate
            assert is_adequate

    def test_get_design_parameters(self, horn_driver, exponential_horn_params):
        """Test getting design parameters for optimization."""
        horn = ExponentialHorn(horn_driver, exponential_horn_params)

        params = horn.get_design_parameters()

        # Check that key parameters are present
        assert 'throat_area_cm2' in params
        assert 'mouth_area_cm2' in params
        assert 'horn_length_cm' in params

        # Each parameter should have (value, min, max) tuple
        for param_name, param_tuple in params.items():
            assert len(param_tuple) == 3
            value, min_val, max_val = param_tuple
            assert min_val <= value <= max_val

    def test_get_summary(self, horn_driver, exponential_horn_params):
        """Test getting comprehensive summary."""
        horn = ExponentialHorn(horn_driver, exponential_horn_params)

        summary = horn.get_summary()

        # Check design parameters
        assert summary['horn_type'] == 'exponential'
        assert summary['throat_area_cm2'] == 50.0
        assert summary['mouth_area_cm2'] == 1000.0
        assert summary['horn_length_cm'] == 120.0

        # Check performance metrics exist
        assert 'f3_hz' in summary
        assert 'f10_hz' in summary
        assert 'system_q' in summary
        assert 'horn_gain_db' in summary

        # Check values are reasonable
        assert summary['f3_hz'] > 0
        assert summary['horn_gain_db'] > 0


@pytest.mark.parametrize("throat_area,mouth_area,expected_gain", [
    (50, 500, 10.0),   # 10*log10(10) = 10 dB
    (50, 1000, 13.01), # 10*log10(20) ≈ 13 dB
    (100, 1000, 10.0), # 10*log10(10) = 10 dB
])
def test_horn_gain_calculation(horn_driver, throat_area, mouth_area, expected_gain):
    """Parametrized test for horn gain calculation."""
    params = EnclosureParameters(
        enclosure_type="tapped_horn",
        vb=0.0,
        throat_area_cm2=throat_area,
        mouth_area_cm2=mouth_area,
        horn_length_cm=120.0
    )

    horn = ExponentialHorn(horn_driver, params)
    gain = horn.calculate_horn_gain()

    assert gain == pytest.approx(expected_gain, rel=0.01)
