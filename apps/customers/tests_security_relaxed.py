import datetime
from django.test import SimpleTestCase, RequestFactory
from django.http import Http404, HttpResponseNotAllowed
from django.core.files.uploadedfile import SimpleUploadedFile
from bson import ObjectId

from apps.accounts.models import User, Organization, ROLE_ANALYST, ROLE_ADMIN
from apps.customers.models import ThirdParty, IndustryInfo
from apps.customers import views as customer_views

class RelaxedAnalystPermissionsSecurityTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        
        # Pure Database Sanitation before each test run
        ThirdParty.objects.delete()
        User.objects.delete()
        Organization.objects.delete()

        # Create two distinct organizations (Tenant Boundaries)
        self.org_alpha = Organization(name="Organization Alpha").save()
        self.org_beta = Organization(name="Organization Beta").save()

        # Create a ThirdParty for Org Alpha
        self.tp_alpha = ThirdParty(
            name="Alpha Corp", short_name="alpha-corp",
            industry=IndustryInfo(sector="Technology"), is_active=True,
            created_at=datetime.datetime.now(datetime.timezone.utc), updated_at=datetime.datetime.now(datetime.timezone.utc)
        ).save()
        self.org_alpha.third_parties = [self.tp_alpha]
        self.org_alpha.save()

        # Create a ThirdParty for Org Beta
        self.tp_beta = ThirdParty(
            name="Beta Corp", short_name="beta-corp",
            industry=IndustryInfo(sector="Healthcare"), is_active=True,
            created_at=datetime.datetime.now(datetime.timezone.utc), updated_at=datetime.datetime.now(datetime.timezone.utc)
        ).save()
        self.org_beta.third_parties = [self.tp_beta]
        self.org_beta.save()

        # Create standard analyst for Org Alpha
        self.analyst_alpha = User(
            username="analyst_alpha", email="alpha@test.com",
            role=ROLE_ANALYST, organization=self.org_alpha, password="pw"
        ).save()

        # Create standard analyst for Org Beta
        self.analyst_beta = User(
            username="analyst_beta", email="beta@test.com",
            role=ROLE_ANALYST, organization=self.org_beta, password="pw"
        ).save()

        # Create Global Platform Admin (should bypass boundaries)
        self.platform_admin = User(
            username="platform_admin", email="admin@test.com",
            role=ROLE_ADMIN, password="pw"
        ).save()

        # Create standard analyst without an organization
        self.analyst_no_org = User(
            username="analyst_no_org", email="noorg@test.com",
            role=ROLE_ANALYST, password="pw"
        ).save()

    # =========================================================================
    # 1. MANUAL CREATION SEGREGATION TESTS
    # =========================================================================

    def test_analyst_create_auto_association(self):
        """
        Verify that when analyst_alpha manually creates a third party, it is
        automatically assigned to Organization Alpha and added to its third_parties list.
        """
        post_data = {
            "name": "New Alpha Vendor",
            "industry_sector": "Technology",
            "industry_subsector": "SaaS",
            "naics_code": 511210,
            "hq_country": "US",
            "employee_count": 100,
            "description": "Enterprise cloud vendor",
            "contact_name": "John Doe",
            "contact_email": "john@alpha-vendor.com",
            "website_url": "https://alpha-vendor.com",
            "contract_exp_date": "2028-12-31"
        }
        
        request = self.factory.post("/customers/third-parties/new/", post_data)
        request.user = self.analyst_alpha
        
        response = customer_views.third_party_create(request)
        self.assertEqual(response.status_code, 302) # Success redirect

        # Verify database insertion
        new_vendor = ThirdParty.objects.get(name="New Alpha Vendor")
        self.assertIsNotNone(new_vendor)

        # Verify auto-association
        self.org_alpha.reload()
        self.assertIn(new_vendor, self.org_alpha.third_parties)
        
        # Verify no leakage to Org Beta
        self.org_beta.reload()
        self.assertNotIn(new_vendor, self.org_beta.third_parties)

    # =========================================================================
    # 2. EDITING BOUNDARY & IDOR PENETRATION TESTS
    # =========================================================================

    def test_analyst_edit_own_third_party_allowed(self):
        """
        Ensure analysts can successfully modify their own organization's third parties.
        """
        post_data = {
            "name": "Alpha Corp Updated",
            "industry_sector": "Technology",
            "industry_subsector": "Hardware",
            "naics_code": 334111,
            "hq_country": "US",
            "employee_count": 500,
            "description": "Updated hardware vendor",
            "contact_name": "Jane Smith",
            "contact_email": "jane@alpha-updated.com",
            "website_url": "https://alpha-updated.com",
            "contract_exp_date": "2029-01-01"
        }
        request = self.factory.post(f"/customers/third-parties/{self.tp_alpha.id}/edit/", post_data)
        request.user = self.analyst_alpha
        
        response = customer_views.third_party_edit(request, str(self.tp_alpha.id))
        self.assertEqual(response.status_code, 302)
        
        # Check updates reflect in DB
        self.tp_alpha.reload()
        self.assertEqual(self.tp_alpha.name, "Alpha Corp Updated")

    def test_analyst_edit_other_tenant_raises_404(self):
        """
        PENETRATION TEST: An analyst attempting to edit a third party belonging to another organization
        must receive an Http404 error (silently rejecting illegal IDOR/URL injection).
        """
        post_data = {
            "name": "Beta Corp Malicious Edit",
            "industry_sector": "Technology",
            "contact_email": "attacker@alpha.com",
        }
        request = self.factory.post(f"/customers/third-parties/{self.tp_beta.id}/edit/", post_data)
        request.user = self.analyst_alpha # Alpha analyst targeting Beta asset
        
        with self.assertRaises(Http404):
            customer_views.third_party_edit(request, str(self.tp_beta.id))
            
        # Verify no changes actually happened to Beta Corp
        self.tp_beta.reload()
        self.assertEqual(self.tp_beta.name, "Beta Corp")

    # =========================================================================
    # 3. DELETION AND METHOD ABUSE TESTS
    # =========================================================================

    def test_analyst_delete_own_third_party_allowed(self):
        """
        Ensure standard analysts can soft-delete their own third party using POST.
        """
        request = self.factory.post(f"/customers/third-parties/{self.tp_alpha.id}/delete/")
        request.user = self.analyst_alpha
        
        response = customer_views.third_party_delete(request, str(self.tp_alpha.id))
        self.assertEqual(response.status_code, 302)
        
        # Verify soft deletion status
        self.tp_alpha.reload()
        self.assertFalse(self.tp_alpha.is_active)

    def test_analyst_delete_other_tenant_raises_404(self):
        """
        PENETRATION TEST: An analyst trying to soft-delete another tenant's third party
        must receive an Http404 error, and the targeted asset must remain completely unaffected.
        """
        request = self.factory.post(f"/customers/third-parties/{self.tp_beta.id}/delete/")
        request.user = self.analyst_alpha # Alpha analyst targeting Beta asset
        
        with self.assertRaises(Http404):
            customer_views.third_party_delete(request, str(self.tp_beta.id))
            
        # Ensure targeted record remains active
        self.tp_beta.reload()
        self.assertTrue(self.tp_beta.is_active)

    def test_analyst_delete_via_get_not_allowed(self):
        """
        Verify that state-changing deletion endpoints refuse GET requests.
        """
        request = self.factory.get(f"/customers/third-parties/{self.tp_alpha.id}/delete/")
        request.user = self.analyst_alpha
        
        response = customer_views.third_party_delete(request, str(self.tp_alpha.id))
        self.assertIsInstance(response, HttpResponseNotAllowed)

    # =========================================================================
    # 4. CSV UPLOAD BOUNDARY & PARAMETER POLLUTION TESTS
    # =========================================================================

    def test_analyst_csv_upload_auto_associated(self):
        """
        Verify that when an analyst uploads a CSV, all parsed records are strictly associated
        with the analyst's own organization, even if the CSV payload contains columns
        attempting to bypass or define different association rules.
        """
        csv_content = (
            "Name,Website URL\n"
            "Uploaded Corp Alpha,https://uploaded-alpha.com\n"
        )
        csv_file = SimpleUploadedFile("vendors.csv", csv_content.encode("utf-8"), content_type="text/csv")
        
        # Inject custom organization ID trying to force creation under Organization Beta
        request = self.factory.post("/customers/third-parties/upload/csv/", {
            "csv_file": csv_file,
            "organization_id": str(self.org_beta.id) # Malicious Parameter Pollution
        })
        from django.contrib.messages.storage.base import BaseStorage
        class DummyStorage(BaseStorage):
            def _get(self):
                return [], True
            def _store(self, messages, response, *args, **kwargs):
                return []
        setattr(request, '_messages', DummyStorage(request))
        request.user = self.analyst_alpha

        response = customer_views.third_party_csv_upload(request)
        self.assertEqual(response.status_code, 200) # Re-renders list/upload page with success messages

        # Check that the document was created
        tp_uploaded = ThirdParty.objects.get(name="Uploaded Corp Alpha")
        self.assertIsNotNone(tp_uploaded)

        # Enforce that it is mapped strictly to Alpha (and bypassed beta injection)
        self.org_alpha.reload()
        self.assertIn(tp_uploaded, self.org_alpha.third_parties)

        self.org_beta.reload()
        self.assertNotIn(tp_uploaded, self.org_beta.third_parties)

    # =========================================================================
    # 5. PLATFORM ADMIN UNRESTRICTED ACCESS TESTS
    # =========================================================================

    def test_admin_can_edit_any_tenant(self):
        """
        Verify that the global Platform Admin bypasses tenant isolation and can edit any third party.
        """
        post_data = {
            "name": "Global Admin Override",
            "industry_sector": "Technology",
            "industry_subsector": "SaaS",
            "naics_code": 511210,
            "hq_country": "US",
            "employee_count": 100,
            "description": "Enterprise cloud vendor",
            "contact_name": "Admin",
            "contact_email": "admin@global.com",
            "website_url": "https://global.com",
            "contract_exp_date": "2028-12-31"
        }
        request = self.factory.post(f"/customers/third-parties/{self.tp_beta.id}/edit/", post_data)
        request.user = self.platform_admin
        
        response = customer_views.third_party_edit(request, str(self.tp_beta.id))
        self.assertEqual(response.status_code, 302)
        
        # Ensure change persisted
        self.tp_beta.reload()
        self.assertEqual(self.tp_beta.name, "Global Admin Override")

    # =========================================================================
    # 6. FRIENDLY REDIRECTS AND ORG AUTO-PROVISIONING TESTS
    # =========================================================================

    def test_analyst_no_org_redirected_on_create(self):
        """
        Verify that an analyst with no associated organization is gracefully 
        redirected to their profile with a warning message on third-party creation.
        """
        request = self.factory.get("/customers/third-parties/new/")
        request.user = self.analyst_no_org
        
        from django.contrib.messages.storage.base import BaseStorage
        class DummyStorage(BaseStorage):
            def _get(self): return [], True
            def _store(self, messages, response, *args, **kwargs): return []
        setattr(request, '_messages', DummyStorage(request))

        response = customer_views.third_party_create(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/accounts/profile/")

    def test_analyst_no_org_redirected_on_csv_upload(self):
        """
        Verify that an analyst with no associated organization is gracefully 
        redirected to their profile with a warning message on CSV upload.
        """
        request = self.factory.get("/customers/third-parties/upload/csv/")
        request.user = self.analyst_no_org
        
        from django.contrib.messages.storage.base import BaseStorage
        class DummyStorage(BaseStorage):
            def _get(self): return [], True
            def _store(self, messages, response, *args, **kwargs): return []
        setattr(request, '_messages', DummyStorage(request))

        response = customer_views.third_party_csv_upload(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/accounts/profile/")

    def test_profile_save_auto_provisions_and_links_organization(self):
        """
        Verify that when an analyst saves their profile with a Company Name, 
        an Organization document is automatically found/created and linked.
        """
        from apps.accounts import views as account_views
        
        # Test creation of a brand new Organization
        post_data = {
            "first_name": "NoOrg",
            "last_name": "Analyst",
            "email": "noorg@test.com",
            "company_name": "Sovereign Systems Corp"
        }
        request = self.factory.post("/accounts/profile/", post_data)
        request.user = self.analyst_no_org
        
        from django.contrib.messages.storage.base import BaseStorage
        class DummyStorage(BaseStorage):
            def _get(self): return [], True
            def _store(self, messages, response, *args, **kwargs): return []
        setattr(request, '_messages', DummyStorage(request))

        response = account_views.profile_view(request)
        self.assertEqual(response.status_code, 302)

        # Check user fields were updated
        self.analyst_no_org.reload()
        self.assertEqual(self.analyst_no_org.company_name, "Sovereign Systems Corp")
        self.assertIsNotNone(self.analyst_no_org.organization)
        self.assertEqual(self.analyst_no_org.organization.name, "Sovereign Systems Corp")

        # Test referencing an already-existing Organization (no duplicate creation)
        existing_org_count = Organization.objects(name="Sovereign Systems Corp").count()
        self.assertEqual(existing_org_count, 1)

        # Another user saves same company name -> should link to same Org
        another_analyst = User(
            username="another_noorg", email="another@test.com",
            role=ROLE_ANALYST, password="pw"
        ).save()
        post_data2 = {
            "first_name": "Another",
            "last_name": "Analyst",
            "email": "another@test.com",
            "company_name": "Sovereign Systems Corp"
        }
        request2 = self.factory.post("/accounts/profile/", post_data2)
        request2.user = another_analyst
        setattr(request2, '_messages', DummyStorage(request2))

        response2 = account_views.profile_view(request2)
        self.assertEqual(response2.status_code, 302)

        another_analyst.reload()
        self.assertEqual(another_analyst.organization.id, self.analyst_no_org.organization.id)
        self.assertEqual(Organization.objects(name="Sovereign Systems Corp").count(), 1)

