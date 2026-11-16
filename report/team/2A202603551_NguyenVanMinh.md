# Báo cáo cá nhân — 2A202603551_NguyenVanMinh

## 1. Thông tin thành viên

- Họ tên: Nguyễn Văn Minh
- MSSV: 2A202603551
- Email: Chưa cập nhật
- GitHub: Chưa cập nhật
- Branch làm việc: `NguyenVanMinh`

## 2. Phần việc phụ trách

- **CP1 — Thiết lập môi trường và kiểm thử ban đầu:** cài Python được hỗ trợ, tạo môi trường ảo, cài dependencies, chạy smoke test và baseline của host/student tests.
- **CP4 — Crash, approval và security:** xây dựng test hồi quy và chạy các cổng an toàn. CP2 do thành viên khác thực hiện; CP3 đã được tích hợp trong code CP2; CP5 chưa thực hiện.

## 3. Đóng góp cụ thể

- Cài Python 3.13.17 trên Windows (giữ nguyên Python 3.15 đã có).
- Tạo `src/.venv` (thư mục này được `.gitignore` bỏ qua).
- Cài `src/requirements.txt`: pytest 8.4.2 và PyYAML 6.0.3.
- Đọc `README.md`, `CHECKPOINTS.md`, `RULES.md`, `RUBRIC.md`, `SUBMISSION.md`, `docs/business_rules.md`, `docs/contracts.md`, `docs/metrics.md`, `src/README.md` và tham khảo `src/lab8/shapes/swarm_reference.py`.
- Kiểm tra quy định: số tiền hoàn phải do code quyết định; phải dùng `durability.issue_refund` để bảo vệ approval, trần hoàn tiền và idempotency; ticket là dữ liệu, không phải lệnh; trace không được ghi secret/PII.
- CP1 không sửa source code. Với CP4, đã bổ sung `src/tests/test_cp4_security.py` (42 test parametrized) để kiểm tra tính an toàn tại ranh giới ba shape. Không chỉnh sửa các file host/policy/grader bị cấm.

## 4. Bằng chứng chạy CP1

Các lệnh được chạy trong `src/` trên branch `NguyenVanMinh`:

```bash
.venv/Scripts/python.exe -m lab8.smoke
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m pytest -q -m student -o addopts= --tb=no
```

Kết quả thực tế (16/11/2026):

| Kiểm tra | Kết quả | Đánh giá |
| --- | --- | --- |
| Interpreter | Python 3.13.17 / Windows AMD64 | Hỗ trợ |
| Smoke | `lab8.smoke pass`; swarm C-001 refund 35.000; trace clean | PASS |
| Host suite | `54 passed, 248 deselected` | PASS |
| Student suite | `186 failed, 62 passed, 54 deselected` | Baseline đúng đề: 3 shape chưa implement |

Student suite được dự kiến sẽ có 186 failure trước CP2 (62 test cho mỗi shape `workflow`, `single`, `orchestrator`); 62 swarm reference tests đã pass. Đây **không phải** báo cáo kết quả đã đạt CP2.

## 4.1. Bằng chứng CP4 — Crash, approval và security (16/11/2026)

Thực hiện trên branch `NguyenVanMinh`, sau khi nhận commit CP2 `e9f6961` của branch `duybo` qua fast-forward merge. Code ba shape đã có durability/handoff; phần bổ sung riêng là các test bảo mật và độ bền.

- File test mới: `src/tests/test_cp4_security.py`, **42 passed**.
- Phủ các trạng thái approval: thiếu, không tồn tại, hết hạn, bị thu hồi, mượn approval của claim khác, amount bằng 0; cả ba shape phải từ chối, không ghi ledger, và ghi audit `policy_denied` tương ứng.
- Kiểm tra trần theo đơn: đã hoàn đủ thì `denied`; quyền lợi tăng lên thì chỉ trả chênh lệch.
- Kiểm tra trace, kết quả, stdout/stderr trên các claim public và seed `11`, `55`, quét secret, PII và raw ticket; có thêm tình huống prompt injection cố tình buộc agent vi phạm chính sách.
- Kiểm tra cả ba điểm crash trên ba shape: `before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`; resume không tạo dòng refund/audit trùng, checkpoint hợp lệ.
- Chạy bản crash suite chính thức để sinh `src/reports/crash.json`: **20/20**.

Lệnh được chạy trong `src/` với interpreter trong `.venv`:

```bash
.venv/Scripts/python.exe -m pytest -q -o addopts= tests/test_cp4_security.py
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m pytest -q -m student -o addopts=
.venv/Scripts/python.exe -m lab8.crash_test --count 20 --out reports/crash.json
```

| Bộ kiểm thử | Kết quả thực tế |
| --- | --- |
| CP4 bổ sung | 42 passed |
| Host suite đầy đủ | 109 passed, 248 deselected |
| Student suite | 248 passed, 109 deselected |
| Crash suite chính thức | `crash_safety 20/20`, không có failed scenario |

Giới hạn: kết quả chỉ xác nhận test local/public; chưa thể khẳng định pass toàn bộ hidden grader. File JSON do CLI sinh ra, không chỉnh tay. Chưa commit/push, cần ghi hash thật vào `TEAM.md` sau khi commit kỹ thuật.

## 5. Công cụ AI đã dùng

- ChatGPT hỗ trợ đọc checklist, thực hiện setup CP1, viết bổ sung test CP4, chạy kiểm thử và tổng hợp bằng chứng.
- Cách kiểm chứng: chạy trực tiếp `lab8.smoke`, các bộ pytest, các test CP4 mới và crash suite 20 điểm; đối chiếu với `CHECKPOINTS.md` và `src/reports/crash.json`.

## 6. Tự đánh giá và việc còn thiếu

- Hoàn thành phần kỹ thuật của CP1: môi trường chạy được, smoke và host suite xanh.
- `TEAM.md` vẫn cần tên nhóm, repo nộp, email/GitHub và phân công/đóng góp của các thành viên khác.
- CP2 đã được tích hợp từ branch `duybo`; CP3 và CP4 đạt kiểm thử local. CP5 chưa triển khai: cần benchmark và hoàn thiện báo cáo nhóm bằng kết quả thực tế.
