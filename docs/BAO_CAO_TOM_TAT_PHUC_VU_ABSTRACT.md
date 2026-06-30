# BÁO CÁO KẾT QUẢ NGẮN GỌN (PHỤC VỤ VIẾT BÁO CÁO TÓM TẮT / ABSTRACT)
*Số liệu mới nhất tính đến 24/06/2026 - nguồn: hệ thống Rehab AI Monitor, snapshot web local `latest_video_bundle.json` cập nhật 2026-06-24.*

## 1. Đối tượng và dữ liệu

- **04 bệnh nhân nữ**, viêm quanh khớp vai (ICD-10: M75), đang điều trị/được theo dõi phục hồi chức năng.
- **08 video nghiên cứu mới nhất** gồm 04 video bài con lắc Codman và 04 video bài tập với gậy.
- AI đã phân tích **45.446 frame**, trong đó **41.186 frame hợp lệ** và **4.260 frame UNKNOWN**.
- Các chỉ số chính lấy từ payload web chi tiết: Accuracy, PASS/NEAR/FAIL/UNKNOWN, góc vai/khuỷu trung bình, MAE, F1-score, ICC, Precision, Recall.

## 2. Kết quả chính của mô hình AI

| Nhóm bài tập | ACC không tính UNKNOWN | ACC tính cả UNKNOWN | PASS+NEAR / tổng frame | MAE TB | F1 TB | ICC TB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Codman | 71.2% | 71.0% | 89.5% | 13.47° | 0.75 | 0.71 |
| Bài tập với gậy | 38.7% | 33.9% | 47.3% | 21.42° | 0.46 | 0.55 |

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

### Bảng chỉ số nghiên cứu đầy đủ theo video

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

## 3. Kết luận phục vụ abstract

Mô hình marker-less (MediaPipe Pose + so sánh góc vai/khuỷu với REF) khả thi để giám sát từ xa các bài tập phục hồi chức năng khớp vai trên video smartphone. Nhóm Codman cho kết quả tốt hơn bài tập với gậy, với ACC không tính UNKNOWN 71.2% so với 38.7% và F1 trung bình 0.75 so với 0.46. Hạn chế chính hiện tại là bài tập với gậy còn nhiều frame FAIL/UNKNOWN, đặc biệt ở video BN03 - Vũ Thị Hòa, nên cần bổ sung kiểm soát góc quay, che khuất và lỗi bù trừ thân người.

Về hướng phát triển, có thể nâng cấp hệ thống bằng các mô hình Deep Learning trên chuỗi tư thế như CNN-LSTM, TCN, ST-GCN hoặc Transformer/PoseFormer để học trực tiếp diễn biến vận động theo thời gian, phát hiện bù trừ thân người và sai trục vận động tốt hơn ngưỡng góc cố định.

**Từ khóa:** Phục hồi chức năng từ xa; trí tuệ nhân tạo; thị giác máy tính; ước lượng tư thế; khớp vai; MediaPipe Pose.
