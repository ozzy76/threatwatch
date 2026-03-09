from django.shortcuts import render
from django.http import Http404
from apps.accounts.decorators import login_required
from .models import ThreatActor, Campaign


@login_required
def threat_actor_list(request):
    actors = ThreatActor.objects(is_active=True).order_by("name")
    return render(request, "threats/actor_list.html", {"actors": actors})


@login_required
def threat_actor_detail(request, actor_id):
    actor = _get_actor(actor_id)
    campaigns = Campaign.objects(threat_actor=actor).order_by("-start_date")
    return render(request, "threats/actor_detail.html", {
        "actor": actor,
        "campaigns": campaigns,
    })


@login_required
def campaign_detail(request, actor_id, campaign_id):
    actor = _get_actor(actor_id)
    try:
        campaign = Campaign.objects.get(id=campaign_id, threat_actor=actor)
    except Campaign.DoesNotExist:
        raise Http404
    return render(request, "threats/campaign_detail.html", {
        "actor": actor,
        "campaign": campaign,
    })


def _get_actor(actor_id):
    try:
        return ThreatActor.objects.get(id=actor_id)
    except ThreatActor.DoesNotExist:
        raise Http404
