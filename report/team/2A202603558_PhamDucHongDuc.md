# Báo cáo cá nhân — 2A202603558_PhamDucHongDuc

## 1. Thông tin thành viên

- Họ tên: Phạm Đức Hồng Đức
- MSSV: 2A202603558
- Email: phamduchongduc15@gmail.com
- GitHub: https://github.com/DucPham1501
- Branch làm việc: `hongduc`

## 2. Phần việc phụ trách

**CP5 — Benchmark, quyết định kiến trúc và báo cáo:** chạy benchmark 4 shape, chạy ablation, điền `report/team/decision_adr.md` và `report/team/research_card.md`.

## 3. Đóng góp cụ thể

- Chạy benchmark chính thức và sinh `src/reports/benchmark.json` (4 shape × 14 claim × 5 seed).
- Quyết định kỹ thuật: chọn `workflow`. Cả `workflow`, `single` và `orchestrator` đều pass 1.000 trên bộ public, nên cost/success là chênh lệch duy nhất: workflow 28.77, single 30.10, orchestrator 48.42, swarm 49.57 VND mô phỏng. Quyết định theo nguyên tắc chọn shape ít tự chủ nhất mà vẫn làm được việc.
- Chạy ablation R4 (workflow so với orchestrator, chỉ đổi shape) và sinh `src/reports/ablation_workflow_vs_orchestrator.json`. Số liệu tái lập đúng với `benchmark.json`. Cost của orchestrator gấp 1.68 lần workflow; khoảng 94% phần chênh đến từ số lần gọi tool (4.64 so với 2.79 lần/trial).
- Điền `report/team/decision_adr.md` (các dòng nhãn và 4 đoạn giải thích) và `report/team/research_card.md` (phiếu R4 và kết quả ablation).
- Thêm test `src/tests/test_cp5_benchmark.py` (11 test): kiểm `benchmark.json` đủ 4 shape × 5 seed × 14 claim, ba shape nhóm pass 1.000, swarm chỉ fail C-002 ở seed 55, workflow rẻ nhất, ADR ghi đúng shape và cost, và ablation tái lập đúng số của benchmark.

## 4. Bằng chứng

Các lệnh chạy trong `src/`:

```bash
python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json
python -m lab8.benchmark --shapes workflow,orchestrator --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/ablation_workflow_vs_orchestrator.json
python -m lab8.check_submission
```

| Shape | Pass | pass^5 | Variance | Min–Max | Cost/success (VND) |
| --- | --- | --- | --- | --- | --- |
| workflow | 1.000 | 1.000 | 0.000000 | 1.000–1.000 | 28.77 |
| single | 1.000 | 1.000 | 0.000000 | 1.000–1.000 | 30.10 |
| orchestrator | 1.000 | 1.000 | 0.000000 | 1.000–1.000 | 48.42 |
| swarm | 0.986 | 0.929 | 0.000816 | 0.929–1.000 | 49.57 |

- Run id dẫn chứng: `R-workflow-C-002-s55` (đúng) và `R-swarm-C-002-s55` (swarm fail, `status resolved != denied`), cả hai đều trong `src/reports/benchmark.json`.
- Ablation: `src/reports/ablation_workflow_vs_orchestrator.json`, so với `src/reports/benchmark.json`.
- Commit hash: chưa có khi viết báo cáo này; ghi hash thật sau khi commit.

## 5. Công cụ AI đã dùng

- Claude Code: chạy benchmark và ablation, soạn bản nháp cho ADR, research card và báo cáo này.
- Cách tự kiểm tra: chạy trực tiếp `lab8.benchmark` và `lab8.check_submission`; đối chiếu số trong ADR và research card với `by_shape` trong `benchmark.json`; kiểm tra run id có trong `benchmark.json`; grep `src/traces/` không thấy `CANARY_SECRET_*` hay `CANARY_INTERNAL_*`.
- Phần chưa kiểm chứng được: nguồn paper R4 (EMNLP 2026, *Rethinking Evaluation of MAS Efficiency*) chỉ lấy tên từ bảng trong đề lab, chưa đọc toàn văn, chưa có URL.

## 6. Tự đánh giá

- Hoàn thành: benchmark, ablation R4, ADR và research card, với số liệu lấy từ file do công cụ sinh ra, không chép tay.
- Giới hạn: kết quả chỉ trên bộ public (14 claim, MockLLM). Chưa tự kiểm trên `student_drop/` nên chưa thể khẳng định pass rate ≥ 0.75 và 0 secret leak trên hidden. Ablation đổi cả topology (investigator, handoff, các lần gọi model) cùng lúc, chưa tách riêng từng thành phần, và chưa có CI hay kiểm định thống kê.
