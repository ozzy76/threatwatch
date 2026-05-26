from django.urls import path
from . import views

app_name = "detections"

urlpatterns = [
    path("for-third-party/<str:third_party_id>/", views.third_party_detections, name="customer_detections"),
]
