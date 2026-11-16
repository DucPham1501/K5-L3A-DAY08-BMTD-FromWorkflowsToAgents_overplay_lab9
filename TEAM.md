# Team

## Thông tin nhóm

- Tên nhóm: BMTD
- Lớp: L3A
- Repo nhóm: `K5-L3A-DAY08-BMTD-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt:

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Vũ Hải Tuấn | 2A202603689 | 26ai.tuanvh3@vinuni.edu.vn | [ha1tuan](https://github.com/ha1tuan) | CP2: ba shape workflow, single, orchestrator (kèm phần `crash_at` của CP3) |
|   2 | Đỗ Duy Bộ | 2A202603591 | duybohshl@gmail.com | [flying-bug](https://github.com/flying-bug) | CP3: handoff, idempotency, crash/resume; tích hợp nhánh |
|   3 | Nguyễn Văn Minh | 2A202603551 | minhvjjp@gmail.com | [killy-mv](https://github.com/killy-mv/) | CP1: setup môi trường; CP4: crash, approval, security |
|   4 | Phạm Đức Hồng Đức | 2A202603558 | phamduchongduc15@gmail.com | [DucPham1501](https://github.com/DucPham1501) | CP5: benchmark, ablation, ADR, research card |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Vũ Hải Tuấn (2A202603689) | CP2: ba shape workflow, single, orchestrator | `e9f6961` | `src/tests/test_cp2_shapes.py` (13 test) |
| Đỗ Duy Bộ (2A202603591) | CP3: handoff, idempotency, crash; tích hợp nhánh | `2ee89e0`, `820e659`, `67294a7`, `5552e25`, `e0536db` | `src/tests/test_cp3_handoff_idempotency.py` (19 test) |
| Nguyễn Văn Minh (2A202603551) | CP1: setup; CP4: security, approval, crash testing | `78cc2a0`, `499188e` | `src/tests/test_cp4_security.py` (42 test) |
| Phạm Đức Hồng Đức (2A202603558) | CP5: benchmark, ablation, ADR, research card | `357432f`, `bbb4d01` | `src/tests/test_cp5_benchmark.py` |

## Cá nhân

Báo cáo chi tiết của từng thành viên nằm trong `report/team/`. Tóm tắt dưới đây lấy từ các báo cáo đó.

## 2A202603689_VuHaiTuan

### Phần việc phụ trách

- CP2: viết `src/lab8/shapes/workflow.py`, `single.py`, `orchestrator.py`, cùng chữ ký `run_claim` với swarm.
- Phần CP3 nằm ở dòng gọi refund: truyền `crash_at` vào `durability.issue_refund`, không bắt `InjectedCrash`.

### Đóng góp cụ thể

- **Workflow:** các bước cố định; quote lấy từ order row qua `compute_compensation`, truyền quote đầy đủ cho host.
- **Single:** vòng ReAct tối đa 8 bước; model chỉ chọn tool đọc, còn code giữ quyền tính tiền và ghi refund.
- **Orchestrator:** handoff qua `make_handoff` với `facts={}`, investigator chỉ có tool đọc, chỉ orchestrator ghi refund.
- **Cả ba shape:**
  - ghi trace ở mọi nhánh, không ghi ticket, claim row hay order row;
  - lỗi bất ngờ trả `failed`, không ném exception.
- **Test:** `test_cp2_shapes.py`, kiểm các tình huống:
  - ticket injection;
  - quét secret/PII trong trace;
  - handoff chỉ chứa field allowlist;
  - claim không tồn tại;
  - store hỏng.

### Bằng chứng

- Commit `e9f6961`.
- Ma trận student: 248/248 passed (mỗi shape 62/62).
- Crash suite: 20/20.
- Chi tiết: [report/team/2A202603689_VuHaiTuan.md](report/team/2A202603689_VuHaiTuan.md).

## 2A202603591_DoDuyBo

### Phần việc phụ trách

- CP3: kiểm chứng ghi tiền an toàn khi gọi lại và khi crash, và kiểm handoff không mang secret.
- Tích hợp các nhánh của nhóm và hoàn tất phần máy chấm đọc của CP5: commit hash trong ADR, bảng đóng góp.

### Đóng góp cụ thể

- Rà code ba shape theo từng yêu cầu CP3 (`crash_at`, `InjectedCrash`, quote đầy đủ, handoff allowlist).
- Test `test_cp3_handoff_idempotency.py` (19 test):
  - handoff trong trace chỉ có field allowlist và tool chỉ đọc;
  - chạy 3 lần cùng claim vẫn chỉ có 1 refund;
  - số tiền khác sau khi đã commit → `amount_conflict`, giữ số cũ.
- Merge các nhánh `hongduc` và `NguyenVanMinh` vào `duybo`, ghi hash `67294a7` vào ADR.
- Kiểm tra benchmark tái lập được.
- Tự kiểm 24 claim theo kiểu hidden:
  - workflow, single, orchestrator đều 120/120;
  - swarm 119/120.

### Bằng chứng

- Commit `2ee89e0`, `820e659`, `67294a7`, `5552e25`, `e0536db`.
- Crash rồi resume, 3 shape × 3 điểm crash: mỗi trường hợp đúng 1 dòng ledger và 1 audit `refund_committed`.
- Quét 84 trace: 0 trace vi phạm.
- Chi tiết: [report/team/2A202603591_DoDuyBo.md](report/team/2A202603591_DoDuyBo.md).

## 2A202603551_NguyenVanMinh

### Phần việc phụ trách

- CP1: thiết lập môi trường và baseline kiểm thử.
- CP4: crash, approval và security.

### Đóng góp cụ thể

- Cài Python 3.13 và `.venv`; chạy smoke và baseline. Kết quả: host 54 passed, student 186 failed / 62 passed, đúng như đề dự kiến.
- Test `test_cp4_security.py` (42 test):
  - approval thiếu, không tồn tại, hết hạn, bị thu hồi, mượn của claim khác, amount bằng 0;
  - trần theo đơn;
  - quét secret/PII trong trace và stdout/stderr;
  - prompt injection;
  - 3 điểm crash trên 3 shape.
- Sinh `src/reports/crash.json` bằng crash suite chính thức.

### Bằng chứng

- Commit `78cc2a0`, `499188e`.
- Crash suite: `crash_safety 20/20`.
- Host 109 passed; student 248 passed.
- Chi tiết: [report/team/2A202603551_NguyenVanMinh.md](report/team/2A202603551_NguyenVanMinh.md).

## 2A202603558_PhamDucHongDuc

### Phần việc phụ trách

- CP5: benchmark 4 shape, ablation, quyết định kiến trúc, ADR và research card.

### Đóng góp cụ thể

- Chạy benchmark 4 shape × 14 claim × 5 seed, sinh `src/reports/benchmark.json`.
- Chọn `workflow`: ba shape của nhóm cùng pass 1.000 trên bộ public, nên chọn theo cost/success thấp nhất (28.77 VND mô phỏng).
- Ablation R4 workflow với orchestrator, sinh `src/reports/ablation_workflow_vs_orchestrator.json`. Cost của orchestrator gấp 1.68 lần workflow, phần chênh chủ yếu do số lần gọi tool.
- Điền `decision_adr.md` và `research_card.md`.
- Test `test_cp5_benchmark.py`: kiểm bằng chứng benchmark và ablation đã commit.

### Bằng chứng

- Commit `357432f`, `bbb4d01`.
- Run id `R-workflow-C-002-s55` (đúng) và `R-swarm-C-002-s55` (swarm fail), cả hai trong `src/reports/benchmark.json`.
- Chi tiết: [report/team/2A202603558_PhamDucHongDuc.md](report/team/2A202603558_PhamDucHongDuc.md).
