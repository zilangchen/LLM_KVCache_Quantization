#!/usr/bin/env python3
"""
Collect environment information for reproducibility.

Outputs:
    - env/versions.txt: Human-readable environment info
    - env/requirements_freeze.txt: pip freeze output

Usage:
    python scripts/collect_env.py
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_git_commit() -> str:
    """Get current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()[:8]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def get_gpu_info() -> str:
    """Get GPU information using nvidia-smi."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "No GPU detected or nvidia-smi not available"


def get_cuda_version() -> str:
    """Get CUDA version from nvcc."""
    try:
        result = subprocess.run(
            ["nvcc", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        # Parse version from output
        for line in result.stdout.split("\n"):
            if "release" in line.lower():
                return line.strip()
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "nvcc not available"


def get_python_packages() -> dict:
    """Get versions of key Python packages."""
    packages = {}

    try:
        import torch
        packages["torch"] = torch.__version__
        packages["torch.cuda"] = torch.version.cuda or "N/A"
        packages["torch.cuda.available"] = str(torch.cuda.is_available())
        if torch.cuda.is_available():
            packages["torch.cuda.device_name"] = torch.cuda.get_device_name(0)
    except ImportError:
        packages["torch"] = "not installed"

    try:
        import transformers
        packages["transformers"] = transformers.__version__
    except ImportError:
        packages["transformers"] = "not installed"

    try:
        import triton
        packages["triton"] = triton.__version__
    except ImportError:
        packages["triton"] = "not installed"

    try:
        import accelerate
        packages["accelerate"] = accelerate.__version__
    except ImportError:
        packages["accelerate"] = "not installed"

    try:
        import numpy
        packages["numpy"] = numpy.__version__
    except ImportError:
        packages["numpy"] = "not installed"

    try:
        import pandas
        packages["pandas"] = pandas.__version__
    except ImportError:
        packages["pandas"] = "not installed"

    return packages


def pip_freeze(output_path: Path) -> None:
    """Run pip freeze and save to file."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            check=True,
        )
        output_path.write_text(result.stdout)
        print(f"✓ pip freeze saved to {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to run pip freeze: {e}")


def main():
    """Main function to collect and save environment info."""
    # Determine project root (assuming script is in scripts/)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    env_dir = project_root / "env"

    # Ensure env directory exists
    env_dir.mkdir(exist_ok=True)

    # Collect info
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    git_commit = get_git_commit()
    gpu_info = get_gpu_info()
    cuda_version = get_cuda_version()
    packages = get_python_packages()

    # Build versions.txt content
    lines = [
        "# Environment versions for reproducibility",
        f"# Collected at: {timestamp}",
        f"# Git commit: {git_commit}",
        "",
        "## System",
        f"Python: {sys.version}",
        f"Platform: {sys.platform}",
        "",
        "## GPU / CUDA",
        f"GPU: {gpu_info}",
        f"CUDA (nvcc): {cuda_version}",
        "",
        "## Python Packages",
    ]

    for pkg, version in packages.items():
        lines.append(f"{pkg}: {version}")

    lines.append("")

    # Write versions.txt
    versions_path = env_dir / "versions.txt"
    versions_path.write_text("\n".join(lines))
    print(f"✓ Environment info saved to {versions_path}")

    # Run pip freeze
    freeze_path = env_dir / "requirements_freeze.txt"
    pip_freeze(freeze_path)

    print("\n--- Summary ---")
    print(f"Git commit: {git_commit}")
    print(f"GPU: {gpu_info}")
    print(f"torch: {packages.get('torch', 'N/A')}")
    print(f"transformers: {packages.get('transformers', 'N/A')}")
    print(f"triton: {packages.get('triton', 'N/A')}")


if __name__ == "__main__":
    main()
