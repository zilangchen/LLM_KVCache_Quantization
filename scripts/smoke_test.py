#!/usr/bin/env python3
"""
Smoke test: Minimal inference script to verify model loading and generation.

This script verifies:
1. Model can be loaded
2. Greedy decoding works
3. Output is non-empty
4. Metadata (git commit, hardware) is recorded

Usage:
    python scripts/smoke_test.py
    python scripts/smoke_test.py --prompt "Your custom prompt"
    python scripts/smoke_test.py --max_new_tokens 64

Output:
    Prints generated text and metadata to stdout.
    Optionally writes structured output to results/runs/smoke_test_<timestamp>.json
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from src.utils.repro import get_git_commit, get_hardware_info, set_seed  # QUA-001: centralized
from src.utils.hf import resolve_pretrained_path
from scripts.config_utils import ALLOWED_MODEL_IDS  # SMK-008: model whitelist


def main():
    """Main smoke test function."""
    parser = argparse.ArgumentParser(description="Smoke test for model inference")
    parser.add_argument(
        "--prompt",
        type=str,
        default="Hello, I am a language model. My purpose is",
        help="Input prompt for generation",
    )
    parser.add_argument(
        "--max_new_tokens",
        type=int,
        default=32,
        help="Maximum number of tokens to generate",
    )
    parser.add_argument(
        "--model_id",
        type=str,
        default="Qwen/Qwen2.5-1.5B-Instruct",
        help="HuggingFace model ID",
    )
    parser.add_argument(
        "--model_revision",
        type=str,
        default=None,
        help="Optional model revision (commit hash/tag) for strict reproducibility.",
    )
    parser.add_argument(
        "--save_output",
        action="store_true",
        help="Save structured output to results/runs/",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1234,
        help="Random seed (default: 1234)",
    )
    parser.add_argument(
        "--out_dir",
        type=str,
        default="results/runs",
        help="Output directory for JSON (default: results/runs)",
    )
    # SMK-005: BREAKING CHANGE — This flag changes exit code semantics.
    # Without --cpu-ok, missing CUDA causes exit(1) (failure).  With
    # --cpu-ok, missing CUDA causes exit(0) (success/skip).  CI pipelines
    # that previously expected exit(1) on CPU-only runners must be updated
    # if --cpu-ok is added to their invocation.
    parser.add_argument(
        "--cpu-ok",
        action="store_true",
        dest="cpu_ok",
        help=(
            "Allow exit(0) when CUDA is not available. "
            "Use this in CI environments that lack a GPU so the job is "
            "marked as skipped/passing rather than failed."
        ),
    )
    args = parser.parse_args()

    print("=" * 60)
    print("SMOKE TEST: Model Loading and Generation")
    print("=" * 60)

    # Step 1: Import dependencies
    print("\n[1/4] Importing dependencies...")
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        print(f"  ✓ torch {torch.__version__}")
        print(f"  ✓ CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"  ✓ GPU: {torch.cuda.get_device_name(0)}")
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        print("  Please run: pip install -r requirements.txt")
        sys.exit(1)

    # Check CUDA availability.
    # SMK-001: Exit with a non-zero code by default so CI jobs without a GPU
    # are not silently marked as passing.  Pass --cpu-ok to allow exit(0) in
    # environments (e.g., CPU-only CI runners) where the absence of CUDA is
    # an expected, intentional condition rather than a failure.
    if not torch.cuda.is_available():
        print("\n  WARNING: CUDA is not available!")
        print("  This script requires a GPU to run.")
        print("  If you're developing locally, the code structure is correct.")
        print("  Please run on a GPU-enabled server for actual verification.")
        if args.cpu_ok:
            print("  (--cpu-ok set: exiting with code 0)")
            sys.exit(0)
        else:
            print("  (Use --cpu-ok to suppress this error in CPU-only CI environments.)")
            sys.exit(1)

    # Step 2: Load model and tokenizer
    # SMK-008: validate model_id against whitelist before trust_remote_code
    if args.model_id not in ALLOWED_MODEL_IDS:
        print(f"\n  ERROR: model_id '{args.model_id}' not in ALLOWED_MODEL_IDS whitelist.")
        print(f"  Allowed: {sorted(ALLOWED_MODEL_IDS)}")
        print("  Refusing to load with trust_remote_code=True for unknown model.")
        sys.exit(1)
    print(f"\n[2/4] Loading model: {args.model_id}...")
    try:
        model_path = resolve_pretrained_path(args.model_id, revision=args.model_revision)
        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            revision=args.model_revision,
            trust_remote_code=True,
        )
        print("  ✓ Tokenizer loaded")

        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            revision=args.model_revision,
            trust_remote_code=True,
        )
        print("  ✓ Model loaded")
        print(f"  ✓ Model dtype: {model.dtype}")
        print(f"  ✓ Device: {model.device}")
    except Exception as e:
        print(f"  ✗ Model loading failed: {e}")
        print("\n  Possible causes:")
        print("  - Network issue (cannot download model)")
        print("  - Insufficient GPU memory (OOM)")
        print("  - Model ID incorrect")
        sys.exit(1)

    # Step 2b: Verify project Engine/Cache pipeline is importable (SMK-006)
    print("\n[2b/4] Verifying project Engine/Cache pipeline imports...")
    try:
        from src.engine.generate_loop import generate_from_ids  # noqa: F401
        from src.cache.fp16_cache import FP16KVCache  # noqa: F401
        from src.cache.int8_cache import INT8KVCache  # noqa: F401
        print("  ✓ Engine generate_from_ids importable")
        print("  ✓ FP16KVCache importable")
        print("  ✓ INT8KVCache importable")
    except ImportError as e:
        print(f"  ✗ Engine/Cache pipeline import failed: {e}")
        print("  WARNING: src/engine/ or src/cache/ may be broken.")
        # Non-fatal for smoke test — the HF generate path still works.

    # Step 3: Generate with greedy decoding
    print(f"\n[3/4] Generating text (greedy, max_new_tokens={args.max_new_tokens})...")
    print(f"  Prompt: {args.prompt[:50]}...")
    try:
        # Tokenize input
        inputs = tokenizer(args.prompt, return_tensors="pt").to(model.device)

        # Set seed for reproducibility
        set_seed(seed=args.seed, deterministic=True)

        # Generate with greedy decoding (aligned with configs/exp_matrix.yaml)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,  # greedy
                temperature=None,  # Not used with do_sample=False
                top_p=None,
                top_k=None,
                pad_token_id=tokenizer.eos_token_id,
            )

        # Decode output.
        # SMK-003: We strip the prompt by slicing on its *character* length
        # rather than on the token boundary.  This is a known approximation:
        # the tokenizer's decode() may normalise whitespace or special chars,
        # so the decoded prefix can differ slightly from the raw prompt string.
        # For a smoke test whose sole purpose is to confirm that *some* new
        # text was produced, this heuristic is acceptable.  A production
        # evaluation pipeline should decode only the new-token slice
        # (outputs[0][inputs["input_ids"].shape[-1]:]) to avoid the ambiguity.
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        new_text = generated_text[len(args.prompt):]
        print("  ✓ Generation complete")
    except torch.cuda.OutOfMemoryError:
        print("  ✗ Out of GPU memory!")
        print("  Try reducing --max_new_tokens or using a smaller model")
        sys.exit(1)
    except Exception as e:
        print(f"  ✗ Generation failed: {e}")
        sys.exit(1)

    # Step 4: Display results
    print("\n[4/4] Results")
    print("-" * 60)
    print(f"Input:  {args.prompt}")
    print(f"Output: {new_text.strip()}")
    print("-" * 60)

    # Metadata
    git_commit = get_git_commit()
    hardware = get_hardware_info()
    timestamp = datetime.now().isoformat()

    result = {
        "run_id": f"smoke_test_{timestamp.replace(':', '-')}",
        "model_id": args.model_id,
        "model_revision": getattr(args, "model_revision", None),  # SMK-010
        "seed": getattr(args, "seed", 1234),  # SMK-010: record seed for reproducibility
        "prompt": args.prompt,
        "generated_text": new_text.strip(),
        "max_new_tokens": args.max_new_tokens,
        "git_commit": git_commit,
        "hardware": hardware,
        "timestamp": timestamp,
        "status": "success" if new_text.strip() else "empty_output",
    }

    print(f"\nMetadata:")
    print(f"  Git commit: {git_commit}")
    print(f"  GPU: {hardware['gpu']}")
    print(f"  Timestamp: {timestamp}")

    # Verify non-empty output
    if not new_text.strip():
        print("\n⚠️  WARNING: Generated text is empty!")
        result["status"] = "empty_output"
    else:
        print("\n✓ SMOKE TEST PASSED")

    # Optionally save output
    if args.save_output:
        script_dir = Path(__file__).resolve().parent
        project_root = script_dir.parent
        runs_dir = Path(args.out_dir)
        if not runs_dir.is_absolute():
            runs_dir = project_root / runs_dir
        runs_dir.mkdir(parents=True, exist_ok=True)

        output_file = runs_dir / f"smoke_test_{timestamp.replace(':', '-')}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Output saved to {output_file}")

    return 0 if result["status"] == "success" else 1


# SEC-004: Error messages may contain local paths — expected for research CLI tools.
if __name__ == "__main__":
    sys.exit(main())
