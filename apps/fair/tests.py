import datetime
from django.test import SimpleTestCase, RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import Http404
from bson import ObjectId

from apps.accounts.models import User, ROLE_ANALYST, ROLE_ADMIN
from apps.customers.models import ThirdParty, IndustryInfo
from apps.fair.models import FairScenario, FairAnalysisRun
from apps.fair.forms import FairScenarioForm, FairCalibrateForm
from apps.fair.monte_carlo import run_simulation, sample_pert, sample_poisson
from apps.fair import views


class FairMonteCarloTest(SimpleTestCase):
    """
    Unit tests for the FAIR quantitative risk Monte Carlo engine.
    """
    def test_pert_distribution_sampling(self):
        # Sample Beta-PERT multiple times to check if values are within bounds
        low, mode, high = 10.0, 50.0, 100.0
        for _ in range(100):
            val = sample_pert(low, mode, high)
            self.assertTrue(low <= val <= high)

    def test_poisson_distribution_sampling(self):
        # Sample Poisson
        lam = 5.0
        samples = [sample_poisson(lam) for _ in range(500)]
        avg = sum(samples) / len(samples)
        # Poisson mean should be close to lambda (within a reasonable margin)
        self.assertTrue(2.0 < avg < 8.0)

    def test_run_simulation_expected_outcomes(self):
        inputs = {
            "tef": (1.0, 3.0, 5.0),
            "vuln": (0.4, 0.5, 0.6),
            "primary_loss": (10000.0, 20000.0, 30000.0),
            "secondary_loss_freq": (0.1, 0.2, 0.3),
            "secondary_loss_mag": (50000.0, 100000.0, 150000.0),
            "insurance_premium": 5000.0,
            "regulatory_penalty_multiplier": 1.2
        }
        results = run_simulation(inputs, iterations=1000)
        
        # Verify result dictionary has expected metrics
        self.assertIn("min_ale", results)
        self.assertIn("max_ale", results)
        self.assertIn("avg_ale", results)
        self.assertIn("median_ale", results)
        self.assertIn("var_95", results)
        self.assertIn("loss_exceedance_curve", results)

        # Sanity check values
        self.assertTrue(results["min_ale"] >= 0.0)
        self.assertTrue(results["max_ale"] >= results["avg_ale"])
        self.assertTrue(results["avg_ale"] >= results["min_ale"])


class FairFormsTest(SimpleTestCase):
    """
    Tests validation of calibrated input forms and scoping forms.
    """
    def test_calibrate_form_valid_ranges(self):
        data = {
            "tef_min": 1.0, "tef_mode": 2.0, "tef_max": 3.0, "tef_rationale": "Test",
            "vuln_min": 0.1, "vuln_mode": 0.5, "vuln_max": 0.9, "vuln_rationale": "Test",
            "primary_loss_min": 100.0, "primary_loss_mode": 500.0, "primary_loss_max": 1000.0, "primary_loss_rationale": "Test",
            "secondary_loss_freq_min": 0.0, "secondary_loss_freq_mode": 0.2, "secondary_loss_freq_max": 0.5, "secondary_loss_freq_rationale": "Test",
            "secondary_loss_mag_min": 1000.0, "secondary_loss_mag_mode": 5000.0, "secondary_loss_mag_max": 10000.0, "secondary_loss_mag_rationale": "Test",
        }
        form = FairCalibrateForm(data=data)
        self.assertTrue(form.is_valid())

    def test_calibrate_form_invalid_ranges(self):
        # mode is less than min, should fail validation
        data = {
            "tef_min": 5.0, "tef_mode": 2.0, "tef_max": 10.0, "tef_rationale": "Test",
            "vuln_min": 0.1, "vuln_mode": 0.5, "vuln_max": 0.9, "vuln_rationale": "Test",
            "primary_loss_min": 100.0, "primary_loss_mode": 500.0, "primary_loss_max": 1000.0, "primary_loss_rationale": "Test",
            "secondary_loss_freq_min": 0.0, "secondary_loss_freq_mode": 0.2, "secondary_loss_freq_max": 0.5, "secondary_loss_freq_rationale": "Test",
            "secondary_loss_mag_min": 1000.0, "secondary_loss_mag_mode": 5000.0, "secondary_loss_mag_max": 10000.0, "secondary_loss_mag_rationale": "Test",
        }
        form = FairCalibrateForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("tef_mode", form.errors)


class FairViewsSecurityAndMultiTenancyTest(SimpleTestCase):
    """
    Tests security access control and multi-tenant data segregation.
    """
    def setUp(self):
        # Set up a request factory
        self.factory = RequestFactory()

        # Clean/Initialize in-memory mock collections
        ThirdParty.objects.delete()
        User.objects.delete()
        FairScenario.objects.delete()
        FairAnalysisRun.objects.delete()

        # Create two Third Parties (tenants)
        self.customer_a = ThirdParty(
            name="Tenant Alpha",
            short_name="alpha",
            industry=IndustryInfo(sector="Technology", subsector="Software"),
            hq_country="US",
            is_active=True,
            created_at=datetime.datetime.now(datetime.timezone.utc),
            updated_at=datetime.datetime.now(datetime.timezone.utc)
        )
        self.customer_a.save()

        self.customer_b = ThirdParty(
            name="Tenant Beta",
            short_name="beta",
            industry=IndustryInfo(sector="Healthcare", subsector="Hospitals"),
            hq_country="US",
            is_active=True,
            created_at=datetime.datetime.now(datetime.timezone.utc),
            updated_at=datetime.datetime.now(datetime.timezone.utc)
        )
        self.customer_b.save()

        # Create user restricted to Customer A (Tenant A)
        self.user_a = User(
            username="analyst_a",
            email="analyst_a@example.com",
            is_active=True,
            role=ROLE_ANALYST,
            allowed_third_party_ids=[self.customer_a.id]
        )
        self.user_a.set_password("SecurePassword123")
        self.user_a.save()

        # Create global admin user
        self.user_admin = User(
            username="super_admin",
            email="admin@example.com",
            is_active=True,
            role=ROLE_ADMIN,
            is_staff=True,
            allowed_third_party_ids=[]
        )
        self.user_admin.set_password("SuperSecretPassword")
        self.user_admin.save()

        # Create a scenario owned by Customer A (linked to third party)
        self.scenario_a = FairScenario(
            third_party=self.customer_a,
            name="Ransomware attack on client records",
            asset="EHR Database",
            threat_effect="destruction",
            created_by=self.user_admin,
            created_at=datetime.datetime.now(datetime.timezone.utc),
            updated_at=datetime.datetime.now(datetime.timezone.utc)
        )
        self.scenario_a.save()

    def test_analyst_can_access_allowed_third_party_dashboard(self):
        request = self.factory.get(f"/risk/?third_party_id={self.customer_a.id}")
        request.user = self.user_a

        # Render dashboard view
        response = views.dashboard(request)
        self.assertEqual(response.status_code, 200)

    def test_analyst_cannot_access_unallowed_third_party_dashboard(self):
        # User A is NOT allowed to view Third Party B's dashboard (segregation)
        request = self.factory.get(f"/risk/?third_party_id={self.customer_b.id}")
        request.user = self.user_a

        # Should raise 404 Http404 to hide tenant existence
        with self.assertRaises(Http404):
            views.dashboard(request)

    def test_admin_can_access_any_third_party_dashboard(self):
        # Admin is not restricted by allowed_third_party_ids
        request = self.factory.get(f"/risk/?third_party_id={self.customer_b.id}")
        request.user = self.user_admin

        response = views.dashboard(request)
        self.assertEqual(response.status_code, 200)

    def test_scoping_wizard_access_control(self):
        # Analyst A can access allowed scoping wizard
        request = self.factory.get("/risk/new/")
        request.user = self.user_a
        response = views.scoping_wizard(request)
        self.assertEqual(response.status_code, 200)

    def test_user_model_backward_compatibility_with_legacy_allowed_customer_ids(self):
        # Create a user dictionary with legacy 'allowed_customer_ids' field
        legacy_id = ObjectId()
        user = User(
            username="legacy_analyst",
            email="legacy@example.com",
            password="somepassword",
            allowed_customer_ids=[legacy_id]
        )
        # Verify that it popped and correctly assigned the IDs to 'allowed_third_party_ids'
        self.assertEqual(user.allowed_third_party_ids, [legacy_id])
