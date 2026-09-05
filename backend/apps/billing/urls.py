from rest_framework.routers import DefaultRouter

from .views import MonthlyReportViewSet

router = DefaultRouter()
router.register("monthly-reports", MonthlyReportViewSet, basename="monthlyreport")

urlpatterns = router.urls
