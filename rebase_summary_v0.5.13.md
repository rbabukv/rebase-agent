# Rebase Summary — v0.5.13

**Branch:** `rebase_20260619045053_cba18f4d_3d30c5d8`  
**Date:** 2026-06-19  
**Upstream base:** `v0.5.13`  
**Internal start:** `a58c0b8d`

## Command

```bash
python /home/rbabu/rebase-agent/agent.py --internal https://github.com/intel-innersource/frameworks.ai.pytorch.sglang --upstream https://github.com/sgl-project/sglang --internal-branch master_next --upstream-branch main --github-repo intel-innersource/frameworks.ai.pytorch.sglang --work-dir /home/rbabu/rebase-agent/workspace --upstream-base v0.5.13 --internal-start a58c0b8d0d --skip-commits 79a1cc8459,ec8728ab14,d973a5865d,57ba3558eb -v
```

## Per-Commit Breakdown

| # | Internal SHA | Rebase SHA | Description | Status | Confidence |
|---|-------------|------------|-------------|--------|------------|
| 1 | [`a58c0b8d`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/a58c0b8d0d1a2da18860bb1630412426e9217c4b) | [`b2754691`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/b275469155224ebcfb603c1f31dac33afad8d40f) | [Internal][DevOps] Create test_sync_branches.yml workflow to sync master_next and v0.1.0_next (#34) | Clean | — |
| 2 | [`79a1cc84`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/79a1cc84597ccc4b4baacbba30d5c0f88cdc1176) | — | [BMG][UT][Basic Server][Basic Infra] Fix hard coded device type in UTs (#28) | Skipped (user-specified) | — |
| 3 | [`d28811dc`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/d28811dcaa27caff6b7b1b76a9c3d3fb84aa3d38) | [`3f270a7a`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/3f270a7a59826f129678244b7d8623bb9ba081ce) | Update pyproject_xpu.toml to use innsersource sgl-kernel-xpu repo (#33) | Clean | — |
| 4 | [`a85a7d3e`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/a85a7d3e94324294f940234c966239984948c9ae) | [`dc1dc8ce`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/dc1dc8cea82449583c946ef61e5382f0d8124f09) | [BMG][UT] backend modified to accomodate xpu (#39) | Clean | — |
| 5 | [`928fa799`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/928fa7992c8d8d38c710fa85f4f3cd53093c4b35) | [`96095ac6`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/96095ac607ed9cb103ece756ff6c9832da552bf2) | [SGLANGT-196] Fix Structured Output Outlines Backend (#41) | Clean | — |
| 6 | [`a2280d67`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/a2280d67337e531d160d178fdaac14f7949be29f) | [`fee35de3`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/fee35de3b5d7d4dd239f1d16808761cb2cb47555) | fix unittests by installing requirements from toml | Clean | — |
| 7 | [`98614bdf`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/98614bdfe67ee551310111d4bbd630c7bd1f84a6) | [`57b89b80`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/57b89b806fda14332686f6cdb1c88d2340b0ffe9) | [SGLANG][UT] Making UTs compatible to run on XPU targets | Conflict | `server_args.py`: 62% |
| 8 | [`ec8728ab`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/ec8728ab14d48589232772ed15a3a420dc9f1c5a) | — | [Workaround]Remove Auto-detect device | Skipped (user-specified) | — |
| 9 | [`9109e10f`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/9109e10f11de0f824457216108fa9aa59d57fb5d) | [`baf408bd`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/baf408bd705ce7c9f55327cb5f411ef486166663) | add fid accuracy benchmark for sglang diffusion | Clean | — |
| 10 | [`c5aef5fd`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/c5aef5fd5ce260b824350d184bc4d275adbeb8cb) | [`301ab273`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/301ab273713ea9f1c750ae4e33ac68b99b22afdd) | Enable topk logits dump to verify accuracy (#65) | Clean | — |
| 11 | [`0d7a6050`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/0d7a60506e49ee0fedca155c0de80681e939bec5) | [`55e5241b`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/55e5241b2e97c4f7d4bd4ea4f69fd282f94f56e3) | Enable benchmark to test with image inputs for Multimodal. | Conflict | `bench_one_batch.py`: 72% |
| 12 | [`2d1b265a`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/2d1b265a718203968e87235be0ca566e9c64827b) | [`95ad0df3`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/95ad0df31ad79dfd6b0b2488cfa9d8d699a3e386) | Make UTs compatible for XPU runs (#67) | Conflict | `server_args.py`: 92% |
| 13 | [`b155fcdc`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/b155fcdc2cda2f60553b491a0cdfebb97f5b46b0) | [`6c7096fb`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/6c7096fbad33be6afa35739630c7bdf312c3644f) | [Workaround] support fp32 in  RotaryEmbedding | Conflict | `server_args.py`: 72% |
| 14 | [`a0b7507d`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/a0b7507d8f959659292667fbfc29e388a857f09c) | — | Support --correctness-test for bench_one_batch | Skipped (revert pair with 3d30c5d8) | — |
| 15 | [`102f0e04`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/102f0e04551400e58bd1395dfe8ddb2cf1906236) | [`c36ab1e2`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/c36ab1e202fce854b24becae543a73983d990e32) | Adding changes for xpu support for test_index_buf_accessor | Conflict | `index_buf_accessor.py`: 72%<br>`test_index_buf_accessor.py`: 90% |
| 16 | [`34031654`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/340316548cc9487b4577da2c642e949b57752531) | [`23c2fc6a`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/23c2fc6a38cdf8e293d2a5f44e53f8fb426dd9c4) | Sync make_local_attention_virtual_batches with upstream vLLM (#110) | Clean | — |
| 17 | [`1c6dd070`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/1c6dd070e8cfa3db9b27dfc6b59bcce109f604fa) | [`f85ab21a`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/f85ab21a1d26dfef50a12975bef418eb2faf4442) | Add Triton fallback for moe_align_block_size (#107) | Conflict | `moe_align_block_size.py`: 62% |
| 18 | [`d973a586`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/d973a5865d3d31bcd6c2224c796f8e5229cd521f) | — | Normalize local page table values (#106) | Skipped (user-specified) | — |
| 19 | [`57ba3558`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/57ba3558eb6af41440859fa88b86769a3ea95eb0) | — | add activation func for ZLM t2i on xpu | Skipped (user-specified) | — |
| 20 | [`57940713`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/57940713c2efd413d34c0279f5c60719e5df6492) | [`44495586`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/44495586c28009977fcb3db4dcf9853c2c25c51a) | Re-export network utilities from sglang.srt.utils package (#125) | Clean | — |
| 21 | [`ca49885f`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/ca49885f12b42eebe4cd98f4d9b8a7bc613078d1) | [`6d1231f2`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/6d1231f21581d4f18ddf66153c2a47f0741fa038) | [SGLANGT-669] SGLang JIT Kernel Support for Intel XPU (#100) | Conflict | `norm.py`: 82% |
| 22 | [`eaae9aed`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/eaae9aedba156cde411c0ac7bbfb4a4ba7f01f8d) | [`528a88a8`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/528a88a8a16f7264d436e80db71a42660af1f778) | [Internal][DevOps]Create sync_CRI_branches.yml‎ (#137) | Clean | — |
| 23 | [`32f003f5`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/32f003f51694a9dace5a49d571d05132b7d0f3e4) | [`c382b88f`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/c382b88f4c89c0848cd4aed7d27c3d172dbbd3ce) | Fix hard-coded CUDA device in Mamba memory pool for XPU support (#141) | Clean | — |
| 24 | [`6e5cce51`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/6e5cce5129feff0964461cdfb80c526d56cbae03) | [`d76072dd`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/d76072dd4afc982b3df4f122abab12e217575908) | [jit_kernel] Add XPU/SYCL support for RoPE kernel (#134) | Clean | — |
| 25 | [`0214f9c7`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/0214f9c7527edf803d903a05c4dfda4cb0926a03) | [`0c7e9016`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/0c7e901672e14cebdd59307dbfdca419aa92a0c8) | Skip redundant moe_sum_reduce for single-expert routing on XPU (#108) | Clean | — |
| 26 | [`61a0890a`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/61a0890a2a37c207034d1e26ceecf926144754f3) | [`0da561d3`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/0da561d3aaeab2f73d16486ec7f79e90073e55f0) | Fixed incorrect indexing for slot 0 compatibility | Conflict (upstream match 61cc70e8 92%) | `bench_one_batch.py`: 62% |
| 27 | [`de0f25ae`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/de0f25ae36b519af880f017a577c277a8d76c119) | [`e8c67364`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/e8c67364bb7a26a89b719cf69e97f5be65cf9f2e) | [Internal][DevOps]Update test_sync_branches.yml (#166) | Clean | — |
| 28 | [`3d30c5d8`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/3d30c5d8dd0fcadd07d94f40ca2904bf5daf184b) | — | Revert "Support --correctness-test for bench_one_batch" | Skipped (revert pair with a0b7507d) | — |

## Summary

| Metric | Value |
|--------|-------|
| Total commits | 28 |
| Clean cherry-picks | 14 |
| Conflicts resolved | 8 |
| **Total skipped** | **6** |
|   ↳ User-specified | 4 |
|   ↳ Revert pair | 2 |
| Total files resolved | 9 |
| Average confidence | **74%** |

## Skipped Commits — Revert Pair Details

| Original SHA | Original Subject | Revert SHA | Revert Subject |
|-------------|-----------------|-----------|---------------|
| [`a0b7507d`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/a0b7507d8f959659292667fbfc29e388a857f09c) | Support --correctness-test for bench_one_batch | [`3d30c5d8`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/3d30c5d8dd0fcadd07d94f40ca2904bf5daf184b) | Revert "Support --correctness-test for bench_one_batch" |

## Files Needing Manual Review (< 70%)

| File | Confidence | Reason | Internal SHA | Rebase SHA |
|------|------------|--------|-------------|------------|
| `python/sglang/srt/server_args.py` | **62%** | min of 1 blocks; lowest: 62% | [`98614bdf`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/98614bdfe67ee551310111d4bbd630c7bd1f84a6) — [SGLANG][UT] Making UTs compatible to run on XPU targets | [`57b89b80`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/57b89b806fda14332686f6cdb1c88d2340b0ffe9) |
| `python/sglang/srt/layers/moe/moe_runner/triton_utils/moe_align_block_size.py` | **62%** | This is a complex merge where the commit's changes (adding triton fallback with _use_triton_moe_align flag) need to coexist with upstream's lora refactoring code. I placed the triton path as the first branch and kept the lora/sgl_kernel logic in the else branch, but the exact intended interaction between these two features is ambiguous. | [`1c6dd070`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/1c6dd070e8cfa3db9b27dfc6b59bcce109f604fa) — Add Triton fallback for moe_align_block_size (#107) | [`f85ab21a`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/f85ab21a1d26dfef50a12975bef418eb2faf4442) |
| `python/sglang/bench_one_batch.py` | **62%** | min of 1 blocks; lowest: 62% | [`61a0890a`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/61a0890a2a37c207034d1e26ceecf926144754f3) — Fixed incorrect indexing for slot 0 compatibility | [`0da561d3`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/0da561d3aaeab2f73d16486ec7f79e90073e55f0) |
