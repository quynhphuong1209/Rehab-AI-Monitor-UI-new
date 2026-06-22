# Cấu trúc dữ liệu JSON và dataset

*Cập nhật: 22/06/2026. Tài liệu này mô tả các file đang được web FastAPI/React sử dụng trong thư mục `database/`.*

## Nguyên tắc chung

- Dữ liệu nghiệp vụ được lưu bằng JSON phẳng để dễ kiểm tra, sao lưu và đồng bộ.
- `database/video_list.json` là nguồn hiển thị chính cho danh sách video, biểu đồ, frame gallery và số liệu AI.
- Artifact nặng như video, frames, CSV và zip được quản lý qua registry và thư mục `database/dataset/` thay vì trộn trực tiếp vào một thư mục chung.
- Backend luôn đọc bản mới nhất trên đĩa trước khi trả payload dashboard.

## File chính

| File/thư mục | Vai trò | Ghi chú vận hành |
| --- | --- | --- |
| `users.json` | Tài khoản admin, NCV, bác sĩ/KTV và bệnh nhân | Lưu role, thông tin hồ sơ và dữ liệu xác thực. |
| `video_list.json` | Danh sách video và kết quả AI | Chứa video thô, video đã phân tích, metrics PASS/NEAR/FAIL/UNKNOWN, MAE, ICC, F1, đường dẫn frames/csv. |
| `media_registry.json` | Registry artifact media | Backend dùng để tìm video/frames/csv/zip khi render web hoặc tải xuống. |
| `latest_video_bundle.json` | Snapshot bundle mới nhất | Tăng tốc tải dữ liệu video/frames/biểu đồ trên web. |
| `doctor_evaluations.json` | Phiếu đánh giá PHCN/NCKH | Các nút lưu/gửi sẽ ghi lịch sử vào đây. |
| `patient_symptoms.json` | Khai báo triệu chứng/VAS | Hiển thị ở dashboard bác sĩ/KTV và bệnh nhân. |
| `lich_su_tap_luyen.json` | Lịch sử/lịch nhắc tập luyện | Dùng cho tab lịch nhắc nhở và theo dõi tiến độ. |
| `research_data.json` | Dữ liệu nghiên cứu | Dùng cho phiếu NCKH và thống kê NCV. |
| `reference_codman.json`, `reference_gay.json`, `reference_day.json` | REF mẫu | Dùng để so sánh góc vai/khuỷu theo bài tập. |
| `pose_classifier.pkl`, `pose_classifier_features.json` | ML pose classifier | Dùng trong bước train/apply ML. |
| `dataset/` | Kho kết quả mới nhất có cấu trúc | Chia theo bệnh nhân/bài tập, gồm video, frames, csv, json, charts và zip. |

## Cấu trúc `database/dataset/`

```text
database/dataset/
  <benh_nhan>/
    <bai_tap_or_video>/
      videos/     # video thô và video overlay skeleton/ref/ml
      frames/     # ảnh frame đã trích xuất/overlay
      csv/        # tọa độ, metrics hoặc bảng kết quả
      json/       # metadata, summary, manifest
      charts/     # ảnh biểu đồ tải từ web
      zip/        # bundle tải xuống
```

## Luồng cập nhật

1. Bệnh nhân upload video: backend thêm bản ghi vào `video_list.json` và lưu video thô vào dataset.
2. NCV chạy phân tích: backend/worker xuất video overlay, frames, CSV/JSON; cập nhật metrics trong `video_list.json` và registry.
3. Web hiển thị: dashboard lấy danh sách qua `dashboard_video_items`, hiện trỏ sang `latest_patient_exercise_videos` để luôn lấy 8 video mới nhất theo bệnh nhân/bài tập.
4. Người dùng bấm tải/lưu/gửi: API ghi artifact hoặc metadata mới về dataset/JSON, sau đó dashboard đọc lại bản mới nhất.

## Snapshot hiện tại

- Video mới nhất hiển thị: **8**.
- Tổng frame: **52626**.
- PASS / NEAR / FAIL / UNKNOWN: **26239 / 6281 / 8054 / 4872**.
- Accuracy AI theo frame hợp lệ: **64.67%**.
- MAE trung bình: **14.38°**.
- ICC trung bình: **0.000**.
