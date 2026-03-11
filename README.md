# MergeThreatWatch

A threat intelligence platform that contextualizes cybersecurity risk at the customer level — built to demonstrate how technology can turn raw threat data into actionable business insight.

---

## Origin

This project was built as part of the interview process for [Merge](https://merge.dev), a unified API platform serving B2B SaaS companies. The goal was to show how software can bridge the gap between technical threat intelligence and the business conversations that matter most — customer renewals, prospect research, and proactive risk communication.

The core question it answers: *"Given what we know about this customer — their industry, their country, their breach history — which threat actors should we be most concerned about, and what should we be doing about it?"*

---

## What It Does

MergeThreatWatch is a private web application for analyst teams. It ingests threat actor and campaign data from the [MITRE ATT&CK framework](https://attack.mitre.org/) and maps it against a portfolio of customers to surface relevant, prioritized risk.

### Customer Risk Profiles

Each customer record captures the context needed to assess their exposure:

- Industry sector (with NAICS code support)
- Headquarters country
- Known breach history
- Contract status and expiration date
- Associated threat actors and detection coverage

### Threat Actor Matching

When viewing a customer, the platform automatically identifies which MITRE ATT&CK threat actors are relevant based on industry sector and geography. Relevance is scored using Words of Estimative Probability (WEP):

- **Highly Likely** — actor targets both the customer's sector and their country
- **Likely** — actor targets the customer's sector

This gives analysts an immediately actionable view without manual research.

### Detection Coverage

For each customer, the platform maps the ATT&CK techniques used by associated threat actors to the organization's detection catalog — showing which adversary behaviors are covered and where gaps exist.

### Threat Profile Reports

Analysts can generate a formatted PDF threat profile for any customer on demand. Reports are automatically stored in Google Cloud Storage and available for download via time-limited signed URLs. Each report captures:

- Customer overview and industry context
- Relevant threat actors with WEP assessments
- Known breach history
- Detection coverage summary

Reports are versioned by generation date and archived per customer, creating a historical record useful in recurring business reviews.

---

## Business Development Use Cases

This tool was designed with two high-value conversations in mind:

**Prospecting**
Before approaching a new prospect, a business development team can load the company's profile and generate a threat brief. Walking into a meeting with specific, credible intelligence about risks facing that prospect's industry — and concrete detection coverage to address them — is a meaningful differentiator.

**Contract Renewal Preparation**
Before a renewal discussion, account teams can pull a current threat profile to demonstrate ongoing value: here are the threat actors targeting your sector this quarter, here is how our detection coverage maps to their techniques, and here is what has changed since your last renewal. It reframes the conversation from cost to risk management.

---

## Tech Stack

| Component | Technology |
|---|---|
| Web framework | [Django 6.0](https://docs.djangoproject.com/en/6.0/) |
| Database | [MongoDB Atlas](https://www.mongodb.com/atlas) via [MongoEngine](https://docs.mongoengine.org/) |
| Sessions / Cache | [Redis](https://redis.io/) |
| Threat data | [MITRE ATT&CK](https://attack.mitre.org/) via [mitreattack-python](https://mitreattack-python.readthedocs.io/) |
| PDF generation | [WeasyPrint](https://doc.courtbouillon.org/weasyprint/stable/) |
| Static files | [WhiteNoise](https://whitenoise.readthedocs.io/) |
| Report storage | [Google Cloud Storage](https://cloud.google.com/storage) |
| Secrets | [Google Secret Manager](https://cloud.google.com/secret-manager) |
| Hosting | [Google Cloud Run](https://cloud.google.com/run) (containerized, auto-scaling) |
| CI/CD | [Google Cloud Build](https://cloud.google.com/build) triggered on push to `main` |

No Django ORM — persistence is handled entirely through MongoEngine, keeping the data model flexible for the document-oriented nature of threat intelligence data.

---

## Application Structure

```
apps/
├── accounts/       # Auth: custom MongoEngine backend, roles (analyst / admin)
├── customers/      # Customer profiles, breach history, sector-to-actor matching
├── threats/        # MITRE ATT&CK sync: threat actors, campaigns, techniques
├── detections/     # Detection catalog mapped to ATT&CK technique IDs
└── reports/        # PDF threat profile generation and GCS storage

config/
├── settings/
│   ├── base.py         # Shared settings
│   ├── development.py  # Local overrides
│   └── production.py   # Cloud Run production settings

mitre/
├── client.py       # MITRE ATT&CK API wrapper
└── sync.py         # Sync logic for actors and campaigns
```

---

## Getting Started (Local Development)

```bash
# Clone and enter the project
git clone https://github.com/YOUR_ORG/mergethreatwatch.git
cd mergethreatwatch

# Create and activate a virtual environment (Python 3.14+)
python3.14 -m venv 2026mtw
source 2026mtw/bin/activate

# Install dependencies
pip install -r requirements/base.txt

# Configure environment
cp .env.example .env
# Edit .env: set MONGODB_URI, SECRET_KEY, and other values

# Verify setup
python manage.py check

# Start the server
python manage.py runserver
```

### First-time data setup

```bash
# Create an admin user
python manage.py create_user --username admin --email you@example.com --staff --role admin

# Pull MITRE ATT&CK threat actors and campaigns
python manage.py sync_mitre
```

---

## Deployment

The application is containerized and deployed to Google Cloud Run. A push to `main` automatically triggers a Cloud Build pipeline that builds the Docker image and deploys the new revision.

See [`docs/operations-runbook.md`](docs/operations-runbook.md) for the full deployment guide, including one-time GCP infrastructure setup, secret management, rollback procedures, and CI/CD configuration.

---

## Access Control

There is no public registration. All accounts are provisioned by an administrator.

| Role | Capabilities |
|---|---|
| **Analyst** | View customers, threat actors, detections; generate and download reports |
| **Admin** | All analyst capabilities + create/edit/archive customers, manage users |

Sessions are Redis-backed with an 8-hour timeout and secure cookie configuration.
