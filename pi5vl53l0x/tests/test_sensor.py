"""Unit tests for the VL53L0X sensor driver."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest

from pi5vl53l0x.core.sensor import VL53L0X


def _make_mock_bus_device() -> MagicMock:
    """Create a mock bus object with standard I2C behavior."""
    bus = MagicMock()
    bus.read_byte_data.return_value = 0x00
    bus.write_byte_data.return_value = None
    bus.read_word_data.return_value = 0
    bus.write_word_data.return_value = None
    bus.read_i2c_block_data.return_value = [0x00] * 6
    bus.write_i2c_block_data.return_value = None
    return bus


def _setup_init_responses(bus: MagicMock) -> None:
    """Configure the mock bus to pass through full initialization."""

    def smart_read(address: int, register: int) -> int:
        del address

        if register == 0xC0:
            return 0xEE
        if register == 0x01:
            return 0x01
        if register == 0x91:
            return 0x28
        if register == 0x84:
            return 0x10
        if register == 0x89:
            return 0x00
        if register == 0x60:
            return 0x00
        if register == 0x83:
            return 0x01
        if register == 0x92:
            return 12
        if register == 0x13:
            return 0x07
        if register in (0x50, 0x70):
            return 0x0E

        return 0x00

    def smart_read_word(address: int, register: int) -> int:
        del address, register
        return 0x0100

    bus.read_byte_data.side_effect = smart_read
    bus.read_word_data.side_effect = smart_read_word


@pytest.fixture
def mock_bus() -> MagicMock:
    """Create a mock bus with full init support."""
    bus = _make_mock_bus_device()
    _setup_init_responses(bus)
    return bus


@pytest.fixture
def sensor(mock_bus: MagicMock) -> VL53L0X:
    """Create a VL53L0X instance with successful initialization."""
    return VL53L0X(
        i2c_bus=1,
        i2c_address=0x29,
        bus_factory=MagicMock(return_value=mock_bus),
    )


class TestInit:
    """Tests for VL53L0X initialization."""

    def test_successful_init(self, sensor: VL53L0X) -> None:
        """Sensor should initialize successfully with valid responses."""
        assert sensor._initialized is True

    def test_init_verifies_model_id(self, mock_bus: MagicMock) -> None:
        """Init should check Model ID is 0xEE."""
        original_side_effect = mock_bus.read_byte_data.side_effect

        def wrong_id(address: int, register: int) -> int:
            if register == 0xC0:
                return 0x00
            return original_side_effect(address, register)

        mock_bus.read_byte_data.side_effect = wrong_id

        with pytest.raises(ConnectionError, match="Invalid Model ID"):
            VL53L0X(bus_factory=MagicMock(return_value=mock_bus))

    def test_init_cleanup_on_failure(self) -> None:
        """I2C bus should be closed if init fails."""
        bus = _make_mock_bus_device()

        def always_wrong(address: int, register: int) -> int:
            del address
            if register == 0xC0:
                return 0x00
            return 0x00

        bus.read_byte_data.side_effect = always_wrong

        with pytest.raises(ConnectionError):
            VL53L0X(bus_factory=MagicMock(return_value=bus))

        bus.close.assert_called()

    def test_firmware_boot_timeout(self) -> None:
        """Should raise TimeoutError if firmware doesn't boot."""
        bus = _make_mock_bus_device()

        def no_boot(address: int, register: int) -> int:
            del address
            if register == 0xC0:
                return 0xEE
            if register == 0x01:
                return 0x00
            return 0x00

        bus.read_byte_data.side_effect = no_boot

        with pytest.raises(TimeoutError, match="firmware did not boot"):
            VL53L0X(bus_factory=MagicMock(return_value=bus), firmware_boot_timeout=0.05)


class TestGetRange:
    """Tests for the get_range() method."""

    def test_returns_distance_mm(self, sensor: VL53L0X, mock_bus: MagicMock) -> None:
        """get_range should return distance in mm."""
        original = mock_bus.read_byte_data.side_effect

        def range_read(address: int, register: int) -> int:
            if register == 0x13:
                return 0x07
            return original(address, register)

        mock_bus.read_byte_data.side_effect = range_read
        mock_bus.read_word_data.side_effect = lambda address, register: 0xFA00

        result = sensor.get_range()
        assert result == 250

    def test_raises_runtime_error_if_not_initialized(self, mock_bus: MagicMock) -> None:
        """get_range should raise RuntimeError if not initialized."""
        test_sensor = VL53L0X(bus_factory=MagicMock(return_value=mock_bus))
        test_sensor._initialized = False

        with pytest.raises(RuntimeError, match="not initialized"):
            test_sensor.get_range()

    def test_raises_timeout_on_no_data(self, sensor: VL53L0X, mock_bus: MagicMock) -> None:
        """get_range should raise TimeoutError if measurement never completes."""

        def never_ready(address: int, register: int) -> int:
            del address
            if register == 0x13:
                return 0x00
            return 0x00

        mock_bus.read_byte_data.side_effect = never_ready
        sensor._measurement_timing_budget_us = 1000

        with pytest.raises(TimeoutError, match="did not complete"):
            sensor.get_range()

    def test_applies_offset(self, sensor: VL53L0X, mock_bus: MagicMock) -> None:
        """get_range should subtract offset from raw measurement."""
        original = mock_bus.read_byte_data.side_effect

        def range_read(address: int, register: int) -> int:
            if register == 0x13:
                return 0x07
            return original(address, register)

        mock_bus.read_byte_data.side_effect = range_read
        mock_bus.read_word_data.side_effect = lambda address, register: 0xFA00

        sensor.set_offset(10)
        result = sensor.get_range()
        assert result == 240


class TestGetData:
    """Tests for get_data() and raw-value correctness."""

    def test_raw_value_is_truly_raw(self, sensor: VL53L0X, mock_bus: MagicMock) -> None:
        """get_data() raw_value should be the actual raw sensor value."""
        original = mock_bus.read_byte_data.side_effect

        def range_read(address: int, register: int) -> int:
            if register == 0x13:
                return 0x07
            return original(address, register)

        mock_bus.read_byte_data.side_effect = range_read
        mock_bus.read_word_data.side_effect = lambda address, register: 0xFA00

        sensor.set_offset(10)
        data = sensor.get_data()

        assert data["raw_value"] == 250
        assert data["distance_mm"] == 240
        assert data["is_valid"] is True

    def test_error_returns_safe_defaults(self, sensor: VL53L0X, mock_bus: MagicMock) -> None:
        """get_data() should return safe defaults on error."""
        mock_bus.read_byte_data.side_effect = Exception("bus error")

        data = sensor.get_data()
        assert data["distance_mm"] == -1
        assert data["is_valid"] is False
        assert data["raw_value"] is None
        assert "timestamp" in data

    def test_invalid_range_detection(self, sensor: VL53L0X, mock_bus: MagicMock) -> None:
        """get_data() should detect out-of-range values."""
        original = mock_bus.read_byte_data.side_effect

        def range_read(address: int, register: int) -> int:
            if register == 0x13:
                return 0x07
            return original(address, register)

        mock_bus.read_byte_data.side_effect = range_read
        mock_bus.read_word_data.side_effect = lambda address, register: 0xFE1F

        data = sensor.get_data()
        assert data["is_valid"] is False


class TestHealthAndRecovery:
    """Tests for health_check() and reinitialize()."""

    def test_health_check_ok(self, sensor: VL53L0X, mock_bus: MagicMock) -> None:
        """health_check should return True if model ID matches."""
        original = mock_bus.read_byte_data.side_effect

        def model_read(address: int, register: int) -> int:
            if register == 0xC0:
                return 0xEE
            return original(address, register)

        mock_bus.read_byte_data.side_effect = model_read
        assert sensor.health_check() is True

    def test_health_check_fail(self, sensor: VL53L0X, mock_bus: MagicMock) -> None:
        """health_check should return False on I2C error."""
        mock_bus.read_byte_data.side_effect = Exception("bus error")
        assert sensor.health_check() is False

    def test_reinitialize(self, sensor: VL53L0X, mock_bus: MagicMock) -> None:
        """reinitialize should re-run full init sequence."""
        _setup_init_responses(mock_bus)
        sensor.reinitialize()
        assert sensor._initialized is True


class TestAsync:
    """Tests for async get_range_async()."""

    def test_get_range_async(self, sensor: VL53L0X, mock_bus: MagicMock) -> None:
        """get_range_async should return same result as get_range."""
        original = mock_bus.read_byte_data.side_effect

        def range_read(address: int, register: int) -> int:
            if register == 0x13:
                return 0x07
            return original(address, register)

        mock_bus.read_byte_data.side_effect = range_read
        mock_bus.read_word_data.side_effect = lambda address, register: 0xFA00

        result = asyncio.run(sensor.get_range_async())
        assert result == 250


class TestContextManager:
    """Tests for context manager protocol."""

    def test_context_manager_closes(self, mock_bus: MagicMock) -> None:
        """__exit__ should close I2C connection."""
        with VL53L0X(bus_factory=MagicMock(return_value=mock_bus)) as _sensor:
            pass
        mock_bus.close.assert_called()


class TestUtilities:
    """Tests for get_ranges() and calibrate()."""

    def test_get_ranges_returns_list(self, sensor: VL53L0X, mock_bus: MagicMock) -> None:
        """get_ranges should return a list of ints."""
        original = mock_bus.read_byte_data.side_effect

        def range_read(address: int, register: int) -> int:
            if register == 0x13:
                return 0x07
            return original(address, register)

        mock_bus.read_byte_data.side_effect = range_read
        mock_bus.read_word_data.side_effect = lambda address, register: 0xFA00

        result = sensor.get_ranges(3)
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(range_mm == 250 for range_mm in result)

    def test_calibrate(self, sensor: VL53L0X, mock_bus: MagicMock) -> None:
        """calibrate should return offset between measured and target."""
        original = mock_bus.read_byte_data.side_effect

        def range_read(address: int, register: int) -> int:
            if register == 0x13:
                return 0x07
            return original(address, register)

        mock_bus.read_byte_data.side_effect = range_read
        mock_bus.read_word_data.side_effect = lambda address, register: 0xFA00

        offset = sensor.calibrate(target_distance_mm=200, num_samples=3)
        assert offset == 50


class TestBackwardCompat:
    """Tests for backward compatibility."""

    def test_driver_import(self) -> None:
        """pi5vl53l0x.driver should export VL53L0X."""
        from pi5vl53l0x.core.sensor import VL53L0X as CoreVL53L0X
        from pi5vl53l0x.driver import VL53L0X as DriverVL53L0X

        assert DriverVL53L0X is CoreVL53L0X

    def test_package_import(self) -> None:
        """pi5vl53l0x should export VL53L0X."""
        from pi5vl53l0x import VL53L0X as PkgVL53L0X
        from pi5vl53l0x.core.sensor import VL53L0X as CoreVL53L0X

        assert PkgVL53L0X is CoreVL53L0X

    def test_direct_read_write_methods(self, sensor: VL53L0X, mock_bus: MagicMock) -> None:
        """Sensor should expose read_byte/write_byte for compatibility."""
        original = mock_bus.read_byte_data.side_effect

        def compat_read(address: int, register: int) -> int:
            if register == 0xAA:
                return 0x55
            return original(address, register)

        mock_bus.read_byte_data.side_effect = compat_read

        assert sensor.read_byte(0xAA) == 0x55
        sensor.write_byte(0xBB, 0xCC)

    def test_close_method(self, sensor: VL53L0X, mock_bus: MagicMock) -> None:
        """close() should work on sensor instance."""
        sensor.close()
        mock_bus.close.assert_called()
