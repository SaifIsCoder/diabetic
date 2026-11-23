# Sprint 7 Audit & Gate Check: Backend Architecture & Performance

**Sprint:** Sprint 7 (Track 5)  
**Target:** WSGI Concurrency Tuning, TensorFlow Thread Clamping, TFLite Inference Engine Support, and Concurrency Benchmarking  
**Status:** **STAGE B — PLAN & GATE CHECK APPROVED**  
**Date:** 2026-11-23  

---

## 1. Confirmed Audit Findings & Target Defects

1. **PR-07: Gunicorn Micro-Pool Thread Starvation & Healthcheck Timeout**
   - *Confirmed Root Cause:* `gunicorn.conf.py` hardcoded `workers = 2`, `threads = 2`, capping total simultaneous request handling to 4 concurrent connections. External calls to Gemini (15s timeout) or concurrent image decodes easily saturate all 4 threads. Inbound container health checks (`curl http://localhost:5000/api/health`) are blocked in the backlog queue, exceeding the 10s healthcheck timeout and causing orchestrator crashloops.
   - *Proposed Remediation:* Update `gunicorn.conf.py` to support dynamic environment sizing (`GUNICORN_WORKERS`, `GUNICORN_THREADS`) defaulting to `workers = 2`, `threads = 4` (total 8 threads minimum), add `timeout = 60` and `keepalive = 5`, and ensure `/api/health` bypasses heavy worker lock contention.
2. **PERF-01: TFLite Inference Runtime Integration with Bitwise Parity**
   - *Confirmed Root Cause:* The repository contains both `retfound_model.keras` (82.3MB) and `retfound_model.tflite` (28.98MB). Phase 0 ML audit confirmed exact FP32 single-precision parity between Keras and TFLite ($1.19 \times 10^{-7}$ max diff). TFLite runs in ~71ms compared to Keras ~520ms, but backend only loads Keras.
   - *Proposed Remediation:* Implement dual-engine support in `app.py` via `USE_TFLITE` flag (defaulting to Keras with auto-fallback). If `USE_TFLITE` is enabled or `tf.lite.Interpreter` is available, execute inference via TFLite interpreter for up to 7x faster response times, while preserving identical output schemas and numerical classifications.
3. **PERF-03: Unbounded TensorFlow Thread Contention & Memory Spikes**
   - *Confirmed Root Cause:* TensorFlow defaults to spawning as many threadpool workers as host CPU cores per worker process, leading to thread thrashing and memory spikes under concurrent inference.
   - *Proposed Remediation:* Configure `tf.config.threading.set_intra_op_parallelism_threads(2)` and `set_inter_op_parallelism_threads(2)` in `app.py` upon initialization to constrain CPU thread count and stabilize memory consumption under load.

---

## 2. Governance Gate Check

| Action | Nature | Gate Status |
| :--- | :--- | :--- |
| Incurring paid cloud upgrades or changing production capacity | Paid cloud | **BLOCKED — HUMAN APPROVAL REQUIRED** |
| Retraining or replacing underlying model weights | Model replacement | **BLOCKED — HUMAN APPROVAL REQUIRED** |
| Sizing Gunicorn WSGI threads in `gunicorn.conf.py` | Reversible local config | **Auto-proceed** |
| Clamping TensorFlow thread parallelism in `app.py` | Reversible local code | **Auto-proceed** |
| Supporting optional TFLite execution path with Keras fallback | Reversible local code | **Auto-proceed** |
| Automated concurrency benchmark tests in `tests/test_performance_concurrency.py` | Automated tests | **Auto-proceed** |

---

## 3. Implementation Plan & File Locks

- **Exclusive File Owner:** `Backend Performance Engineer` (`teamwork_worker`)
- **Locked Files:**
  - `gunicorn.conf.py`
  - `app.py`
  - `tests/test_performance_concurrency.py`
  - `docs/backend_performance_benchmarks.md`
  - `s:\unimate\diabetic\sprint_7_implementation.md`
- **Rollback Path:**
  - `git checkout -- gunicorn.conf.py app.py`
  - Delete `tests/test_performance_concurrency.py`, `docs/backend_performance_benchmarks.md`, and `sprint_7_implementation.md`
