from pathlib import Path

from docx import Document


SUMMARY = (
    "Phục hồi chức năng tại nhà thiếu giám sát còn thiếu công cụ lượng hóa khách quan. "
    "Nghiên cứu thử nghiệm mô hình thị giác máy tính đánh giá bài tập khớp vai qua video "
    "smartphone, đối chiếu bác sĩ/kỹ thuật viên PHCN. Dữ liệu gồm 4 người bệnh viêm quanh "
    "khớp vai (ICD-10: M75), 8 video: 4 bài con lắc Codman và 4 bài tập với gậy, cập nhật "
    "24/06/2026. Hệ thống dùng MediaPipe Pose trích xuất 33 điểm mốc, tính góc vai-khuỷu, "
    "phân loại PASS/NEAR/FAIL/UNKNOWN theo ngưỡng ±45°/±30°/±15° với Codman và ±30° với "
    "bài gậy, kết hợp Random Forest. Codman đạt ACC 71,2%, PASS+NEAR/tổng frame 89,5%, "
    "F1/ICC 0,75/0,71, MAE/RMSE 13,5°/16,8°, Precision/Recall 0,76/0,74. Bài gậy đạt "
    "ACC 38,7%, PASS+NEAR 47,3%, F1/ICC 0,46/0,55, MAE/RMSE 21,4°/26,8°, "
    "Precision/Recall 0,48/0,44. Accuracy Codman theo ba giai đoạn giảm "
    "85,4%→79,3%→48,0%. Kết quả gợi ý mô hình khả thi cho telerehabilitation, nhưng cần "
    "bổ sung nhận diện bù trừ tư thế và mở rộng mẫu."
)


doc_path = Path("Bao_cao_tom_tat_Rehab_AI_Monitor.docx")
doc = Document(str(doc_path))
doc.paragraphs[7].text = SUMMARY
doc.save(str(doc_path))
print(len(SUMMARY.replace("–", " ").replace("—", " ").split()))
