#!/usr/bin/env python3
"""
HuggingFace Hub helpers.

Why this exists:
- Some Transformers code paths may call Hub APIs (e.g. model_info) even when
  weights/tokenizers are already cached, which makes long-running experiments
  flaky under proxied or unstable networks.
- Resolving `model_id` to a *local snapshot directory* avoids those network calls
  while keeping compatibility with normal `from_pretrained(...)` usage.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import os


def resolve_pretrained_path(model_id: str, revision: Optional[str] = None) -> str:
    """
    Resolve a model identifier to a local snapshot path when possible.

    Behavior:
    - If `model_id` already points to an existing local path, return it.
    - Otherwise, try `snapshot_download(..., local_files_only=True)` first
      (no network).
    - If not cached and we're not in offline mode, fall back to downloading.
    - If all else fails, return the original `model_id` and let Transformers
      handle it (best-effort).
    """
    if not model_id:
        return model_id

    candidate = Path(model_id).expanduser()
    if candidate.exists():
        return str(candidate)

    try:
        from huggingface_hub import snapshot_download
    except Exception:
        return model_id

    offline = (
        os.environ.get("HF_HUB_OFFLINE") == "1"
        or os.environ.get("TRANSFORMERS_OFFLINE") == "1"
    )

    try:
        return snapshot_download(repo_id=model_id, revision=revision, local_files_only=True)
    except Exception as exc:
        if offline:
            raise RuntimeError(
                "HF offline 模式下未找到本地缓存模型；请先联网运行一次下载模型，或取消 "
                "HF_HUB_OFFLINE/TRANSFORMERS_OFFLINE。"
            ) from exc

    try:
        return snapshot_download(repo_id=model_id, revision=revision)
    except Exception:
        return model_id

