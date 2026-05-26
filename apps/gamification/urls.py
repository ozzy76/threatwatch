from django.urls import path
from apps.gamification import views

app_name = "gamification"

urlpatterns = [
    path("select-persona/", views.persona_select_view, name="select_persona"),
    path("onboarding/", views.onboarding_view, name="onboarding"),
    path("api/ssl-check/", views.api_ssl_check, name="api_ssl_check"),
    path("overworld/", views.overworld_view, name="overworld"),
    path("node/<str:node_id>/", views.node_play_view, name="node_play"),
    path("world/<str:world_id>/boss/", views.boss_fight_view, name="boss_fight"),
    path("reset/", views.reset_quest_view, name="reset_quest"),
]
