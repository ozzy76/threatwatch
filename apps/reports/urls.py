from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("generate/<str:customer_id>/", views.generate_report, name="generate_report"),
    path("customer/<str:customer_id>/", views.report_history, name="report_history"),
    path("download/<str:report_id>/", views.download_report, name="download_report"),
]
