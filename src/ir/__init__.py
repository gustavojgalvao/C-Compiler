"""Módulo de Representação Intermediária (IR)."""
from .ir_nodes import *
from .ir_builder import IRBuilder
from .optimizer import IROptimizer
from .interpreter import IRExecutor

__all__ = ["IRBuilder", "IROptimizer", "IRExecutor"]
