from django.test import SimpleTestCase, RequestFactory
from django.http import Http404
from django.contrib.messages.storage.fallback import FallbackStorage
from bson import ObjectId
import datetime

from apps.accounts.models import User, Organization, ROLE_ANALYST, ROLE_ADMIN
from apps.customers.models import ThirdParty, IndustryInfo, Breach
from apps.customers import views as customer_views
from apps.accounts import views as account_views
from apps.fair.models import FairScenario
from apps.fair import views as fair_views
from apps.reports.models import Report
from apps.reports import views as report_views

class MultiTenantIsolationAndProfileSecurityTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        
        # Clean collection states
        ThirdParty.objects.delete()
        User.objects.delete()
        Organization.objects.delete()
        Breach.objects.delete()
        Report.objects.delete()
        FairScenario.objects.delete()

        # Create Organizations
        self.org_alpha = Organization(name="Organization Alpha").save()
        self.org_beta = Organization(name="Organization Beta").save()

        # Tenant 1 (Alpha)
        self.tenant_alpha = ThirdParty(
            name="Tenant Alpha", short_name="alpha",
            industry=IndustryInfo(sector="Technology"), is_active=True,
            created_at=datetime.datetime.utcnow(), updated_at=datetime.datetime.utcnow()
        ).save()

        # Tenant 2 (Beta)
        self.tenant_beta = ThirdParty(
            name="Tenant Beta", short_name="beta",
            industry=IndustryInfo(sector="Healthcare"), is_active=True,
            created_at=datetime.datetime.utcnow(), updated_at=datetime.datetime.utcnow()
        ).save()

        # Link Third Parties to Organizations
        self.org_alpha.third_parties = [self.tenant_alpha]
        self.org_alpha.save()
        
        self.org_beta.third_parties = [self.tenant_beta]
        self.org_beta.save()

        # Analyst belonging to Organization Alpha
        self.analyst_alpha = User(
            username="analyst_alpha", email="alpha@test.com",
            role=ROLE_ANALYST, organization=self.org_alpha,
            password="dummy_hash"
        ).save()

        # Analyst belonging to Organization Beta
        self.analyst_beta = User(
            username="analyst_beta", email="beta@test.com",
            role=ROLE_ANALYST, organization=self.org_beta,
            password="dummy_hash"
        ).save()

        # Global Platform Admin
        self.platform_admin = User(
            username="platform_admin", email="admin@test.com",
            role=ROLE_ADMIN, password="dummy_hash"
        ).save()

    def test_analyst_cannot_query_other_tenant_details(self):
        """Standard analyst must get Http404 when querying another organization's third party."""
        with self.assertRaises(Http404):
            customer_views._get_allowed_third_party(self.analyst_alpha, str(self.tenant_beta.id))

    def test_analyst_can_query_own_tenant_details(self):
        """Standard analyst must successfully resolve their organization's third party."""
        resolved = customer_views._get_allowed_third_party(self.analyst_alpha, str(self.tenant_alpha.id))
        self.assertEqual(resolved.id, self.tenant_alpha.id)

    def test_admin_can_query_any_tenant_details(self):
        """Platform admins must bypass restriction and successfully resolve any organization."""
        resolved = customer_views._get_allowed_third_party(self.platform_admin, str(self.tenant_beta.id))
        self.assertEqual(resolved.id, self.tenant_beta.id)

    def test_analyst_third_party_list_exclusion(self):
        """Analyst's customer list must only include their own organization's third parties."""
        qs = customer_views._allowed_third_parties(self.analyst_alpha)
        self.assertIn(self.tenant_alpha, qs)
        self.assertNotIn(self.tenant_beta, qs)

    def test_admin_third_party_list_all(self):
        """Platform admins should see all active third parties across all organizations."""
        qs = customer_views._allowed_third_parties(self.platform_admin)
        self.assertIn(self.tenant_alpha, qs)
        self.assertIn(self.tenant_beta, qs)

    def test_auto_populate_names_from_email_dot_separated(self):
        """Test parsing email addresses with dots to extract first/last names."""
        user = User(username="test_dot", email="robert.tables@example.com", password="dummy_hash").save()
        account_views.auto_populate_names_from_email(user)
        user.reload()
        self.assertEqual(user.first_name, "Robert")
        self.assertEqual(user.last_name, "Tables")

    def test_auto_populate_names_from_email_dash_separated(self):
        """Test parsing email addresses with dashes to extract first/last names."""
        user = User(username="test_dash", email="alice-smith@example.com", password="dummy_hash").save()
        account_views.auto_populate_names_from_email(user)
        user.reload()
        self.assertEqual(user.first_name, "Alice")
        self.assertEqual(user.last_name, "Smith")

    def test_auto_populate_names_from_email_single_word(self):
        """Test parsing email address with no delimiter to extract first name as capitalization."""
        user = User(username="test_single", email="melissa@example.com", password="dummy_hash").save()
        account_views.auto_populate_names_from_email(user)
        user.reload()
        self.assertEqual(user.first_name, "Melissa")
        self.assertEqual(user.last_name, "")
