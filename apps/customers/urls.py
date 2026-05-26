from django.urls import path
from . import views

app_name = "customers"

urlpatterns = [
    path("", views.third_party_list, name="customer_list"),
    path("third-parties/new/", views.third_party_create, name="customer_create"),
    path("third-parties/upload/csv/", views.third_party_csv_upload, name="third_party_csv_upload"),
    path("third-parties/<str:third_party_id>/", views.third_party_detail, name="customer_detail"),
    path("third-parties/<str:third_party_id>/breaches/", views.breach_list, name="breach_list"),
    path("third-parties/<str:third_party_id>/edit/", views.third_party_edit, name="customer_edit"),
    path("third-parties/<str:third_party_id>/delete/", views.third_party_delete, name="customer_delete"),
]
