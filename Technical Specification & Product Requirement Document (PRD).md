# **Technical Specification & Product Requirement Document (PRD)**

**Project Title:** ThreatWatch Gamified Compliance Campaign Engine

**Target Integration Environment:** https://github.com/ozzy76/threatwatch

**Compliance Registry Engine:** Secure Controls Framework (scf-full-2026.1.json)

**Design Paradigm:** The Eco-Cyber Metropolis (Strategic Smart City Metaphor)

## **1\. Executive Project Scope & Vision**

This document details the architectural specifications for translating the technical compliance directives of the Secure Controls Framework (SCF), HIPAA, and PCI-DSS into an interactive, visual smart-city campaign map.

The application architecture segments user interaction into two balanced operational viewpoints:

* **Campaign Mode (The City Grid Overworld):** A progressive map mapping districts and sectors, utilized to run risk profiles, identify core assets, and execute remediation workflows.  
* **Command Center Mode (Live Telemetry Dashboard):** A real-time, runtime interface tracking system health, infrastructure alerts, and live vulnerability streaming.

### **Dynamic Persona Adaptation Logic**

The platform tracks an omnipresent state variable userPersona ("BUSINESS\_OWNER" | "IT\_STAFF"). The interface modifies layout density, terminology, and component access based on this setting:

* **BUSINESS\_OWNER:** Completely jargon-free interface layer. Replaces compliance phrasing with physical urban metaphors (e.g., city walls, infrastructure armor, biometric checkpoints). Uses single-question progressive wizards.  
* **IT\_STAFF:** Exposes explicit technical control descriptors (e.g., AST-01, IAC-02), embeds batch automation tools (e.g., CSV imports), and outputs developer-ready policy ledgers.

## **2\. Universal Design System: "The Eco-Cyber Metropolis"**

To maintain absolute uniformity across both the Campaign Map and the Command Center Dashboard, all newly engineered components must inherit this design theme:

* **Visual Identity:** Clean, high-contrast, illustrative isometric grid layout with thick clean strokes and vibrant pastel-neon balancing accents.  
* **The Color Palette:**  
  * **Secure / Aligned State:** Vibrant Mint Green (\#24C854)  
  * **Warning / Exposed State:** Energy Gold Amber (\#FFCC00)  
  * **Breached / High-Risk State:** Neon Crimson Red (\#E52521)  
  * **Canvas Environment Background:** Crisp Sky Blue (\#5C94FC) paired with floating, soft-shadowed white container boxes styled like sleek, clean cloud platforms.  
* **Structural Geometry:** All container blocks, modal boxes, and data rows must leverage heavy rounded corners (border-radius: 16px to 24px) outlined with solid dark charcoal strokes (2px to 3px), abandoning sharp corporate edges for a tactile, premium animated comic feel.  
* **Typography Hierarchy:** Interface headers must render in a friendly, heavy, rounded sans-serif (e.g., *Fredoka* or *Nunito*), while pure data arrays use a clean, geometric monospaced typeface.

## **3\. Phase 1: Onboarding & Time-To-Value (TTV) Scanner**

### **Demographics Intake Engine**

Users advance through a 6-step progressive intake wizard processing basic corporate characteristics:

1. company\_name (Standard input)  
2. business\_industry (Selectable illustrative cards: E-Commerce, Healthcare, SaaS, Finance, Retail, Professional Services)  
3. business\_purpose (Text area evaluating high-level scope characteristics)  
4. business\_structure (Radio elements: LLC, Corporation, Sole Proprietorship)  
5. locations (Multi-select checkbox mapping regional legal jurisdictions like CCPA/GDPR)  
6. website\_url (Text input with high-visibility skip option: *"I don't have a business website right now"*)

### **Asynchronous SSL Security Scanner**

Submitting a target domain initiates an automated background verification call. The platform triggers an immediate **15%**visual advancement on the global progress bar while evaluating network transport encryption:

```
                  [ User Inputs URL ]
                           │
                           ▼
             [ Trigger Background SSL Ping ]
                           │
            ┌──────────────┴──────────────┐
            ▼                             ▼
     [ HTTPS Active ]               [ HTTP Only ]
            │                             │
            ▼                             ▼
    (SUCCESS STATE)                  (GAP STATE)
   - Droid Mascot Cheers           - Droid holds Wrench
   - +50 Security Gems             - "SSL Patch" Quest added
   - Shield Token awarded          - Clean remediation prompt
```

*   
  **The Bypass State:** Clicking the skip trigger routes the user cleanly past the scanner with positive reinforcement from the mascot: *"No website? No problem at all\! Honestly, that’s one less asset for hackers to target. Let's move on to locking down your internal setup\!"*

## **4\. Complete 8-Sector Master Campaign Map Configuration**

This schema maps all 32 core compliance domains into an integrated urban topology. Programmatic development agents must map all interface completion interactions back to the user's primary framework ledger file (scf-full-2026.1.json).

JSON

```
{
  "$schema": "https://threatwatch.cyber/schemas/gamified-compliance.v1.json",
  "blueprint_metadata": {
    "target_repository": "https://github.com/ozzy76/threatwatch",
    "engine_version": "2026.05.26",
    "framework_source": "scf-full-2026.1.json"
  },
  "campaign_map_master": {
    "sector_1": {
      "world_id": "W1_AST",
      "scf_domain_mapping": "AST",
      "theme_styles": {
        "background_asset": "cyber_metropolis_city_grid.svg",
        "path_style": "animated_neon_transit_line",
        "active_node_animation": "pulse_glow"
      },
      "nodes": [
        {
          "node_id": "W1_AST_01",
          "scf_control_references": ["AST-01", "AST-04"],
          "display_title": "The Physical Grid",
          "ui_modes": {
            "BUSINESS_OWNER": {
              "interaction_type": "TactileSliders",
              "prompt": "Let's log the infrastructure footprint. Count the physical workstation devices your team uses to run the city:",
              "configuration": { "sliders": ["Laptops", "Desktops", "BYOD Mobile Devices", "Local Servers"] }
            },
            "IT_STAFF": {
              "interaction_type": "CsvDragAndDrop",
              "prompt": "Upload active directory, MDM inventory list, or asset tracking ledger:",
              "configuration": { "accepted_extensions": [".csv", ".json"], "auto_parse_mapping": "SCF_AST_01_PARSER" }
            }
          },
          "rewards": { "gems": 50, "badge": "Hardware Cartographer" }
        },
        {
          "node_id": "W1_AST_02",
          "scf_control_references": ["AST-02", "AST-05"],
          "display_title": "Cloud Sky-Rises",
          "ui_modes": {
            "BUSINESS_OWNER": {
              "interaction_type": "LogoGridSelect",
              "prompt": "Where do your digital operations live on the web? Tag your cloud hostings and outposts:",
              "configuration": { "logos": ["Google Workspace", "Microsoft 365", "Dropbox", "AWS", "Salesforce"] }
            },
            "IT_STAFF": {
              "interaction_type": "TechnicalCheckboxMatrix",
              "prompt": "Identify and verify deployed multi-tenant cloud architectures and IaaS configurations:",
              "configuration": { "categories": ["SaaS Production Apps", "Cloud Storage Buckets", "VPC Compute Instances"] }
            }
          },
          "rewards": { "gems": 75 }
        },
        {
          "node_id": "W1_AST_03",
          "scf_control_references": ["AST-03"],
          "display_title": "The Operational Inventory",
          "ui_modes": {
            "BUSINESS_OWNER": {
              "interaction_type": "SimpleDropdownSelect",
              "prompt": "What primary software engine configurations drive your workflows daily?",
              "configuration": { "options": ["Windows Ecosystem", "Apple/macOS Platform", "Cloud/Browser-Only Tools"] }
            },
            "IT_STAFF": {
              "interaction_type": "TextInputList",
              "prompt": "Enumerate operating system images and deployment baselines for tracking:",
              "configuration": { "placeholder": "e.g., Ubuntu 24.04 LTS, macOS Sequoia Enterprise Build" }
            }
          },
          "rewards": { "gems": 75 }
        }
      ],
      "boss_fight": {
        "trigger_node_condition": "ALL_NODES_COMPLETE",
        "ui_variant": "CityCensusModal",
        "mascot_asset_variant": "city_planner",
        "summary_engine": "GENERATE_SCF_ASSET_INVENTORY_JSON",
        "deliverable_action": "DOWNLOAD_PDF_ASSET_INVENTORY_REPORT",
        "labels": {
          "BUSINESS_OWNER": "Incredible job! We’ve mapped your entire metropolitan footprint. Your asset inventory report is locked and ready for audit reviews.",
          "IT_STAFF": "Asset discovery initialization pipeline finalized. Generating comprehensive audit logs for structural SCF system validation."
        },
        "state_mutations": { "gems_increment": 200, "global_progress_percentage": 15, "unlock_next_world": "W2_IAC" }
      }
    },
    "sector_2": {
      "world_id": "W2_IAC",
      "scf_domain_mapping": "IAC",
      "theme_styles": {
        "background_asset": "biometric_checkpoint_sector.svg",
        "path_style": "laser_beam_trail",
        "active_node_animation": "identity_scan_flicker"
      },
      "nodes": [
        {
          "node_id": "W2_IAC_01",
          "scf_control_references": ["IAC-01"],
          "display_title": "The Gatekeeper Roll Call",
          "ui_modes": {
            "BUSINESS_OWNER": {
              "interaction_type": "BinaryVisualCardSelect",
              "prompt": "When team members access city applications, does everyone use their own unique ID, or are groups sharing generic master logins?",
              "configuration": {
                "card_true": { "label": "Unique Personal IDs", "illustration": "individual_id_badges" },
                "card_false": { "label": "Shared Shared Access Keys", "illustration": "group_sharing_one_key", "action": "INJECT_REMEDIATION_COUNTER" }
              }
            },
            "IT_STAFF": {
              "interaction_type": "ToggleList",
              "prompt": "Confirm unique attribution tracking and eliminate active generic or non-person organizational credentials:",
              "configuration": { "toggles": ["Enforced unique UPN tracking", "Disabled active generic shared administrative accounts"] }
            }
          },
          "rewards": { "gems": 100 }
        },
        {
          "node_id": "W2_IAC_02",
          "scf_control_references": ["IAC-02", "IAC-03"],
          "display_title": "Biometric Access Control",
          "ui_modes": {
            "BUSINESS_OWNER": {
              "interaction_type": "CardBranchingSelect",
              "prompt": "When accessing core operational centers (like emails or finances), do your systems enforce a second confirmation step, like a mobile authorization code?",
              "configuration": {
                "options": [
                  { "label": "Yes, universally enforced!", "value": "COMPLIANT" },
                  { "label": "Enforced only for specific roles.", "value": "PARTIAL" },
                  { "label": "What is two-step authorization?", "value": "EXPLAIN", "action": "TRIGGER_CONTEXTUAL_MFA_ANIMATION" }
                ]
              }
            },
            "IT_STAFF": {
              "interaction_type": "MatrixControlGrid",
              "prompt": "Audit Multi-Factor Authentication enforcement states across systems architecture environments:",
              "configuration": {
                "rows": ["Administrative Access Channels", "Remote Infrastructure/VPN Entry Points", "Standard Workspace Identity Sessions"],
                "columns": ["MFA Enforced globally", "SMS/Voice Fallback Allowed", "Insecure Single-Factor Authentication active"]
              }
            }
          },
          "rewards": { "gems": 100 }
        },
        {
          "node_id": "W2_IAC_03",
          "scf_control_references": ["IAC-11", "IAC-12"],
          "display_title": "The Vault Locks",
          "ui_modes": {
            "BUSINESS_OWNER": {
              "interaction_type": "RadioListExploratory",
              "prompt": "Where are passwords stored across the organization? Be completely transparent, the system droids won't judge!",
              "configuration": {
                "options": [
                  { "label": "Written down physically on papers or notebooks.", "compliance_weight": 0 },
                  { "label": "Stored unencrypted within digital spreadsheets or browser defaults.", "compliance_weight": 1 },
                  { "label": "Managed inside an enterprise credential vault (e.g., 1Password, Bitwarden).", "compliance_weight": 3, "ui_action": "UPGRADE_DISTRICT_OUTPOST_VISUAL" }
                ]
              }
            },
            "IT_STAFF": {
              "interaction_type": "TechnicalInputFields",
              "prompt": "Specify complexity configuration criteria for enterprise access control management systems:",
              "configuration": { "fields": ["Minimum character length parameters", "Entropy requirements", "Rotation/Expiry configurations"] }
            }
          },
          "rewards": { "gems": 100 }
        }
      ],
      "boss_fight": {
        "trigger_node_condition": "ALL_NODES_COMPLETE",
        "ui_variant": "InteractiveBreachSimulatorModal",
        "simulation_parameters": {
          "adversary": "Intruder_Brute_Force",
          "conditional_gate_check": "W2_IAC_02_VALUE",
          "animations": {
            "on_compliant": { "sequence": ["intruder_attempts_entry", "biometric_shield_blocks_access", "mascot_victory_pose"] },
            "on_non_compliant": { "sequence": ["intruder_bypasses_gate", "checkpoint_shatters", "mascot_deploys_remediation_wizard"] }
          }
        },
        "deliverable_action": "GENERATE_CUSTOM_IDENTITY_ACCESS_CONTROL_POLICY_DOC",
        "state_mutations": { "gems_increment": 300, "global_progress_percentage": 30, "award_badge": "The Gatekeeper’s Crest", "unlock_next_world": "W3_END" }
      }
    },
    "sector_3": {
      "world_id": "W3_END",
      "scf_domain_mapping": "END",
      "theme_styles": {
        "background_asset": "power_station_perimeter.svg",
        "path_style": "circuit_trace_line",
        "active_node_animation": "plasma_charge"
      },
      "nodes": [
        {
          "node_id": "W3_END_01",
          "scf_control_references": ["END-01", "END-02"],
          "display_title": "Grid Armor",
          "ui_modes": {
            "BUSINESS_OWNER": {
              "interaction_type": "VisualToggleGrid",
              "prompt": "System anomalies look for vulnerable nodes on your endpoint endpoints. Are workstations reinforced with active defense software like Defender or CrowdStrike?",
              "configuration": {
                "options": [
                  { "label": "Yes, comprehensively armored!", "value": "EDR_ACTIVE", "ui_effect": "apply_shield_overlays" },
                  { "label": "Partial or unverified states.", "value": "EDR_PARTIAL", "ui_effect": "yellow_warning_glow" },
                  { "label": "No active protection software verified.", "value": "EDR_NONE", "ui_effect": "gray_out_nodes" }
                ]
              }
            },
            "IT_STAFF": {
              "interaction_type": "TechnicalDropdownAndInput",
              "prompt": "Specify deployed Endpoint Detection and Response (EDR) configurations:",
              "configuration": { "supported_agents": ["CrowdStrike Falcon", "Microsoft Defender for Endpoint", "SentinelOne"], "mdm_sync_toggle": "Sync via MDM API" }
            }
          },
          "rewards": { "gems": 100, "badge": "Armor Bearer" }
        },
        {
          "node_id": "W3_END_02",
          "scf_control_references": ["END-06"],
          "display_title": "The Patch Forge",
          "ui_modes": {
            "BUSINESS_OWNER": {
              "interaction_type": "MarioCardSelection",
              "prompt": "Sustained software cracks compromise workstation structures. How are patches deployed across systems?",
              "configuration": {
                "cards": [
                  { "id": "slow_turtle", "title": "Manual Maintenance", "description": "Left to users to accept whenever prompted manually.", "icon": "manual_wrench" },
                  { "id": "automatic_clock", "title": "Automated Cycles", "description": "Forced updates execute within a 7-day window.", "icon": "timed_updater" },
                  { "id": "star_power", "title": "Centralized Orchestration", "description": "Forced global overrides update all tools automatically overnight.", "icon": "plasma_bolt" }
                ]
              }
            },
            "IT_STAFF": {
              "interaction_type": "SlidingThresholdMatrix",
              "prompt": "Define organizational patch deployment and vulnerability remediation SLAs:",
              "configuration": { "critical_patch_window_days": [1, 3, 7, 14, 30], "automated_enforcement_policy": "boolean" }
            }
          },
          "rewards": { "gems": 125 }
        },
        {
          "node_id": "W3_END_03",
          "scf_control_references": ["END-03", "IAC-04"],
          "display_title": "Metropolitan Permissions",
          "ui_modes": {
            "BUSINESS_OWNER": {
              "interaction_type": "BinaryMetaphorSelect",
              "prompt": "Do standard terminal users access endpoints with full administrative rights, allowing uncontrolled program installation?",
              "configuration": {
                "option_compliant": { "title": "Standard Access Rules", "desc": "Explicit authorization required to make configurations.", "animation": "secure_station" },
                "option_risk": { "title": "Unrestricted Root Entry", "desc": "Every employee can run and execute unverified software blocks.", "animation": "system_glitch_outbreak" }
              }
            },
            "IT_STAFF": {
              "interaction_type": "LeastPrivilegeCheckboxAudit",
              "prompt": "Enforce Least Privilege Architecture (SCF END-03). Verify restriction of administrative access:",
              "configuration": { "assertions": ["Standard endpoints run under restricted non-privileged user space context.", "Privilege escalation requires verified central validation challenge."] }
            }
          },
          "rewards": { "gems": 125 }
        }
      ],
      "boss_fight": {
        "trigger_node_condition": "ALL_NODES_COMPLETE",
        "ui_variant": "InteractivePhishingFleetSimulationModal",
        "simulation_parameters": {
          "hazard_event": "Malware_Swarm_Infiltration",
          "dependencies": ["W3_END_01_VALUE", "W3_END_02_VALUE"],
          "animations": {
            "success_branch": { "trigger_condition": "EDR_ACTIVE && (automatic_clock || star_power)", "sequence": ["anomalies_drop_payloads", "district_shields_deflect_attack", "mascot_victory_pose"] },
            "failure_branch": { "trigger_condition": "EDR_NONE || slow_turtle", "sequence": ["anomalies_drop_payloads", "outpost_flickers_offline", "mascot_deploys_remediation_patch"] }
          }
        },
        "deliverable_action": "GENERATE_STANDARD_ENDPOINT_SECURITY_POLICY_PDF",
        "state_mutations": { "gems_increment": 400, "global_progress_percentage": 50, "award_badge": "The Iron Outpost Badge", "unlock_next_world": "W4_DAT" }
      }
    },
    "sector_4": {
      "world_id": "W4_DAT",
      "scf_domain_mapping": ["DAT", "CRY", "PRI"],
      "theme_styles": {
        "background_asset": "central_core_data_bank.svg",
        "path_style": "glowing_bus_trail",
        "active_node_animation": "encryption_sparkle"
      },
      "nodes": [
        {
          "node_id": "W4_DAT_01",
          "scf_control_references": ["DAT-01", "PRI-01"],
          "display_title": "Asset Classification",
          "ui_modes": {
            "BUSINESS_OWNER": {
              "interaction_type": "DragAndDropSortingGame",
              "prompt": "Organize your data assets into safe classifications to structure protection tiers:",
              "configuration": { "bins": ["Public Records", "Operational Info", "Highly Sensitive PII/Financial Vaults"], "visual_style": "cyber_vault_bins" }
            },
            "IT_STAFF": {
              "interaction_type": "DataClassificationSchemaMatrix",
              "prompt": "Establish data identification and classification matrices (SCF DAT-01 / PRI-01):",
              "configuration": { "tiers": ["Public / Unclassified", "Internal Use Only", "Confidential / Restricted / PII / PHI"], "regulatory_tags": ["HIPAA_PHI", "PCI_DSS_CHD", "GDPR_PII"] }
            }
          },
          "rewards": { "gems": 150, "badge": "Grand Archivist" }
        },
        {
          "node_id": "W4_DAT_02",
          "scf_control_references": ["CRY-01", "DAT-02"],
          "display_title": "Static Core Encryption",
          "ui_modes": {
            "BUSINESS_OWNER": {
              "interaction_type": "TactileChestLockSelect",
              "prompt": "When sensitive database blocks reside inside static storage storage, are they cryptographically scrambled?",
              "configuration": {
                "options": [
                  { "label": "Completely encrypted and scrambled.", "value": "REST_ENCRYPTED", "icon": "reinforced_vault" },
                  { "label": "Stored in plaintext without active transformation.", "value": "REST_PLAINTEXT", "icon": "open_storage_bay" },
                  { "label": "Current baseline unidentified.", "value": "REST_UNKNOWN", "icon": "question_block" }
                ]
              }
            },
            "IT_STAFF": {
              "interaction_type": "CryptographicStandardVerification",
              "prompt": "Verify structural implementation of Data-at-Rest cryptographic profiles (SCF CRY-01):",
              "configuration": { "minimum_standard": "AES-256 cipher encryption required", "target_environments": ["Cloud Volumes", "Local Backups", "SaaS Storage Buckets"] }
            }
          },
          "rewards": { "gems": 150 }
        },
        {
          "node_id": "W4_DAT_03",
          "scf_control_references": ["CRY-03"],
          "display_title": "Transit Pipeline Protection",
          "ui_modes": {
            "BUSINESS_OWNER": {
              "interaction_type": "CarrierMetaphorGrid",
              "prompt": "When routing operational information across the open web, do your pipeline pathways isolate data streams from spoofing?",
              "configuration": {
                "options": [
                  { "title": "Secure Pipelines (TLS/HTTPS Enforced)", "desc": "Information routes within an isolated capsule rail.", "compliant": true },
                  { "title": "Cleartext Channels (HTTP Open Port)", "desc": "Information travels across an open public motorway.", "compliant": false }
                ]
              }
            },
            "IT_STAFF": {
              "interaction_type": "CipherSuitePolicyAudit",
              "prompt": "Audit and enforce Data-in-Transit cryptographic operational configurations (SCF CRY-03):",
              "configuration": { "disallowed_protocols": ["SSLv3", "TLS 1.0", "TLS 1.1"], "mandatory_protocols": ["TLS 1.2 minimum", "TLS 1.3 preferred"], "hsts_enforcement": "boolean" }
            }
          },
          "rewards": { "gems": 150 }
        }
      ],
      "boss_fight": {
        "trigger_node_condition": "ALL_NODES_COMPLETE",
        "ui_variant": "TheGreatDataHeistSimulator",
        "simulation_parameters": { "adversary": "Data_Thief_Infiltration", "evaluations": { "vault_door_status": "W4_DAT_02_VALUE", "transit_pipeline_status": "W4_DAT_03_VALUE" }, "animations": { "perfect_defense": { "trigger_condition": "REST_ENCRYPTED && COMPLIANT", "sequence": ["thief_breaches_vault", "finds_unreadable_scrambled_code_blocks", "thief_retreats_failed", "mascot_celebration"] }, "data_leak_warning": { "trigger_condition": "REST_PLAINTEXT || REST_UNKNOWN", "sequence": ["thief_extracts_plaintext_blocks", "mascot_triggers_emergency_freeze", "remediation_blueprint_drop"] } } },
        "deliverable_action": "GENERATE_DATA_PROTECTION_AND_PRIVACY_STANDARDS_LEDGER",
        "state_mutations": { "gems_increment": 500, "global_progress_percentage": 75, "award_badge": "Master of the Vault Key", "unlock_next_world": "W5_NET_SYS" }
      }
    },
    "sector_5": {
      "world_id": "W5_NET_SYS",
      "scf_domain_mapping": ["NET", "CHS", "WLS", "SA", "CM", "MA"],
      "theme_styles": {
        "background_asset": "subterranean_pipe_conduits.svg",
        "path_style": "pulsing_energy_stream",
        "active_node_animation": "lightning_arc"
      },
      "nodes": [
        {
          "node_id": "W5_NET_01",
          "scf_control_references": ["NET-01", "NET-04"],
          "display_title": "Boundary Routing Filters",
          "ui_modes": {
            "BUSINESS_OWNER": {
              "interaction_type": "BinaryVisualCardSelect",
              "prompt": "Does your office infrastructure feature an isolated firewall boundary configuration protecting city terminals from perimeter tracking?",
              "configuration": {
                "card_true": { "label": "Dedicated Boundary Firewall Active", "illustration": "armored_checkpoint" },
                "card_false": { "label": "Standard Consumer Router Only", "illustration": "unprotected_conduit" }
              }
            },
            "IT_STAFF": {
              "interaction_type": "NetworkTopologyChecklist",
              "prompt": "Verify network boundary architecture and perimeter access control lists (ACLs):",
              "configuration": { "requirements": ["Default-deny inbound traffic stance", "Stateful inspection tracking enabled", "Quarterly configuration audit matrix"] }
            }
          },
          "rewards": { "gems": 150 }
        },
        {
          "node_id": "W5_NET_02",
          "scf_control_references": ["WLS-01", "NET-09"],
          "display_title": "Wireless Network Segregation",
          "ui_modes": {
            "BUSINESS_OWNER": {
              "interaction_type": "MarioCardSelection",
              "prompt": "When unverified guests access office Wi-Fi arrays, are they routed into the same channel containing core internal systems?",
              "configuration": {
                "cards": [
                  { "id": "open_bridge", "title": "Shared Unified Channels", "description": "All devices share internal resource access paths.", "icon": "broken_gate" },
                  { "id": "guarded_gate", "title": "Isolated Sub-Network", "description": "Guest access paths route to direct internet gateways with zero internal routing loops.", "icon": "quarantined_island" }
                ]
              }
            },
            "IT_STAFF": {
              "interaction_type": "WirelessSecurityForm",
              "prompt": "Audit organizational wireless access configuration parameters (SCF WLS-01):",
              "configuration": { "encryption_standard": ["WPA3-Enterprise", "WPA2-AES-PSK"], "vlan_segmentation": "Enforced logical VLAN segregation verified between corporate and guest endpoints" }
            }
          },
          "rewards": { "gems": 150, "badge": "Grid Technician" }
        }
      ],
      "boss_fight": {
        "trigger_node_condition": "ALL_NODES_COMPLETE",
        "ui_variant": "TrafficFloodInvasionModal",
        "simulation_parameters": { "hazard_event": "Volumetric_DDoS_Flood", "dependencies": ["W5_NET_01_VALUE"], "animations": { "success_branch": { "trigger_condition": "NET_FIREWALL_ACTIVE && Guarded_Gate", "sequence": ["traffic_surge_hits_perimeter", "boundary_filters_isolate_malicious_packets", "mascot_victory_salute"] } } },
        "state_mutations": { "gems_increment": 400, "global_progress_percentage": 60, "unlock_next_world": "W6_GOV" }
      }
    },
    "sector_6": {
      "world_id": "W6_GOV",
      "scf_domain_mapping": ["GOV", "RM", "HRS", "SAT", "PPL", "SEA", "EPH"],
      "theme_styles": {
        "background_asset": "municipal_training_academy.svg",
        "path_style": "polished_stone_walkway",
        "active_node_animation": "academy_ledger_pulse"
      },
      "nodes": [
        {
          "node_id": "W6_SAT_01",
          "scf_control_references": ["SAT-01", "SAT-03"],
          "display_title": "Sentry Boot Camp",
          "ui_modes": {
            "BUSINESS_OWNER": {
              "interaction_type": "TrainingVerificationMiniGame",
              "prompt": "Verify security training metrics. Complete the mini-game by allocating validation logs to active staff:",
              "configuration": { "game_engine": "DRAG_DROP_VERIFY", "game_assets": { "draggable_item": "training_scroll_asset", "target_slots": ["Staff_Unit_Alpha", "Staff_Unit_Beta", "Staff_Unit_Gamma"] } }
            },
            "IT_STAFF": {
              "interaction_type": "TrainingRosterUpload",
              "prompt": "Upload verification parameters for annual security awareness and training compliance criteria:",
              "configuration": { "accept_formats": [".csv", ".xlsx"], "parse_columns": ["employee_email", "completion_status", "last_phish_test_date"] }
            }
          },
          "rewards": { "gems": 200, "badge": "Troop Commander" }
        },
        {
          "node_id": "W6_GOV_02",
          "scf_control_references": ["PPL-01", "GOV-01"],
          "display_title": "Administrative Directives",
          "ui_modes": {
            "BUSINESS_OWNER": {
              "interaction_type": "OneClickPolicySign",
              "prompt": "Establish corporate governance. Adopt pre-mapped administrative policy configurations customized for current regional standards:",
              "configuration": { "action_hook": "GENERATE_AND_SIGN_MASTER_POLICY" }
            },
            "IT_STAFF": {
              "interaction_type": "PolicyMappingMatrix",
              "prompt": "Map internal control policies to required corporate governance framework frameworks:",
              "configuration": { "required_policies": ["Information Security Plan", "Acceptable Use Standard", "Vendor Management Policy"] }
            }
          },
          "rewards": { "gems": 150 }
        }
      ],
      "boss_fight": {
        "trigger_node_condition": "ALL_NODES_COMPLETE",
        "ui_variant": "Compliance_Audit_Showdown",
        "deliverable_action": "EXPORT_METROPOLITAN_COMPLIANCE_BOOK_PDF",
        "state_mutations": { "gems_increment": 500, "global_progress_percentage": 75, "unlock_next_world": "W7_MON" }
      }
    },
    "sector_7": {
      "world_id": "W7_MON",
      "scf_domain_mapping": ["A&A", "VPM", "MON", "THR", "RS", "PM", "TCO", "VMM"],
      "theme_styles": {
        "background_asset": "sentry_radar_watchtowers.svg",
        "path_style": "radar_ping_line",
        "active_node_animation": "sonar_ping"
      },
      "nodes": [
        {
          "node_id": "W7_VPM_01",
          "scf_control_references": ["VPM-01", "VPM-02"],
          "display_title": "Sentry Array Deployment",
          "ui_modes": {
            "BUSINESS_OWNER": {
              "interaction_type": "MascotActionActivate",
              "prompt": "Deploy automated radar systems to monitor infrastructure boundaries for potential systemic weaknesses:",
              "configuration": { "button_label": "Initialize System Sentry Array" }
            },
            "IT_STAFF": {
              "interaction_type": "VulnerabilityScannerHook",
              "prompt": "Configure scan configurations and scheduling parameters for automated perimeter vulnerability assessments:",
              "configuration": { "scan_intervals": ["Daily", "Weekly", "Monthly"], "target_scope": ["External CIDR Blocks", "Internal Production Subnets"] }
            }
          },
          "rewards": { "gems": 200, "badge": "Watchtower Sentry", "dashboard_widget_unlock": "vulnerability_telemetry_table" }
        },
        {
          "node_id": "W7_MON_02",
          "scf_control_references": ["MON-01", "A&A-02"],
          "display_title": "The Central Log Archive",
          "ui_modes": {
            "BUSINESS_OWNER": {
              "interaction_type": "BinaryVisualCardSelect",
              "prompt": "Are system access paths recording transactional trails to identify structural entry events?",
              "configuration": {
                "card_true": { "label": "Immutable Logs Active", "icon": "secure_system_ledger" },
                "card_false": { "label": "No Logging Enabled", "icon": "blindfolded_sentry" }
              }
            },
            "IT_STAFF": {
              "interaction_type": "SiemConfigurationForm",
              "prompt": "Verify ingestion architecture and immutability tracking of structural infrastructure logging trails (SCF A&A-02):",
              "configuration": { "log_retention_period_days": 90, "siem_integration_active": "boolean" }
            }
          },
          "rewards": { "gems": 200, "dashboard_widget_unlock": "live_threat_telemetry_hud" }
        }
      ],
      "boss_fight": {
        "trigger_node_condition": "ALL_NODES_COMPLETE",
        "ui_variant": "Live_Dashboard_Integration_Reveal",
        "labels": {
          "BUSINESS_OWNER": "Monitoring array integration complete. Live tracking metrics are now initialized within the main Command Center console layout.",
          "IT_STAFF": "Continuous telemetry streaming verified. Activating corresponding runtime tracking widgets inside the core user interface workspace."
        },
        "state_mutations": { "gems_increment": 500, "global_progress_percentage": 90, "unlock_next_world": "W8_CRT" }
      }
    },
    "sector_8": {
      "world_id": "W8_CRT",
      "scf_domain_mapping": ["IR", "BCP", "DRP", "PE", "DSI", "FCE", "OPS", "IOM"],
      "theme_styles": {
        "background_asset": "emergency_operations_center.svg",
        "path_style": "hazard_stripe_trail",
        "active_node_animation": "emergency_beacon"
      },
      "nodes": [
        {
          "node_id": "W8_DRP_01",
          "scf_control_references": ["DRP-01", "BCP-02"],
          "display_title": "Isolated Backup Capsules",
          "ui_modes": {
            "BUSINESS_OWNER": {
              "interaction_type": "TactileCapsuleCheck",
              "prompt": "If an operational catastrophe system crash compromises the city grid, do isolated external recovery copies exist to rebuild infrastructure?",
              "configuration": {
                "options": [
                  { "label": "Yes, immutable off-site daily backups executed.", "value": "BACKUP_ISOLATED" },
                  { "label": "Backups exist but connect directly to the active system tree.", "value": "BACKUP_CONNECTED" },
                  { "label": "No current system data backup strategy configured.", "value": "BACKUP_NONE" }
                ]
              }
            },
            "IT_STAFF": {
              "interaction_type": "DisasterRecoverySlaForm",
              "prompt": "Define organizational Recovery Point Objectives (RPO) and Recovery Time Objectives (RTO):",
              "configuration": { "rpo_threshold_hours": 24, "rto_threshold_hours": 4, "immutable_backups_enforced": "boolean" }
            }
          },
          "rewards": { "gems": 250, "badge": "Time Mage" }
        }
      ],
      "boss_fight": {
        "trigger_node_condition": "ALL_NODES_COMPLETE",
        "ui_variant": "Ransomware_Invasion_Simulation",
        "simulation_parameters": {
          "crisis_scenario": "Systemic_Ransomware_Lockdown",
          "required_mitigation_action": "DEPLOY_RECOVERY_CAPSULE",
          "animations": {
            "victory_sequence": {
              "trigger_action_success": "USER_INITIALIZED_CAPSULE_RECOVERY_TIMED",
              "sequence": ["terminal_glitches_red", "system_ransomware_alert_presents", "user_triggers_recovery_capsule", "clean_state_snapshot_rebuilds_grid", "city_victory_fireworks"],
              "audio": "metropolis_clear_fanfare.mp3"
            },
            "defeat_sequence": {
              "trigger_condition": "BACKUP_NONE",
              "sequence": ["terminal_glitches_red", "metropolitan_grid_goes_dark", "mascot_deploys_remediation_manual"],
              "audio": "catastrophe_defeat_drone.mp3"
            }
          }
        },
        "deliverable_action": "GENERATE_COMPREHENSIVE_INCIDENT_RESPONSE_PLAYBOOK_PDF",
        "state_mutations": { "gems_increment": 1000, "global_progress_percentage": 100, "award_badge": "Savior of the Metropolis", "campaign_completed": true }
      }
    }
  }
}
```

## **5\. UI Layout Transition & Hyperloop Animation Blueprint**

Navigating from the text/table data view of the Command Center to the graphical Campaign Map canvas requires an explicit visual transition mechanism. This is handled via an integrated **Hyperloop Transit** layout wrapper component.

### **Transition Workflow Mechanics**

1. **Initiation:** The user clicks the green transit hub option in the primary utility rail.  
2. **Phase 1 (The Intake):** The rendering canvas decreases in scale (scale(0.85)), applies a directional blur filter, and moves vertically down along the Y-axis to simulate entering a transit pipe enclosure.  
3. **Phase 2 (The Transit Loop):** An abstract underworld circuitry backdrop animates upward at high velocity. The platform triggers an 8-bit tracking transit audio element.  
4. **Phase 3 (The Landing):** The Campaign Map camera frames the starting transit checkpoint node of the active sector map. The map surface grows to full scale (scale(1.0)). The system helper droid sprite scales upward directly out of the transit terminal node container to lock focus on the active node checkpoint.

### **Framer Motion Production React Code Implementation**

TypeScript

```
import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const hyperloopEase = [0.6, -0.28, 0.735, 0.045];

interface TransitionWrapperProps {
  currentMode: 'COMMAND_CENTER' | 'TRANSIT_TUBE' | 'CAMPAIGN_MAP';
  children: [React.ReactElement, React.ReactElement]; 
}

export const HyperloopTransitController: React.FC<TransitionWrapperProps> = ({ 
  currentMode, 
  children 
}) => {
  return (
    <div className="relative w-full h-screen overflow-hidden bg-[#5C94FC]">
      <AnimatePresence mode="wait">
        {currentMode === 'COMMAND_CENTER' && (
          <motion.div
            key="command-center-canvas"
            initial={{ y: 0, scale: 1, opacity: 1, filter: 'blur(0px)' }}
            exit={{ 
              y: '100%', 
              scale: 0.88, 
              opacity: 0, 
              filter: 'blur(8px)' 
            }}
            transition={{ duration: 0.5, ease: hyperloopEase }}
            className="w-full h-full"
          >
            {/* Slot 0: Live Monitoring Telemetry Panels */}
            {children[0]}
          </motion.div>
        )}

        {currentMode === 'TRANSIT_TUBE' && (
          <motion.div
            key="hyperloop-transit-screen"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="absolute inset-0 flex flex-col items-center justify-center bg-[#07101E]"
            style={{
              backgroundImage: 'url("/assets/neon_grid_conduits.svg")',
              backgroundRepeat: 'repeat-y',
              backgroundPosition: 'center'
            }}
          >
            <motion.div 
              animate={{ backgroundPositionY: ['0px', '-1000px'] }}
              transition={{ repeat: Infinity, duration: 0.6, ease: 'linear' }}
              className="absolute inset-0 opacity-30"
              style={{ backgroundImage: 'url("/assets/speed_lines.svg")' }}
            />
            <div className="text-[#24C854] font-mono text-xs tracking-widest uppercase bg-[#07101E] px-4 py-2 border-2 border-[#24C854] rounded-md animate-pulse">
              ROUTING DATA CORE PIPELINES...
            </div>
          </motion.div>
        )}

        {currentMode === 'CAMPAIGN_MAP' && (
          <motion.div
            key="campaign-map-canvas"
            initial={{ y: '-100%', scale: 0.85, opacity: 0 }}
            animate={{ 
              y: 0, 
              scale: 1, 
              opacity: 1 
            }}
            transition={{ 
              type: 'spring', 
              stiffness: 110, 
              damping: 14, 
              mass: 1 
            }}
            className="w-full h-full"
          >
            {/* Slot 1: Isometric Smart City Map Canvas */}
            {children[1]}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
```

## **7\. Operational Code Modification & Dashboard Transformation Requirements**

Automated developer agents must rewrite existing UI widgets across target layout directories to enforce uniform compliance with the structural design model:

1. **Information Panel Modification:** Identify tabular elements and list views inside tracking modules. Enforce container conversions to match the floating white platform specification (thick charcoal stroke borders, rounded corners, soft layer drop-shadows).  
2. **Telemetry Status Badges:** Deprecate plain text monitoring fields (e.g., status strings reading "Healthy" or "Critical"). Replace with interactive retro game tokens: healthy configurations render a **Green Super Mushroom** status chip, and exposed unpatched profiles expose a **Blinking Red Shell** graphic element.  
3. **Mascot Presence Engine:** Mount the provided droid helper graphic asset within global header structures. Code state hook hooks that evaluate tracking metrics to modify the mascot's facial animations and accessory objects dynamically based on database updates (e.g., maintaining standard scanning sequences during safe monitoring periods, or rendering tactical engineering armor options when critical network anomalies bypass boundary controls).  
4. **Teaser Lock Implementation:** Live monitoring dashboard telemetry widgets tied to locked campaign sectors must remain visible but render as dimmed, padlocked, floating **Mystery Blocks**. Clicking a locked telemetry widget triggers an informational pop-up speech bubble from the mascot directing users to enter the campaign map to clear the matching sector requirement.

