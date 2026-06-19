"""Role and navigation model constants."""

from __future__ import annotations


ROLE_ADMIN = "Quản trị viên"
ROLE_PATIENT = "Bệnh nhân"
ROLE_DOCTOR_KTV = "Bác sĩ / KTV PHCN"
ROLE_RESEARCHER = "Nghiên cứu viên"

CLINICAL_RESEARCH_ROLES = {ROLE_DOCTOR_KTV, ROLE_RESEARCHER}

DEFAULT_ROLE = ROLE_PATIENT


def main_tab_titles_for_role(role: str | None, *, has_doctor_video_output: bool = False) -> list[str]:
    """Return the main tab contract for each role."""

    if role == ROLE_ADMIN:
        return [
            "🏠 TRANG CHỦ",
            "🛠️ QUẢN TRỊ VIÊN",
            "📚 THÔNG TIN TỔNG HỢP",
            "👥 HỒ SƠ ĐỀ TÀI & ĐỘI NGŨ CHUYÊN GIA",
            "💬 PHẢN HỒI",
        ]
    if role == ROLE_DOCTOR_KTV:
        titles = ["🏠 TRANG CHỦ", "📊 QUẢN LÝ ĐÁNH GIÁ & NCKH"]
        if has_doctor_video_output:
            titles.append("🎬 VIDEO & ẢNH")
        titles += [
            "⏰ LỊCH NHẮC NHỞ",
            "📚 THÔNG TIN TỔNG HỢP",
            "👥 HỒ SƠ ĐỀ TÀI & ĐỘI NGŨ CHUYÊN GIA",
            "📞 THÔNG TIN LIÊN HỆ",
            "💬 PHẢN HỒI",
        ]
        return titles
    if role == ROLE_PATIENT:
        return [
            "🏠 TRANG CHỦ",
            "📊 KẾT QUẢ ĐÁNH GIÁ",
            "⏰ LỊCH NHẮC NHỞ",
            "📚 THÔNG TIN TỔNG HỢP",
            "📞 THÔNG TIN LIÊN HỆ",
            "💬 PHẢN HỒI",
        ]
    return [
        "🏠 TRANG CHỦ",
        "📊 KẾT QUẢ ĐÁNH GIÁ",
        "🔬 PHÂN TÍCH & TRÍCH XUẤT DỮ LIỆU",
        "📚 THÔNG TIN TỔNG HỢP",
        "👥 HỒ SƠ ĐỀ TÀI & ĐỘI NGŨ CHUYÊN GIA",
        "💬 PHẢN HỒI",
    ]


def role_key(role: str | None) -> str:
    text = str(role or "").casefold()
    if "quản" in text or "quan" in text:
        return "admin"
    if "nghiên" in text or "nghien" in text or "ncv" in text:
        return "researcher"
    if "bác" in text or "bac" in text or "ktv" in text:
        return "doctor_ktv"
    return "patient"
