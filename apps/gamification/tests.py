import json
from django.test import SimpleTestCase, RequestFactory
from django.urls import reverse
from django.contrib.messages.storage.fallback import FallbackStorage
from apps.accounts.models import User, Organization
from apps.gamification import views


class GamificationSystemTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        
        # Clean collections
        User.objects.delete()
        Organization.objects.delete()
        
        # Create a mock test user
        self.user = User(
            username="test_gamer",
            email="gamer@test.com",
            first_name="Slay",
            last_name="Secure",
            company_name="Test Defense Corp",
            is_active=True,
            role="analyst"
        )
        self.user.set_password("SuperSecret2026!")
        self.user.save()

    def tearDown(self):
        User.objects.delete()

    def _add_messages_to_request(self, request):
        """Mock Django messages storage onto the request."""
        request.session = {}
        setattr(request, '_messages', FallbackStorage(request))

    def test_persona_selection_and_ledger_defaults(self):
        """Verifies choosing a persona initializes user gamification ledger states."""
        request = self.factory.post(reverse("gamification:select_persona"), {"persona": "BUSINESS_OWNER"})
        request.user = self.user
        self._add_messages_to_request(request)
        
        response = views.persona_select_view(request)
        self.assertEqual(response.status_code, 302)  # Redirects to onboarding
        
        user_refresh = User.objects(username="test_gamer").first()
        self.assertEqual(user_refresh.active_persona, "BUSINESS_OWNER")
        self.assertEqual(user_refresh.security_gems_balance, 0)
        self.assertEqual(user_refresh.current_progress_percentage, 0)

    def test_onboarding_answers_post(self):
        """Verifies posting onboarding survey answers stores them on the User document."""
        self.user.active_persona = "IT_STAFF"
        self.user.save()

        payload = {
            "business_industry": "saas",
            "business_purpose": "Building a secure compliance microservice.",
            "business_structure": "Corporation",
            "locations": ["US", "EU"],
            "website_url": "https://secure-saas.com"
        }
        
        request = self.factory.post(
            reverse("gamification:onboarding"),
            data=json.dumps(payload),
            content_type="application/json"
        )
        request.user = self.user
        self._add_messages_to_request(request)

        response = views.onboarding_view(request)
        self.assertEqual(response.status_code, 200)
        
        user_refresh = User.objects(username="test_gamer").first()
        self.assertEqual(user_refresh.business_industry, "saas")
        self.assertEqual(user_refresh.business_purpose, "Building a secure compliance microservice.")
        self.assertEqual(user_refresh.business_structure, "Corporation")
        self.assertEqual(user_refresh.locations, ["US", "EU"])

    def test_api_ssl_check_https_success(self):
        """Tests that a valid HTTPS URL awards gems, a Secure Shield Badge, and increments progress."""
        payload = {"url": "https://secure-vault.com"}
        
        request = self.factory.post(
            reverse("gamification:api_ssl_check"),
            data=json.dumps(payload),
            content_type="application/json"
        )
        request.user = self.user
        self._add_messages_to_request(request)

        response = views.api_ssl_check(request)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data["state"], "SUCCESS_STATE")
        
        user_refresh = User.objects(username="test_gamer").first()
        self.assertIn("Secure Shield Badge", user_refresh.earned_badges)
        self.assertEqual(user_refresh.security_gems_balance, 50)
        self.assertGreater(user_refresh.current_progress_percentage, 0)

    def test_api_ssl_check_http_gap(self):
        """Tests that an insecure HTTP URL triggers GAP_STATE and injects SSL_REMEDIATION to the queue."""
        payload = {"url": "http://cleartext-leak.com"}
        
        request = self.factory.post(
            reverse("gamification:api_ssl_check"),
            data=json.dumps(payload),
            content_type="application/json"
        )
        request.user = self.user
        self._add_messages_to_request(request)

        response = views.api_ssl_check(request)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data["state"], "GAP_STATE")
        
        user_refresh = User.objects(username="test_gamer").first()
        self.assertIn("SSL_REMEDIATION", user_refresh.remediation_queue)

    def test_node_completion_reward_payout(self):
        """Verifies playing a node saves the answers, increases gems balance and progress."""
        self.user.active_persona = "BUSINESS_OWNER"
        self.user.save()

        # Perform mock quest completion POST
        answers_payload = {"laptops": "25", "servers": "2"}
        request = self.factory.post(
            reverse("gamification:node_play", args=["W1_AST_01"]),
            {"answers": json.dumps(answers_payload)}
        )
        request.user = self.user
        self._add_messages_to_request(request)

        response = views.node_play_view(request, "W1_AST_01")
        self.assertEqual(response.status_code, 302)  # Redirects to overworld

        user_refresh = User.objects(username="test_gamer").first()
        self.assertIn("W1_AST_01", user_refresh.node_completions)
        self.assertEqual(user_refresh.security_gems_balance, 50)  # Physical Realm awards 50 gems
        self.assertIn("Gear Spotter", user_refresh.earned_badges)

    def test_world_3_boss_fight_success(self):
        """Verifies completing World 3 boss awards the Iron Outpost Badge, gems and sets progress."""
        self.user.active_persona = "BUSINESS_OWNER"
        self.user.node_completions = {
            "W3_END_01": {"answers": {"edr_status": "EDR_COMPLIANT"}},
            "W3_END_02": {"answers": {"patch_sla": "fast_remediation"}},
            "W3_END_03": {"answers": {"admin_privilege": "standard_enforced"}}
        }
        self.user.security_gems_balance = 100
        self.user.current_progress_percentage = 30
        self.user.save()

        request = self.factory.post(reverse("gamification:boss_fight", args=["world_3"]))
        request.user = self.user
        self._add_messages_to_request(request)

        response = views.boss_fight_view(request, "world_3")
        self.assertEqual(response.status_code, 302)

        user_refresh = User.objects(username="test_gamer").first()
        self.assertIn("The Iron Outpost Badge", user_refresh.earned_badges)
        self.assertEqual(user_refresh.security_gems_balance, 500)  # 100 base + 400 reward
        self.assertEqual(user_refresh.current_progress_percentage, 40)

    def test_world_4_boss_fight_success(self):
        """Verifies completing World 4 boss awards the Master of the Vault Key Badge, gems and sets progress."""
        self.user.active_persona = "BUSINESS_OWNER"
        self.user.node_completions = {
            "W4_DAT_01": {"answers": {}},
            "W4_DAT_02": {"answers": {"vault_encryption": "REST_ENCRYPTED"}},
            "W4_DAT_03": {"answers": {"transit_compliant": "true"}}
        }
        self.user.security_gems_balance = 200
        self.user.current_progress_percentage = 40
        self.user.save()

        request = self.factory.post(reverse("gamification:boss_fight", args=["world_4"]))
        request.user = self.user
        self._add_messages_to_request(request)

        response = views.boss_fight_view(request, "world_4")
        self.assertEqual(response.status_code, 302)

        user_refresh = User.objects(username="test_gamer").first()
        self.assertIn("Master of the Vault Key", user_refresh.earned_badges)
        self.assertEqual(user_refresh.security_gems_balance, 700)  # 200 base + 500 reward
        self.assertEqual(user_refresh.current_progress_percentage, 50)

    def test_world_5_boss_fight_success(self):
        """Verifies completing World 5 boss awards the Grid Technician Badge, gems and sets progress to 60."""
        self.user.active_persona = "BUSINESS_OWNER"
        self.user.node_completions = {
            "W5_NET_01": {"answers": {"firewall_status": "FIREWALL_ACTIVE"}},
            "W5_NET_02": {"answers": {"wifi_status": "isolated_segment"}}
        }
        self.user.security_gems_balance = 300
        self.user.current_progress_percentage = 50
        self.user.save()

        request = self.factory.post(reverse("gamification:boss_fight", args=["world_5"]))
        request.user = self.user
        self._add_messages_to_request(request)

        response = views.boss_fight_view(request, "world_5")
        self.assertEqual(response.status_code, 302)

        user_refresh = User.objects(username="test_gamer").first()
        self.assertIn("Grid Technician", user_refresh.earned_badges)
        self.assertEqual(user_refresh.security_gems_balance, 700)  # 300 base + 400 reward
        self.assertEqual(user_refresh.current_progress_percentage, 60)

    def test_world_6_boss_fight_success(self):
        """Verifies completing World 6 boss awards the Troop Commander Badge, gems and sets progress to 75."""
        self.user.active_persona = "BUSINESS_OWNER"
        self.user.node_completions = {
            "W6_SAT_01": {"answers": {}},
            "W6_GOV_02": {"answers": {}}
        }
        self.user.security_gems_balance = 400
        self.user.current_progress_percentage = 60
        self.user.save()

        request = self.factory.post(reverse("gamification:boss_fight", args=["world_6"]))
        request.user = self.user
        self._add_messages_to_request(request)

        response = views.boss_fight_view(request, "world_6")
        self.assertEqual(response.status_code, 302)

        user_refresh = User.objects(username="test_gamer").first()
        self.assertIn("Troop Commander", user_refresh.earned_badges)
        self.assertEqual(user_refresh.security_gems_balance, 900)  # 400 base + 500 reward
        self.assertEqual(user_refresh.current_progress_percentage, 75)

    def test_world_7_boss_fight_success(self):
        """Verifies completing World 7 boss awards the Watchtower Sentry Badge, gems and sets progress to 90."""
        self.user.active_persona = "BUSINESS_OWNER"
        self.user.node_completions = {
            "W7_VPM_01": {"answers": {}},
            "W7_MON_02": {"answers": {"logbook_status": "LOGBOOK_RETAINED"}}
        }
        self.user.security_gems_balance = 500
        self.user.current_progress_percentage = 75
        self.user.save()

        request = self.factory.post(reverse("gamification:boss_fight", args=["world_7"]))
        request.user = self.user
        self._add_messages_to_request(request)

        response = views.boss_fight_view(request, "world_7")
        self.assertEqual(response.status_code, 302)

        user_refresh = User.objects(username="test_gamer").first()
        self.assertIn("Watchtower Sentry", user_refresh.earned_badges)
        self.assertEqual(user_refresh.security_gems_balance, 1000)  # 500 base + 500 reward
        self.assertEqual(user_refresh.current_progress_percentage, 90)

    def test_world_8_boss_fight_success(self):
        """Verifies completing World 8 boss awards the Savior of the Kingdom Badge, gems and sets progress to 100."""
        self.user.active_persona = "BUSINESS_OWNER"
        self.user.node_completions = {
            "W8_DRP_01": {"answers": {"backup_status": "BACKUP_ISOLATED"}}
        }
        self.user.security_gems_balance = 600
        self.user.current_progress_percentage = 90
        self.user.save()

        request = self.factory.post(reverse("gamification:boss_fight", args=["world_8"]))
        request.user = self.user
        self._add_messages_to_request(request)

        response = views.boss_fight_view(request, "world_8")
        self.assertEqual(response.status_code, 302)

        user_refresh = User.objects(username="test_gamer").first()
        self.assertIn("Savior of the Kingdom", user_refresh.earned_badges)
        self.assertEqual(user_refresh.security_gems_balance, 1600)  # 600 base + 1000 reward
        self.assertEqual(user_refresh.current_progress_percentage, 100)

