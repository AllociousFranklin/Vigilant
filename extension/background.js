// VIGILANT Extension - Background Service Worker
const API_URL = 'http://localhost:8000/api/scan';
const SCAN_TIMEOUT = 3000; // 3 second timeout for backend response

// Cache for scan results to avoid redundant calls
const scanCache = new Map();

// Add logging helper
function log(message, data = null) {
    const timestamp = new Date().toLocaleTimeString();
    if (data) {
        console.log(`[VIGILANT ${timestamp}] ${message}`, data);
    } else {
        console.log(`[VIGILANT ${timestamp}] ${message}`);
    }
}

chrome.webNavigation.onBeforeNavigate.addListener(async (details) => {
    // Only handle main frame navigations and http/https
    if (details.frameId !== 0 || !details.url.startsWith('http')) return;

    const url = details.url;
    log('Navigation detected', { url });

    // Skip common trusted domains to save latency
    const trustedDomains = ['google.com', 'bing.com', 'duckduckgo.com', 'localhost'];
    if (trustedDomains.some(d => url.includes(d))) {
        log('Skipping trusted domain');
        return;
    }

    // Check cache FIRST
    if (scanCache.has(url)) {
        const cached = scanCache.get(url);
        log('Using cached result', { risk_score: cached.risk_score, severity: cached.severity });
        
        // Apply tiered blocking based on risk_score
        if (cached.risk_score > 60) {
            // CRITICAL HARD BLOCK (no override possible)
            log('Hard blocking CRITICAL threat', { risk_score: cached.risk_score });
            blockPage(details.tabId, cached, true);
        } else if (cached.risk_score >= 40) {
            // WARNING with override allowed
            log('Warning user of suspicious content', { risk_score: cached.risk_score });
            blockPage(details.tabId, cached, false);
        } else {
            // LOW RISK - allow but still logged to history
            log('Low risk detection', { risk_score: cached.risk_score });
        }
        return;
    }

    // Scan the URL
    try {
        log('Sending scan request to backend');
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), SCAN_TIMEOUT);
        
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, channel: 'url' }),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);

        if (!response.ok) {
            log('Backend returned error', { status: response.status });
            return;
        }

        const result = await response.json();
        log('Scan complete', { risk_score: result.risk_score, severity: result.severity });
        
        // Cache result
        scanCache.set(url, result);

        // Apply tiered blocking based on risk_score (40-60 = warn, >60 = hard block)
        if (result.risk_score > 60) {
            // CRITICAL HARD BLOCK
            log('Hard blocking CRITICAL threat', { risk_score: result.risk_score });
            blockPage(details.tabId, result, true);
        } else if (result.risk_score >= 40) {
            // WARNING with override allowed
            log('Warning user of suspicious content', { risk_score: result.risk_score });
            blockPage(details.tabId, result, false);
        } else {
            // LOW RISK - allow but still logged to history by backend
            log('Low risk detection - allowing navigation', { risk_score: result.risk_score });
        }
    } catch (err) {
        if (err.name === 'AbortError') {
            log('Scan request timeout - allowing navigation');
        } else {
            log('VIGILANT background scan error', err);
        }
        // Fallback: allow navigation on error
    }
});

function blockPage(tabId, result, isHardBlock) {
    // Send message to content script to show overlay
    // Pass isHardBlock flag so content script knows if override is allowed
    chrome.tabs.sendMessage(tabId, {
        action: 'SHOW_WARNING',
        data: result,
        isHardBlock: isHardBlock
    }).catch(err => {
        log('Failed to send message to content script', err);
    });
}

// Clear cache every hour
chrome.alarms.create('clearCache', { periodInMinutes: 60 });
chrome.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === 'clearCache') {
        log('Clearing scan cache (hourly)');
        scanCache.clear();
    }
});
