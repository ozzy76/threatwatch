"""
Helpers for the sync_mitre management command.
Upserts ThreatActor.known_techniques and Campaign documents from MITRE ATT&CK.
"""
import datetime
import logging
import re

_SECTOR_KEYWORDS = {
    r"government": "Government",
    r"public sector": "Government",
    r"public administration": "Government",
    r"military": "Defense",
    r"defense": "Defense",
    r"defence": "Defense",
    r"aerospace": "Aerospace & Defense",
    r"financial": "Financial Services",
    r"banking": "Financial Services",
    r"finance sector": "Financial Services",
    r"insurance": "Financial Services",
    r"investment": "Financial Services",
    r"healthcare": "Healthcare",
    r"hospital": "Healthcare",
    r"medical": "Healthcare",
    r"pharmaceutical": "Healthcare",
    r"biotech": "Healthcare",
    r"clinical": "Healthcare",
    r"\benergy\b": "Energy",
    r"oil and gas": "Energy",
    r"utilities": "Energy",
    r"power grid": "Energy",
    r"nuclear": "Energy",
    r"renewable energy": "Energy",
    r"technology": "Technology",
    r"high.tech": "Technology",
    r"software": "Technology",
    r"\bit sector": "Technology",
    r"information technology": "Technology",
    r"semiconductor": "Technology",
    r"telecom": "Telecommunications",
    r"telecommunications": "Telecommunications",
    r"wireless carrier": "Telecommunications",
    r"education": "Education",
    r"university": "Education",
    r"academic": "Education",
    r"research institute": "Education",
    r"think tank": "Think Tank / NGO",
    r"non.governmental": "Think Tank / NGO",
    r"\bngo\b": "Think Tank / NGO",
    r"civil society": "Think Tank / NGO",
    r"nonprofit": "Think Tank / NGO",
    r"media": "Media",
    r"entertainment": "Media",
    r"broadcast": "Media",
    r"journalism": "Media",
    r"transport": "Transportation",
    r"logistics": "Transportation",
    r"shipping": "Transportation",
    r"aviation": "Transportation",
    r"maritime": "Transportation",
    r"manufacturing": "Manufacturing",
    r"industrial": "Manufacturing",
    r"retail": "Retail",
    r"e.commerce": "Retail",
    r"critical infrastructure": "Critical Infrastructure",
    r"professional services": "Professional Services",
    r"consulting": "Professional Services",
    r"law firm": "Professional Services",
    r"legal services": "Professional Services",
    r"accounting firm": "Professional Services",
    r"staffing": "Professional Services",
    r"human resources": "Professional Services",
    r"managed service": "Professional Services",
}


def _extract_sectors(description: str) -> list[str]:
    """Return a deduplicated list of sector names detected in the description."""
    text = (description or "").lower()
    found = []
    for pattern, sector in _SECTOR_KEYWORDS.items():
        if re.search(pattern, text) and sector not in found:
            found.append(sector)
    return found

logger = logging.getLogger(__name__)


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


def _tech_ref_from_stix(technique_stix) -> dict:
    """Convert a STIX technique object to a MitreTechniqueRef dict."""
    tid = None
    for ref in technique_stix.get("external_references", []):
        if ref.get("source_name") == "mitre-attack":
            tid = ref.get("external_id")
            break

    name = technique_stix.get("name", "")
    url = None
    for ref in technique_stix.get("external_references", []):
        if ref.get("source_name") == "mitre-attack":
            url = ref.get("url")
            break

    # Kill chain tactic
    kill_chains = technique_stix.get("kill_chain_phases", [])
    tactic = kill_chains[0]["phase_name"].replace("-", " ").title() if kill_chains else ""

    return {"technique_id": tid, "name": name, "tactic": tactic, "url": url}


def sync_actors(mitre_client, stdout=None):
    """Upsert ThreatActor documents from MITRE group data."""
    from apps.threats.models import ThreatActor, MitreTechniqueRef

    groups = mitre_client.get_groups()
    updated = created = 0

    for group in groups:
        props = group.get("modified", None)
        ext_refs = group.get("external_references", [])
        mitre_id = None
        for ref in ext_refs:
            if ref.get("source_name") == "mitre-attack":
                mitre_id = ref.get("external_id")
                break

        if not mitre_id:
            continue

        name = group.get("name", "")
        aliases = group.get("aliases", [])
        description = group.get("description", "")

        # Fetch techniques used by this group
        try:
            techniques_stix = mitre_client.get_techniques_used_by_group(group["id"])
        except Exception:
            techniques_stix = []

        tech_refs = []
        for t in techniques_stix:
            ref_dict = _tech_ref_from_stix(t)
            if ref_dict["technique_id"]:
                tech_refs.append(MitreTechniqueRef(**ref_dict))

        sectors = _extract_sectors(description)

        existing = ThreatActor.objects(mitre_group_id=mitre_id).first()
        if existing:
            existing.name = name
            existing.aliases = [a for a in aliases if a != name]
            existing.description = description
            existing.known_techniques = tech_refs
            existing.target_industries = sectors
            existing.updated_at = _now()
            existing.save()
            updated += 1
        else:
            ThreatActor(
                name=name,
                aliases=[a for a in aliases if a != name],
                mitre_group_id=mitre_id,
                description=description,
                known_techniques=tech_refs,
                target_industries=sectors,
                is_active=True,
                created_at=_now(),
                updated_at=_now(),
            ).save()
            created += 1

    msg = f"Actors: {created} created, {updated} updated."
    if stdout:
        stdout.write(msg)
    logger.info(msg)


def sync_campaigns(mitre_client, stdout=None):
    """Upsert Campaign documents from MITRE campaign data."""
    from apps.threats.models import Campaign, ThreatActor, MitreTechniqueRef

    campaigns_stix = mitre_client.get_campaigns()
    updated = created = 0

    for camp in campaigns_stix:
        ext_refs = camp.get("external_references", [])
        mitre_id = None
        for ref in ext_refs:
            if ref.get("source_name") == "mitre-attack":
                mitre_id = ref.get("external_id")
                break

        name = camp.get("name", "")
        description = camp.get("description", "")

        # Techniques
        try:
            techniques_stix = mitre_client.get_techniques_used_by_campaign(camp["id"])
        except Exception:
            techniques_stix = []

        tech_refs = []
        for t in techniques_stix:
            ref_dict = _tech_ref_from_stix(t)
            if ref_dict["technique_id"]:
                tech_refs.append(MitreTechniqueRef(**ref_dict))

        existing = Campaign.objects(mitre_campaign_id=mitre_id).first() if mitre_id else None
        if existing:
            existing.name = name
            existing.description = description
            existing.techniques = tech_refs
            existing.updated_at = _now()
            existing.save()
            updated += 1
        else:
            Campaign(
                name=name,
                mitre_campaign_id=mitre_id,
                description=description,
                techniques=tech_refs,
                created_at=_now(),
                updated_at=_now(),
            ).save()
            created += 1

    msg = f"Campaigns: {created} created, {updated} updated."
    if stdout:
        stdout.write(msg)
    logger.info(msg)
