# **Mascot & Header Integration Hand-off Package**

**Target Architecture:** Django Monolith / Pure Templates Layout (HTML / Vanilla JS / Bootstrap 5)

**Design Theme:** The Eco-Cyber Metropolis (Vibrant, Thick-Outlined Cartoon Aesthetic)

**Assets:** \* mascot.png \-\> **State A (Idle Monitor):** Slow ambient vertical floating loop.

* mascot1.png \-\> **State B (Action Flare):** High-energy squash, stretch, and spring jump bounce.

## **1\. Global Header HTML Structure (header.html)**

This layout houses the top navigation bar, the arcade-style player stats HUD, and the fixed home base for the helper droid on the far right.

HTML

```
<nav class="navbar navbar-expand-lg bg-light border-bottom border-3 border-dark sticky-top px-4 py-2" style="border-radius: 0 0 24px 24px;">
    <div class="container-fluid">
        <a class="navbar-brand fw-bold text-dark fs-3" href="#">ThreatWatch</a>
        
        <div class="d-flex align-items-center mx-auto">
            <button id="enter-campaign-btn" class="btn btn-success border-2 border-dark fw-bold rounded-pill px-4 me-3">
                🚀 Launch Campaign
            </button>
            <div class="bg-white border border-2 border-dark rounded-pill px-3 py-1 d-flex align-items-center">
                <span class="me-2">💎</span>
                <span id="global-gem-count" class="font-monospace fw-bold text-dark">1,250</span>
            </div>
        </div>

        <div class="position-relative d-flex align-items-center" id="global-mascot-anchor">
            <div id="mascot-speech-bubble" class="border border-2 border-dark rounded-3 bg-white p-2 shadow-sm position-absolute">
                <p id="mascot-commentary-text" class="m-0 small fw-bold text-dark"></p>
            </div>
            
            <div class="mascot-container is-idle">
                <img src="/static/assets/mascot.png" class="mascot-sprite state-idle" alt="Droid Idle Base">
                <img src="/static/assets/mascot1.png" class="mascot-sprite state-action" alt="Droid Action Flare">
                <div class="mascot-shadow"></div>
            </div>
        </div>
    </div>
</nav>
```

## **2\. Mascot & Commentary Stylesheets (mascot.css)**

This style engine manages layout layers, switches asset visibilities via opacity changes to prevent blank loading flashes, and defines the retro game layout physics.

CSS

```
/* threatwatch/static/css/mascot.css */

#global-mascot-anchor {
    height: 60px;
    width: 60px;
    cursor: pointer;
}

.mascot-container {
    position: relative;
    width: 60px;
    height: 60px;
}

.mascot-sprite {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: contain;
    opacity: 0;
    transition: opacity 0.15s ease-in-out;
}

/* --- STATE A: IDLE HOVER --- */
.mascot-container.is-idle .state-idle {
    opacity: 1;
    animation: droidHover 3s ease-in-out infinite;
}
.mascot-container.is-idle .mascot-shadow {
    animation: shadowScale 3s ease-in-out infinite;
}

/* --- STATE B: ACTION SPRING JUMP --- */
.mascot-container.is-celebrating .state-action {
    opacity: 1;
    animation: droidJump 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

@keyframes droidHover {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-8px); }
}
@keyframes shadowScale {
    0%, 100% { transform: scale(1); opacity: 0.25; }
    50% { transform: scale(0.8); opacity: 0.12; }
}
@keyframes droidJump {
    0% { transform: scale(1) translateY(0); }
    20% { transform: scale(1.2, 0.8) translateY(3px); } /* Squash */
    50% { transform: scale(0.8, 1.2) translateY(-18px) rotate(8deg); } /* Stretch & leap */
    72% { transform: scale(1.05, 0.95) translateY(1px); } /* Cushion landing */
    100% { transform: scale(1) translateY(0); }
}

.mascot-shadow {
    width: 32px;
    height: 5px;
    background: rgba(7, 16, 30, 0.25);
    border-radius: 50%;
    position: absolute;
    bottom: -4px;
    left: 14px;
}

/* --- CONTEXTUAL SPEECH BUBBLE --- */
#mascot-speech-bubble {
    width: 240px;
    right: 75px;
    top: 50%;
    transform: translateY(-50%) scale(0);
    transform-origin: right center;
    transition: transform 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275), opacity 0.2s;
    opacity: 0;
    z-index: 1050;
    border-radius: 12px !important;
}

/* Comic-strip pointer widget */
#mascot-speech-bubble::after {
    content: '';
    position: absolute;
    right: -10px;
    top: 50%;
    transform: translateY(-50%);
    border-width: 5px;
    border-style: solid;
    border-color: transparent transparent transparent #212529;
}

#mascot-speech-bubble.is-visible {
    transform: translateY(-50%) scale(1);
    opacity: 1;
}
```

## **3\. State Controller & Interactivity Layer (commentary.js)**

Provides public API hooks to easily toggle expressions and broadcast pop-up messages across your dashboard forms, quiz modules, and simulation endpoints.

JavaScript

```
// threatwatch/static/js/commentary.js

/**
 * Triggers the action sprite shift and physical jump animation sequence.
 */
function triggerMascotCelebration() {
    const mascot = document.querySelector('.mascot-container');
    if (!mascot) return;

    mascot.classList.remove('is-idle');
    mascot.classList.add('is-celebrating');

    // Revert cleanly to ambient tracking loop once animation clears
    setTimeout(() => {
        mascot.classList.remove('is-celebrating');
        mascot.classList.add('is-idle');
    }, 600);
}

/**
 * Deploys the contextual speech window extending from the header utility base.
 * @param {string} textString - The narrative message to display.
 * @param {number} durationMs - Expiry window visibility in milliseconds.
 */
function letMascotComment(textString, durationMs = 4000) {
    const bubble = document.getElementById('mascot-speech-bubble');
    const textField = document.getElementById('mascot-commentary-text');
    
    if (!bubble || !textField) return;

    textField.innerText = textString;
    bubble.classList.add('is-visible');
    triggerMascotCelebration();

    setTimeout(() => {
        bubble.classList.remove('is-visible');
    }, durationMs);
}
```

## **4\. Refactoring Integration Instructions for Agents**

1. **Mount to Root Base:** Include header.html within global base views (base.html) so the navigation HUD tracks persistently across all application route adjustments.  
2. **Bind Onboarding Hooks:** Wire triggerMascotCelebration() directly into successful forms processing events (e.g., when the demographics scanner completes an input, fire the function to visually reinforce progress).  
3. **Connect Runtime Dashboard Telemetry:** Hook letMascotComment() into client-side monitoring alert tables. When automated JavaScript simulation ticks fire high-priority vulnerabilities or threat events, surface matching notifications using the script interface.

