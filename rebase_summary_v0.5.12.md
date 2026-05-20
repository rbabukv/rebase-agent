# Rebase Summary — v0.5.12

**Branch:** `rebase_20260520101051_25f2e430_4cc6f624`  
**Date:** 2026-05-20  
**Upstream base:** `v0.5.12`  
**Internal start:** `1519acf`

## Command

```bash
python /home/rbabu/rebase-agent/agent.py --internal https://github.com/intel-innersource/frameworks.ai.pytorch.sglang --upstream https://github.com/sgl-project/sglang --internal-branch master_next --upstream-branch main --github-repo intel-innersource/frameworks.ai.pytorch.sglang --work-dir /home/rbabu/rebase-agent/workspace --upstream-base v0.5.12 --internal-start 1519acf --skip-commits 1519acf,f678e997,4b172f2c,14c79c0a,087a1449,615596c5,7c85481e,1c428612,b5fd30ce,87a5f428,e483a64d,3166c01f,3a7e43c0,d3c336fc,10dc37d6,4efdd7df,daa66e72,1d57bc81,76754ff3,19e16eab,b58a077e -v
```

## Per-Commit Breakdown

| # | Internal SHA | Rebase SHA | Description | Status | Confidence |
|---|-------------|------------|-------------|--------|------------|
| 1 | [`1519acf3`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/1519acf37c23f2189adb93f57ca9cd2db1bebf18) | — | [Hotfix] Fix router gemm on sm103 (#22134) | Skipped (user-specified) | — |
| 2 | [`f678e997`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/f678e997f68f39b26589b2be9d9ae3d6209b7aa7) | — | XPU Graph Runner (#3) | Skipped (user-specified) | — |
| 3 | [`4b172f2c`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/4b172f2ce140b703c91271b544bdee2b790f37c9) | — | Add intel_xpu as backend for GptOssForCausalLM, enabled for bf16 dtype (#24) | Skipped (user-specified) | — |
| 4 | [`443d15cd`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/443d15cd7da6de0926bc308d79a04567416ba4e2) | [`d669dcd7`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/d669dcd742c5e0c04a5eee4a14c9e3f12efda64c) | [SGLANGT-180] Create test_sync_branches.yml workflow to sync master_next and v0.1.0_next (#34) | Clean | — |
| 5 | [`511817a1`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/511817a1e80d697afe36b7884cb3a953f57d7c2b) | [`be221b26`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/be221b26e68e65aeab3f716c8e0d963a72863bfd) | [BMG][UT][Basic Server][Basic Infra] Fix hard coded device type in UTs (#28) | Clean | — |
| 6 | [`ace02cc8`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/ace02cc81cd3b135bfce6a56b2f82a17f0273348) | [`1d3e0bc7`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/1d3e0bc7308949f8b715b3424704403c9a12ee7e) | Update pyproject_xpu.toml to use innsersource sgl-kernel-xpu repo (#33) | Clean | — |
| 7 | [`6f6f5aef`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/6f6f5aef5bf695e434049fac3ae0431fb51370b2) | [`85f9073a`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/85f9073a61bc41e06fa8307329131fc470433029) | [BMG][UT] backend modified to accomodate xpu (#39) | Clean | — |
| 8 | [`70d11ed5`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/70d11ed54d1b1780a5ceb9c328e26ee0c969736f) | [`a5157b8c`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/a5157b8c1a6abbeb8bfad3760ef5d24c98aa0ca9) | [SGLANGT-196] Fix Structured Output Outlines Backend (#41) | Clean | — |
| 9 | [`4efdd7df`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/4efdd7df6e1b43593eaee158b1bd957b0514a8aa) | — | Support determinism on XPU device (#45) | Skipped (user-specified) | — |
| 10 | [`daa66e72`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/daa66e72483bdf268374ed981890f6851458cf71) | — | Fix XPU compatibility issues in CUDA graph runner and model layers (#35) | Skipped (user-specified) | — |
| 11 | [`dd9f409e`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/dd9f409efa12414dad22c9e7e2bbf2da054a9b45) | [`3b65d7a5`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/3b65d7a5190d3ae142393b9e3632ac2716dd9f22) | fix unittests by installing requirements from toml | Clean | — |
| 12 | [`14c79c0a`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/14c79c0a4176db0a0f0b635f97f69622da9e496d) | — | Enable Sglang diffusion with flux.1-dev  (#53) | Skipped (user-specified) | — |
| 13 | [`1d57bc81`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/1d57bc81a91a76b9a0773ee5f2aaf62cadf9b6c3) | — | Update forward_moe_native to support GPT-OSS MoE: (#36) | Skipped (user-specified) | — |
| 14 | [`68181181`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/6818118125122829cac41d386145c3633577dda0) | [`a893facf`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/a893facfe20c4ed809ece7035efa7f365dd5ebdb) | [SGLANG][UT] Making UTs compatible to run on XPU targets | Conflict | `server_args.py`: 98% |
| 15 | [`fc350bc0`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/fc350bc0dad596987abd1a2d2b9a2941229d1f24) | [`748b5667`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/748b5667362810492b13bd1410ca2d6b69aa2dac) | Squashed commit of the following: | Clean | — |
| 16 | [`087a1449`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/087a1449995523816df69e941154341166757c63) | — | Enable DeepSeek R1 inference on XPU | Skipped (user-specified) | — |
| 17 | [`615596c5`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/615596c51f1c1214dbc26c6e027bd8a4454ed9fc) | — | integrate rms_norm | Skipped (user-specified) | — |
| 18 | [`6078df23`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/6078df231b92601047d82a76c6632569c18fbb36) | [`11c4a2b8`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/11c4a2b8a8b68ed00ff378d9abca01cd55862358) | add fid accuracy benchmark for sglang diffusion | Clean | — |
| 19 | [`e4c675eb`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/e4c675eb6ea14aa4e4d0e8ccba078e69322712ce) | [`ef1f6bb8`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/ef1f6bb83461bb9d3d26a26731c3d089eea01618) | Enable topk logits dump to verify accuracy (#65) | Clean | — |
| 20 | [`4d65101f`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/4d65101f0a7b223ff4833e2b06e15e4eae53ae97) | [`6bc4f967`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/6bc4f9679c83e073806aeb3729b44212343b1e8f) | Enable benchmark to test with image inputs for Multimodal. | Clean | — |
| 21 | [`441659e2`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/441659e26c19bc4561b0add28ceb18a87465ac7c) | [`0867bd3e`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/0867bd3ebf0794119abe8be2f9a15b41d8c25686) | Make UTs compatible for XPU runs (#67) | Conflict | `test_embed_interpolate_unittest.py`: N/A |
| 22 | [`1c428612`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/1c428612fc5d8746a601de30d283f94c4e23868d) | — | Update fused_moe.py to revert temporary changes | Skipped (user-specified) | — |
| 23 | [`7c85481e`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/7c85481e708e6602e559f1e410fb44b485e2f0bb) | — | fix multiple prompts generations | Skipped (user-specified) | — |
| 24 | [`b5fd30ce`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/b5fd30cecfbe583fd7977512c7b58a015e5d23b0) | — | [SGLANGT-557] Use device-agnostic helpers for Mamba tests (#77) | Skipped (user-specified) | — |
| 25 | [`e377a4aa`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/e377a4aa6605f79b4d0eebcfba3cabae4c5fe5b2) | [`01feb788`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/01feb788db6ce94a4cb4c22fcf919ea18c2e707f) | work around to support fp32 in  RotaryEmbedding until there is a fix for torch.ops.sgl_kernel.rotary_embedding use SGLANG_XPU_USE_ROPE_NATIVE to fall back to native path | Conflict | `server_args.py`: 98% |
| 26 | [`a970dc80`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/a970dc804a0ec6833abfd244c9553ba2594b1bac) | [`5018d545`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/5018d545ecd9ae21ac977ee1950b0bf43e524040) | Support --correctness-test for bench_one_batch | Clean | — |
| 27 | [`76754ff3`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/76754ff31627f02991f9d5871f4639bf71b8bf34) | — | add xpu attn backend | Skipped (user-specified) | — |
| 28 | [`78d08137`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/78d0813741e440ad135cbdc6d0cb096a6e162760) | [`77e48d4a`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/77e48d4a12e5420096fb8a61dd0ff7cb177a43b8) | Adding changes for xpu support for test_index_buf_accessor | Clean | — |
| 29 | [`e483a64d`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/e483a64d6a8d0bce3af3fe1b172f19375b3e4514) | — | [Intel GPU] Upgrade pytorch xpu version to 2.11 (#101) | Skipped (user-specified) | — |
| 30 | [`3166c01f`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/3166c01fae443a0cb1f3f9c750cbf365d5850033) | — | Port Sarvam model to XPU (#96) | Skipped (user-specified) | — |
| 31 | [`19e16eab`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/19e16eab8b0047f137c0682b0e7fba86086c9e75) | — | Added xpu support and device select using get_device function (#105) | Skipped (user-specified) | — |
| 32 | [`b58a077e`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/b58a077eca7ef8d7d03783ae06c7623384fd4591) | — | Add Intel XPU support to test_kda_kernels.py (#109) | Skipped (user-specified) | — |
| 33 | [`87a5f428`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/87a5f4289bf89dbaee1c070ab4d7d66411854a87) | — | Support apply_router_weight_on_input for llama4 for fused_experts (#103) | Skipped (user-specified) | — |
| 34 | [`2e79eb99`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/2e79eb99fe281822977cf6d688a5596c2014ed07) | [`6d870c50`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/6d870c50000df2603bd750e1c8d1b9d037fceab9) | Sync make_local_attention_virtual_batches with upstream vLLM (#110) | Clean | — |
| 35 | [`b14ea4f3`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/b14ea4f3b46766acd468da8affaa8934d7ed7c5c) | [`b6f062a3`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/b6f062a3dfc8d8a65c3b4c546b395fec03c21905) | Add Triton fallback for moe_align_block_size (#107) | Conflict | `moe_align_block_size.py`: 95% |
| 36 | [`c528b5b6`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/c528b5b6185f3270814e3c4e66b992f80bb4c6ff) | [`9a637be4`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/9a637be459a2e004bbf3c8a29c4ef090aad20158) | Skip redundant moe_sum_reduce for single-expert routing on XPU (#108) | Conflict (manual) | `fused_moe.py`: 100% |
| 37 | [`91dd3aeb`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/91dd3aeb73dd4897b373970f6ca1841d7f093664) | [`6c13ec7d`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/6c13ec7db63b9c2c980d0553dc3351719fe6b94c) | Normalize local page table values (#106) | Clean | — |
| 38 | [`87f6a243`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/87f6a243c941729c6626a1edfde9e159bf49050c) | [`d7e1fcaf`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/d7e1fcaf3a55ab98880a2cf84bec249f9de7e6d7) | add activation func for ZLM t2i on xpu | Conflict | `activation.py`: 82% |
| 39 | [`10dc37d6`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/10dc37d6cd9de3d5461f51b3c6cabe98f907281b) | — | Pass alpha and limit params in xpu fused_xperts moe kernel call for GPT-OSS bf16 model (#112) | Skipped (user-specified) | — |
| 40 | [`102465d2`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/102465d29a6ef4b5daf07e02f7c6c296d596839d) | [`2a338cec`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/2a338cec620afb519561caa03dc2dc8e8fb4b4f0) | Re-export network utilities from sglang.srt.utils package (#125) | Clean | — |
| 41 | [`3a7e43c0`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/3a7e43c01646d3e146a818bc5aa82f4de91b1bfd) | — | [Intel GPU] Enable pipeline parallelism on XPU | Skipped (user-specified) | — |
| 42 | [`5fa32f8b`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/5fa32f8b4ab3ca486871f9f3f8435b983dcf101f) | [`4c7ade67`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/4c7ade67a2ff4264922614739304533322e29a39) | [SGLANGT-669] SGLang JIT Kernel Support for Intel XPU (#100) | Clean | — |
| 43 | [`f3ecf86c`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/f3ecf86cc238060297393a9a704ea1b102e8be35) | [`fa95b2f6`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/fa95b2f6211df3508a2fd72f371b5ec9e97bbb93) | Create sync_CRI_branches.yml‎ (#137) | Clean | — |
| 44 | [`d3c336fc`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/d3c336fc8ee80c189f2c3e6e8675509ffc63c0d2) | — | [Intel GPU] Integrate flash_mla_decode in Intel XPU attention backend (#23557) (#69) | Skipped (user-specified) | — |
| 45 | [`afa311fd`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/afa311fdc4f02add9e96d51c003e6d1fecba1111) | [`0f5ac86d`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/0f5ac86d23c50a99d0fc6293ad558acb60727b2d) | Fix hard-coded CUDA device in Mamba memory pool for XPU support (#141) | Clean | — |
| 46 | [`5db666e3`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/5db666e325eb5d62a620f65db0f984c746ec0904) | [`cdba5390`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/cdba5390675026cff6b7195522011bca076f767e) | [jit_kernel] Add XPU/SYCL support for RoPE kernel (#134) | Clean | — |
| 47 | [`4cc6f624`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/4cc6f62476e099960dbe9ceba4736cba89800caa) | [`93163955`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/931639552bb81257ebd486bc1ca2f082e5db4751) | jit_kernel RMSNorm failures on XPU due to unsupported hidden_size validation (#159) | Clean | — |

## Summary

| Metric | Value |
|--------|-------|
| Total commits | 47 |
| Clean cherry-picks | 20 |
| Conflicts resolved | 6 |
| **Total skipped** | **21** |
|   ↳ User-specified | 21 |
| Total files resolved | 6 |
| Average confidence | **94%** |

## Resolution Warnings

| File | Issue | Internal SHA | Rebase SHA |
|------|-------|-------------|------------|
| `test/srt/ascend/test_embed_interpolate_unittest.py` | file not in upstream; removed from commit — review if intended | [`441659e2`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/441659e26c19bc4561b0add28ceb18a87465ac7c) — Make UTs compatible for XPU runs (#67) | [`0867bd3e`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/0867bd3ebf0794119abe8be2f9a15b41d8c25686) |

## Files Needing Manual Review (< 70%)

| File | Confidence | Reason | Internal SHA | Rebase SHA |
|------|------------|--------|-------------|------------|
| `test/srt/ascend/test_embed_interpolate_unittest.py` | **N/A** | file not in upstream; removed from commit — review if intended | [`441659e2`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/441659e26c19bc4561b0add28ceb18a87465ac7c) — Make UTs compatible for XPU runs (#67) | [`0867bd3e`](https://github.com/intel-innersource/frameworks.ai.pytorch.sglang/commit/0867bd3ebf0794119abe8be2f9a15b41d8c25686) |
