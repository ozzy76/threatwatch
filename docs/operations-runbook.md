# ThreatWatch — Operations Runbook

**Application:** ThreatWatch
**Stack:** Django 6.0.3 · MongoEngine · Redis · Google Cloud Run · Cloud Build
**Last updated:** 2026-03-31

---

## Table of Contents

1. [Technology Overview](#1-technology-overview)
2. [Prerequisites](#2-prerequisites)
3. [Local Development Setup](#3-local-development-setup)
4. [Environment Variables & Secrets](#4-environment-variables--secrets)
5. [One-Time GCP Infrastructure Setup](#5-one-time-gcp-infrastructure-setup)
6. [Manual Deployment](#6-manual-deployment)
7. [CI/CD: GitHub → Cloud Build → Cloud Run](#7-cicd-github--cloud-build--cloud-run)
8. [User & Data Management](#8-user--data-management)
9. [Monitoring & Logs](#9-monitoring--logs)
10. [Rollback Procedure](#10-rollback-procedure)
11. [Routine Maintenance](#11-routine-maintenance)
12. [Teardown & Resume](#12-teardown--resume)

---

## 1. Technology Overview

| Layer | Technology | Docs |
|---|---|---|
| Web framework | [Django 6.0](https://docs.djangoproject.com/en/6.0/) | django.org |
| Database ODM | [MongoEngine 0.29](https://docs.mongoengine.org/) | mongoengine.org |
| Database | [MongoDB Atlas](https://www.mongodb.com/docs/atlas/) | mongodb.com |
| Cache / Sessions | [Redis](https://redis.io/docs/) | redis.io |
| PDF generation | [WeasyPrint 68](https://doc.courtbouillon.org/weasyprint/stable/) | courtbouillon.org |
| Static files | [WhiteNoise 6](https://whitenoise.readthedocs.io/en/stable/) | whitenoise.readthedocs.io |
| File storage | [Google Cloud Storage](https://cloud.google.com/storage/docs) | cloud.google.com |
| Secrets | [Google Secret Manager](https://cloud.google.com/secret-manager/docs) | cloud.google.com |
| Container runtime | [Google Cloud Run](https://cloud.google.com/run/docs) | cloud.google.com |
| CI/CD | [Google Cloud Build](https://cloud.google.com/build/docs) | cloud.google.com |
| WSGI server | [Gunicorn 25](https://docs.gunicorn.org/en/stable/) | gunicorn.org |
| MITRE ATT&CK | [mitreattack-python](https://mitreattack-python.readthedocs.io/en/latest/) | readthedocs.io |
| Dependency config | [python-decouple](https://github.com/HBNetwork/python-decouple) | github.com |

---

## 2. Prerequisites

Install the following tools on your workstation before proceeding.

### Required CLI tools

| Tool | Install docs | Purpose |
|---|---|---|
| Python 3.14+ | [python.org/downloads](https://www.python.org/downloads/) | Runtime |
| Git | [git-scm.com](https://git-scm.com/downloads) | Source control |
| Google Cloud SDK (`gcloud`) | [cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install) | GCP management |
| Docker | [docs.docker.com/get-docker](https://docs.docker.com/get-docker/) | Local container builds |

### Authenticate gcloud

```bash
gcloud auth login
gcloud auth configure-docker us-west1-docker.pkg.dev
gcloud config set project YOUR_GCP_PROJECT_ID
```

Reference: [gcloud auth docs](https://cloud.google.com/sdk/gcloud/reference/auth)

---

## 3. Local Development Setup

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_ORG/threatwatch.git
cd threatwatch

# 2. Create and activate Python virtualenv
python3.14 -m venv 2026mtw
source 2026mtw/bin/activate          # macOS/Linux
# 2026mtw\Scripts\activate           # Windows

# 3. Install development dependencies
pip install -r requirements/base.txt

# 4. Configure environment
cp .env.example .env
# Edit .env — fill in MONGODB_URI, SECRET_KEY, etc. (see Section 4)

# 5. Verify Django configuration
python manage.py check

# 6. Start the development server
python manage.py runserver
```

Open http://127.0.0.1:8000 in your browser.

> **Note:** Development uses an in-memory cache for sessions. Production uses Redis.
> The `.env` file is gitignored and must never be committed.

---

## 4. Environment Variables & Secrets

### Local `.env` file (development only)

The `.env.example` file in the repo shows all required variables:

```ini
DJANGO_SETTINGS_MODULE=config.settings.development
SECRET_KEY=your-secret-key-here
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/threatwatch?tls=true
GCS_BUCKET_NAME=threatwatch-reports
REDIS_URL=redis://127.0.0.1:6379/0
ALLOWED_HOSTS=localhost,127.0.0.1
```

Generate a secure `SECRET_KEY`:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Production secrets (Google Secret Manager)

In production, Cloud Build injects secrets directly into Cloud Run at deploy time. Never put production secrets in `.env` or source code.

| Secret Manager name | Maps to env var | Description |
|---|---|---|
| `MTW_APP_SECRET_KEY` | `SECRET_KEY` | Django secret key |
| `mtw-mongodb-URI` | `MONGODB_URI` | MongoDB Atlas connection string |
| `redis-url` | `REDIS_URL` | Redis connection URL |

Create or update a secret:
```bash
# Create
echo -n "your-secret-value" | gcloud secrets create MTW_APP_SECRET_KEY --data-file=-

# Update (add new version)
echo -n "your-new-value" | gcloud secrets versions add MTW_APP_SECRET_KEY --data-file=-
```

Reference: [Secret Manager quickstart](https://cloud.google.com/secret-manager/docs/quickstart)

---

## 5. One-Time GCP Infrastructure Setup

Run these commands once when provisioning the environment for the first time.

### 5a. Enable required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  storage.googleapis.com \
  vpcaccess.googleapis.com
```

### 5b. Create Artifact Registry repository

```bash
gcloud artifacts repositories create threatwatch \
  --repository-format=docker \
  --location=us-west1 \
  --description="ThreatWatch container images"
```

Reference: [Artifact Registry docs](https://cloud.google.com/artifact-registry/docs)

### 5c. Create GCS bucket for reports

```bash
gcloud storage buckets create gs://threatwatch-reports \
  --location=us-west1 \
  --uniform-bucket-level-access
```

Reference: [Cloud Storage docs](https://cloud.google.com/storage/docs/creating-buckets)

### 5d. Create VPC connector (for private Redis/MongoDB access)

```bash
gcloud compute networks vpc-access connectors create mtw-app-access \
  --region=us-west1 \
  --range=10.8.0.0/28
```

Reference: [Serverless VPC Access docs](https://cloud.google.com/vpc/docs/configure-serverless-vpc-access)

### 5e. Grant Cloud Build permissions

Cloud Build's service account needs permission to deploy to Cloud Run and access secrets.

```bash
PROJECT_NUMBER=$(gcloud projects describe $GOOGLE_CLOUD_PROJECT --format="value(projectNumber)")
CB_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member="serviceAccount:${CB_SA}" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member="serviceAccount:${CB_SA}" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member="serviceAccount:${CB_SA}" \
  --role="roles/iam.serviceAccountUser"
```

Reference: [Cloud Build IAM docs](https://cloud.google.com/build/docs/securing-builds/configure-access-for-cloud-build-service-account)

### 5f. Store production secrets in Secret Manager

```bash
# Django secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" | \
  gcloud secrets create MTW_APP_SECRET_KEY --data-file=-

# MongoDB URI (replace with your Atlas connection string)
echo -n "mongodb+srv://user:pass@cluster.mongodb.net/threatwatch?tls=true" | \
  gcloud secrets create mtw-mongodb-URI --data-file=-

# Redis URL (replace with your Redis instance URL)
echo -n "redis://10.x.x.x:6379/0" | \
  gcloud secrets create redis-url --data-file=-
```

---

## 6. Manual Deployment

Use this for one-off deploys outside of the automated CI/CD pipeline.

```bash
# Build and push the Docker image manually
IMAGE="us-west1-docker.pkg.dev/$GOOGLE_CLOUD_PROJECT/threatwatch/app:manual-$(date +%Y%m%d%H%M%S)"

docker build -t "$IMAGE" .
docker push "$IMAGE"

# Deploy to Cloud Run
gcloud run deploy threatwatch \
  --image="$IMAGE" \
  --region=us-west1 \
  --platform=managed \
  --min-instances=1 \
  --max-instances=10 \
  --memory=1Gi \
  --cpu=1 \
  --timeout=300 \
  --set-env-vars="DJANGO_SETTINGS_MODULE=config.settings.production,ALLOWED_HOSTS=.a.run.app,.your-domain.com,GCS_BUCKET_NAME=threatwatch-reports" \
  --set-secrets="SECRET_KEY=MTW_APP_SECRET_KEY:latest,MONGODB_URI=mtw-mongodb-URI:latest,REDIS_URL=redis-url:latest" \
  --vpc-connector=mtw-app-access \
  --vpc-egress=all-traffic \
  --allow-unauthenticated
```

Reference: [gcloud run deploy reference](https://cloud.google.com/sdk/gcloud/reference/run/deploy)

---

## 7. CI/CD: GitHub → Cloud Build → Cloud Run

The `cloudbuild.yaml` at the repo root defines the automated pipeline:

1. **Build** — Docker image tagged with `$COMMIT_SHA`
2. **Push** — Image pushed to Artifact Registry
3. **Deploy** — Cloud Run updated to the new image

### 7a. Connect GitHub repository to Cloud Build

1. Open [Cloud Build triggers](https://console.cloud.google.com/cloud-build/triggers) in the GCP console.
2. Click **Connect Repository**.
3. Select **GitHub (Cloud Build GitHub App)** and follow the OAuth flow to authorize GCP.
4. Select your GitHub organization and the `threatwatch` repository.
5. Click **Connect**.

Reference: [Cloud Build GitHub integration](https://cloud.google.com/build/docs/automating-builds/github/connect-repo-github)

### 7b. Create the build trigger

```bash
gcloud builds triggers create github \
  --repo-owner=YOUR_GITHUB_ORG \
  --repo-name=threatwatch \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml \
  --name=threatwatch-deploy-on-push \
  --description="Deploy to Cloud Run on push to main"
```

Or via the console: **Cloud Build → Triggers → Create Trigger** and fill in:

| Field | Value |
|---|---|
| Name | `threatwatch-deploy-on-push` |
| Event | Push to a branch |
| Repository | `YOUR_ORG/threatwatch` |
| Branch | `^main$` |
| Build configuration | Cloud Build configuration file (cloudbuild.yaml) |

Reference: [Build triggers docs](https://cloud.google.com/build/docs/automating-builds/create-manage-triggers)

### 7c. How the pipeline works

```
git push origin main
       │
       ▼
GitHub notifies Cloud Build
       │
       ▼
Cloud Build runs cloudbuild.yaml
  Step 1: docker build -t .../app:$COMMIT_SHA .
  Step 2: docker push .../app:$COMMIT_SHA
  Step 3: gcloud run deploy threatwatch --image=.../app:$COMMIT_SHA
       │
       ▼
Cloud Run serves new revision
```

Build logs are available at [console.cloud.google.com/cloud-build/builds](https://console.cloud.google.com/cloud-build/builds).

### 7d. Recommended GitHub branch protection

Protect `main` so only reviewed code is deployed:

1. In GitHub: **Settings → Branches → Add branch ruleset**
2. Apply to branch `main`
3. Enable:
   - Require pull request reviews before merging (minimum 1 reviewer)
   - Require status checks to pass (add your Cloud Build check if using GitHub Checks)
   - Restrict who can push to matching branches

Reference: [GitHub branch protection rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)

---

## 8. User & Data Management

### Create an analyst account

There is no public registration. All accounts are provisioned by an administrator via the management command:

```bash
# On a local dev machine
python manage.py create_user \
  --username jsmith \
  --email jsmith@your-domain.com \
  --first-name Jane \
  --last-name Smith \
  --role analyst

# Create an admin account
python manage.py create_user \
  --username admin \
  --email admin@your-domain.com \
  --staff \
  --role admin
```

The command will prompt securely for a password. Passwords must be at least 12 characters.

### Run this command against production (Cloud Run)

Use [Cloud Run jobs](https://cloud.google.com/run/docs/execute/jobs) or execute a one-off command via the Cloud Run admin console → **Edit & Deploy New Revision → Command override**.

Alternatively, connect to the container via Cloud Shell:
```bash
gcloud run jobs execute --region=us-west1 --wait \
  -- python manage.py create_user --username jsmith --email jsmith@your-domain.com
```

### Sync MITRE ATT&CK data

```bash
# Sync everything (actors + campaigns)
python manage.py sync_mitre

# Sync only threat actors
python manage.py sync_mitre --actors-only

# Sync only campaigns
python manage.py sync_mitre --campaigns-only
```

Run this after initial deploy and periodically to keep ATT&CK data current.

Reference: [MITRE ATT&CK](https://attack.mitre.org/) · [mitreattack-python docs](https://mitreattack-python.readthedocs.io/en/latest/)

---

## 9. Monitoring & Logs

### View Cloud Run logs

```bash
# Stream live logs
gcloud run services logs tail threatwatch --region=us-west1

# Query recent logs (last 1 hour)
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="threatwatch"' \
  --freshness=1h \
  --format="table(timestamp, severity, textPayload)"
```

Reference: [Cloud Run logging docs](https://cloud.google.com/run/docs/logging)

### View logs in GCP console

Navigate to: **Cloud Run → threatwatch → Logs tab**

Or use [Cloud Logging](https://console.cloud.google.com/logs) with filter:
```
resource.type="cloud_run_revision"
resource.labels.service_name="threatwatch"
```

### Check service status

```bash
gcloud run services describe threatwatch --region=us-west1
```

---

## 10. Rollback Procedure

Cloud Run keeps all previous revisions. A rollback is a traffic shift — no redeployment needed.

### Via gcloud

```bash
# List revisions (newest first)
gcloud run revisions list --service=threatwatch --region=us-west1

# Route 100% of traffic to a specific previous revision
gcloud run services update-traffic threatwatch \
  --region=us-west1 \
  --to-revisions=threatwatch-XXXXXXX=100
```

### Via console

1. Open **Cloud Run → threatwatch → Revisions**
2. Select the target revision
3. Click **Manage Traffic** and set it to 100%

Reference: [Cloud Run traffic management](https://cloud.google.com/run/docs/rollouts-rollbacks-traffic-migration)

---

## 11. Routine Maintenance

### Dependency updates

```bash
# Review outdated packages
source 2026mtw/bin/activate
pip list --outdated

# Update a package (test locally first)
pip install --upgrade django
pip freeze | grep Django >> requirements/base.txt  # update version pin
```

Always test locally with `python manage.py check` and run through key flows before merging a dependency bump.

### Django system check

Run before every deployment to catch configuration issues:
```bash
python manage.py check --deploy
```

### MongoDB index maintenance

MongoEngine creates indexes automatically on first query. To force index creation:
```bash
python manage.py shell -c "
from apps.customers.models import Customer
from apps.threats.models import ThreatActor, Campaign
Customer.ensure_indexes()
ThreatActor.ensure_indexes()
Campaign.ensure_indexes()
"
```

### Secret rotation

When rotating a secret (e.g., `SECRET_KEY`):
```bash
# 1. Add a new version
echo -n "new-secret-value" | gcloud secrets versions add MTW_APP_SECRET_KEY --data-file=-

# 2. Redeploy Cloud Run so it picks up the :latest version
gcloud run deploy threatwatch \
  --image=$(gcloud run services describe threatwatch --region=us-west1 --format="value(spec.template.spec.containers[0].image)") \
  --region=us-west1

# 3. Disable the old version after confirming the service is healthy
gcloud secrets versions disable VERSION_NUMBER --secret=MTW_APP_SECRET_KEY
```

Reference: [Secret rotation best practices](https://cloud.google.com/secret-manager/docs/best-practices#rotation)

### Scaling configuration

Current Cloud Run settings (set in `cloudbuild.yaml`):

| Setting | Value | Notes |
|---|---|---|
| Min instances | 1 | Avoids cold starts |
| Max instances | 10 | Horizontal scale limit |
| Memory | 1 GiB | Required for WeasyPrint PDF rendering |
| CPU | 1 vCPU | Increase if PDF generation is slow |
| Request timeout | 300 s | Long timeout for report generation |

To adjust:
```bash
gcloud run services update threatwatch \
  --region=us-west1 \
  --memory=2Gi \
  --max-instances=20
```

---

## 12. Teardown & Resume

### Quick reference

| Goal | Command |
|------|---------|
| Shut down all production GCP resources | `bash scripts/terminate-prod.sh` |
| Rebuild all infrastructure and redeploy | `bash scripts/resume-prod.sh` |

### What terminate-prod.sh deletes

All billable GCP resources:
- Global HTTPS Load Balancer (forwarding rule, proxy, cert, URL map, backend, NEG)
- Cloud Armor security policy
- Cloud Run service `threatwatch`
- Artifact Registry repository `threatwatch` (all images)
- VPC Access Connector `mtw-app-access`
- Redis Memorystore instance `mtw-app-redis`
- Cloud NAT `mtw-nat` and Cloud Router `mtw-router`
- Static external IP
- Secret Manager secret `redis-url`
- IAM bindings for Cloud Build and Cloud Run service accounts

**Not deleted:** `MTW_APP_SECRET_KEY`, `mtw-mongodb-URI` secrets (data retained), GCS bucket `threatwatch-reports` (run `gcloud storage rm -r gs://threatwatch-reports` manually if data is not needed).

### Manual steps after terminate

1. **Hover DNS:** Remove `A` record `mtw` → `<LB-IP>`
2. **MongoDB Atlas:** Remove the Cloud NAT static IP (`<NAT-IP>/32`) from the IP Access List

### What resume-prod.sh recreates

All infrastructure in correct order, then deploys from source. The Redis AUTH string and internal IP change on recreation — the script fetches them and updates the `redis-url` secret automatically.

### Manual steps after resume

1. **MongoDB Atlas:** Add the new NAT IP (printed by the script) to the IP Access List **before** the script continues past the prompt
2. **Hover DNS:** Update `A` record `mtw` → new LB IP (printed at end of script)
3. **SSL cert:** Becomes `ACTIVE` within ~10 minutes of DNS propagation

### Verification after teardown

```bash
gcloud run services list --region=us-west1                           # empty
gcloud compute forwarding-rules list --global                        # empty
gcloud redis instances list --region=us-west1                        # empty
gcloud compute networks vpc-access connectors list --region=us-west1 # empty
dig mtw.your-domain.com A                                           # NXDOMAIN after DNS TTL
```

---

## Quick Reference

```bash
# Local dev
source 2026mtw/bin/activate && python manage.py runserver

# System health check
python manage.py check --deploy

# Create user
python manage.py create_user --username X --email Y [--staff] [--role admin|analyst]

# Sync MITRE data
python manage.py sync_mitre

# Manual deploy
gcloud run deploy threatwatch --source . --region=us-west1

# View live logs
gcloud run services logs tail threatwatch --region=us-west1

# Rollback to previous revision
gcloud run services update-traffic threatwatch --region=us-west1 --to-revisions=REVISION_ID=100
```
