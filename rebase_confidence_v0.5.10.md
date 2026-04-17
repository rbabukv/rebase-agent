# Rebase Confidence Scoring — v0.5.10

**Branch:** `rebase_20260407161516_1519acf3_715f9cb7`  
**Date:** 2026-04-07  
**Upstream base:** `v0.5.10`  
**Internal start:** `d0eec66`

## Per-Commit Breakdown

| # | Internal SHA | Rebase SHA | Description | Status | Confidence |
|---|-------------|------------|-------------|--------|------------|
| 1 | `d0eec662` | `6e728d899` | [Intel XPU] Add XPU Support to apply_vocab_mask #10726 (#1) | Conflict | 82% |
| 2 | `6701f64c` | — | XPU profiler (#2) | Skipped (in upstream) | — |
| 3 | `b9f4fb7f` | `ec5821e20` | [Bugfix]Fix KeyError by syncing global completion template name (#5) | Conflict | 92% |
| 4 | `9ab40059` | `e16512050` | Tests/fix attributeerror error (#6) | Clean | — |
| 5 | `c1c13f0e` | `4f2ec34dd` | Update cutlass_w4a8_moe.py (#10) | Clean | — |
| 6 | `e0326f9b` | `449dcf1b0` | [Intel XPU]Add XPU device support to Triton attention kernel tests (#11) | Clean | — |
| 7 | `f593abfa` | `459d64fe1` | XPU Graph Runner (#3) | Clean | — |
| 8 | `0051723b` | `b21f6eaea` | Add intel_xpu as backend for GptOssForCausalLM (#24) | Conflict | 92% |
| 9 | `d1f11413` | `1f7657c79` | [SGLANGT-180] Create test_sync_branches.yml workflow (#34) | Clean | — |
| 10 | `a32cf48e` | `1be9ba125` | [BMG][UT] Fix hard coded device type in UTs (#28) | Conflict | 72% |
| 11 | `5d2b9c90` | `bf1a06f03` | Add XPU profiler activity support in benchmark (#31) | Conflict | 72% |
| 12 | `584675bb` | `a41935c1e` | Update pyproject_xpu.toml (#33) | Clean | — |
| 13 | `55f32217` | `20d5f46f0` | [BMG][UT] backend modified to accomodate xpu (#39) | Clean | — |
| 14 | `a72140a1` | `09423ee18` | Update page_table for local attn (#44) | Clean | — |
| 15 | `3c27d741` | `8dc5294d6` | [SGLANGT-196] Fix Structured Output Outlines Backend (#41) | Clean | — |
| 16 | `dd8a3c5a` | `0a67a9870` | Revert "Update page_table for local attn (#44)" | Clean | — |
| 17 | `da5a5126` | `a4472d020` | Support determinism on XPU device (#45) | Clean | — |
| 18 | `2da39b3f` | `e5d4eb80b` | Fix XPU compatibility issues in CUDA graph runner (#35) | Conflict | 95%, 97% |
| 19 | `dd1bb668` | `c1e8a80fc` | Fix assertion tolerance for bfloat16 in extend attention test (#55) | Conflict | 95% |
| 20 | `a14f9511` | `369050fd9` | fix unittests by installing requirements from toml | Conflict | 92%, 92%, 90%, 97% |
| 21 | `dff1c7b2` | `af6d2fb2c` | Enable Sglang diffusion with flux.1-dev (#53) | Conflict | 90%, 82%, 72%, 90%, **42%** |
| 22 | `0c02739d` | `03d00279c` | Update forward_moe_native to support GPT-OSS MoE (#36) | Clean | — |
| 23 | `1b76e53b` | `2b33c879f` | [SGLANG][UT] Making UTs compatible to run on XPU targets | Conflict | 85% |
| 24 | `e06961a2` | `109386640` | Squashed commit of the following: | Clean | — |
| 25 | `f6e3541c` | `ff9e113c7` | apply_router_weight_on_input=_is_cuda (#58) | Clean | — |
| 26 | `564c263b` | `8bb59a165` | Revert "apply_router_weight_on_input=_is_cuda (#58)" | Clean | — |
| 27 | `38d45333` | `a9ee0f720` | Enable DeepSeek R1 inference on XPU | Conflict | 90%, 95% |
| 28 | `9f466ccb` | — | Update tuning_fused_moe_triton.py | Skipped (in upstream) | — |
| 29 | `8f861acb` | `95e4b2d17` | integrate rms_norm | Conflict | 82% |
| 30 | `3732daa0` | `b7dc1c467` | add fid accuracy benchmark for sglang diffusion | Clean | — |
| 31 | `ad1b5d73` | `974e12b1e` | Enable topk logits dump to verify accuracy (#65) | Conflict | 72% |
| 32 | `6d7d63d2` | `e0dca07af` | Enable benchmark to test with image inputs for Multimodal | Conflict | 85% |
| 33 | `0816fa87` | `b22071b3f` | Make UTs compatible for XPU runs (#67) | Clean | — |
| 34 | `e7d99d97` | `9fbb42a35` | Update fused_moe.py to revert temporary changes | Clean | — |
| 35 | `52152319` | — | Adding correct path for module not found error (#73) | Skipped (in upstream) | — |
| 36 | `a03084a1` | `e4128f3df` | Adding correct path for module not found error (#74) | Conflict | 97% |
| 37 | `cc8342c7` | `a82475e52` | fix multiple prompts generations | Conflict | 100%, **62%** |
| 38 | `7ea2b65f` | `7dd14998a` | [SGLANGT-557] Use device-agnostic helpers for Mamba tests (#77) | Conflict | 95% |
| 39 | `eb59db43` | — | [SGLANGT-557] Use correct tolerance for bf16 test (#85) | Skipped (in upstream) | — |
| 40 | `8ea48734` | `1269ce3e1` | fp32 RotaryEmbedding workaround for XPU | Conflict | **N/A (-1%)** |
| 41 | `d098fa21` | `a980e6f8f` | Support --correctness-test for bench_one_batch | Conflict | 72% |
| 42 | `dcee9fce` | `e4222c49f` | [SGLANGT-666]: skip check count of chunked reqs | Conflict | 72% |
| 43 | `49651e30` | — | router scaling is done in moe_sum_reduce & fix EP | Skipped (in upstream) | — |
| 44 | `76d9e33e` | `da8e18f0c` | add xpu attn backend | Clean | — |
| 45 | `4d0ed336` | `46d40f9d2` | fix interface | Clean | — |
| 46 | `ccb59ae5` | `bc368613c` | fix xpu attn backend interface | Conflict | 90% |
| 47 | `7ee5b21a` | `9637fb10c` | update xpu attention name | Conflict | 95% |
| 48 | `533b0bd6` | `be2d1f7a0` | Adding changes for xpu support for test_index_buf_accessor | Clean | — |
| 49 | `44253471` | `5416f6557` | Added support for xpu for test_index_buf_accessor | Clean | — |
| 50 | `099c3de1` | `81dfac15b` | Added xpu support for test_layernorm | Clean | — |
| 51 | `4f03a1c8` | `379373ee3` | Added support for xpu for test_trtllm_fp8_kv_kernel | Clean | — |
| 52 | `3fd442d8` | `85c5a202d` | Apply suggestion from @Copilot | Clean | — |
| 53 | `c995a855` | `be7f48d00` | Apply suggestion from @Copilot | Clean | — |
| 54 | `a2bdae50` | `aaee641b0` | Update test_index_buf_accessor.py | Clean | — |
| 55 | `cd908b94` | `0225fe158` | Update test_trtllm_fp8_kv_kernel.py | Clean | — |
| 56 | `8ea66cef` | `5f37b1113` | Update test_index_buf_accessor.py | Clean | — |
| 57 | `0a5141df` | `d18d334ef` | Update test_trtllm_fp8_kv_kernel.py | Clean | — |
| 58 | `72f07e60` | `a2dfd1fe9` | [Intel GPU] Upgrade pytorch xpu version to 2.11 (#101) | Conflict | 97%, 92%, 95% |
| 59 | `be71e832` | `5a8183fc4` | Port Sarvam model to XPU (#96) | Conflict | 100% |
| 60 | `7c056bc1` | `1c1e9ff4d` | Added xpu support and device select (#105) | Clean | — |
| 61 | `0dfd45c7` | `cd5563415` | Add Intel XPU support to test_kda_kernels.py (#109) | Clean | — |
| 62 | `610f728b` | `4c1d67dab` | Support apply_router_weight_on_input for llama4 (#103) | Clean | — |
| 63 | `44deed32` | `50b65b103` | Sync make_local_attention_virtual_batches with upstream vLLM (#110) | Conflict | 100% |
| 64 | `f6941927` | `6b2111d32` | Add Triton fallback for moe_align_block_size (#107) | Clean | — |
| 65 | `715f9cb7` | `73ac35e76` | Skip redundant moe_sum_reduce for single-expert routing on XPU (#108) | Clean | — |

## Summary

| Metric | Value |
|--------|-------|
| Total commits | 65 |
| Clean cherry-picks | 33 |
| Skipped (already in upstream) | 5 |
| Conflicts resolved | 27 |
| Total files resolved | 37 |
| Average confidence | **87%** |

## Files Needing Manual Review (< 70%)

| File | Confidence | Internal SHA | Rebase SHA |
|------|------------|-------------|------------|
| `python/sglang/multimodal_gen/runtime/models/dits/flux.py` | **42%** | `dff1c7b2` — Enable Sglang diffusion with flux.1-dev | `af6d2fb2c` |
| `python/sglang/multimodal_gen/runtime/entrypoints/diffusion_generator.py` | **62%** | `cc8342c7` — fix multiple prompts generations | `a82475e52` |
| `python/sglang/srt/layers/rotary_embedding.py` | **N/A** | `8ea48734` — fp32 RotaryEmbedding workaround (confidence marker missing) | `1269ce3e1` |
