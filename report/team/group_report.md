# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm: BMTD
- Thành viên: xem `TEAM.md` (Vũ Hải Tuấn, Đỗ Duy Bộ, Nguyễn Văn Minh, Phạm Đức Hồng Đức)
- Commit chốt (trùng `report/team/decision_adr.md`): 67294a7

## 2. Mục tiêu và cách tiếp cận

**Bài toán.** Xử lý claim hoàn phí vận chuyển của LogiX-VN theo bốn kiến trúc dùng chung chữ ký `run_claim`, rồi chọn kiến trúc **ít tự chủ nhất mà vẫn làm được việc** dựa trên số đo.

Nhóm coi đây trước hết là bài về **ranh giới**:
- Số tiền, approval và chống ghi trùng do code và host quyết định.
- Model chỉ đọc và soạn chữ.
- Chữ trong ticket là dữ liệu của khách, không phải lệnh.
- Trace là ranh giới bảo mật, không phải công cụ debug.

**Chia việc.** Nhóm 4 người, mỗi người một checkpoint, mỗi người làm trên nhánh riêng:

| Checkpoint | Người phụ trách | Nhánh |
|---|---|---|
| CP1: setup và baseline | Minh | `NguyenVanMinh` |
| CP2: ba shape | Tuấn | `haituan` |
| CP3: handoff, idempotency, crash; tích hợp nhánh | Bộ | `duybo` |
| CP4: crash, approval, security | Minh | `NguyenVanMinh` |
| CP5: benchmark, ablation, ADR | Đức | `hongduc` |

Bộ merge các nhánh lại vào `duybo`.

**Thứ tự làm.**
1. Chạy swarm tham chiếu (shape D, có sẵn) ở CP1 để có baseline: host 54 passed; student 186 failed / 62 passed, đúng như đề dự kiến.
2. Viết workflow (A) trước, vì đây là shape đơn giản nhất và đi qua đủ năm nhánh status. Single (B) và orchestrator (C) dựng trên cùng khuôn đó.
3. CP3 và CP4 bổ sung test tại ranh giới của chính ba shape.
4. CP5 so sánh 4 shape trên cùng điều kiện.

## 3. Giải pháp

Code ba shape nằm ở `src/lab8/shapes/workflow.py`, `single.py`, `orchestrator.py`.

**Phần cả ba shape dùng chung:**
- Đọc claim qua `get_claim_view`, không `SELECT *`.
- Thiếu `order_id` → `needs_info`.
- `lookup_order` theo principal; không thấy đơn → `escalated`.
- Quote bằng `compute_compensation` trên **order row**. Hàm này tự lọc policy cũ và policy tương lai, và lấy số lớn hơn khi cả ship và hỏng hàng cùng đủ điều kiện.
- Quote = 0 → `denied` và không gọi host.
- Quote > 0 → `durability.issue_refund(conn, claim_id, <quote đầy đủ>, crash_at=crash_at)`. Kết quả host suy ra status: `ok` → `resolved`; `conflict` → `failed`; còn lại → `denied` (host tự ghi audit `policy_denied`).
- **Không shape nào đọc số trong ticket**, nên không mắc lỗi `REFERENCE_WEAKNESS` của swarm.
- **Truyền quote đầy đủ, không tự trừ phần đã hoàn:** host tự trừ theo trần của đơn. Nếu shape trừ trước thì T14 bị trừ hai lần.

**Ranh giới code / model:**

| Shape | Model làm gì | Code giữ quyền gì |
|---|---|---|
| A workflow | 1 lần gọi MockLLM `draft` để soạn chữ trả lời | Mọi bước đọc, tính quote, gọi host |
| B single | `decide` trong `run_react(max_steps=8)` chỉ chọn tool đọc (`lookup_order`, `compute_compensation`) | Số tiền lấy từ kết quả tool, không lấy từ model. Sau vòng lặp, code gọi `issue_refund`. Chạm trần 8 bước → `failed` |
| C orchestrator | MockLLM `plan`, `investigate`, `draft` | Handoff qua `make_handoff` với `facts={}`. Investigator chỉ có `lookup_order`, `lookup_refund_history`, `compute_compensation`, chạy với `worker=True` nên tool ghi bị host chặn. Chỉ orchestrator gọi `issue_refund` |

**Handoff được sanitize bằng allowlist trong code, không bằng tóm tắt của LLM.**
- `make_handoff` chỉ giữ các field trong `ALLOWED_FIELDS`, `facts` chỉ giữ `FACT_KEYS`, rồi `sanitize` từ chối nếu còn canary.
- Trace ghi bản handoff đã sanitize, không ghi parent context.

**Trace contract v1.** Mọi nhánh return, kể cả lỗi, đều ghi trace có `run_id` khớp.

| Event | Nội dung |
|---|---|
| `claim` | chỉ `has_order_id` |
| `lookup_order` | `visible`, `reason` |
| `handoff` | bản đã sanitize (chỉ orchestrator) |
| `investigator` | `order_visible`, `order_reason`, `already_refunded_vnd` |
| `react` | tên tool đã gọi, kết quả dừng (chỉ single) |
| `quote` | amount, reason, clause_ids, parts |
| `issue_refund` | `ok`, `reason`, `conflict` |
| `decision` | status, proposal_amount, reason |
| `crash` / `error` | điểm crash, hoặc chỉ tên loại exception |

Cố ý **không** ghi: ticket, claim row (có `parent_secret` và header), order row (có SĐT, địa chỉ, `internal_note`, tên hàng), và message của exception.

**Độ bền.**
- `InjectedCrash` được ghi vào trace rồi `raise` lại, không bị nuốt.
- Mọi lỗi khác trả `failed` (`exception:<TênLỗi>`), vì đề cấm `run_claim` ném exception.
- Idempotency dựa trên khóa `refund:{claim_id}` của host. Demo `python -m lab8.demo.buggy_workflow` in `unsafe refund rows: 2` cho thấy chỉ dùng checkpoint của shape là không đủ.

## 4. Kết quả

Benchmark lấy từ `src/reports/benchmark.json`, với các biến được giữ cố định:
- 14 claim public, seed 11, 22, 33, 44, 55;
- `as_of` 2026-11-15, MockLLM, giá mô phỏng trong `pricing.yaml`;
- mỗi trial một SQLite mới.

| Shape | Pass rate | pass^5 | Seed min–max | Variance | Cost/success (VND mô phỏng) | Mean / p95 steps | Model calls / tool calls (TB) |
|---|---:|---:|---|---:|---:|---|---|
| workflow | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 28.77 | 4.43 / 5 | 1.00 / 2.79 |
| single | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 30.10 | 3.50 / 4 | 3.79 / 2.79 |
| orchestrator | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 48.42 | 4.36 / 5 | 2.93 / 4.64 |
| swarm | 0.986 | 0.929 | 0.929–1.000 | 0.000816 | 49.57 | 2.80 / 3 | 3.00 / 4.66 |

- **Trial duy nhất fail:** `R-swarm-C-002-s55`, lý do `status resolved != denied`. Ở seed 55, swarm tin số "trễ 5 ngày" trong ticket, trong khi order ghi 2 ngày. Workflow ở cùng seed vẫn đúng (`R-workflow-C-002-s55`).
- **Crash safety:** `20/20` (`src/reports/crash.json`).
- **Test của nhóm:**
  - Cổng host trên nhánh tích hợp: 128 passed.
  - Ma trận student: 248/248.
  - Test thêm theo từng checkpoint: CP2 (13 test), CP3 (19 test), CP4 (42 test), CP5 (`test_cp5_benchmark.py`).
- **`python -m lab8.check_submission`:** 0 FAIL.
- **Tự kiểm kiểu hidden:** nhóm chưa có `student_drop/` nên chưa chạy self-check chính thức. Bộ thay thế là 24 claim tự dựng theo các kiểu đề nêu (ticket nói dối, injection, homoglyph, approval hỏng/mượn/hết hạn, đơn đã hoàn, policy cũ…), nhãn viết tay theo `business_rules.md`, chấm bằng `lab8.metrics.trial_pass` trên 5 seed:
  - workflow, single, orchestrator: 120/120;
  - swarm: 119/120.
  
  Đây chỉ là tự kiểm, không thay được điểm hidden chính thức.

**Ablation R4** (workflow so với orchestrator, chỉ đổi shape): chạy lại cho số khớp hoàn toàn với `benchmark.json`.
- Cost/success của orchestrator gấp 1.68 lần workflow.
- Khoảng 94% phần chênh đến từ 1.86 lần gọi tool thêm mỗi trial; token model chỉ chiếm khoảng 1.08 VND.

Quyết định kiến trúc và lý do: xem `report/team/decision_adr.md`. Nhóm chọn **workflow**: cùng độ đúng với B và C trên bộ public, rẻ nhất, số bước dự đoán được, ít bề mặt tự chủ nhất. Phiếu nghiên cứu và ablation: xem `report/team/research_card.md`.

## 5. Khó khăn và cách xử lý

| Khó khăn | Bằng chứng | Cách xử lý |
|---|---|---|
| Python mặc định trên máy là 3.15, đề yêu cầu 3.11–3.13 | `python --version` → `Python 3.15.2`; `py -0p` liệt kê thêm 3.13 | Tạo venv bằng `py -3.13 -m venv .venv` (Python 3.13.17); smoke in `lab8.smoke pass` |
| Lọc test theo shape bị lẫn: `-k single` khớp cả tên test `test_public_single_run_cases` của mọi shape | `-k single` ra `60 failed, 182 passed` dù shape single đã đúng | Dùng `-k "single and not orchestrator and not workflow and not swarm"` → `62 passed` |
| Review code phát hiện shape có thể ném exception (lỗi SQLite, `HandoffError`…) trong khi contract cấm | Báo cáo của reviewer theo spec trích dòng contract: "`run_claim` không được ném exception" | Bọc `run_claim`: `InjectedCrash` vẫn `raise`, lỗi khác trả `failed` kèm trace; thêm `test_broken_store_returns_failed_instead_of_raising` |
| Test đầu tiên xanh ngay, chưa chắc nó bắt được lỗi | — | Chạy test injection trên swarm: fail đúng (`assert 'resolved' == 'denied'`), chứng tỏ test phân biệt được shape tin ticket với shape không tin |
| Merge nhánh làm mất dữ liệu `TEAM.md`: bản trên `haituan` đè bảng đóng góp 4 dòng của `duybo` | `git show origin/duybo:TEAM.md` có 4 dòng, HEAD chỉ còn 1 | Viết lại `TEAM.md` từ báo cáo cá nhân và lịch sử git; `check_submission` → `bảng đóng góp có 4 thành viên` |
| Commit test CP5 `bbb4d01` mới nằm trên `origin/hongduc`, chưa merge vào nhánh nộp | `git branch -a --contains bbb4d01` → chỉ `remotes/origin/hongduc` | Cần merge `origin/hongduc` trước khi chốt commit nộp |

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và các báo cáo cá nhân:
- `report/team/2A202603689_VuHaiTuan.md`: CP2, ba shape (`e9f6961`, `test_cp2_shapes.py`).
- `report/team/2A202603591_DoDuyBo.md`: CP3 và tích hợp nhánh (`2ee89e0`, `test_cp3_handoff_idempotency.py`).
- `report/team/2A202603551_NguyenVanMinh.md`: CP1 và CP4 (`78cc2a0`, `test_cp4_security.py`).
- `report/team/2A202603558_PhamDucHongDuc.md`: CP5 (`357432f`, `bbb4d01`, `test_cp5_benchmark.py`).

## 7. Hạn chế và hướng cải thiện

- **Model:** MockLLM không phải model sản xuất; latency là `unavailable`. Cost là giá mô phỏng (`tool_call_vnd` = 10 và giá token trong `pricing.yaml`), không phải hóa đơn API. Tỉ lệ 1.68 lần phụ thuộc trực tiếp vào bảng giá này.
- **Bộ public không phân biệt được độ đúng:** A, B, C cùng pass 1.000 trên 14 claim, nên quyết định hiện chỉ dựa vào cost.
- **Shape single không thật sự "agentic":** `decide` là máy trạng thái xác định, nên không dao động theo seed như một LLM thật. Variance bằng 0 của B và C phản ánh thiết kế, không chứng minh độ ổn định với model thật.
- **Ablation chưa tách thành phần:** nó đổi cả topology cùng lúc (investigator, handoff, các lần gọi model), chưa tách riêng từng thành phần, và chưa có kiểm định thống kê.
- **Nguồn R4 chưa được kiểm trên bản gốc:** tên paper (EMNLP 2026) lấy từ bảng trong đề; nhóm chưa đọc toàn văn.
- **Điều kiện đổi quyết định:**
  - Hidden (40 claim × 5 seed) cho workflow dưới 0.75.
  - Hoặc workflow thấp hơn rõ rệt so với orchestrator ở các claim cần suy luận mà luật cố định không bắt được (ticket mơ hồ, nhiều đơn, homoglyph).
  
  Khi đó nhóm sẽ so lại pass rate, cost và variance trên cùng claim và cùng seed trước khi đổi.
- **Hướng cải thiện:**
  - Chạy self-check trên `student_drop/` khi có.
  - Tách ablation theo từng thành phần của orchestrator.
  - Thêm test cho policy tương lai và approval của claim khác bằng dữ liệu tự tạo.

## 8. Tài liệu tham khảo

- Đề lab: `README.md`, `CHECKPOINTS.md`, `RUBRIC.md`, `RULES.md`, `SUBMISSION.md`.
- `docs/business_rules.md`, `docs/contracts.md` (output contract, trace contract v1), `docs/metrics.md`, `docs/architecture.md`.
- Code tham chiếu: `src/lab8/shapes/swarm_reference.py`, `src/lab8/durability.py`, `src/lab8/handoff.py`, `src/lab8/runtime.py`.
- R4 · Evaluation confounders: EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* (theo thư viện tham khảo slide 68–69 của buổi lý thuyết; nhóm chưa kiểm bản gốc).
- Công cụ AI: Claude Code và ChatGPT. Cách dùng và cách tự kiểm tra ghi trong báo cáo cá nhân của từng thành viên.
