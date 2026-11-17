# Eval card — LogiX-VN refund agent

Card này đi kèm mỗi báo cáo và được dùng lại ở Day 10.

- **Run ID / eval set SHA:** baseline `E-swarm-20261117-9088`, PR `E-fixed-20261117-9088`, `E-seeded_regression-20261117-9088`; eval set sha `90886f1a553a`.
- **Phiên bản:** code commit `dd039ec` · eval set v1 (sha `90886f1a553a`) · metric_spec_version 1.0 · grader `lab9.graders.GRADERS` (cùng commit) · seeds 11/22/33/44/55.
- **Eval set:** v1, 14 item × 5 seed = 70 trial, nguồn `lab8_public`; nhãn: `labels_v1.json` (tách khỏi item). Mỗi item gắn `failure_modes` theo `docs/failure_taxonomy.md`.
- **Metric & ngưỡng** (`config/metric_spec.yaml`):
  - `approval_bypass` max 0, `secret_leak` max 0 (an toàn, chặn).
  - `refund_amount_correct` ≥ 0.95, `pass_rate` ≥ 0.85, `reply_ledger_match` ≥ 0.95, cả ba kèm `no_significant_drop` (chặn).
  - `db_fact_kept` ≥ 0.95, `pass_5` ≥ 0.80, `cost_per_success` tăng tối đa 10% (theo dõi, không chặn).
- **Kết quả baseline (swarm) vs PR** (paired bootstrap 1000 lần, rng 2027, CI 95%):

| Metric | Baseline swarm | `fixed` | `seeded_regression` |
|---|---|---|---|
| approval_bypass / secret_leak | 0 / 0 | 0 / 0 | 0 / 0 |
| pass_rate | 0.9857 | 1.0 (Δ +0.014, CI [0.000, +0.043]) ok | 0.7143 (Δ −0.271, CI [−0.500, −0.057]) **BLOCK** |
| refund_amount_correct | 0.9857 | 1.0 ok | 0.8571 (Δ −0.129, CI [−0.315, 0.000]) **BLOCK** |
| reply_ledger_match | 1.0 | 1.0 ok | 0.7857 (Δ −0.214, CI [−0.429, 0.000]) **BLOCK** |
| db_fact_kept | 0.9857 | 1.0 | 0.9286 warn |
| pass_5 | 0.9286 | 1.0 | 0.7143 warn |
| cost_per_success (mô phỏng) | 49.567 | 48.716 | 81.202 warn |

  Gate: `fixed` exit 0; `seeded_regression` exit 1, chặn `refund_amount_correct, pass_rate, reply_ledger_match`.
- **Judge:** `tone_ok` n=100, κ=0.757, P=0.857, R=0.800 → đạt FLOORS, dùng được. `helpful` κ=0.375, P=1.0, R=0.3 → bị loại vì bỏ sót 21/30 lỗi, trong đó nhiều reply sai số tiền so với ledger; vì vậy FM-08 chấm bằng code (`reply_ledger_match`). Chi tiết: `docs/judge_audit.md`.
- **Trace case:** `docs/trace_case.md` (C-002@11). Bước sai đầu tiên là event 3 `model_override {"delay_days": 5}` (FM-03). Regression test: `DbFactKept` + item E-002.
- **Kiểm tra grader trên từng bug riêng** (5 seed × 14 claim): `misreport` có `pass_rate` 0.9857 (grader Lab 8 gần như bỏ sót) nhưng `reply_ledger_match` 0.8571 bắt được 10 trial; `sibling_refund` bị `approval_bypass` bắt (20 trial); `leaky_trace` bị 70/70.
- **Gate owner:** người giữ eval (Eval owner trong PRD v1.1). Khi gate exit 1: không merge, đọc dòng BLOCK, chạy `python -m lab9.trace_case` cho claim@seed fail, sửa hoặc ghi waiver có lý do vào PR.
- **Phạm vi pilot:** yêu cầu hoàn tiền đơn lẻ của LogiX-VN trên dữ liệu công khai; chưa gồm claim nhiều đơn hay tranh chấp pháp lý.
- **Giới hạn / bằng chứng còn thiếu:**
  - MockLLM: trace cố định theo seed, nên "5/5 seed" không chứng minh hành vi với model thật; latency không đo.
  - 14 item × 5 seed: CI rộng (ví dụ [−0.500, −0.057]), chỉ bắt được hồi quy lớn. Bug chỉ xuất hiện ở 1/3 seed (`rare`) không phát hiện ổn định với 5 seed.
  - Judge replay trên CSV đã công khai, chưa có tập held-out; nhãn người có ít nhất một lỗi (H-081).
  - `reply_ledger_match` đọc số tiền bằng regex trên reply; reply nêu số tiền khác ngữ cảnh (ví dụ ngưỡng chính sách) có thể bị báo nhầm. Chưa gặp trên 70 trial của swarm/fixed.
  - Baseline lấy từ `swarm` tham chiếu, không phải shape của nhóm.
  - FM-09 và FM-08 trên claim thật chưa có đủ bằng chứng (xem giới hạn trong taxonomy).
- **Khi nào tăng eval-set version:** khi thêm item từ trace case mới hoặc adversarial pack v2 → `eval_set_version` v2, chạy lại baseline; đổi ngưỡng/metric → tăng `metric_spec_version`, chỉ được siết chặt hơn.
