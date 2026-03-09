from django.urls import path
from . import views

app_name = "detections"

urlpatterns = [
    path("for-customer/<str:customer_id>/", views.customer_detections, name="customer_detections"),
]
