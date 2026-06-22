# Báo cáo số liệu local mới nhất - Rehab AI Monitor

*Cập nhật: 22/06/2026 (2026-06-22T19:31:03+07:00). Nguồn dữ liệu: `database/video_list.json`, chọn bằng backend `latest_patient_exercise_videos(..., limit=8)`. Đây là 8 video mới nhất theo từng bệnh nhân và từng bài tập đang hiển thị trên web local.*

## Tóm tắt nhanh

- Số bệnh nhân trong bộ 8 video mới nhất: **4**.
- Tổng video hiển thị: **8** gồm **4 Codman** và **4 bài tập với gậy**.
- Tổng frame video: **52626**; frame hợp lệ/đã chấm: **40574**.
- PASS / NEAR / FAIL / UNKNOWN: **26239 / 6281 / 8054 / 4872**.
- Accuracy AI theo frame hợp lệ: **64.67%**.
- MAE trung bình: **14.38°**; ICC trung bình: **0.000**; F1-score trung bình: **0.828**.

## Bảng 8 video mới nhất trên web

| Bệnh nhân | Bài tập | Video | Tổng frame | Frame hợp lệ | PASS | NEAR | FAIL | UNKNOWN | Accuracy | MAE | ICC | F1-score | Kết luận |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Cao Thị Thường | Codman | 042541_Cao Thị Thường -  Codman.mp4 | 2763 | 2763 | 2321 | 186 | 256 | 0 | 84% | 9.882 | 0 | 0.913 | Đúng |
| Cao Thị Thường | Bài tập với gậy | 042916_Cao Thị Thường - Bài tập với gậy_ftmp.mp4 | 10771 | 3591 | 1914 | 815 | 862 | 0 | 53.30% | 22.585 | 0 | 0.695 | Gần đúng |
| Hoàng Hạnh Nguyên | Codman | Hoàng Hạnh Nguyên - Codman.mp4 | 3348 | 3338 | 3058 | 132 | 148 | 10 | 91.61% | 4.668 | 0 | 0.956 | Đúng |
| Hoàng Hạnh Nguyên | Bài tập với gậy | Hoàng Hạnh Nguyên - Bài tập với gậy.mp4 | 11774 | 11010 | 5951 | 1947 | 3112 | 764 | 54.05% | 25.558 | 0 | 0.702 | Gần đúng |
| Nguyễn Thị Nga | Codman | 162458_Nguyễn Thị Nga - Codman.mp4 | 2628 | 2628 | 2540 | 53 | 35 | 0 | 96.65% | 3.972 | 0 | 0.983 | Đúng |
| Nguyễn Thị Nga | Bài tập với gậy | Nguyễn Thị Nga - Bài tập với gậy.mp4 | 9069 | 9069 | 5071 | 2382 | 1616 | 0 | 55.92% | 22.331 | 0 | 0.717 | Gần đúng |
| Vũ Thị Hòa | Codman | 165504_Vũ Thị Hoà - Codman.mp4 | 2740 | 2740 | 2740 | 0 | 0 | 0 | 100% | 2.881 | 0 | 1 | Đúng |
| Vũ Thị Hòa | Bài tập với gậy | Vũ Thị Hoà - Bài tập với gậy.mp4 | 9533 | 5435 | 2644 | 766 | 2025 | 4098 | 48.65% | 23.199 | 0 | 0.655 | Sai |

## Giai đoạn Codman

Chỉ bài tập **Codman** hiển thị và lưu theo G1/G2/G3. Bài tập với gậy dùng đánh giá tổng thể theo cùng video, không hiển thị thẻ giai đoạn ở đầu ảnh/video.

| Bệnh nhân | Giai đoạn | Sai số | Tổng frame | PASS | NEAR | FAIL | UNKNOWN | Accuracy | MAE | ICC |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Nguyễn Thị Nga | G1 - Khởi đầu | ±45° | 738 | 712 | 26 | 0 | 0 | 78.70% | 12.903 | 0.722 |
| Nguyễn Thị Nga | G2 - Hồi phục | ±30° | 1031 | 955 | 73 | 3 | 0 | 64% | 9.059 | 0.799 |
| Nguyễn Thị Nga | G3 - Chuẩn xác | ±15° | 859 | 417 | 100 | 342 | 0 | 28.80% | 13.689 | 0.706 |
| Vũ Thị Hòa | G1 - Khởi đầu | ±45° | 797 | 796 | 1 | 0 | 0 | 99.90% | 11.398 | 0.752 |
| Vũ Thị Hòa | G2 - Hồi phục | ±30° | 1135 | 1135 | 0 | 0 | 0 | 100% | 10.900 | 0.762 |
| Vũ Thị Hòa | G3 - Chuẩn xác | ±15° | 808 | 255 | 254 | 299 | 0 | 31.60% | 13.495 | 0.710 |

## Cách vận hành dữ liệu hiện tại

- Bệnh nhân upload video: backend lưu video thô vào registry/dataset và thêm bản ghi vào `database/video_list.json` để NCV, bác sĩ/KTV và bệnh nhân đều thấy cùng danh sách.
- NCV chạy phân tích: luồng xử lý gồm mở/transcode video, MediaPipe skeleton, so sánh REF đúng/sai/gần đúng, train/apply ML, xuất video/frames/CSV/JSON, sau đó cập nhật `video_list.json` và thư mục `database/dataset`.
- Bác sĩ/KTV: xem video thô và video đã phân tích nếu NCV đã gửi; hoàn thành phiếu PHCN/NCKH rồi lưu/gửi cho NCV và bệnh nhân.
- Bệnh nhân: xem kết quả video/frames/biểu đồ đã được gửi, khai triệu chứng và theo dõi lịch nhắc.
- Tất cả bảng danh sách trên giao diện đăng nhập hiện lấy từ cùng hàm `dashboard_video_items`, hàm này đã trỏ sang `latest_patient_exercise_videos` để tránh hiển bản cũ.

## File dữ liệu chính

- `database/video_list.json`: nguồn chính cho danh sách video, metrics, frame gallery, đường dẫn video/frames/csv và trạng thái phân tích.
- `database/media_registry.json`: registry media/artifact đã sinh ra, giúp backend tìm lại file video, frames và CSV.
- `database/latest_video_bundle.json`: snapshot bundle mới nhất để web tải nhanh dữ liệu hiển thị.
- `database/doctor_evaluations.json`: phiếu đánh giá PHCN và nhận xét bác sĩ/KTV.
- `database/patient_symptoms.json`: khai báo triệu chứng/VAS của bệnh nhân.
- `database/lich_su_tap_luyen.json`: lịch sử tập luyện và lịch nhắc.
- `database/research_data.json`: dữ liệu phiếu NCKH.
- `database/reference_codman.json`, `database/reference_gay.json`, `database/reference_day.json`: dữ liệu REF mẫu.
- `database/pose_classifier.pkl`, `database/pose_classifier_features.json`: mô hình và đặc trưng ML.
- `database/dataset/`: nơi backend tự đồng bộ kết quả mới nhất theo từng bệnh nhân, chia `videos/`, `frames/`, `csv/`, `json/`, `charts/`, `zip/`.

## Ghi chú đồng bộ

- Khi local hoặc server tạo bản kết quả mới, API export/save sẽ ghi lại metadata và đồng bộ artifact về `database/dataset/<benh_nhan>/<bai_tap>/...`.
- Nút tải trên web lấy file qua backend để người dùng tải xuống máy hiện tại; nếu chạy server công khai thì file tải xuống máy người dùng truy cập.
- Nếu chỉ số nghiên cứu thay đổi sau khi chạy lại, cập nhật lại `video_list.json` trước rồi tạo lại báo cáo này để số liệu khớp biểu đồ, video và frame gallery.
