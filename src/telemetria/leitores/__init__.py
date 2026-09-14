"""Módulo de leitores de telemetria unificados."""

from __future__ import annotations

from .cosworth_pi import (
    CosworthPdsReader,
    CosworthPidReader,
    TransformacaoLinear,
    parse_cosworth_metadata,
)

__all__ = [
    "CosworthPidReader",
    "CosworthPdsReader",
    "TransformacaoLinear",
    "parse_cosworth_metadata",
]
