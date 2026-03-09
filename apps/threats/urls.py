from django.urls import path
from . import views

app_name = "threats"

urlpatterns = [
    path("actors/", views.threat_actor_list, name="actor_list"),
    path("actors/<str:actor_id>/", views.threat_actor_detail, name="actor_detail"),
    path("actors/<str:actor_id>/campaigns/<str:campaign_id>/", views.campaign_detail, name="campaign_detail"),
]
