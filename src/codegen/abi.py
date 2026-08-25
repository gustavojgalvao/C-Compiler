"""
Definições de ABI para convenções de chamada x86-64.
"""
from typing import List
from src.codegen.registers import RDI, RSI, RDX, RCX, R8, R9, EDI, ESI, EDX, ECX, R8D, R9D

class SystemV_ABI:
    """Convenção System V AMD64 (Linux, macOS, BSD)."""
    ARG_REGISTERS_64: List[str] = [RDI, RSI, RDX, RCX, R8, R9]
    ARG_REGISTERS_32: List[str] = [EDI, ESI, EDX, ECX, R8D, R9D]
    STACK_ALIGNMENT: int = 16


class Windows_x64_ABI:
    """Convenção Microsoft x64 (Windows)."""
    ARG_REGISTERS_64: List[str] = [RCX, RDX, R8, R9]
    ARG_REGISTERS_32: List[str] = [ECX, EDX, R8D, R9D]
    SHADOW_SPACE_BYTES: int = 32
    STACK_ALIGNMENT: int = 16
