"""
CRC Polynomial Specifications for Space Communication.

References:
- CCSDS 131.0-B-5 (TM Synchronization and Channel Coding)
- IEEE 802.3 Standard CRC-32
"""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class CRCParameters:
    """CRC algorithm configuration parameters."""
    name: str
    width: int            # Bits (16 or 32)
    polynomial: int       # Generator polynomial
    initial_value: int    # Initial remainder
    final_xor: int        # Final XOR value
    reflect_in: bool      # Reflect input bytes
    reflect_out: bool     # Reflect output remainder
    check_value: int      # Expected result for ASCII string '123456789'


# Standard CRC Profiles
CRC16_CCITT = CRCParameters(
    name="CRC-16-CCITT",
    width=16,
    polynomial=0x1021,
    initial_value=0xFFFF,
    final_xor=0x0000,
    reflect_in=False,
    reflect_out=False,
    check_value=0x29B1,
)

CRC32_IEEE = CRCParameters(
    name="CRC-32",
    width=32,
    polynomial=0x04C11DB7,
    initial_value=0xFFFFFFFF,
    final_xor=0xFFFFFFFF,
    reflect_in=True,
    reflect_out=True,
    check_value=0xCBF43926,
)

SUPPORTED_CRC_PROFILES: Dict[str, CRCParameters] = {
    "CRC-16-CCITT": CRC16_CCITT,
    "CRC-16": CRC16_CCITT,
    "CRC-32": CRC32_IEEE,
    "CRC-32-IEEE": CRC32_IEEE,
}
