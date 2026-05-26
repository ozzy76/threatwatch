from django.urls import path, include

urlpatterns = [
    path("accounts/", include("apps.accounts.urls")),
    path("", include("apps.customers.urls")),
    path("threats/", include("apps.threats.urls")),
    path("detections/", include("apps.detections.urls")),
    path("reports/", include("apps.reports.urls")),
    path("", include("apps.fair.urls")),
]

