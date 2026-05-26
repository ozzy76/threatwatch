/* ==========================================================================
   Real-Time Client-Side Telemetry Simulation Engine
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // 1. ANOMALY COUNTER SIMULATOR
    const anomalyCounter = document.getElementById('live-anomaly-count');
    if (anomalyCounter) {
        setInterval(() => {
            let currentCount = parseInt(anomalyCounter.innerText, 10);
            // 85% chance to block an anomaly, minor 15% chance to increment active queue
            if (Math.random() < 0.15) {
                animateCounterPulse(anomalyCounter, currentCount + 1);
            }
        }, 4000); 
    }

    // 2. NETWORK CONDUIT LOAD GAUGE SIMULATOR
    const loadBar = document.getElementById('conduit-load-bar');
    const loadText = document.getElementById('conduit-load-text');
    if (loadBar && loadText) {
        setInterval(() => {
            // Generate a realistic load jitter between 62% and 78%
            let randomizedLoad = Math.floor(Math.random() * (78 - 62 + 1)) + 62;
            loadBar.style.width = randomizedLoad + '%';
            loadText.innerText = randomizedLoad + '%';
            
            // Contextual color modifications using design guidelines
            if (randomizedLoad > 75) {
                loadBar.className = 'progress-bar bg-danger'; // ThreatWatch Crimson
                loadBar.style.backgroundColor = '#E52521';
                
                // Let the mascot warning comment trigger occasionally on load spikes
                if (typeof letMascotComment === 'function' && Math.random() < 0.3) {
                    letMascotComment("Warning! Subterranean data conduit pressure is exceeding safe 75% capacity!", 4000);
                }
            } else {
                loadBar.className = 'progress-bar bg-success'; // ThreatWatch Emerald Mint
                loadBar.style.backgroundColor = '#24C854';
            }
        }, 2500);
    }

    // 3. SECTOR RADAR PING SIMULATOR
    const radarLogs = document.getElementById('radar-activity-logs');
    if (radarLogs) {
        const sampleMascotLogs = [
            "Sentry Tower Sector 4 completed telemetry packet sweep.",
            "Identity gateway checked UPN authorization headers cleanly.",
            "Endpoint defense matrix verified integrity on Node-014.",
            "Data core encryption key rotation completed successfully.",
            "Subterranean pipeline traffic load optimized automatically.",
            "Boundary firewall blocked inbound packet probe on port 22.",
            "Wireless sector segmented client SSID connection.",
            "Daily training records compiled into verification roster.",
            "Dynamic policy rules evaluated with compliance matrix.",
            "Backup capsule image sync completed with offset storage."
        ];
        
        setInterval(() => {
            let randomLog = sampleMascotLogs[Math.floor(Math.random() * sampleMascotLogs.length)];
            let timestamp = new Date().toLocaleTimeString();
            
            let logRow = document.createElement('div');
            logRow.className = 'mono-log-entry text-muted small py-1 border-bottom border-light text-truncate ec-mono';
            logRow.style.opacity = '0';
            logRow.style.fontFamily = 'monospace';
            logRow.innerHTML = `<span class="text-success" style="color: #24C854 !important;">[${timestamp}]</span> ${randomLog}`;
            
            radarLogs.insertBefore(logRow, radarLogs.firstChild);
            if (radarLogs.childNodes.length > 8) {
                radarLogs.removeChild(radarLogs.lastChild);
            }
            
            // Trigger quick animation fade-in
            setTimeout(() => { 
                logRow.style.opacity = '1'; 
                logRow.style.transition = 'opacity 0.3s ease'; 
            }, 50);

            // Occasional positive comment from the mascot about log health
            if (Math.random() < 0.1 && typeof letMascotComment === 'function') {
                letMascotComment("Radar activity feed indicates 100% compliant boundary traffic. Outstanding scan results!", 3500);
            }
        }, 3000);
    }

    // 4. MYSTERY BLOCK CLICK HANDLER
    const overlays = document.querySelectorAll('.mystery-lock-overlay');
    overlays.forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            e.stopPropagation(); // Stop standard propagation/event bubbling
            const sectorId = overlay.getAttribute('data-sector-id');
            const sectorName = overlay.getAttribute('data-sector-name') || `Sector ${sectorId}`;
            if (typeof letMascotComment === 'function') {
                letMascotComment(`This system monitor is currently offline! Venture through Campaign Sector [${sectorId}] (${sectorName}) to clear the compliance requirements and initialize this operational tracking node.`, 6000);
            }
        });
    });
});

function animateCounterPulse(element, newValue) {
    element.innerText = newValue;
    element.style.transform = 'scale(1.25)';
    element.style.color = '#FFCC00'; // Flash Energy Gold temporarily
    element.style.transition = 'transform(1.15) transform 0.15s cubic-bezier(0.175, 0.885, 0.32, 1.275), color 0.15s';
    
    // Play sound on anomaly increment
    if (typeof window.playEcoCitySound === 'function') {
        window.playEcoCitySound('click');
    }
    
    setTimeout(() => {
        element.style.transform = 'scale(1)';
        element.style.color = ''; // Restore standard color palette spacing
    }, 200);

    // Let the mascot celebrate and comment on blocked threats
    if (Math.random() < 0.25 && typeof letMascotComment === 'function') {
        const messages = [
            "Shields up! I just deflected another unauthorized entry packet!",
            "A boundary probe was detected, but my security filters neutralized it instantly!",
            "Intrusion attempt blocked cleanly! Our defensive matrices are holding strong.",
            "Halt! Unverified UPN header blocked at our gateway checkpoint!"
        ];
        letMascotComment(messages[Math.floor(Math.random() * messages.length)], 3500);
    }
}
