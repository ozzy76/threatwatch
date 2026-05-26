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

    // Clear any previous active timers
    if (window.mascotBubbleTimeout) {
        clearTimeout(window.mascotBubbleTimeout);
    }

    window.mascotBubbleTimeout = setTimeout(() => {
        bubble.classList.remove('is-visible');
    }, durationMs);
}

/**
 * Handles clicks on the mascot by showing a dynamic commentary message
 * based on the user's active persona and progress percentage.
 */
function handleMascotClick() {
    const anchor = document.getElementById('global-mascot-anchor');
    if (!anchor) return;

    const persona = anchor.getAttribute('data-persona') || 'UNASSIGNED';
    const progress = parseInt(anchor.getAttribute('data-progress') || '0', 10);
    
    let message = "Greetings, Defender! Let's lock down our Eco-Cyber Metropolis!";

    if (persona === 'BUSINESS_OWNER') {
        if (progress <= 10) {
            message = "Welcome, Founder! Let's get started by scanning your website to secure your base of operations!";
        } else if (progress <= 40) {
            message = "You're off to a flying start! Let's keep solving compliance quests to earn precious gems.";
        } else if (progress <= 75) {
            message = "Our city grid is becoming incredibly resilient! Let's clear more sectors to unlock dashboard tracking.";
        } else {
            message = "Spectacular work! Your corporate defenses are completely fortified. Our metropolis is safe under your watch!";
        }
    } else if (persona === 'IT_STAFF') {
        if (progress <= 10) {
            message = "Sentry console initialized. Let's run a security sweep on the primary public domain.";
        } else if (progress <= 40) {
            message = "Asset inventory mapping in progress. Proceed through active controls to align with SCF guidelines.";
        } else if (progress <= 75) {
            message = "Perimeter telemetry and boundary filtering modules are online. Keep processing the active controls!";
        } else {
            message = "All compliance baselines fully satisfied! System audit complete. Excellent administration, Operator!";
        }
    } else {
        message = "Welcome, Defender! Let's select your operational role first to start our security campaign!";
    }

    letMascotComment(message, 5000);
}
