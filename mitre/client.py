"""
Singleton wrapper for MitreAttackData.

Loads the Enterprise ATT&CK STIX bundle once per container lifetime.
Uses a GCS-cached copy when available; falls back to direct download.
"""
import logging
import os
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

_instance = None
_STIX_FILENAME = "enterprise-attack.json"


def get_mitre_client():
    """Return the singleton MitreAttackData instance."""
    global _instance
    if _instance is None:
        _instance = _load_client()
    return _instance


def _load_client():
    from mitreattack.stix20 import MitreAttackData

    stix_path = _resolve_stix_path()
    logger.info("Loading MITRE ATT&CK data from %s", stix_path)
    return MitreAttackData(str(stix_path))


def _resolve_stix_path() -> Path:
    """
    Resolution order:
    1. MITRE_STIX_PATH env var (explicit local file)
    2. GCS bucket (downloads and caches locally)
    3. Local cache dir ~/.cache/mergethreatwatch/
    """
    env_path = os.environ.get("MITRE_STIX_PATH")
    if env_path:
        return Path(env_path)

    cache_dir = Path(tempfile.gettempdir()) / "mergethreatwatch"
    cache_dir.mkdir(parents=True, exist_ok=True)
    local_path = cache_dir / _STIX_FILENAME

    if local_path.exists():
        logger.info("Using cached STIX bundle at %s", local_path)
        return local_path

    # Try GCS first
    gcs_bucket = os.environ.get("GCS_BUCKET_NAME")
    if gcs_bucket:
        try:
            _download_from_gcs(gcs_bucket, f"mitre/{_STIX_FILENAME}", local_path)
            return local_path
        except Exception as exc:
            logger.warning("GCS STIX download failed (%s); falling back to URL download", exc)

    _download_from_url(local_path)
    return local_path


def _download_from_gcs(bucket_name: str, object_name: str, dest: Path):
    from google.cloud import storage as gcs
    client = gcs.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    blob.download_to_filename(str(dest))
    logger.info("Downloaded STIX bundle from gs://%s/%s", bucket_name, object_name)


def _download_from_url(dest: Path):
    import ssl
    import urllib.request
    import certifi
    url = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"
    logger.info("Downloading STIX bundle from %s", url)
    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_ctx))
    with opener.open(url) as resp, open(dest, "wb") as f:
        f.write(resp.read())
    logger.info("STIX bundle saved to %s", dest)
