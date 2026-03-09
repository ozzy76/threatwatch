from django.urls import path
from . import views

app_name = "customers"

urlpatterns = [
    path("", views.customer_list, name="customer_list"),
    path("customers/new/", views.customer_create, name="customer_create"),
    path("customers/<str:customer_id>/", views.customer_detail, name="customer_detail"),
    path("customers/<str:customer_id>/breaches/", views.breach_list, name="breach_list"),
    path("customers/<str:customer_id>/edit/", views.customer_edit, name="customer_edit"),
    path("customers/<str:customer_id>/delete/", views.customer_delete, name="customer_delete"),
]
