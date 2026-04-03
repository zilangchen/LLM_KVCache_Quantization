"""Inference engine and generation loop."""

from src.engine.generate_loop import (
    generate,
    generate_from_ids,
    GenerationOutput,
    GenerationBatchOutput,
)
# ENG-075: Export public symbols that 5+ scripts depend on.
from src.engine.patch_model import (
    apply_int8_fused_patch,
    remove_int8_fused_patch,
)

__all__ = [
    "generate",
    "generate_from_ids",
    "GenerationOutput",
    "GenerationBatchOutput",
    "apply_int8_fused_patch",
    "remove_int8_fused_patch",
]
