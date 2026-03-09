"""
Google Cloud Storage helpers for PDF report persistence.
"""
import datetime
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def upload_pdf(pdf_bytes: bytes, customer_id: str, report_id: str) -> tuple[str, str]:
    """
    Upload PDF bytes to GCS.
    Returns (bucket_name, object_path).
    """
    from google.cloud import storage as gcs

    bucket_name = settings.GCS_BUCKET_NAME
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")
    object_path = f"reports/{customer_id}/{ts}-{report_id}.pdf"

    client = gcs.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_path)
    blob.upload_from_string(pdf_bytes, content_type="application/pdf")
    logger.info("Uploaded PDF to gs://%s/%s (%d bytes)", bucket_name, object_path, len(pdf_bytes))
    return bucket_name, object_path


def generate_signed_url(bucket_name: str, object_path: str, expiry_minutes: int = 30) -> str:
    """Generate a signed GCS URL for temporary download access."""
    from google.cloud import storage as gcs

    client = gcs.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_path)
    url = blob.generate_signed_url(
        expiration=datetime.timedelta(minutes=expiry_minutes),
        method="GET",
        version="v4",
    )
    logger.info("Generated signed URL for gs://%s/%s (expires %dmin)", bucket_name, object_path, expiry_minutes)
    return url
