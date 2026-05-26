/* ==========================================================================
   Hyperloop State Transition Controller with Synth Audio Effects
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('hyperloop-container');
    const enterCampaignBtn = document.getElementById('enter-campaign-btn');
    const exitCampaignBtn = document.getElementById('exit-campaign-btn');

    // Simple Synth sound effects using native Web Audio API
    window.playEcoCitySound = function(type) {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            const gainNode = ctx.createGain();
            
            osc.connect(gainNode);
            gainNode.connect(ctx.destination);
            
            if (type === 'transit') {
                // Energetic retro-futuristic rising whistle
                osc.type = 'sawtooth';
                osc.frequency.setValueAtTime(200, ctx.currentTime);
                osc.frequency.exponentialRampToValueAtTime(1200, ctx.currentTime + 0.7);
                gainNode.gain.setValueAtTime(0.06, ctx.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.7);
                osc.start();
                osc.stop(ctx.currentTime + 0.7);
            } else if (type === 'click') {
                // Short, tactile clicky blip
                osc.type = 'triangle';
                osc.frequency.setValueAtTime(440, ctx.currentTime);
                osc.frequency.setValueAtTime(880, ctx.currentTime + 0.05);
                gainNode.gain.setValueAtTime(0.1, ctx.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.15);
                osc.start();
                osc.stop(ctx.currentTime + 0.15);
            } else if (type === 'unlock') {
                // Dynamic chord chime (retro level-up tone)
                osc.type = 'sine';
                osc.frequency.setValueAtTime(523.25, ctx.currentTime); // C5
                osc.frequency.setValueAtTime(659.25, ctx.currentTime + 0.08); // E5
                osc.frequency.setValueAtTime(783.99, ctx.currentTime + 0.16); // G5
                osc.frequency.setValueAtTime(1046.50, ctx.currentTime + 0.24); // C6
                gainNode.gain.setValueAtTime(0.08, ctx.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.6);
                osc.start();
                osc.stop(ctx.currentTime + 0.6);
            }
        } catch (err) {
            console.log("AudioContext blocked or uninitialized. User interaction required.");
        }
    };

    if (enterCampaignBtn) {
        enterCampaignBtn.addEventListener('click', (e) => {
            e.preventDefault();
            window.playEcoCitySound('transit');
            container.className = 'mode-transit';
            
            setTimeout(() => {
                container.className = 'mode-campaign-map';
                window.playEcoCitySound('unlock');
                if (typeof spawnHelperMascot === 'function') spawnHelperMascot();
            }, 750); 
        });
    }

    if (exitCampaignBtn) {
        exitCampaignBtn.addEventListener('click', (e) => {
            e.preventDefault();
            window.playEcoCitySound('transit');
            container.className = 'mode-transit';
            
            setTimeout(() => {
                container.className = 'mode-command-center';
                window.playEcoCitySound('click');
            }, 600);
        });
    }
    
    // Mystery Block locking clicking behavior
    const lockedBlocks = document.querySelectorAll('.mystery-lock-overlay');
    lockedBlocks.forEach(block => {
        block.addEventListener('click', (e) => {
            e.stopPropagation();
            window.playEcoCitySound('click');
            const sectorName = block.getAttribute('data-sector-name') || 'the matching sector';
            const sectorId = block.getAttribute('data-sector-id') || 'X';
            
            // Highlight the warning state by targeting speech bubble
            const bubble = document.getElementById('sentry-speech-text');
            if (bubble) {
                bubble.innerText = `🚨 This system monitor is currently offline! Venture through Campaign Sector ${sectorId} (${sectorName}) to clear the compliance requirements and initialize this operational tracking node.`;
                
                // Pulsate speech bubble for focus
                const containerBubble = bubble.closest('.sentry-speech-bubble');
                if (containerBubble) {
                    containerBubble.style.transform = 'scale(1.08)';
                    containerBubble.style.borderColor = '#FFCC00';
                    setTimeout(() => {
                        containerBubble.style.transform = 'scale(1)';
                        containerBubble.style.borderColor = '#15171a';
                    }, 350);
                }
            }
        });
    });
});
