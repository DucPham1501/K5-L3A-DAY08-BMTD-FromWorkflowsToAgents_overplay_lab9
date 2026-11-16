# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: 67294a7
- Run id dẫn chứng: R-workflow-C-002-s55 (đúng ở seed 55), đối chứng R-swarm-C-002-s55 (swarm fail), cả hai trong src/reports/benchmark.json
- Pass rate / pass^5 / seed min-max / variance: 1.000 / 1.000 / 1.000–1.000 / 0.000000 (bộ public, 14 claim × 5 seed = 70 trial)
- Cost per success (mô phỏng, VND): 28.77
- Crash safety: 20/20 (src/reports/crash.json)
- Secret leak / approval bypass: 0 / 0 trên bộ public (70/70 trial pass, evaluator quét chuỗi cấm trong trace và kết quả); chưa tự kiểm trên student_drop/

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

Nhóm chọn `workflow` (shape A) vì quy trình claim là tuần tự và quyết định bằng luật: đọc claim, tra đơn, tính quote từ order row, rồi gọi `durability.issue_refund`. Trên cùng 14 claim public, cùng 5 seed (11, 22, 33, 44, 55), cùng bảng giá và cùng MockLLM, ba shape nhóm viết (workflow, single, orchestrator) đều đạt pass rate 1.000, pass^5 1.000 và variance 0. Chênh lệch chỉ nằm ở cost/success: workflow 28.77 VND, single 30.10, orchestrator 48.42, swarm 49.57 (số mô phỏng, không phải hóa đơn API). Workflow rẻ nhất, có số bước dự đoán được (trung bình 4.43, p95 5) và chỉ gọi model 1 lần để soạn chữ trả lời. Tiền và approval do code quyết, nên workflow có ít bề mặt tự chủ nhất mà vẫn làm đủ việc. Swarm đạt 0.986 / pass^5 0.929 vì ở seed 55 tin số ngày trong ticket ở claim C-002 (`status resolved != denied`); workflow ở cùng seed vẫn đúng.

## Có đáng đổi lấy multi-agent không

Trên bộ public thì không. Orchestrator và swarm không có pass rate cao hơn, trong khi cost/success cao hơn khoảng 68–72% so với workflow (48.42 và 49.57 so với 28.77). Phần chênh gần như hoàn toàn do số lần gọi tool: workflow 2.79 lần/trial, orchestrator 4.64 lần/trial, với giá tool 10 VND/lần; phần token model chỉ khoảng 0.91 so với 1.99 VND/trial (xem ablation trong `research_card.md`). Quyết định sẽ đảo lại nếu bộ hidden (40 claim × 5 seed) cho thấy workflow dưới 0.75, hoặc thấp hơn rõ rệt so với orchestrator ở các nhóm claim cần suy luận mà luật cố định không bắt được (ví dụ ticket mơ hồ, nhiều đơn, homoglyph). Nếu có khoảng cách pass rate như vậy, nhóm sẽ so lại pass rate trên cùng claim và cùng seed với cost và variance trước khi đổi. Hiện chưa có dữ liệu hidden có nhãn, nên đây là điều kiện chứ chưa phải kết luận.

## Trace và bằng chứng

Trace của workflow ghi các event: `claim` (chỉ `claim_id` và cờ `has_order_id`), `lookup_order` (`visible`, `reason`), `quote` (amount, reason, clause_ids, parts), `issue_refund` (`ok`, `reason`, `conflict`), `decision` (status, proposal_amount, reason), và khi lỗi thì `crash` (điểm crash) hoặc `error` (chỉ tên kiểu exception). Trace luôn được ghi ở mọi nhánh return, kể cả `needs_info`, `escalated`, `denied`, `failed`.

Cố ý **không** ghi: nội dung ticket, order row, số điện thoại, địa chỉ, tên hàng, ghi chú nội bộ, `parent_secret`, header thô, và message của exception (có thể chứa dữ liệu dòng). Lý do là trace là ranh giới bảo mật: grader quét trace và mọi file `<run_id>*` để tìm chuỗi cấm, và các tool đọc chỉ trả field trong allowlist (`get_claim_view`, `lookup_order`). Bằng chứng không lộ secret là evaluator quét trace và kết quả của 70 trial public (không trial nào bị đánh dấu lộ)

## Giới hạn

MockLLM không phải model sản xuất. Latency để `unavailable`. Cost là giá mô phỏng trong `config/pricing.yaml`. Số liệu ở trên là trên 14 claim public; kết luận về hidden (pass rate ≥ 0.75) chưa được xác nhận cho tới khi tự kiểm trên `student_drop/` và grader của giảng viên chấm. Với `workflow`, `single` và `orchestrator` đều pass 1.000 trên public, bộ public không phân biệt được ba shape về độ đúng, nên chênh lệch duy nhất để chọn là cost. Không sửa JSON cho đủ 0.75.
