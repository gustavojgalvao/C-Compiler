"""Módulo de Geração de Código."""
from .registers import *
from .abi import SystemV_ABI, Windows_x64_ABI
from .x86_generator import X86CodeGenerator

__all__ = ["SystemV_ABI", "Windows_x64_ABI", "X86CodeGenerator"]
