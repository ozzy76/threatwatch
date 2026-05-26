from django.urls import path
from . import views

app_name = "fair"

urlpatterns = [
    path("risk/", views.dashboard, name="dashboard"),
    path("risk/new/", views.scoping_wizard, name="scoping_wizard"),
    path("scenarios/<str:scenario_id>/calibrate/", views.calibrate_scenario, name="calibrate_scenario"),
    path("runs/<str:run_id>/", views.analysis_detail, name="analysis_detail"),
    path("scenarios/<str:scenario_id>/recalculate/", views.auto_recalculate, name="auto_recalculate"),
    path("runs/<str:run_id>/pdf/", views.analysis_pdf, name="analysis_pdf"),
]
