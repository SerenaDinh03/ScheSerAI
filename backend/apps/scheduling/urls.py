from rest_framework.routers import DefaultRouter

from .views import ScheduleViewSet, SessionViewSet

router = DefaultRouter()
router.register("sessions", SessionViewSet, basename="session")
router.register("schedules", ScheduleViewSet, basename="schedule")

urlpatterns = router.urls
