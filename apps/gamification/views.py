import json
import logging
from django.shortcuts import render, redirect
from django.http import JsonResponse, Http404, HttpResponse
from apps.accounts.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from apps.accounts.models import User

logger = logging.getLogger(__name__)

# --- Helper to enforce active_persona selection ---
def check_persona_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if not request.user.active_persona or request.user.active_persona == "UNASSIGNED":
            return redirect("gamification:select_persona")
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
def persona_select_view(request):
    """Allows users to select or switch their active gamified persona."""
    if request.method == "POST":
        persona = request.POST.get("persona")
        if persona in ["BUSINESS_OWNER", "IT_STAFF"]:
            request.user.active_persona = persona
            # Initialize other defaults if blank
            if not request.user.security_gems_balance:
                request.user.security_gems_balance = 0
            if not request.user.current_progress_percentage:
                request.user.current_progress_percentage = 0
            request.user.save()
            messages.success(request, f"Persona successfully updated to {persona.replace('_', ' ').title()}!")
            return redirect("gamification:onboarding")
    
    return render(request, "gamification/select_persona.html", {
        "active_persona": request.user.active_persona
    })


@login_required
@check_persona_required
def onboarding_view(request):
    """Handles the multi-step onboarding compliance quest questionnaire."""
    # If already passed onboarding, we can let them review or go straight to overworld.
    # If they POST onboarding data:
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            request.user.business_industry = data.get("business_industry", request.user.business_industry)
            request.user.business_purpose = data.get("business_purpose", request.user.business_purpose)
            request.user.business_structure = data.get("business_structure", request.user.business_structure)
            request.user.locations = data.get("locations", request.user.locations)
            request.user.website_url = data.get("website_url", request.user.website_url)
            request.user.save()
            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return render(request, "gamification/onboarding.html", {
        "user": request.user,
        "active_persona": request.user.active_persona
    })


@csrf_exempt
@login_required
@require_POST
def api_ssl_check(request):
    """
    Simulates a secure domain scan.
    - If HTTPS, returns SUCCESS_STATE (+50 Gems, Secure Shield Badge).
    - If HTTP, returns GAP_STATE (Injects SSL_REMEDIATION).
    - If bypassed/skipped, returns BYPASS_STATE.
    """
    try:
        data = json.loads(request.body)
        url = data.get("url", "").strip()
        bypass = data.get("bypass", False)

        if bypass:
            request.user.current_progress_percentage = max(request.user.current_progress_percentage, 5)
            request.user.save()
            return JsonResponse({
                "status": "bypass",
                "state": "BYPASS_STATE",
                "mascot_animation": "thumbs_up",
                "display_text": (
                    "No website? No problem at all! Honestly, that’s one less asset for hackers to target. "
                    "Let's move on to locking down your internal setup!"
                    if request.user.active_persona == "BUSINESS_OWNER" else
                    "Scope modification updated: Public web assets excluded from control mappings. "
                    "Proceeding directly to internal perimeter evaluation modules."
                )
            })

        if not url:
            return JsonResponse({"error": "No URL provided"}, status=400)

        # Basic simulation: if url contains "https", treat as secure; else if contains "http" treat as HTTP-only.
        # Otherwise, default to HTTPS for standard inputs.
        is_https = True
        if url.startswith("http://") or (not url.startswith("https://") and ".local" in url):
            is_https = False

        if is_https:
            if "Secure Shield Badge" not in request.user.earned_badges:
                request.user.earned_badges.append("Secure Shield Badge")
            request.user.security_gems_balance += 50
            request.user.current_progress_percentage = max(request.user.current_progress_percentage, 10)
            request.user.website_url = url
            request.user.save()

            return JsonResponse({
                "status": "secure",
                "state": "SUCCESS_STATE",
                "mascot_animation": "celebrate",
                "audio_trigger": "chime_success.mp3",
                "particle_effect": "confetti",
                "display_text": (
                    "Boom! Your website is encrypted with HTTPS. Your customer data is safe in transit. "
                    "You just earned your first Secure Shield Badge and +50 Security Gems!"
                    if request.user.active_persona == "BUSINESS_OWNER" else
                    "Domain verification complete. Valid SSL/TLS certificate detected. Asset mapped. "
                    "+50 Gems credited to profile."
                )
            })
        else:
            if "SSL_REMEDIATION" not in request.user.remediation_queue:
                request.user.remediation_queue.append("SSL_REMEDIATION")
            request.user.current_progress_percentage = max(request.user.current_progress_percentage, 10)
            request.user.website_url = url
            request.user.save()

            return JsonResponse({
                "status": "gap",
                "state": "GAP_STATE",
                "mascot_animation": "diagnostic_wrench",
                "audio_trigger": "alert_info.mp3",
                "display_text": (
                    "We scanned your site and noticed your encryption shield is currently down. No stress! "
                    "I've automatically added a quick, step-by-step 'SSL Patch' guide to your dashboard. "
                    "We'll fix it together later!"
                    if request.user.active_persona == "BUSINESS_OWNER" else
                    "Security Alert: Port 80 unencrypted cleartext detected. Target domain lacks mandatory "
                    "HTTPS enforcement. Remediation playbook 'SSL_REMEDIATION' pushed to active sprint log."
                )
            })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@check_persona_required
def overworld_view(request):
    """Renders the game campaign maps showing node progress across Worlds 1 to 8."""
    # Ensure onboarding fields are filled before opening overworld
    if not request.user.business_industry:
        return redirect("gamification:onboarding")

    # Define Node Configurations
    world_1_nodes = [
        {"id": "W1_AST_01", "title": "The Physical Realm", "controls": ["AST-01", "AST-04"]},
        {"id": "W1_AST_02", "title": "The Cloud Outposts", "controls": ["AST-02", "AST-05"]},
        {"id": "W1_AST_03", "title": "The Digital Arsenal", "controls": ["AST-03"]}
    ]
    world_2_nodes = [
        {"id": "W2_IAC_01", "title": "The Roll Call", "controls": ["IAC-01"]},
        {"id": "W2_IAC_02", "title": "The Double Lock", "controls": ["IAC-02", "IAC-03"]},
        {"id": "W2_IAC_03", "title": "The Vault Master", "controls": ["IAC-11", "IAC-12"]}
    ]
    world_3_nodes = [
        {"id": "W3_END_01", "title": "Deployed Armor", "controls": ["END-01", "END-02"]},
        {"id": "W3_END_02", "title": "The Armor Forge", "controls": ["END-06"]},
        {"id": "W3_END_03", "title": "Crown Permissions", "controls": ["END-03", "IAC-04"]}
    ]
    world_4_nodes = [
        {"id": "W4_DAT_01", "title": "Treasure Sorting", "controls": ["DAT-01", "PRI-01"]},
        {"id": "W4_DAT_02", "title": "The Vault Lockers", "controls": ["CRY-01", "DAT-02"]},
        {"id": "W4_DAT_03", "title": "The Courier's Guard", "controls": ["CRY-03"]}
    ]
    world_5_nodes = [
        {"id": "W5_NET_01", "title": "Pipe Inspection", "controls": ["NET-01", "NET-04"]},
        {"id": "W5_NET_02", "title": "The Wi-Fi Drawbridge", "controls": ["WLS-01", "NET-09"]}
    ]
    world_6_nodes = [
        {"id": "W6_SAT_01", "title": "Toad's Training Camp", "controls": ["SAT-01", "SAT-03"]},
        {"id": "W6_GOV_02", "title": "The Royal Decrees", "controls": ["PPL-01", "GOV-01"]}
    ]
    world_7_nodes = [
        {"id": "W7_VPM_01", "title": "Spyglass Deployment", "controls": ["VPM-01", "VPM-02"]},
        {"id": "W7_MON_02", "title": "The Castle Logbook", "controls": ["MON-01", "A&A-02"]}
    ]
    world_8_nodes = [
        {"id": "W8_DRP_01", "title": "The Backup Capsules", "controls": ["DRP-01", "BCP-02"]}
    ]

    # Evaluate completeness
    completions = request.user.node_completions or {}
    w1_complete = all(nid["id"] in completions for nid in world_1_nodes)
    w2_complete = all(nid["id"] in completions for nid in world_2_nodes)
    w3_complete = all(nid["id"] in completions for nid in world_3_nodes)
    w4_complete = all(nid["id"] in completions for nid in world_4_nodes)
    w5_complete = all(nid["id"] in completions for nid in world_5_nodes)
    w6_complete = all(nid["id"] in completions for nid in world_6_nodes)
    w7_complete = all(nid["id"] in completions for nid in world_7_nodes)
    w8_complete = all(nid["id"] in completions for nid in world_8_nodes)

    w1_boss_unlocked = w1_complete
    w1_boss_beaten = "W1_BOSS_COMPLETE" in completions
    
    # World 2 is unlocked once World 1 Boss is defeated
    w2_unlocked = w1_boss_beaten
    w2_boss_unlocked = w2_unlocked and w2_complete
    w2_boss_beaten = "W2_BOSS_COMPLETE" in completions

    # World 3 is unlocked once World 2 Boss is defeated
    w3_unlocked = w2_boss_beaten
    w3_boss_unlocked = w3_unlocked and w3_complete
    w3_boss_beaten = "W3_BOSS_COMPLETE" in completions

    # World 4 is unlocked once World 3 Boss is defeated
    w4_unlocked = w3_boss_beaten
    w4_boss_unlocked = w4_unlocked and w4_complete
    w4_boss_beaten = "W4_BOSS_COMPLETE" in completions

    # World 5 is unlocked once World 4 Boss is defeated
    w5_unlocked = w4_boss_beaten
    w5_boss_unlocked = w5_unlocked and w5_complete
    w5_boss_beaten = "W5_BOSS_COMPLETE" in completions

    # World 6 is unlocked once World 5 Boss is defeated
    w6_unlocked = w5_boss_beaten
    w6_boss_unlocked = w6_unlocked and w6_complete
    w6_boss_beaten = "W6_BOSS_COMPLETE" in completions

    # World 7 is unlocked once World 6 Boss is defeated
    w7_unlocked = w6_boss_beaten
    w7_boss_unlocked = w7_unlocked and w7_complete
    w7_boss_beaten = "W7_BOSS_COMPLETE" in completions

    # World 8 is unlocked once World 7 Boss is defeated
    w8_unlocked = w7_boss_beaten
    w8_boss_unlocked = w8_unlocked and w8_complete
    w8_boss_beaten = "W8_BOSS_COMPLETE" in completions

    return render(request, "gamification/overworld.html", {
        "user": request.user,
        "world_1_nodes": world_1_nodes,
        "world_2_nodes": world_2_nodes,
        "world_3_nodes": world_3_nodes,
        "world_4_nodes": world_4_nodes,
        "world_5_nodes": world_5_nodes,
        "world_6_nodes": world_6_nodes,
        "world_7_nodes": world_7_nodes,
        "world_8_nodes": world_8_nodes,
        "completions": completions,
        "w1_complete": w1_complete,
        "w1_boss_unlocked": w1_boss_unlocked,
        "w1_boss_beaten": w1_boss_beaten,
        "w2_unlocked": w2_unlocked,
        "w2_boss_unlocked": w2_boss_unlocked,
        "w2_boss_beaten": w2_boss_beaten,
        "w3_unlocked": w3_unlocked,
        "w3_boss_unlocked": w3_boss_unlocked,
        "w3_boss_beaten": w3_boss_beaten,
        "w4_unlocked": w4_unlocked,
        "w4_boss_unlocked": w4_boss_unlocked,
        "w4_boss_beaten": w4_boss_beaten,
        "w5_unlocked": w5_unlocked,
        "w5_boss_unlocked": w5_boss_unlocked,
        "w5_boss_beaten": w5_boss_beaten,
        "w6_unlocked": w6_unlocked,
        "w6_boss_unlocked": w6_boss_unlocked,
        "w6_boss_beaten": w6_boss_beaten,
        "w7_unlocked": w7_unlocked,
        "w7_boss_unlocked": w7_boss_unlocked,
        "w7_boss_beaten": w7_boss_beaten,
        "w8_unlocked": w8_unlocked,
        "w8_boss_unlocked": w8_boss_unlocked,
        "w8_boss_beaten": w8_boss_beaten,
    })


@login_required
@check_persona_required
def node_play_view(request, node_id):
    """Renders the play interface for a single quest node depending on the Persona."""
    # Define detailed configuration per node
    node_configs = {
        # --- WORLD 1 NODES ---
        "W1_AST_01": {
            "title": "The Physical Realm",
            "world": "world_1",
            "rewards": {"gems": 50, "badge": "Gear Spotter"},
            "controls": ["AST-01", "AST-04"]
        },
        "W1_AST_02": {
            "title": "The Cloud Outposts",
            "world": "world_1",
            "rewards": {"gems": 75},
            "controls": ["AST-02", "AST-05"]
        },
        "W1_AST_03": {
            "title": "The Digital Arsenal",
            "world": "world_1",
            "rewards": {"gems": 75},
            "controls": ["AST-03"]
        },
        # --- WORLD 2 NODES ---
        "W2_IAC_01": {
            "title": "The Roll Call",
            "world": "world_2",
            "rewards": {"gems": 100},
            "controls": ["IAC-01"]
        },
        "W2_IAC_02": {
            "title": "The Double Lock",
            "world": "world_2",
            "rewards": {"gems": 100},
            "controls": ["IAC-02", "IAC-03"]
        },
        "W2_IAC_03": {
            "title": "The Vault Master",
            "world": "world_2",
            "rewards": {"gems": 100},
            "controls": ["IAC-11", "IAC-12"]
        },
        # --- WORLD 3 NODES ---
        "W3_END_01": {
            "title": "Deployed Armor",
            "world": "world_3",
            "rewards": {"gems": 100, "badge": "Armor Bearer"},
            "controls": ["END-01", "END-02"]
        },
        "W3_END_02": {
            "title": "The Armor Forge",
            "world": "world_3",
            "rewards": {"gems": 125},
            "controls": ["END-06"]
        },
        "W3_END_03": {
            "title": "Crown Permissions",
            "world": "world_3",
            "rewards": {"gems": 125},
            "controls": ["END-03", "IAC-04"]
        },
        # --- WORLD 4 NODES ---
        "W4_DAT_01": {
            "title": "Treasure Sorting",
            "world": "world_4",
            "rewards": {"gems": 150, "badge": "Grand Archivist"},
            "controls": ["DAT-01", "PRI-01"]
        },
        "W4_DAT_02": {
            "title": "The Vault Lockers",
            "world": "world_4",
            "rewards": {"gems": 150},
            "controls": ["CRY-01", "DAT-02"]
        },
        "W4_DAT_03": {
            "title": "The Courier's Guard",
            "world": "world_4",
            "rewards": {"gems": 150},
            "controls": ["CRY-03"]
        },
        # --- WORLD 5 NODES ---
        "W5_NET_01": {
            "title": "Pipe Inspection",
            "world": "world_5",
            "rewards": {"gems": 150},
            "controls": ["NET-01", "NET-04"]
        },
        "W5_NET_02": {
            "title": "The Wi-Fi Drawbridge",
            "world": "world_5",
            "rewards": {"gems": 150, "badge": "Grid Technician"},
            "controls": ["WLS-01", "NET-09"]
        },
        # --- WORLD 6 NODES ---
        "W6_SAT_01": {
            "title": "Toad's Training Camp",
            "world": "world_6",
            "rewards": {"gems": 200, "badge": "Troop Commander"},
            "controls": ["SAT-01", "SAT-03"]
        },
        "W6_GOV_02": {
            "title": "The Royal Decrees",
            "world": "world_6",
            "rewards": {"gems": 150},
            "controls": ["PPL-01", "GOV-01"]
        },
        # --- WORLD 7 NODES ---
        "W7_VPM_01": {
            "title": "Spyglass Deployment",
            "world": "world_7",
            "rewards": {"gems": 200, "badge": "Watchtower Sentry"},
            "controls": ["VPM-01", "VPM-02"]
        },
        "W7_MON_02": {
            "title": "The Castle Logbook",
            "world": "world_7",
            "rewards": {"gems": 200},
            "controls": ["MON-01", "A&A-02"]
        },
        # --- WORLD 8 NODES ---
        "W8_DRP_01": {
            "title": "The Backup Capsules",
            "world": "world_8",
            "rewards": {"gems": 250, "badge": "Time Mage"},
            "controls": ["DRP-01", "BCP-02"]
        }
    }

    if node_id not in node_configs:
        raise Http404("Node not found")

    config = node_configs[node_id]

    if request.method == "POST":
        # Process completions
        answers = request.POST.get("answers", "{}")
        try:
            answers_dict = json.loads(answers)
        except Exception:
            answers_dict = {"raw_post": dict(request.POST.items())}

        completions = request.user.node_completions or {}
        
        # Award gems and badges if not already completed
        if node_id not in completions:
            rewards = config["rewards"]
            request.user.security_gems_balance += rewards.get("gems", 0)
            badge = rewards.get("badge")
            if badge and badge not in request.user.earned_badges:
                request.user.earned_badges.append(badge)
            
            # Increment progress dynamically
            request.user.current_progress_percentage = min(request.user.current_progress_percentage + 5, 100)

        completions[node_id] = {
            "answers": answers_dict,
            "completed_at": str(User().id)  # placeholder value to save
        }
        request.user.node_completions = completions
        request.user.save()

        messages.success(request, f"Successfully completed {config['title']}! Rewards claimed.")
        return redirect("gamification:overworld")

    # Load existing progress if any
    existing_completion = (request.user.node_completions or {}).get(node_id, {})

    return render(request, "gamification/node_play.html", {
        "node_id": node_id,
        "config": config,
        "existing_completion": existing_completion,
        "active_persona": request.user.active_persona
    })


@login_required
@check_persona_required
def boss_fight_view(request, world_id):
    """Renders the Boss Fight scenario view and handles mutations upon beating it."""
    completions = request.user.node_completions or {}

    if world_id == "world_1":
        # Check prerequisites
        world_1_nodes = ["W1_AST_01", "W1_AST_02", "W1_AST_03"]
        if not all(nid in completions for nid in world_1_nodes):
            messages.error(request, "Unlock the Boss Fight by completing all World 1 nodes first!")
            return redirect("gamification:overworld")

        if request.method == "POST":
            # Complete World 1 Boss Fight
            if "W1_BOSS_COMPLETE" not in completions:
                completions["W1_BOSS_COMPLETE"] = True
                request.user.security_gems_balance += 200
                request.user.current_progress_percentage = max(request.user.current_progress_percentage, 15)
                request.user.node_completions = completions
                request.user.save()
                messages.success(request, "Excellent! Asset Management Baseline established. World 2 Unlocked!")
            return redirect("gamification:overworld")

        return render(request, "gamification/boss_fight.html", {
            "world_id": "world_1",
            "active_persona": request.user.active_persona,
            "gems_balance": request.user.security_gems_balance,
            "progress": request.user.current_progress_percentage
        })

    elif world_id == "world_2":
        # Check prerequisites
        world_2_nodes = ["W2_IAC_01", "W2_IAC_02", "W2_IAC_03"]
        if not all(nid in completions for nid in world_2_nodes):
            messages.error(request, "Unlock the Cyber Security Breach Simulator by completing all World 2 nodes first!")
            return redirect("gamification:overworld")

        # Let's see if the user selected compliant MFA in W2_IAC_02
        w2_iac_02_data = completions.get("W2_IAC_02", {}).get("answers", {})
        mfa_value = w2_iac_02_data.get("mfa_enforced", "NOT_COMPLIANT")

        if request.method == "POST":
            if "W2_BOSS_COMPLETE" not in completions:
                completions["W2_BOSS_COMPLETE"] = True
                request.user.security_gems_balance += 300
                request.user.current_progress_percentage = max(request.user.current_progress_percentage, 30)
                badge_name = "The Gatekeeper's Crest"
                if badge_name not in request.user.earned_badges:
                    request.user.earned_badges.append(badge_name)
                request.user.node_completions = completions
                request.user.save()
                messages.success(request, f"Breach Simulator Complete! You've earned the '{badge_name}' Badge and +300 gems!")
            return redirect("gamification:overworld")

        return render(request, "gamification/boss_fight.html", {
            "world_id": "world_2",
            "active_persona": request.user.active_persona,
            "mfa_value": mfa_value,
            "gems_balance": request.user.security_gems_balance,
            "progress": request.user.current_progress_percentage
        })

    elif world_id == "world_3":
        # Check prerequisites
        world_3_nodes = ["W3_END_01", "W3_END_02", "W3_END_03"]
        if not all(nid in completions for nid in world_3_nodes):
            messages.error(request, "Unlock the Boss Fight by completing all World 3 nodes first!")
            return redirect("gamification:overworld")

        # Evaluate answers for success path
        w3_end_01_data = completions.get("W3_END_01", {}).get("answers", {})
        edr_value = w3_end_01_data.get("edr_status", "EDR_NONE")

        w3_end_02_data = completions.get("W3_END_02", {}).get("answers", {})
        patch_value = w3_end_02_data.get("patch_sla", "slow_turtle")

        if request.method == "POST":
            if "W3_BOSS_COMPLETE" not in completions:
                completions["W3_BOSS_COMPLETE"] = True
                request.user.security_gems_balance += 400
                request.user.current_progress_percentage = max(request.user.current_progress_percentage, 40)
                badge_name = "The Iron Outpost Badge"
                if badge_name not in request.user.earned_badges:
                    request.user.earned_badges.append(badge_name)
                request.user.node_completions = completions
                request.user.save()
                messages.success(request, f"Malware Airship Bombardment Beaten! You've earned the '{badge_name}' Badge and +400 gems!")
            return redirect("gamification:overworld")

        return render(request, "gamification/boss_fight.html", {
            "world_id": "world_3",
            "active_persona": request.user.active_persona,
            "edr_value": edr_value,
            "patch_value": patch_value,
            "gems_balance": request.user.security_gems_balance,
            "progress": request.user.current_progress_percentage
        })

    elif world_id == "world_4":
        # Check prerequisites
        world_4_nodes = ["W4_DAT_01", "W4_DAT_02", "W4_DAT_03"]
        if not all(nid in completions for nid in world_4_nodes):
            messages.error(request, "Unlock the Boss Fight by completing all World 4 nodes first!")
            return redirect("gamification:overworld")

        # Evaluate answers for success path
        w4_dat_02_data = completions.get("W4_DAT_02", {}).get("answers", {})
        vault_status = w4_dat_02_data.get("vault_encryption", "REST_PLAINTEXT")

        w4_dat_03_data = completions.get("W4_DAT_03", {}).get("answers", {})
        transit_status = w4_dat_03_data.get("transit_compliant", "false")

        if request.method == "POST":
            if "W4_BOSS_COMPLETE" not in completions:
                completions["W4_BOSS_COMPLETE"] = True
                request.user.security_gems_balance += 500
                request.user.current_progress_percentage = max(request.user.current_progress_percentage, 50)
                badge_name = "Master of the Vault Key"
                if badge_name not in request.user.earned_badges:
                    request.user.earned_badges.append(badge_name)
                request.user.node_completions = completions
                request.user.save()
                messages.success(request, f"The Great Data Heist Simulator Defeated! You've earned the '{badge_name}' Badge and +500 gems!")
            return redirect("gamification:overworld")

        return render(request, "gamification/boss_fight.html", {
            "world_id": "world_4",
            "active_persona": request.user.active_persona,
            "vault_status": vault_status,
            "transit_status": transit_status,
            "gems_balance": request.user.security_gems_balance,
            "progress": request.user.current_progress_percentage
        })

    elif world_id == "world_5":
        # Check prerequisites
        world_5_nodes = ["W5_NET_01", "W5_NET_02"]
        if not all(nid in completions for nid in world_5_nodes):
            messages.error(request, "Unlock the Boss Fight by completing all World 5 nodes first!")
            return redirect("gamification:overworld")

        # Evaluate answers
        w5_net_01_data = completions.get("W5_NET_01", {}).get("answers", {})
        firewall_status = w5_net_01_data.get("firewall_status", "FIREWALL_NONE")

        w5_net_02_data = completions.get("W5_NET_02", {}).get("answers", {})
        wifi_status = w5_net_02_data.get("wifi_status", "open_bridge")

        if request.method == "POST":
            if "W5_BOSS_COMPLETE" not in completions:
                completions["W5_BOSS_COMPLETE"] = True
                request.user.security_gems_balance += 400
                request.user.current_progress_percentage = max(request.user.current_progress_percentage, 60)
                badge_name = "Grid Technician"
                if badge_name not in request.user.earned_badges:
                    request.user.earned_badges.append(badge_name)
                request.user.node_completions = completions
                request.user.save()
                messages.success(request, f"DDoS Storm Invasion Beaten! You've earned the '{badge_name}' Badge and +400 gems!")
            return redirect("gamification:overworld")

        return render(request, "gamification/boss_fight.html", {
            "world_id": "world_5",
            "active_persona": request.user.active_persona,
            "firewall_status": firewall_status,
            "wifi_status": wifi_status,
            "gems_balance": request.user.security_gems_balance,
            "progress": request.user.current_progress_percentage
        })

    elif world_id == "world_6":
        # Check prerequisites
        world_6_nodes = ["W6_SAT_01", "W6_GOV_02"]
        if not all(nid in completions for nid in world_6_nodes):
            messages.error(request, "Unlock the Boss Fight by completing all World 6 nodes first!")
            return redirect("gamification:overworld")

        if request.method == "POST":
            if "W6_BOSS_COMPLETE" not in completions:
                completions["W6_BOSS_COMPLETE"] = True
                request.user.security_gems_balance += 500
                request.user.current_progress_percentage = max(request.user.current_progress_percentage, 75)
                badge_name = "Troop Commander"
                if badge_name not in request.user.earned_badges:
                    request.user.earned_badges.append(badge_name)
                request.user.node_completions = completions
                request.user.save()
                messages.success(request, f"Compliance Audit Showdown Beaten! You've earned the '{badge_name}' Badge and +500 gems!")
            return redirect("gamification:overworld")

        return render(request, "gamification/boss_fight.html", {
            "world_id": "world_6",
            "active_persona": request.user.active_persona,
            "gems_balance": request.user.security_gems_balance,
            "progress": request.user.current_progress_percentage
        })

    elif world_id == "world_7":
        # Check prerequisites
        world_7_nodes = ["W7_VPM_01", "W7_MON_02"]
        if not all(nid in completions for nid in world_7_nodes):
            messages.error(request, "Unlock the Boss Fight by completing all World 7 nodes first!")
            return redirect("gamification:overworld")

        # Evaluate answers
        w7_mon_02_data = completions.get("W7_MON_02", {}).get("answers", {})
        logbook_status = w7_mon_02_data.get("logbook_status", "LOGBOOK_NONE")

        if request.method == "POST":
            if "W7_BOSS_COMPLETE" not in completions:
                completions["W7_BOSS_COMPLETE"] = True
                request.user.security_gems_balance += 500
                request.user.current_progress_percentage = max(request.user.current_progress_percentage, 90)
                badge_name = "Watchtower Sentry"
                if badge_name not in request.user.earned_badges:
                    request.user.earned_badges.append(badge_name)
                request.user.node_completions = completions
                request.user.save()
                messages.success(request, f"Live Dashboard Integration Reveal Complete! You've earned the '{badge_name}' Badge and +500 gems!")
            return redirect("gamification:overworld")

        return render(request, "gamification/boss_fight.html", {
            "world_id": "world_7",
            "active_persona": request.user.active_persona,
            "logbook_status": logbook_status,
            "gems_balance": request.user.security_gems_balance,
            "progress": request.user.current_progress_percentage
        })

    elif world_id == "world_8":
        # Check prerequisites
        world_8_nodes = ["W8_DRP_01"]
        if not all(nid in completions for nid in world_8_nodes):
            messages.error(request, "Unlock the Boss Fight by completing all World 8 nodes first!")
            return redirect("gamification:overworld")

        # Evaluate answers
        w8_drp_01_data = completions.get("W8_DRP_01", {}).get("answers", {})
        backup_status = w8_drp_01_data.get("backup_status", "BACKUP_NONE")

        if request.method == "POST":
            if "W8_BOSS_COMPLETE" not in completions:
                completions["W8_BOSS_COMPLETE"] = True
                request.user.security_gems_balance += 1000
                request.user.current_progress_percentage = max(request.user.current_progress_percentage, 100)
                badge_name = "Savior of the Kingdom"
                if badge_name not in request.user.earned_badges:
                    request.user.earned_badges.append(badge_name)
                request.user.node_completions = completions
                request.user.save()
                messages.success(request, f"Bowser Ransomware Invasion Beaten! You've earned the '{badge_name}' Badge and +1000 gems!")
            return redirect("gamification:overworld")

        return render(request, "gamification/boss_fight.html", {
            "world_id": "world_8",
            "active_persona": request.user.active_persona,
            "backup_status": backup_status,
            "gems_balance": request.user.security_gems_balance,
            "progress": request.user.current_progress_percentage
        })

    else:
        raise Http404("World not found")


@login_required
def reset_quest_view(request):
    """Utility endpoint to completely wipe and reset the gamified compliance state for testing."""
    request.user.active_persona = "UNASSIGNED"
    request.user.current_progress_percentage = 0
    request.user.security_gems_balance = 0
    request.user.earned_badges = []
    request.user.remediation_queue = []
    request.user.business_industry = ""
    request.user.business_purpose = ""
    request.user.business_structure = ""
    request.user.locations = []
    request.user.website_url = ""
    request.user.node_completions = {}
    request.user.save()

    messages.info(request, "Compliance quest state successfully reset to default.")
    return redirect("gamification:select_persona")

