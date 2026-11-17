"""
Unit Tests for CRC-16-CCITT and CRC-32 Engines.
"""

import pytest
from src.error_detection.crc_engine import CRCEngine
from src.error_detection.polynomials import CRC16_CCITT, CRC32_IEEE


class TestCRCEngine:

    def test_crc16_ccitt_standard_vector(self):
        # ASCII "123456789" -> 0x29B1 for CRC-16-CCITT (CCSDS profile)
        engine = CRCEngine(CRC16_CCITT)
        test_data = b"123456789"
        crc = engine.calculate(test_data)
        assert crc == CRC16_CCITT.check_value
        assert crc == 0x29B1

    def test_crc32_standard_vector(self):
        # ASCII "123456789" -> 0xCBF43926 for standard IEEE 802.3 CRC-32
        engine = CRCEngine(CRC32_IEEE)
        test_data = b"123456789"
        crc = engine.calculate(test_data)
        assert crc == CRC32_IEEE.check_value
        assert crc == 0xCBF43926

    def test_append_and_verify_clean_data(self):
        engine = CRCEngine("CRC-16-CCITT")
        payload = b"SPACECRAFT_TELEMETRY_PACKET"
        frame_with_crc = engine.append_crc(payload)

        assert len(frame_with_crc) == len(payload) + 2
        is_valid, rx_crc, comp_crc = engine.verify(frame_with_crc)
        assert is_valid is True
        assert rx_crc == comp_crc

    def test_detect_single_bit_flip(self):
        engine = CRCEngine("CRC-16-CCITT")
        payload = b"CRITICAL_HEALTH_DATA"
        frame_with_crc = bytearray(engine.append_crc(payload))

        # Invert single bit at byte 5
        frame_with_crc[5] ^= 0x01

        is_valid, rx_crc, comp_crc = engine.verify(bytes(frame_with_crc))
        assert is_valid is False
        assert rx_crc != comp_crc

    def test_detect_crc_footer_corruption(self):
        engine = CRCEngine("CRC-16-CCITT")
        payload = b"SENSOR_READINGS"
        frame_with_crc = bytearray(engine.append_crc(payload))

        # Corrupt the CRC trailer itself
        frame_with_crc[-1] ^= 0xFF

        is_valid, rx_crc, comp_crc = engine.verify(bytes(frame_with_crc))
        assert is_valid is False
