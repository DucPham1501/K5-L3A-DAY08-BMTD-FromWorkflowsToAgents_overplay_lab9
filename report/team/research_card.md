# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R4 · Evaluation confounders |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* (theo thư viện tham khảo slide 68–69). URL và loại bằng chứng chưa được nhóm kiểm lại trên bản gốc; cần bổ sung trước khi nộp. |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Theo mô tả trong đề lab: so sánh hiệu quả giữa các hệ multi-agent dễ bị nhiễu bởi prompt, tool, seed và cách tính cost, nên phải giữ cố định các yếu tố đó mới quy được chênh lệch cho topology. Nhóm chưa đọc toàn văn, không mở rộng thêm. |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Setup của nhóm: MockLLM (không phải model sản xuất), 14 claim public, seed 11/22/33/44/55, giá mô phỏng trong `config/pricing.yaml`, mỗi trial một SQLite mới, latency `unavailable`. Kết luận chỉ áp dụng cho setup này. |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Đổi workflow (A) sang orchestrator (C), giữ nguyên mọi thứ khác: pass rate không đổi (1.000), cost/success tăng khoảng 1.5–1.8 lần, chủ yếu do số lần gọi tool tăng (thêm investigator đọc `lookup_refund_history` và đọc lại claim). Chênh lệch do topology, không do seed. |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Cố định: MockLLM, bộ tool đọc, `as_of` 2026-11-15, seed 11,22,33,44,55, 14 claim public, `pricing.yaml`, evaluator `lab8.metrics`. Biến duy nhất đổi: shape (workflow so với orchestrator). Chạy lại benchmark riêng cho hai shape rồi kiểm số có tái lập đúng với `benchmark.json` không (loại seed noise), và tách cost mỗi trial thành phần tool (số tool call × 10 VND) và phần token model. |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Lỗi dự kiến: kết luận sai nếu chênh cost thật ra do seed hoặc do giá khác nhau giữa các shape. Đo bằng cost/success, `seed_variance`, và `mean_tool_calls` / `mean_model_calls` ở `by_shape`. |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn): `python -m lab8.benchmark --shapes workflow,orchestrator --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/ablation_workflow_vs_orchestrator.json` (chạy trong `src/`, sau lệnh benchmark 4 shape ghi `reports/benchmark.json`).
- Run id / file report: `src/reports/ablation_workflow_vs_orchestrator.json`, so với `src/reports/benchmark.json`. Ví dụ run id: `R-workflow-C-001-s11`, `R-orchestrator-C-001-s11`.
- Kết quả so với hypothesis (đúng / sai / không kết luận được), kèm số liệu: **Đúng.** Chạy lại cho số trùng khớp từng chỉ số với `benchmark.json` (pass rate, pass^5, variance, cost, số tool/model call), nên chênh lệch không đến từ seed. Pass rate cùng 1.000, pass^5 cùng 1.000, variance cùng 0. Cost/success: workflow 28.77, orchestrator 48.42 VND, tỉ lệ 1.683 lần, nằm trong khoảng dự đoán. Phân rã mỗi trial: workflow 28.77 = 27.86 (tool, 2.79 lần × 10) + 0.91 (model, 1.0 lần gọi); orchestrator 48.42 = 46.43 (tool, 4.64 lần) + 1.99 (model, 2.93 lần). Tức khoảng 94% phần chênh (19.65 VND) đến từ 1.86 lần gọi tool thêm, chỉ khoảng 1.08 VND từ token model. Chênh lệch cost là do topology thêm bước đọc, không mang lại pass rate cao hơn trên bộ public.
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`. Cost là giá mô phỏng, nên tỉ lệ 1.68 phụ thuộc vào `tool_call_vnd` = 10 và giá token trong `pricing.yaml`. Ablation đổi cả topology gồm nhiều thành phần cùng lúc (investigator, handoff, lần gọi model plan/investigate), chưa tách riêng từng thành phần. Bộ public chỉ có 14 claim và cả hai shape đều pass 1.000, nên ablation không nói được gì về độ đúng trên hidden; chưa có CI hay kiểm định thống kê.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
