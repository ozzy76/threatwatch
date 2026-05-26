import datetime
import logging
from django.shortcuts import render, redirect
from django.http import Http404, HttpResponseNotAllowed
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.conf import settings
from apps.accounts.decorators import login_required
from apps.accounts.models import ROLE_ADMIN
from apps.customers.views import _get_allowed_third_party, _normalize_third_party_sector
from apps.threats.models import ThreatActor, Campaign
from .models import FairScenario, FairAnalysisRun
from .forms import FairScenarioForm, FairCalibrateForm
from .monte_carlo import run_simulation
from bson import ObjectId

logger = logging.getLogger(__name__)


def _can_access_scenario(user, scenario):
    if getattr(user, "role", None) == ROLE_ADMIN:
        return True
    # If scenario belongs to a third party, user MUST belong to that third party
    if scenario.third_party:
        allowed_ids = [str(i) for i in user.effective_allowed_third_party_ids]
        if str(scenario.third_party.id) in allowed_ids:
            return True
    # For unassigned / global scenarios, ensure it was created by the same user
    elif scenario.created_by == user:
        return True
    return False


@login_required
def dashboard(request):
    third_party_id = request.GET.get("third_party_id")
    filtered_third_party = None
    if third_party_id:
        filtered_third_party = _get_allowed_third_party(request.user, third_party_id)
        if getattr(request.user, "role", None) != ROLE_ADMIN:
            allowed_ids = [str(i) for i in request.user.effective_allowed_third_party_ids]
            if str(filtered_third_party.id) not in allowed_ids:
                raise Http404

    from mongoengine.queryset.visitor import Q

    if getattr(request.user, "role", None) == ROLE_ADMIN:
        scenarios_query = FairScenario.objects(is_active=True)
    else:
        allowed_ids = [ObjectId(i) for i in request.user.effective_allowed_third_party_ids]
        scenarios_query = FairScenario.objects(Q(is_active=True) & (Q(third_party__in=allowed_ids) | Q(third_party=None, created_by=request.user)))

    if filtered_third_party:
        scenarios = scenarios_query.filter(third_party=filtered_third_party)
    else:
        scenarios = scenarios_query

    active_scenarios_data = []
    total_avg_ale = 0.0
    alert_count = 0

    recent_campaigns = Campaign.objects().order_by("-created_at")[:5]

    for scenario in scenarios:
        latest_run = FairAnalysisRun.objects(scenario=scenario, is_active=True).order_by("-created_at").first()
        
        needs_recalc = False
        recalc_reason = ""
        
        # Check if there is threat actor activity targeting linked third party's sector
        if latest_run and scenario.third_party and scenario.third_party.industry:
            sectors = _normalize_customer_sector(scenario.third_party.industry.sector)
            if sectors:
                scenario_campaigns = Campaign.objects(target_industries__in=sectors).order_by("-created_at")[:5]
                if scenario_campaigns:
                    latest_campaign = scenario_campaigns[0]
                    if latest_campaign.created_at and latest_campaign.created_at > latest_run.created_at:
                        needs_recalc = True
                        recalc_reason = "New threat campaign active in the wild targeting linked third-party industry."
                        alert_count += 1
                        
        if latest_run:
            total_avg_ale += latest_run.avg_ale
            if scenario.updated_at > latest_run.created_at:
                needs_recalc = True
                recalc_reason = "Scenario parameters (insurance/regulatory multiplier) updated."
                alert_count += 1

        active_scenarios_data.append({
            "scenario": scenario,
            "latest_run": latest_run,
            "needs_recalc": needs_recalc,
            "recalc_reason": recalc_reason
        })

    return render(request, "fair/dashboard.html", {
        "scenarios": active_scenarios_data,
        "total_avg_ale": total_avg_ale,
        "alert_count": alert_count,
        "recent_campaigns": recent_campaigns,
        "filtered_third_party": filtered_third_party,
    })


@login_required
@require_http_methods(["GET", "POST"])
def scoping_wizard(request):
    if request.method == "POST":
        form = FairScenarioForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            
            threat_agent = None
            if d["threat_agent_id"]:
                try:
                    threat_agent = ThreatActor.objects.get(id=d["threat_agent_id"])
                except ThreatActor.DoesNotExist:
                    pass

            third_party = None
            if d["third_party_id"]:
                from apps.customers.models import ThirdParty
                try:
                    # Validate that user is allowed to access this third party
                    third_party = _get_allowed_third_party(request.user, d["third_party_id"])
                except Http404:
                    messages.error(request, "Invalid third party selection.")
                    return redirect("fair:scoping_wizard")

            now = datetime.datetime.now(datetime.timezone.utc)
            scenario = FairScenario(
                third_party=third_party,
                name=d["name"],
                description=d["description"],
                asset=d["asset"],
                threat_agent=threat_agent,
                threat_agent_text=d["threat_agent_text"],
                threat_effect=d["threat_effect"],
                insurance_premium=d["insurance_premium"] or 0.0,
                regulatory_penalty_multiplier=d["regulatory_penalty_multiplier"] or 1.0,
                created_by=request.user,
                created_at=now,
                updated_at=now,
            )
            scenario.save()
            messages.success(request, f"Scenario '{scenario.name}' scoped successfully. Now enter calibrated estimates.")
            return redirect("fair:calibrate_scenario", scenario_id=str(scenario.id))
    else:
        form = FairScenarioForm()

    return render(request, "fair/scope_wizard.html", {
        "form": form
    })


@login_required
@require_http_methods(["GET", "POST"])
def calibrate_scenario(request, scenario_id):
    try:
        scenario = FairScenario.objects.get(id=scenario_id, is_active=True)
    except FairScenario.DoesNotExist:
        raise Http404

    # Restrict access
    if not _can_access_scenario(request.user, scenario):
        raise Http404

    latest_run = FairAnalysisRun.objects(scenario=scenario, is_active=True).order_by("-created_at").first()

    if request.method == "POST":
        form = FairCalibrateForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            
            inputs = {
                "tef": (d["tef_min"], d["tef_mode"], d["tef_max"]),
                "vuln": (d["vuln_min"], d["vuln_mode"], d["vuln_max"]),
                "primary_loss": (d["primary_loss_min"], d["primary_loss_mode"], d["primary_loss_max"]),
                "secondary_loss_freq": (d["secondary_loss_freq_min"], d["secondary_loss_freq_mode"], d["secondary_loss_freq_max"]),
                "secondary_loss_mag": (d["secondary_loss_mag_min"], d["secondary_loss_mag_mode"], d["secondary_loss_mag_max"]),
                "insurance_premium": scenario.insurance_premium,
                "regulatory_penalty_multiplier": scenario.regulatory_penalty_multiplier
            }
            
            results = run_simulation(inputs)
            
            safeguards = []
            
            mfa_inputs = inputs.copy()
            mfa_inputs["vuln"] = (d["vuln_min"] * 0.4, d["vuln_mode"] * 0.4, d["vuln_max"] * 0.4)
            mfa_sim = run_simulation(mfa_inputs)
            safeguards.append({
                "name": "Access Controls (MFA & Privileged Access)",
                "description": "Enforce MFA globally and isolate privileged credentials.",
                "reduction": "Reduces Vulnerability by 60%",
                "cost": 15000.0,
                "before_avg": results["avg_ale"],
                "after_avg": mfa_sim["avg_ale"],
                "savings": round(results["avg_ale"] - mfa_sim["avg_ale"], 2)
            })

            edr_inputs = inputs.copy()
            edr_inputs["vuln"] = (d["vuln_min"] * 0.6, d["vuln_mode"] * 0.6, d["vuln_max"] * 0.6)
            edr_sim = run_simulation(edr_inputs)
            safeguards.append({
                "name": "Advanced Endpoint Detection & Response (EDR)",
                "description": "Deploy EDR agents to detect and block active client compromises.",
                "reduction": "Reduces Vulnerability by 40%",
                "cost": 25000.0,
                "before_avg": results["avg_ale"],
                "after_avg": edr_sim["avg_ale"],
                "savings": round(results["avg_ale"] - edr_sim["avg_ale"], 2)
            })

            train_inputs = inputs.copy()
            train_inputs["tef"] = (d["tef_min"] * 0.7, d["tef_mode"] * 0.7, d["tef_max"] * 0.7)
            train_sim = run_simulation(train_inputs)
            safeguards.append({
                "name": "Continuous Security Awareness & Phishing Drills",
                "description": "Run simulated monthly phishing campaigns and training.",
                "reduction": "Reduces Threat Event Frequency by 30%",
                "cost": 5000.0,
                "before_avg": results["avg_ale"],
                "after_avg": train_sim["avg_ale"],
                "savings": round(results["avg_ale"] - train_sim["avg_ale"], 2)
            })

            run = FairAnalysisRun(
                scenario=scenario,
                run_by=request.user,
                created_at=datetime.datetime.now(datetime.timezone.utc),
                rationale={
                    "tef": d["tef_rationale"],
                    "vuln": d["vuln_rationale"],
                    "primary_loss": d["primary_loss_rationale"],
                    "secondary_loss_freq": d["secondary_loss_freq_rationale"],
                    "secondary_loss_mag": d["secondary_loss_mag_rationale"]
                },
                tef_min=d["tef_min"],
                tef_mode=d["tef_mode"],
                tef_max=d["tef_max"],
                vuln_min=d["vuln_min"],
                vuln_mode=d["vuln_mode"],
                vuln_max=d["vuln_max"],
                primary_loss_min=d["primary_loss_min"],
                primary_loss_mode=d["primary_loss_mode"],
                primary_loss_max=d["primary_loss_max"],
                secondary_loss_freq_min=d["secondary_loss_freq_min"],
                secondary_loss_freq_mode=d["secondary_loss_freq_mode"],
                secondary_loss_freq_max=d["secondary_loss_freq_max"],
                secondary_loss_mag_min=d["secondary_loss_mag_min"],
                secondary_loss_mag_mode=d["secondary_loss_mag_mode"],
                secondary_loss_mag_max=d["secondary_loss_mag_max"],
                min_ale=results["min_ale"],
                max_ale=results["max_ale"],
                avg_ale=results["avg_ale"],
                median_ale=results["median_ale"],
                var_95=results["var_95"],
                loss_exceedance_curve=results["loss_exceedance_curve"],
                safeguard_recommendations=safeguards
            )
            run.save()
            
            scenario.updated_at = datetime.datetime.now(datetime.timezone.utc)
            scenario.save()

            messages.success(request, "Monte Carlo simulation completed successfully. 10,000 runs executed.")
            return redirect("fair:analysis_detail", run_id=str(run.id))
    else:
        if latest_run:
            initial = {
                "tef_min": latest_run.tef_min,
                "tef_mode": latest_run.tef_mode,
                "tef_max": latest_run.tef_max,
                "tef_rationale": latest_run.rationale.get("tef", ""),
                
                "vuln_min": latest_run.vuln_min,
                "vuln_mode": latest_run.vuln_mode,
                "vuln_max": latest_run.vuln_max,
                "vuln_rationale": latest_run.rationale.get("vuln", ""),
                
                "primary_loss_min": latest_run.primary_loss_min,
                "primary_loss_mode": latest_run.primary_loss_mode,
                "primary_loss_max": latest_run.primary_loss_max,
                "primary_loss_rationale": latest_run.rationale.get("primary_loss", ""),
                
                "secondary_loss_freq_min": latest_run.secondary_loss_freq_min,
                "secondary_loss_freq_mode": latest_run.secondary_loss_freq_mode,
                "secondary_loss_freq_max": latest_run.secondary_loss_freq_max,
                "secondary_loss_freq_rationale": latest_run.rationale.get("secondary_loss_freq", ""),
                
                "secondary_loss_mag_min": latest_run.secondary_loss_mag_min,
                "secondary_loss_mag_mode": latest_run.secondary_loss_mag_mode,
                "secondary_loss_mag_max": latest_run.secondary_loss_mag_max,
                "secondary_loss_mag_rationale": latest_run.rationale.get("secondary_loss_mag", "")
            }
            form = FairCalibrateForm(initial=initial)
        else:
            form = FairCalibrateForm()

    return render(request, "fair/calibrate_form.html", {
        "scenario": scenario,
        "form": form
    })


@login_required
def analysis_detail(request, run_id):
    try:
        run = FairAnalysisRun.objects.get(id=run_id, is_active=True)
    except FairAnalysisRun.DoesNotExist:
        raise Http404

    scenario = run.scenario
    if not _can_access_scenario(request.user, scenario):
        raise Http404

    past_runs = list(FairAnalysisRun.objects(scenario=scenario, is_active=True).order_by("-created_at"))
    
    previous_run = None
    trend_direction = "stable"
    trend_diff_val = 0.0
    trend_pct = 0.0

    if len(past_runs) > 1:
        previous_run = past_runs[1]
        trend_diff_val = run.avg_ale - previous_run.avg_ale
        
        if previous_run.avg_ale > 0:
            trend_pct = (trend_diff_val / previous_run.avg_ale) * 100.0

        if trend_diff_val < 0:
            trend_direction = "decreased"
            trend_diff_val = abs(trend_diff_val)
            trend_pct = abs(trend_pct)
        elif trend_diff_val > 0:
            trend_direction = "increased"

    exceedance_data = []
    svg_points = []
    thresholds_sorted = sorted([int(k) for k in run.loss_exceedance_curve.keys()])
    num_points = len(thresholds_sorted)
    
    for idx, thresh in enumerate(thresholds_sorted):
        prob = run.loss_exceedance_curve[str(thresh)]
        exceedance_data.append({
            "threshold": thresh,
            "probability": prob
        })
        
        if num_points > 1:
            x = 80 + idx * (680 / (num_points - 1))
            y = 20 + (100 - prob) * (330 / 100)
            svg_points.append({
                "x": round(x, 1),
                "y": round(y, 1),
                "threshold": thresh,
                "probability": prob
            })

    # Prepare safeguards list to calculate net benefit and ROI dynamically for safe rendering
    safeguards_computed = []
    if run.safeguard_recommendations:
        for control in run.safeguard_recommendations:
            c = dict(control)
            savings = c.get("savings", 0.0)
            cost = c.get("cost", 0.0)
            c["net_benefit"] = savings - cost
            c["roi_pct"] = round((savings / cost) * 100) if cost > 0 else 0
            safeguards_computed.append(c)
    run.safeguard_recommendations = safeguards_computed

    return render(request, "fair/analysis_detail.html", {
        "run": run,
        "scenario": scenario,
        "customer": scenario.third_party,
        "previous_run": previous_run,
        "trend_direction": trend_direction,
        "trend_diff_val": trend_diff_val,
        "trend_pct": round(trend_pct, 1),
        "exceedance_data": exceedance_data,
        "svg_points": svg_points
    })


@login_required
@require_http_methods(["POST"])
def auto_recalculate(request, scenario_id):
    try:
        scenario = FairScenario.objects.get(id=scenario_id, is_active=True)
    except FairScenario.DoesNotExist:
        raise Http404

    if not _can_access_scenario(request.user, scenario):
        raise Http404

    latest_run = FairAnalysisRun.objects(scenario=scenario, is_active=True).order_by("-created_at").first()

    if not latest_run:
        messages.error(request, "No prior estimates found. Please calibrate the scenario manually first.")
        return redirect("fair:calibrate_scenario", scenario_id=str(scenario.id))

    inputs = {
        "tef": (latest_run.tef_min, latest_run.tef_mode, latest_run.tef_max),
        "vuln": (latest_run.vuln_min, latest_run.vuln_mode, latest_run.vuln_max),
        "primary_loss": (latest_run.primary_loss_min, latest_run.primary_loss_mode, latest_run.primary_loss_max),
        "secondary_loss_freq": (latest_run.secondary_loss_freq_min, latest_run.secondary_loss_freq_mode, latest_run.secondary_loss_freq_max),
        "secondary_loss_mag": (latest_run.secondary_loss_mag_min, latest_run.secondary_loss_mag_mode, latest_run.secondary_loss_mag_max),
        "insurance_premium": scenario.insurance_premium,
        "regulatory_penalty_multiplier": scenario.regulatory_penalty_multiplier
    }

    results = run_simulation(inputs)

    safeguards = []
    mfa_inputs = inputs.copy()
    mfa_inputs["vuln"] = (latest_run.vuln_min * 0.4, latest_run.vuln_mode * 0.4, latest_run.vuln_max * 0.4)
    mfa_sim = run_simulation(mfa_inputs)
    safeguards.append({
        "name": "Access Controls (MFA & Privileged Access)",
        "description": "Enforce MFA globally and isolate privileged credentials.",
        "reduction": "Reduces Vulnerability by 60%",
        "cost": 15000.0,
        "before_avg": results["avg_ale"],
        "after_avg": mfa_sim["avg_ale"],
        "savings": round(results["avg_ale"] - mfa_sim["avg_ale"], 2)
    })

    edr_inputs = inputs.copy()
    edr_inputs["vuln"] = (latest_run.vuln_min * 0.6, latest_run.vuln_mode * 0.6, latest_run.vuln_max * 0.6)
    edr_sim = run_simulation(edr_inputs)
    safeguards.append({
        "name": "Advanced Endpoint Detection & Response (EDR)",
        "description": "Deploy EDR agents to detect and block active client compromises.",
        "reduction": "Reduces Vulnerability by 40%",
        "cost": 25000.0,
        "before_avg": results["avg_ale"],
        "after_avg": edr_sim["avg_ale"],
        "savings": round(results["avg_ale"] - edr_sim["avg_ale"], 2)
    })

    new_run = FairAnalysisRun(
        scenario=scenario,
        run_by=request.user,
        created_at=datetime.datetime.now(datetime.timezone.utc),
        rationale=latest_run.rationale,
        tef_min=latest_run.tef_min,
        tef_mode=latest_run.tef_mode,
        tef_max=latest_run.tef_max,
        vuln_min=latest_run.vuln_min,
        vuln_mode=latest_run.vuln_mode,
        vuln_max=latest_run.vuln_max,
        primary_loss_min=latest_run.primary_loss_min,
        primary_loss_mode=latest_run.primary_loss_mode,
        primary_loss_max=latest_run.primary_loss_max,
        secondary_loss_freq_min=latest_run.secondary_loss_freq_min,
        secondary_loss_freq_mode=latest_run.secondary_loss_freq_mode,
        secondary_loss_freq_max=latest_run.secondary_loss_freq_max,
        secondary_loss_mag_min=latest_run.secondary_loss_mag_min,
        secondary_loss_mag_mode=latest_run.secondary_loss_mag_mode,
        secondary_loss_mag_max=latest_run.secondary_loss_mag_max,
        min_ale=results["min_ale"],
        max_ale=results["max_ale"],
        avg_ale=results["avg_ale"],
        median_ale=results["median_ale"],
        var_95=results["var_95"],
        loss_exceedance_curve=results["loss_exceedance_curve"],
        safeguard_recommendations=safeguards
    )
    new_run.save()

    scenario.updated_at = datetime.datetime.now(datetime.timezone.utc)
    scenario.save()

    messages.success(request, f"Continuous calculation completed automatically. Total exposure: ${results['avg_ale']:,.2f}.")
    return redirect("fair:analysis_detail", run_id=str(new_run.id))


@login_required
def analysis_pdf(request, run_id):
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    from apps.reports.models import Report

    try:
        run = FairAnalysisRun.objects.get(id=run_id, is_active=True)
    except FairAnalysisRun.DoesNotExist:
        raise Http404

    scenario = run.scenario
    if not _can_access_scenario(request.user, scenario):
        raise Http404

    thresholds_sorted = sorted([int(k) for k in run.loss_exceedance_curve.keys()])
    num_points = len(thresholds_sorted)
    svg_points = []
    for idx, thresh in enumerate(thresholds_sorted):
        prob = run.loss_exceedance_curve[str(thresh)]
        if num_points > 1:
            x = 80 + idx * (680 / (num_points - 1))
            y = 20 + (100 - prob) * (330 / 100)
            svg_points.append({
                "x": round(x, 1),
                "y": round(y, 1),
                "threshold": thresh,
                "probability": prob
            })

    context = {
        "run": run,
        "scenario": scenario,
        "customer": scenario.third_party,
        "generated_by": request.user,
        "generated_at": datetime.datetime.now(datetime.timezone.utc),
        "svg_points": svg_points,
    }

    html_string = render_to_string("fair/report_pdf.html", context)
    
    try:
        from weasyprint import HTML
        base_url = settings.BASE_DIR
        pdf_bytes = HTML(string=html_string, base_url=str(base_url)).write_pdf()
        
        try:
            from apps.reports.storage import upload_pdf
            report = Report(
                customer=scenario.third_party,
                generated_by=request.user,
                generated_at=datetime.datetime.now(datetime.timezone.utc),
                gcs_object_path="pending",
                gcs_bucket="pending",
                snapshot_data={
                    "customer_name": scenario.third_party.name if scenario.third_party else "Enterprise Internal",
                    "scenario_name": scenario.name,
                    "avg_ale": run.avg_ale,
                    "max_ale": run.max_ale,
                    "min_ale": run.min_ale,
                },
                file_size_bytes=len(pdf_bytes),
                is_available=False,
            )
            report.save()
            cust_id_str = str(scenario.third_party.id) if scenario.third_party else "global"
            bucket_name, object_path = upload_pdf(pdf_bytes, cust_id_str, str(report.id))
            report.gcs_object_path = object_path
            report.gcs_bucket = bucket_name
            report.is_available = True
            report.save()
            logger.info("Quantified Risk PDF report saved and uploaded to GCS: %s", report.id)
        except Exception as gcs_err:
            logger.warning("GCS upload bypassed or failed during PDF generation: %s", gcs_err)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="quantified_risk_report_{run.id}.pdf"'
        return response
    except (ImportError, OSError, Exception) as exc:
        logger.warning("WeasyPrint PDF generation bypassed/failed: %s. Falling back to browser-based printing.", exc)
        context["auto_print"] = True
        context["is_fallback"] = True
        return render(request, "fair/report_pdf.html", context)
