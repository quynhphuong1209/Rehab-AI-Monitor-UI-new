# Báo cáo số liệu local mới nhất - Rehab AI Monitor

*Cập nhật: 24/06/2026. Nguồn dữ liệu: `database/latest_video_bundle.json` (`updated_at = 2026-06-24T00:36:19.730122+00:00`), `database/video_list.json` và payload chi tiết từ các artifact `frame_data_all.csv`. Đây là 8 video mới nhất theo từng bệnh nhân và từng bài tập đang hiển thị trên web local.*

## Tóm tắt nhanh

- Số bệnh nhân trong bộ 8 video mới nhất: **4**.
- Tổng video hiển thị trong bộ mới nhất: **8**, gồm **4 Codman** và **4 bài tập với gậy**.
- Tổng frame: **45446**; frame hợp lệ không tính UNKNOWN: **41186**.
- PASS / NEAR / FAIL / UNKNOWN: **19663 / 6670 / 14853 / 4260**.
- Accuracy trung bình 8 video: **54.70%**; Accuracy theo frame hợp lệ: **47.74%**.
- MAE trung bình: **17.45°**; ICC trung bình: **0.63**; F1-score trung bình: **0.60**.

## Bảng 8 video mới nhất trên web

| BN | Bệnh nhân | Bài tập | Video | Kết luận | Accuracy | PASS / NEAR / FAIL / UNKNOWN | Tổng frame | Góc vai TB | Góc khuỷu TB | MAE | F1 | ICC | Precision | Recall | Thời gian |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| BN01 | Hoàng Hạnh Nguyên | Codman | `160754_Hoàng Hạnh Nguyên - Codman.mp4` | Gần đúng | 75.31% | 2492 / 479 / 338 / 39 | 3348 | 47.78° | 153.70° | 10.01° | 0.78 | 0.78 | 0.79 | 0.78 | 07:35 - 24/06/2026 |
| BN01 | Hoàng Hạnh Nguyên | Bài tập với gậy | `Hoàng Hạnh Nguyên - Bài tập với gậy.mp4` | Sai | 37.48% | 4373 / 1078 / 6217 / 106 | 11774 | 43.89° | 131.82° | 24.56° | 0.45 | 0.50 | 0.47 | 0.44 | 07:35 - 24/06/2026 |
| BN02 | Nguyễn Thị Nga | Codman | `162458_Nguyễn Thị Nga - Codman.mp4` | Gần đúng | 78.20% | 2055 / 426 / 147 / 0 | 2628 | 54.91° | 155.41° | 11.47° | 0.81 | 0.75 | 0.81 | 0.80 | 07:35 - 24/06/2026 |
| BN02 | Nguyễn Thị Nga | Bài tập với gậy | `Nguyễn Thị Nga - Bài tập với gậy.mp4` | Sai | 44.09% | 3991 / 1981 / 3080 / 17 | 9069 | 57.96° | 131.20° | 21.48° | 0.51 | 0.55 | 0.53 | 0.50 | 07:35 - 24/06/2026 |
| BN03 | Vũ Thị Hòa | Codman | `165504_Vũ Thị Hoà - Codman.mp4` | Đúng | 90.80% | 2488 / 221 / 31 / 0 | 2740 | 37.38° | 155.42° | 11.78° | 0.92 | 0.74 | 0.92 | 0.92 | 07:36 - 24/06/2026 |
| BN03 | Vũ Thị Hòa | Bài tập với gậy | `Vũ Thị Hoà - Bài tập với gậy.mp4` | Sai | 31.74% | 1725 / 470 / 3240 / 4098 | 9533 | 60.09° | 134.34° | 18.63° | 0.40 | 0.61 | 0.42 | 0.39 | 07:36 - 24/06/2026 |
| BN04 | Cao Thị Thường | Codman | `042541_Cao Thị Thường -  Codman.mp4` | Sai | 40.32% | 1114 / 995 / 654 / 0 | 2763 | 87.88° | 146.22° | 20.59° | 0.48 | 0.57 | 0.49 | 0.46 | 07:34 - 24/06/2026 |
| BN04 | Cao Thị Thường | Bài tập với gậy | `042916_Cao Thị Thường - Bài tập với gậy.mp4` | Sai | 39.68% | 1425 / 1020 / 1146 / 0 | 3591 | 48.45° | 132.96° | 21.04° | 0.47 | 0.56 | 0.49 | 0.46 | 07:35 - 24/06/2026 |

## Tóm tắt theo nhóm bài tập

| Chỉ số | Codman | Bài tập với gậy |
| --- | ---: | ---: |
| Tổng frame | 11479 | 33967 |
| Frame hợp lệ | 11440 | 29746 |
| PASS / NEAR / FAIL / UNKNOWN | 8149 / 2121 / 1170 / 39 | 11514 / 4549 / 13683 / 4221 |
| ACC không tính UNKNOWN | 71.2% | 38.7% |
| ACC tính cả UNKNOWN | 71.0% | 33.9% |
| PASS+NEAR trên tổng frame | 89.5% | 47.3% |
| MAE trung bình | 13.47° | 21.42° |
| F1 / ICC trung bình | 0.75 / 0.71 | 0.46 / 0.55 |
| Precision / Recall trung bình | 0.76 / 0.74 | 0.48 / 0.44 |

## Bảng 4b. Chỉ số nghiên cứu đầy đủ theo từng video

Bảng này đưa các chỉ số đang hiển thị trong bảng nghiên cứu/radar của web local vào phần kết quả chính. Nguồn: `research_metrics` trong payload chi tiết video, đọc từ artifact `frame_data_all.csv` và `database/video_list.json`.

| Mã BN | Bệnh nhân | Bài tập | Accuracy | Tổng frame | PASS/NEAR/FAIL/UNKNOWN | Góc vai TB | Góc khuỷu TB | MAE | F1 | ICC | Precision | Recall |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| BN01 | Hoàng Hạnh Nguyên | Codman | 75.31% | 3348 | 2492/479/338/39 | 47.78° | 153.70° | 10.01° | 0.78 | 0.78 | 0.79 | 0.78 |
| BN01 | Hoàng Hạnh Nguyên | Bài tập với gậy | 37.48% | 11774 | 4373/1078/6217/106 | 43.89° | 131.82° | 24.56° | 0.45 | 0.50 | 0.47 | 0.44 |
| BN02 | Nguyễn Thị Nga | Codman | 78.20% | 2628 | 2055/426/147/0 | 54.91° | 155.41° | 11.47° | 0.81 | 0.75 | 0.81 | 0.80 |
| BN02 | Nguyễn Thị Nga | Bài tập với gậy | 44.09% | 9069 | 3991/1981/3080/17 | 57.96° | 131.20° | 21.48° | 0.51 | 0.55 | 0.53 | 0.50 |
| BN03 | Vũ Thị Hòa | Codman | 90.80% | 2740 | 2488/221/31/0 | 37.38° | 155.42° | 11.78° | 0.92 | 0.74 | 0.92 | 0.92 |
| BN03 | Vũ Thị Hòa | Bài tập với gậy | 31.74% | 9533 | 1725/470/3240/4098 | 60.09° | 134.34° | 18.63° | 0.40 | 0.61 | 0.42 | 0.39 |
| BN04 | Cao Thị Thường | Codman | 40.32% | 2763 | 1114/995/654/0 | 87.88° | 146.22° | 20.59° | 0.48 | 0.57 | 0.49 | 0.46 |
| BN04 | Cao Thị Thường | Bài tập với gậy | 39.68% | 3591 | 1425/1020/1146/0 | 48.45° | 132.96° | 21.04° | 0.47 | 0.56 | 0.49 | 0.46 |

## Diễn giải kết quả cập nhật

- Nhóm Codman đang là phần mạnh hơn của hệ thống: ACC không tính UNKNOWN 71.2%, F1 trung bình 0.75, ICC trung bình 0.71. Tuy vậy GĐ3 giảm còn 48.0% khi siết ngưỡng ±15°, nên không nên mô tả kết quả là đạt chuẩn cho mọi giai đoạn.
- Nhóm bài tập với gậy vẫn là phần hạn chế: 4/4 video được xếp Sai, ACC không tính UNKNOWN 38.7%, ACC tính cả UNKNOWN 33.9%. Video BN03 - Vũ Thị Hòa có 4098 frame UNKNOWN và là ca cần ưu tiên kiểm tra lại điều kiện ghi hình.
- Sau cập nhật, nội dung kết quả nên nhấn mạnh khả năng lượng hóa và phát hiện xu hướng hơn là khẳng định độ chính xác lâm sàng tuyệt đối. Các chỉ số F1/ICC/Precision/Recall được ghi như chỉ số nghiên cứu nội bộ của payload web.
- Hướng phát triển tiếp theo là mở rộng sang mô hình Deep Learning: Về hướng phát triển, hệ thống nên được mở rộng từ cách chấm điểm dựa trên ngưỡng góc và đặc trưng thủ công sang các mô hình Deep Learning học trực tiếp chuỗi vận động theo thời gian. Các hướng khả thi gồm CNN-LSTM hoặc TCN để nhận diện mẫu chuyển động theo frame, ST-GCN để học quan hệ không gian-thời gian giữa các điểm khớp, và Transformer/PoseFormer để mô hình hóa toàn bộ chuỗi tư thế trong một lần tập. Khi có thêm nhãn chuyên gia ở mức frame hoặc từng chu kỳ động tác, các mô hình này có thể học phát hiện bù trừ thân người, co gập khuỷu, lệch trục hai tay, che khuất và sai nhịp vận động tốt hơn so với ngưỡng cố định. Trong giai đoạn tiếp theo, có thể kết hợp RGB video với ước lượng tư thế 3D, dữ liệu độ sâu hoặc cảm biến quán tính trên điện thoại để giảm lỗi do camera đơn, đồng thời huấn luyện mô hình cá thể hóa theo từng bệnh nhân nhằm đưa ra phản hồi thời gian thực cho phục hồi chức năng tại nhà.

## Giai đoạn Codman và bài gậy tổng quan

| BN | Bệnh nhân | Bài/GĐ | Ngưỡng | Accuracy | PASS | NEAR | FAIL | UNKNOWN | Tổng frame | MAE | F1 | ICC | Precision | Recall |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| BN01 | Hoàng Hạnh Nguyên | Codman - GĐ1 | ±45° | 98.65% | 876 | 12 | 0 | 0 | 888 | 25.88° | 0.99 | 0.50 | 0.99 | 0.99 |
| BN01 | Hoàng Hạnh Nguyên | Codman - GĐ2 | ±30° | 93.07% | 1223 | 81 | 10 | 0 | 1314 | 20.29° | 0.94 | 0.57 | 0.94 | 0.94 |
| BN01 | Hoàng Hạnh Nguyên | Codman - GĐ3 | ±15° | 35.50% | 393 | 386 | 328 | 39 | 1146 | 22.83° | 0.43 | 0.52 | 0.45 | 0.42 |
| BN01 | Hoàng Hạnh Nguyên | Bài tập với gậy - tất cả khung | ±30° | 37.48% | 4373 | 1078 | 6217 | 106 | 11774 | 24.56° | 0.45 | 0.50 | 0.47 | 0.44 |
| BN02 | Nguyễn Thị Nga | Codman - GĐ1 | ±45° | 98.10% | 723 | 14 | 0 | 0 | 737 | 25.87° | 0.98 | 0.50 | 0.98 | 0.98 |
| BN02 | Nguyễn Thị Nga | Codman - GĐ2 | ±30° | 88.66% | 915 | 115 | 2 | 0 | 1032 | 22.31° | 0.90 | 0.53 | 0.90 | 0.90 |
| BN02 | Nguyễn Thị Nga | Codman - GĐ3 | ±15° | 48.54% | 417 | 297 | 145 | 0 | 859 | 18.79° | 0.55 | 0.60 | 0.56 | 0.54 |
| BN02 | Nguyễn Thị Nga | Bài tập với gậy - tất cả khung | ±30° | 44.09% | 3991 | 1981 | 3080 | 17 | 9069 | 21.48° | 0.51 | 0.55 | 0.53 | 0.50 |
| BN03 | Vũ Thị Hòa | Codman - GĐ1 | ±45° | 100.00% | 787 | 0 | 0 | 0 | 787 | 18.15° | 0.99 | 0.62 | 0.99 | 0.99 |
| BN03 | Vũ Thị Hòa | Codman - GĐ2 | ±30° | 100.00% | 1145 | 0 | 0 | 0 | 1145 | 17.08° | 0.99 | 0.64 | 0.99 | 0.99 |
| BN03 | Vũ Thị Hòa | Codman - GĐ3 | ±15° | 68.81% | 556 | 221 | 31 | 0 | 808 | 14.66° | 0.73 | 0.69 | 0.73 | 0.72 |
| BN03 | Vũ Thị Hòa | Bài tập với gậy - tất cả khung | ±30° | 31.74% | 1725 | 470 | 3240 | 4098 | 9533 | 18.63° | 0.40 | 0.61 | 0.42 | 0.39 |
| BN04 | Cao Thị Thường | Codman - GĐ1 | ±45° | 45.61% | 374 | 313 | 133 | 0 | 820 | 37.98° | 0.52 | 0.50 | 0.54 | 0.51 |
| BN04 | Cao Thị Thường | Codman - GĐ2 | ±30° | 33.92% | 384 | 574 | 174 | 0 | 1132 | 38.51° | 0.42 | 0.50 | 0.44 | 0.41 |
| BN04 | Cao Thị Thường | Codman - GĐ3 | ±15° | 43.90% | 356 | 108 | 347 | 0 | 811 | 33.96° | 0.51 | 0.50 | 0.52 | 0.49 |
| BN04 | Cao Thị Thường | Bài tập với gậy - tất cả khung | ±30° | 39.68% | 1425 | 1020 | 1146 | 0 | 3591 | 21.04° | 0.47 | 0.56 | 0.49 | 0.46 |

## Điểm cần lưu ý

- Video **BN03 - Vũ Thị Hòa - Bài tập với gậy** đã được cập nhật đúng theo web: Accuracy **31.74%**, tổng frame **9533**, PASS/NEAR/FAIL/UNKNOWN **1725 / 470 / 3240 / 4098**, MAE **18.63°**, F1 **0.40**, ICC **0.61**, Precision **0.42**, Recall **0.39**.
- Nhóm Codman ổn định hơn nhóm bài gậy: ACC không tính UNKNOWN **71.2%** so với **38.7%**.
- Bài tập với gậy có UNKNOWN cao chủ yếu do video BN03; cần kiểm soát góc quay, ánh sáng, che khuất và trục đối xứng hai tay khi ghi hình.
