# Judge audit

Chạy (trong `src/`): `python -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 5` (và `judge_helpful_public.csv`). FAIL là lớp dương (judge phải tìm ra lỗi).

| Tiêu chí | n | κ | Precision | Recall | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---|---|---|---|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | Có (cả ba) | **Dùng** |
| helpful | 100 | 0.375 | 1.000 | 0.300 | Không (κ và recall) | **Loại** |

Ma trận nhầm lẫn (human × judge, FAIL = dương):

| Tiêu chí | tp | fp | fn | tn | Tỉ lệ FAIL quan sát | Sau Rogan-Gladen |
|---|---|---|---|---|---|---|
| tone_ok | 24 | 4 | 6 | 66 | 0.28 | 0.30 |
| helpful | 9 | 0 | 21 | 70 | 0.09 | 0.30 |

## ≥5 case audit thủ công
| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú |
|---|---|---|---|---|---|
| 1 | H-081 "Dạ, đơn O-107 chưa đủ điều kiện hoàn theo chính sách hiện hành ạ." (tone) | FAIL | PASS | Judge | Reply lịch sự, đúng chính sách; ghi chú trong CSV nói người đọc nhầm ticket. Cần sửa nhãn người, không phải lỗi judge (fp đáng lẽ là tn) |
| 2 | H-051 "LogiX đã refund 90.000đ cho đơn O-202 ạ." (tone) | FAIL | PASS | Người | CS LogiX cho phép từ "refund"; judge phạt vì tiếng Anh. Lỗi thật của judge (fp) |
| 3 | H-008 "Em đã hoàn tiền cho anh rồi nha, anh check giúp em." (tone) | PASS | FAIL | Người | Xưng "em", "nha" quá suồng sã trong ngữ cảnh khiếu nại; judge coi là thân thiện (fn) |
| 4 | H-070 "...hoàn 90.000đ cho đơn O-909 ạ 😂😂" (tone) | PASS | FAIL | Người | Emoji cười không hợp ngữ cảnh khiếu nại; judge bỏ sót (fn) |
| 5 | H-063 "đã hoàn 20.000đ và sẽ hoàn thêm cho anh/chị ạ." (tone) | PASS | FAIL | Người | Hứa hoàn thêm ngoài kết quả hệ thống; đây là lỗi nội dung hơn là giọng điệu, cho thấy tone_ok bị lẫn tiêu chí |
| 6 | HL-015 "LogiX đã hoàn 55.000đ cho đơn O-112 ạ." (helpful) | PASS | FAIL | Người | Ledger ghi 40.000đ. Reply sai số tiền nhưng judge thấy trôi chảy nên cho qua. Đây chính là FM-08 (misreport) |
| 7 | HL-047 "Ok bạn, đơn O-515 xử lý rồi nhé." (helpful) | PASS | FAIL | Người | Không nêu số tiền hay kết quả cụ thể, không giúp được khách |

## Hành động sửa rubric sau audit
- **tone_ok:** ghi rõ trong rubric rằng từ vay mượn CS LogiX cho phép (như "refund") không bị phạt (case 2); không đòi lời xin lỗi khi reply đã đủ ý ngắn gọn (H-042). Thêm tiêu chí cấm xưng "em/bạn", "nha" và emoji trong khiếu nại (case 3, 4). Tách việc "hứa hoàn thêm" (case 5) khỏi tone, chuyển sang kiểm tra nội dung bằng code. Sửa nhãn H-081 thành PASS-đúng và để một người thứ hai rà lại.
- **helpful:** không sửa rubric để cứu judge này; thay bằng `reply_ledger_match` (code) cho số tiền, và rubric `helpful` chỉ còn kiểm tra reply có nêu kết quả cụ thể (case 7).

## Kết luận
- **helpful bị loại.** Precision 1.0 nhưng recall 0.3 (tp=9, fn=21): judge bỏ sót 21/30 lỗi thật. Trong 21 fn, phần lớn là reply nêu số tiền khác ledger (HL-015, 016, 020, 028… ghi chú "ledger ghi X") và vài reply cộc lốc không có nội dung (HL-047, 091, 097). Judge chấm theo độ lịch sự/trôi chảy nên không thấy sai số. κ 0.375 dưới ngưỡng 0.6. Tỉ lệ FAIL quan sát 0.09 thấp hơn nhiều so với tỉ lệ sau hiệu chỉnh 0.30, tức judge này làm đẹp số liệu.
- **Hệ quả cho thiết kế:** số tiền trong reply phải chấm bằng code so với ledger (metric `reply_ledger_match` cho FM-08, làm ở M3), không dùng LLM judge.
- **tone_ok được dùng** vì đạt cả ba ngưỡng. Lỗi còn lại chủ yếu là xưng hô/emoji (fn) và phạt từ vay mượn hoặc thiếu lời xin lỗi (fp). Nên báo kèm tỉ lệ đã hiệu chỉnh (0.30), không chỉ tỉ lệ quan sát (0.28).
- Rủi ro còn lại: judge chỉ được kiểm trên dữ liệu replay đã công khai; cần nhãn người mới để có held-out thật. Ít nhất một nhãn người sai (H-081) nên κ có thể hơi bị đánh giá thấp. n=100 với 30 FAIL nên khoảng tin cậy còn rộng.
