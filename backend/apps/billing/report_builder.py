import io
from pathlib import Path

from django.conf import settings

# Tone pastel cho file xuất PNG/PDF (US 4.2).
PASTEL_BG = "#fdf6fb"
PASTEL_HEADER_BG = "#f3e0f7"
PASTEL_ACCENT = "#8e5aa8"
PASTEL_TEXT = "#4a3b5c"

_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]


def build_report_data(student, month: int, year: int) -> dict:
    """Dữ liệu báo cáo học phí 1 học viên trong 1 tháng (US 4.1) - dùng chung
    cho cả xem trước (preview) và xuất file (US 4.2) để không lệch số liệu."""
    from apps.attendance.models import Attendance
    from apps.scheduling.models import Session

    sessions = Session.objects.filter(
        student=student, session_date__year=year, session_date__month=month
    ).order_by("session_date", "start_time")

    rows = []
    total_sessions = 0
    for session in sessions:
        try:
            attendance = session.attendance
            row_status = attendance.get_status_display()
            billable = attendance.is_billable
        except Attendance.DoesNotExist:
            row_status = "Chưa điểm danh"
            billable = False
        if billable:
            total_sessions += 1
        rows.append(
            {
                "session_date": session.session_date,
                "start_time": session.start_time,
                "status": row_status,
                "billable": billable,
            }
        )

    return {
        "student_name": student.name,
        "month": month,
        "year": year,
        "sessions": rows,
        "total_sessions": total_sessions,
        "price_per_session": student.price_per_session,
        "total_amount": total_sessions * student.price_per_session,
    }


def _render_html(data: dict) -> str:
    rows_html = "".join(
        f"<tr><td>{r['session_date'].strftime('%d/%m/%Y')}</td>"
        f"<td>{r['start_time'].strftime('%H:%M')}</td>"
        f"<td>{r['status']}</td></tr>"
        for r in data["sessions"]
    ) or "<tr><td colspan='3'>Không có buổi học nào trong tháng này.</td></tr>"

    return f"""
    <html><head><meta charset="utf-8"><style>
    body {{ font-family: sans-serif; background: {PASTEL_BG}; color: {PASTEL_TEXT}; padding: 24px; }}
    h1 {{ color: {PASTEL_ACCENT}; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
    th, td {{ border: 1px solid #e6cdeb; padding: 8px; text-align: left; }}
    th {{ background: {PASTEL_HEADER_BG}; }}
    .total {{ margin-top: 12px; font-size: 1.1em; font-weight: bold; color: {PASTEL_ACCENT}; }}
    </style></head>
    <body>
    <h1>Báo cáo học phí</h1>
    <p>Học viên: <strong>{data['student_name']}</strong></p>
    <p>Tháng: {data['month']:02d}/{data['year']}</p>
    <table>
        <thead><tr><th>Ngày</th><th>Giờ</th><th>Trạng thái</th></tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
    <p class="total">Tổng buổi tính phí: {data['total_sessions']}</p>
    <p class="total">Giá/buổi: {data['price_per_session']:,.0f} đ</p>
    <p class="total">Tổng tiền: {data['total_amount']:,.0f} đ</p>
    </body></html>
    """


def render_pdf(data: dict) -> bytes:
    from weasyprint import HTML

    return HTML(string=_render_html(data)).write_pdf()


def _load_font(size: int):
    from PIL import ImageFont

    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_png(data: dict) -> bytes:
    from PIL import Image, ImageDraw

    title_font = _load_font(22)
    body_font = _load_font(16)
    header_font = _load_font(16)

    width = 640
    row_height = 28
    row_count = max(len(data["sessions"]), 1)
    height = 190 + row_height * (row_count + 1)

    img = Image.new("RGB", (width, height), PASTEL_BG)
    draw = ImageDraw.Draw(img)

    y = 20
    draw.text((20, y), "Báo cáo học phí", fill=PASTEL_ACCENT, font=title_font)
    y += 36
    draw.text((20, y), f"Học viên: {data['student_name']}", fill=PASTEL_TEXT, font=body_font)
    y += 24
    draw.text((20, y), f"Tháng: {data['month']:02d}/{data['year']}", fill=PASTEL_TEXT, font=body_font)
    y += 30

    draw.rectangle([20, y, width - 20, y + row_height], fill=PASTEL_HEADER_BG)
    draw.text((28, y + 5), "Ngày", fill=PASTEL_ACCENT, font=header_font)
    draw.text((180, y + 5), "Giờ", fill=PASTEL_ACCENT, font=header_font)
    draw.text((300, y + 5), "Trạng thái", fill=PASTEL_ACCENT, font=header_font)
    y += row_height

    if data["sessions"]:
        for row in data["sessions"]:
            draw.text((28, y + 5), row["session_date"].strftime("%d/%m/%Y"), fill=PASTEL_TEXT, font=body_font)
            draw.text((180, y + 5), row["start_time"].strftime("%H:%M"), fill=PASTEL_TEXT, font=body_font)
            draw.text((300, y + 5), row["status"], fill=PASTEL_TEXT, font=body_font)
            y += row_height
    else:
        draw.text((28, y + 5), "Không có buổi học nào trong tháng này.", fill=PASTEL_TEXT, font=body_font)
        y += row_height

    y += 12
    draw.text((20, y), f"Tổng buổi tính phí: {data['total_sessions']}", fill=PASTEL_ACCENT, font=body_font)
    y += 24
    draw.text((20, y), f"Giá/buổi: {data['price_per_session']:,.0f} đ", fill=PASTEL_ACCENT, font=body_font)
    y += 24
    draw.text((20, y), f"Tổng tiền: {data['total_amount']:,.0f} đ", fill=PASTEL_ACCENT, font=body_font)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def generate_report(student, month: int, year: int, file_format: str):
    """Xuất báo cáo ra file + lưu MONTHLY_REPORT (US 4.2). Ghi đè bản cũ của
    cùng tháng/học viên (kể cả khi đổi định dạng PDF<->PNG)."""
    from .models import MonthlyReport

    data = build_report_data(student, month, year)
    content = render_pdf(data) if file_format == "pdf" else render_png(data)

    relative_dir = Path("reports") / str(student.id)
    full_dir = Path(settings.MEDIA_ROOT) / relative_dir
    full_dir.mkdir(parents=True, exist_ok=True)

    file_stem = f"{year}-{month:02d}"
    for existing in full_dir.glob(f"{file_stem}.*"):
        existing.unlink()

    relative_path = relative_dir / f"{file_stem}.{file_format}"
    (Path(settings.MEDIA_ROOT) / relative_path).write_bytes(content)

    report, _ = MonthlyReport.objects.update_or_create(
        student=student,
        month=month,
        year=year,
        defaults={
            "total_sessions": data["total_sessions"],
            "total_amount": data["total_amount"],
            "file_url": str(relative_path),
        },
    )
    return report
