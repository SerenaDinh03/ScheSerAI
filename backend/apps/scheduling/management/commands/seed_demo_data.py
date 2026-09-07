from datetime import time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.billing.models import MonthlyReport
from apps.notifications.models import Notification
from apps.scheduling.models import Schedule, Session
from apps.students.models import Student
from apps.teacher.models import Teacher

STUDENTS = [
    dict(
        name="Nguyễn Minh Anh",
        dob="2014-03-12",
        start_date="2025-02-01",
        price=250000,
        status=Student.Status.ACTIVE,
        note="Học Toán nâng cao, hơi nhút nhát lúc mới học.",
        day_of_week=4,
        start_time=time(14, 0),
        end_time=time(15, 30),
    ),
    dict(
        name="Trần Bảo Ngọc",
        dob="2013-07-22",
        start_date="2024-11-15",
        price=220000,
        status=Student.Status.ACTIVE,
        note="",
        day_of_week=2,
        start_time=time(16, 0),
        end_time=time(17, 30),
    ),
    dict(
        name="Lê Gia Hân",
        dob="2015-01-05",
        start_date="2025-05-20",
        price=200000,
        status=Student.Status.ACTIVE,
        note="Ba mẹ hay đón trễ 10-15 phút.",
        day_of_week=0,
        start_time=time(17, 0),
        end_time=time(18, 0),
    ),
    dict(
        name="Phạm Đức Huy",
        dob="2012-09-30",
        start_date="2024-08-01",
        price=280000,
        status=Student.Status.ACTIVE,
        note="",
        day_of_week=3,
        start_time=time(19, 0),
        end_time=time(20, 30),
    ),
    dict(
        name="Đỗ Khánh Linh",
        dob="2014-12-18",
        start_date="2025-06-10",
        price=230000,
        status=Student.Status.INACTIVE,
        note="Tạm nghỉ để ôn thi học kỳ.",
        day_of_week=None,
        start_time=None,
        end_time=None,
    ),
    dict(
        name="Vũ Anh Thư",
        dob="2013-04-02",
        start_date="2024-10-05",
        price=240000,
        status=Student.Status.ACTIVE,
        note="",
        day_of_week=1,
        start_time=time(18, 0),
        end_time=time(19, 30),
    ),
]


class Command(BaseCommand):
    help = (
        "Tạo dữ liệu mẫu (học viên, lịch cố định, buổi học, điểm danh, báo cáo học "
        "phí, thông báo) để xem thử giao diện với dữ liệu thật thay vì rỗng. An toàn "
        "chạy lại nhiều lần (idempotent theo tên học viên)."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        teacher = Teacher.load()
        if not teacher.name:
            teacher.name = "Cô Dinh"
            teacher.email = teacher.email or "dinhbuithulinh@gmail.com"
            teacher.save()

        today = timezone.localdate()
        students_by_name = {}

        for data in STUDENTS:
            student, _ = Student.objects.get_or_create(
                teacher=teacher,
                name=data["name"],
                defaults={
                    "dob": data["dob"],
                    "start_date": data["start_date"],
                    "price_per_session": data["price"],
                    "status": data["status"],
                    "note": data["note"],
                },
            )
            students_by_name[data["name"]] = student

            if data["day_of_week"] is None:
                continue

            schedule, created = Schedule.objects.get_or_create(
                student=student,
                day_of_week=data["day_of_week"],
                defaults={
                    "start_time": data["start_time"],
                    "end_time": data["end_time"],
                },
            )
            if created:
                schedule.generate_sessions(weeks_ahead=3)

            # Vài buổi học đã qua để có dữ liệu điểm danh/học phí demo.
            for offset, attendance_status in [(6, "present"), (3, "present"), (1, None)]:
                past_date = today - timedelta(days=offset)
                session, made = Session.objects.get_or_create(
                    student=student,
                    session_date=past_date,
                    start_time=data["start_time"],
                    defaults={"end_time": data["end_time"]},
                )
                if made and attendance_status:
                    session.mark_attendance(attendance_status)

        # 1 buổi dời lịch + 1 buổi vắng để Thông báo có nội dung thật.
        thu = students_by_name.get("Vũ Anh Thư")
        if thu:
            absent_session = Session.objects.filter(
                student=thu, session_date=today - timedelta(days=1)
            ).first()
            if absent_session and not absent_session.has_attendance():
                absent_session.mark_attendance("absent")

        han = students_by_name.get("Lê Gia Hân")
        if han:
            reschedule_target = Session.objects.filter(
                student=han, session_date__gte=today, attendance__isnull=True
            ).first()
            if reschedule_target and reschedule_target.status != Session.Status.RESCHEDULED:
                reschedule_target.reschedule(
                    session_date=reschedule_target.session_date + timedelta(days=1),
                    start_time=reschedule_target.start_time,
                )

        # Báo cáo học phí tháng trước (tạo trực tiếp, không render PDF/PNG thật -
        # tránh phụ thuộc WeasyPrint khi seed dữ liệu demo).
        last_month_date = today.replace(day=1) - timedelta(days=1)
        for name, sessions_count in [("Nguyễn Minh Anh", 8), ("Trần Bảo Ngọc", 7), ("Phạm Đức Huy", 9)]:
            student = students_by_name.get(name)
            if not student:
                continue
            MonthlyReport.objects.get_or_create(
                student=student,
                month=last_month_date.month,
                year=last_month_date.year,
                defaults={
                    "total_sessions": sessions_count,
                    "total_amount": sessions_count * student.price_per_session,
                    "file_url": f"reports/{student.id}/{last_month_date.year}-{last_month_date.month:02d}.pdf",
                },
            )

        if not Notification.objects.filter(teacher=teacher).exists():
            Notification.objects.create(
                teacher=teacher, message="Đã đồng bộ các buổi học mẫu lên hệ thống."
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Đã seed {Student.objects.filter(teacher=teacher).count()} học viên, "
                f"{Session.objects.count()} buổi học, {MonthlyReport.objects.count()} báo cáo, "
                f"{Notification.objects.count()} thông báo."
            )
        )
