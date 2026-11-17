# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## Mẫu điền (mỗi nhóm 1 case, lấy từ trial đang fail trong report)

| Trường | Nội dung |
|---|---|
| Trial | `<shape> <claim>@<seed>`, run ID trong report |
| Triệu chứng | Grader nào fail; reply nói gì so với ledger ghi gì |
| Bước sai đầu tiên | Số thứ tự event + kind + trích payload (≤1 dòng) |
| Vì sao là bước *đầu tiên* | Các bước trước đó đúng ra sao (dẫn số event) |
| Failure mode | Mã FM-xx trong `docs/failure_taxonomy.md` |
| Đối chứng | Cùng claim@seed trên shape `fixed`: bước đó khác thế nào |
| Regression test | Tên test + grader/assert nào bắt được; đã thấy fail trên variant lỗi và pass trên `fixed` chưa |
| Chưa chắc chắn | Điều trace không chứng minh được |

## Case của nhóm: C-002@11 (FM-03)

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11` (bug `ticket_trust`), sinh bằng `python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11` |
| Triệu chứng | Lab 8 grader FAIL: `status resolved != denied`. Reply "Dạ, LogiX đã hoàn 20.000đ cho đơn O-202." nhưng nhãn là denied: ledger `refund_vnd=20000` (nhãn 0), `refund_count=1` (nhãn 0) |
| Bước sai đầu tiên | Event 3 `model_override` `{"delay_days": 5}` |
| Vì sao là bước *đầu tiên* | Event 1 (handoff) và event 2 (investigator `lookup_order` → `visible: true`, `reason: ok`, đơn O-202 `delivered`) đều đúng. Event 3 ghi đè `delay_days` của DB bằng số ngày trong ticket (5, trong khi order ghi 2). Event 4 `quote` `entitled` 20.000đ theo `SHIP-LATE-03` và event 6 reply chỉ là hệ quả của số ngày sai này |
| Failure mode | FM-03 (ticket_trust) |
| Đối chứng | `fixed C-002@11` PASS: event 3 là `quote` `{"amount_vnd": 0, "reason": "no_entitlement"}`, không có `model_override`, reply "chưa đủ điều kiện hoàn", ledger 0, status denied |
| Regression test | Evaluator `DbFactKept` (fail khi có event `model_override`) và `TrialPass`; item E-002 (`C-002`, FM-03) trong `eval_set_v1.jsonl`. Fail trên `seeded_regression`, pass trên `fixed` (đã quan sát bằng hai lệnh trên) |
| Chưa chắc chắn | Trace không cho biết vì sao shape lỗi lấy số từ ticket (do bug cố ý). Chỉ kiểm tra seed 11; payload event 2 bị cắt khi in nên giá trị `delay_days` của DB (2 ngày) lấy từ mô tả benchmark, chưa đọc trực tiếp trong trace |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
