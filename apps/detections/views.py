from django.shortcuts import render
from apps.accounts.decorators import login_required
from apps.customers.views import _get_allowed_third_party
from apps.threats.models import ThreatActor
from .models import Detection


@login_required
def third_party_detections(request, third_party_id):
    customer = _get_allowed_third_party(request.user, third_party_id)

    # Collect technique IDs from all threat actors associated with this third party
    technique_ids = set()
    actors = []
    for actor_oid in customer.associated_threat_actor_ids:
        try:
            actor = ThreatActor.objects.get(id=actor_oid)
            actors.append(actor)
            for tech in actor.known_techniques:
                technique_ids.add(tech.technique_id)
        except ThreatActor.DoesNotExist:
            pass

    detections = Detection.objects(
        technique_ids__in=list(technique_ids)
    ).order_by("-priority") if technique_ids else []

    return render(request, "detections/customer_detections.html", {
        "customer": customer,
        "detections": detections,
        "actors": actors,
        "technique_ids": sorted(technique_ids),
    })
