"""
PDF report generator using WeasyPrint.
Renders threat_profile.html template to PDF bytes.
"""
import logging
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)


def generate_pdf(context: dict) -> bytes:
    """Render the threat profile template and return PDF bytes."""
    html_string = render_to_string("reports/threat_profile.html", context)

    try:
        from weasyprint import HTML, CSS
        base_url = settings.BASE_DIR
        pdf_bytes = HTML(string=html_string, base_url=str(base_url)).write_pdf()
        logger.info(
            "Generated PDF for customer %s: %d bytes",
            context.get("customer"),
            len(pdf_bytes),
        )
        return pdf_bytes
    except Exception as exc:
        logger.error("PDF generation failed: %s", exc)
        raise


def build_report_context(customer, user) -> dict:
    """Assemble all data needed for the threat profile report."""
    from apps.customers.models import Breach
    from apps.threats.models import ThreatActor
    from apps.detections.models import Detection
    from bson import ObjectId

    breaches = list(Breach.objects(customer=customer).order_by("-breach_date"))

    actors = []
    technique_ids = set()
    for actor_oid in customer.associated_threat_actor_ids:
        try:
            actor = ThreatActor.objects.get(id=actor_oid)
            actors.append(actor)
            for tech in actor.known_techniques:
                technique_ids.add(tech.technique_id)
        except ThreatActor.DoesNotExist:
            pass

    detections = list(
        Detection.objects(technique_ids__in=list(technique_ids)).order_by("-priority")
    ) if technique_ids else []

    return {
        "customer": customer,
        "generated_by": user,
        "breaches": breaches,
        "actors": actors,
        "detections": detections,
        "technique_ids": sorted(technique_ids),
    }
