#!/usr/bin/env python3
"""
Capture attention weight distributions under FP16 / INT4-symmetric / INT4-RoleAlign
for visualization in the thesis (Figure: attention distribution comparison).

Usage (remote GPU):
  python3 scripts/capture_attention_for_figure.py \
    --model_id Qwen/Qwen2.5-1.5B-Instruct \
    --calib_file artifacts/kv_calib_rolealign_1p5b.json \
    --out_dir results/attention_viz

Outputs:
  - attention_distributions.npz  (per-layer attention weights under 3 modes)
  - attention_preview.pdf        (preliminary visualization)
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))


def _rotate_half(x):
    x1 = x[..., : x.shape[-1] // 2]
    x2 = x[..., x.shape[-1] // 2 :]
    return torch.cat((-x2, x1), dim=-1)


def _apply_rope_to_q(q, cos, sin):
    if cos.dim() == 3:
        cos = cos.unsqueeze(1)
        sin = sin.unsqueeze(1)
    return (q * cos) + (_rotate_half(q) * sin)


def _get_rope_for_position(attn, dummy_q, position_ids):
    """Get RoPE cos/sin for a given position (compatible with multiple model families)."""
    try:
        rotary = attn.rotary_emb
        if hasattr(rotary, "inv_freq"):
            cos, sin = rotary(dummy_q, position_ids)
        else:
            cos, sin = rotary(dummy_q, position_ids)
        return cos, sin
    except Exception:
        return None, None


def quantize_dequantize_symmetric(k, group_size=32, qmax=7):
    """Per-group symmetric quantization (INT4 baseline)."""
    seq, head_dim = k.shape
    num_groups = head_dim // group_size
    k_view = k.view(seq, num_groups, group_size)
    absmax = k_view.abs().amax(dim=-1, keepdim=True).clamp(min=1e-5)
    scale = absmax / qmax
    q = torch.round(k_view / scale).clamp(-qmax, qmax)
    return (q * scale).view(seq, head_dim)


def quantize_dequantize_perchannel_k(k, percentile=99.9, qmax=7):
    """Per-channel asymmetric quantization for Key (INT4-RoleAlign style)."""
    # k: [seq, head_dim]
    # Per-channel: scale computed across seq dim for each channel
    abs_k = k.abs()
    if percentile >= 100.0:
        channel_max = abs_k.amax(dim=0)  # [head_dim]
    else:
        channel_max = torch.quantile(abs_k.float(), percentile / 100.0, dim=0)
    scale = channel_max.clamp(min=1e-5) / qmax  # [head_dim]
    q = torch.round(k / scale.unsqueeze(0)).clamp(-qmax, qmax)
    return q * scale.unsqueeze(0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_id", type=str, default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--calib_file", type=str, default=None,
                        help="RoleAlign calibration JSON (for k_percentile)")
    parser.add_argument("--seq_len", type=int, default=512)
    parser.add_argument("--n_samples", type=int, default=2,
                        help="Number of WikiText samples to average over")
    parser.add_argument("--out_dir", type=str, default="results/attention_viz")
    parser.add_argument("--seed", type=int, default=1234)
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load calibration percentile
    k_percentile = 99.9  # default
    if args.calib_file and Path(args.calib_file).exists():
        with open(args.calib_file) as f:
            calib = json.load(f)
        ra = calib.get("role_aware", {})
        k_percentile = ra.get("k_percentile", 99.9)
        print(f"Using k_percentile={k_percentile} from {args.calib_file}")

    # Load model
    print(f"Loading {args.model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_id, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_id, torch_dtype=torch.float16, device_map="auto",
        trust_remote_code=True,
    )
    model.eval()

    num_layers = model.config.num_hidden_layers
    num_heads = model.config.num_attention_heads
    num_kv_heads = model.config.num_key_value_heads
    head_dim = model.config.hidden_size // num_heads
    sm_scale = 1.0 / (head_dim ** 0.5)
    n_rep = num_heads // num_kv_heads

    print(f"Model: {num_layers}L, {num_heads}H (KV={num_kv_heads}), d={head_dim}")

    # Load data
    print("Loading WikiText-2...")
    data = load_dataset("wikitext", "wikitext-2-raw-v1", split="test")
    samples = []
    for text in data["text"]:
        if len(text.strip()) >= 20:
            enc = tokenizer(text, return_tensors="pt")["input_ids"]
            if enc.size(1) > args.seq_len:
                enc = enc[:, :args.seq_len]
            if enc.size(1) >= 64:  # need some minimum length
                samples.append(enc)
            if len(samples) >= args.n_samples:
                break

    # Storage: [n_samples, n_layers, n_heads, seq_len] for each mode
    all_fp16 = []
    all_int4_sym = []
    all_int4_ra = []
    all_kl_sym = []
    all_kl_ra = []

    print(f"Capturing attention distributions ({len(samples)} samples)...")
    with torch.no_grad():
        for s_idx, input_ids in enumerate(samples):
            input_ids = input_ids.to(model.device)
            outputs = model(input_ids, use_cache=True, output_hidden_states=True)
            hidden_states = outputs.hidden_states
            past_kv = outputs.past_key_values
            if not isinstance(past_kv, tuple) and hasattr(past_kv, "to_legacy_cache"):
                past_kv = past_kv.to_legacy_cache()

            fp16_layers = []
            sym_layers = []
            ra_layers = []
            kl_sym_layers = []
            kl_ra_layers = []

            for l_idx in range(num_layers):
                layer = model.model.layers[l_idx]
                attn = layer.self_attn

                # Get Q for last token (with layernorm + RoPE)
                hs = hidden_states[l_idx][:, -1:, :]
                normed = layer.input_layernorm(hs)
                q = attn.q_proj(normed)
                bsz = q.shape[0]
                q = q.view(bsz, 1, num_heads, head_dim).transpose(1, 2)

                q_norm_fn = getattr(attn, "q_norm", None)
                if q_norm_fn is not None:
                    q = q_norm_fn(q)

                seq_len_val = hidden_states[l_idx].shape[1]
                pos_ids = torch.tensor([[seq_len_val - 1]], device=q.device, dtype=torch.long)
                rope_cos, rope_sin = _get_rope_for_position(attn, q, pos_ids)
                if rope_cos is not None:
                    q = _apply_rope_to_q(q, rope_cos, rope_sin)

                q = q.squeeze(0).squeeze(1).float()  # [num_heads, head_dim]

                # Get K from past_key_values (already has RoPE)
                k_full = past_kv[l_idx][0].squeeze(0).float()  # [kv_heads, seq, head_dim]

                # Compute attention for each head
                fp16_heads = []
                sym_heads = []
                ra_heads = []
                kl_sym_head = []
                kl_ra_head = []

                for h_idx in range(num_heads):
                    kv_h = h_idx // n_rep
                    q_h = q[h_idx]  # [head_dim]
                    k_h = k_full[kv_h]  # [seq, head_dim]

                    # FP16 attention
                    logits_fp16 = (q_h @ k_h.T) * sm_scale
                    p_fp16 = torch.softmax(logits_fp16, dim=-1)

                    # INT4 symmetric (per-group, group_size=32)
                    k_sym = quantize_dequantize_symmetric(k_h, group_size=32, qmax=7)
                    logits_sym = (q_h @ k_sym.T) * sm_scale
                    p_sym = torch.softmax(logits_sym, dim=-1)

                    # INT4 RoleAlign (per-channel K)
                    k_ra = quantize_dequantize_perchannel_k(k_h, percentile=k_percentile, qmax=7)
                    logits_ra = (q_h @ k_ra.T) * sm_scale
                    p_ra = torch.softmax(logits_ra, dim=-1)

                    # KL divergence
                    eps = 1e-6
                    p_f = p_fp16.clamp(min=eps)
                    p_s = p_sym.clamp(min=eps)
                    p_r = p_ra.clamp(min=eps)
                    kl_s = (p_f * (p_f.log() - p_s.log())).sum().item()
                    kl_r = (p_f * (p_f.log() - p_r.log())).sum().item()

                    fp16_heads.append(p_fp16.cpu().numpy())
                    sym_heads.append(p_sym.cpu().numpy())
                    ra_heads.append(p_ra.cpu().numpy())
                    kl_sym_head.append(kl_s)
                    kl_ra_head.append(kl_r)

                fp16_layers.append(fp16_heads)
                sym_layers.append(sym_heads)
                ra_layers.append(ra_heads)
                kl_sym_layers.append(kl_sym_head)
                kl_ra_layers.append(kl_ra_head)

            all_fp16.append(fp16_layers)
            all_int4_sym.append(sym_layers)
            all_int4_ra.append(ra_layers)
            all_kl_sym.append(kl_sym_layers)
            all_kl_ra.append(kl_ra_layers)
            print(f"  Sample {s_idx+1}/{len(samples)} done")

    # Save KL values (compact) — [n_samples, n_layers, n_heads]
    kl_sym_arr = np.array(all_kl_sym)  # [n_samples, n_layers, n_heads]
    kl_ra_arr = np.array(all_kl_ra)

    # Save attention distributions for one representative sample, selected layers
    # (full distributions are too large for all layers)
    selected_layers = [0, num_layers // 4, num_layers // 2, 3 * num_layers // 4, num_layers - 1]
    selected_layers = sorted(set(selected_layers))

    attn_save = {}
    for l_idx in selected_layers:
        for h_idx in range(min(num_heads, 4)):  # save first 4 heads per layer
            attn_save[f"fp16_L{l_idx}_H{h_idx}"] = all_fp16[0][l_idx][h_idx]
            attn_save[f"int4sym_L{l_idx}_H{h_idx}"] = all_int4_sym[0][l_idx][h_idx]
            attn_save[f"int4ra_L{l_idx}_H{h_idx}"] = all_int4_ra[0][l_idx][h_idx]

    npz_path = out_dir / "attention_distributions.npz"
    np.savez_compressed(
        npz_path,
        kl_sym=kl_sym_arr,
        kl_ra=kl_ra_arr,
        selected_layers=np.array(selected_layers),
        num_layers=num_layers,
        num_heads=num_heads,
        num_kv_heads=num_kv_heads,
        head_dim=head_dim,
        k_percentile=k_percentile,
        **attn_save,
    )
    print(f"Saved: {npz_path} ({npz_path.stat().st_size / 1024:.1f} KB)")

    # Generate preview figure: per-layer mean KL
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        mean_kl_sym = kl_sym_arr.mean(axis=(0, 2))  # [n_layers]
        mean_kl_ra = kl_ra_arr.mean(axis=(0, 2))

        fig, ax = plt.subplots(1, 1, figsize=(8, 3.5))
        x = range(num_layers)
        ax.bar([i - 0.2 for i in x], mean_kl_sym, width=0.4, label="INT4-Symmetric", color="#e74c3c", alpha=0.8)
        ax.bar([i + 0.2 for i in x], mean_kl_ra, width=0.4, label="INT4-RoleAlign", color="#2ecc71", alpha=0.8)
        ax.set_xlabel("Layer Index")
        ax.set_ylabel("Mean KL Divergence (vs FP16)")
        ax.set_title("Attention Distribution Distortion: INT4-Symmetric vs INT4-RoleAlign")
        ax.legend()
        ax.set_yscale("log")
        fig.tight_layout()
        preview_path = out_dir / "attention_preview.pdf"
        fig.savefig(preview_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        print(f"Preview saved: {preview_path}")
    except Exception as e:
        print(f"Preview generation skipped: {e}")

    # Print summary
    print("\n=== Summary ===")
    print(f"Mean KL (INT4-Symmetric vs FP16): {kl_sym_arr.mean():.6f}")
    print(f"Mean KL (INT4-RoleAlign vs FP16): {kl_ra_arr.mean():.6f}")
    print(f"KL reduction ratio: {kl_sym_arr.mean() / max(kl_ra_arr.mean(), 1e-10):.1f}x")
    print(f"\nPer-layer worst KL (Symmetric): layer {mean_kl_sym.argmax()}, KL={mean_kl_sym.max():.6f}")
    print(f"Per-layer worst KL (RoleAlign):  layer {mean_kl_ra.argmax()}, KL={mean_kl_ra.max():.6f}")


if __name__ == "__main__":
    main()
