// VIGILANT Extension - Background Service Worker
const API_URL = 'http://localhost:8000/api/scan';

// Cache for scan results to avoid redundant calls
const scanCache = new Map();

chrome.webNavigation.onBeforeNavigate.addListener(async (details) => {
    // Only handle main frame navigations and http/https
    if (details.frameId !== 0 || !details.url.startsWith('http')) return;

    const url = details.url;

    // Skip common trusted domains to save latency
    const trustedDomains = ['google.com', 'bing.com', 'duckduckgo.com', 'localhost'];
    if (trustedDomains.some(d => url.includes(d))) return;

    // Check cache
    if (scanCache.has(url)) {
        const cached = scanCache.get(url);
        if (cached.severity === 'HIGH' || cached.severity === 'CRITICAL') {
            blockPage(details.tabId, cached);
        }
        return;
    }

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, channel: 'url' })
        });

        if (!response.ok) return;

        const result = await response.json();
        scanCache.set(url, result);

        if (result.severity === 'HIGH' || result.severity === 'CRITICAL') {
            blockPage(details.tabId, result);
        }
    } catch (err) {
        console.error('VIGILANT background scan failed:', err);
    }
});

function blockPage(tabId, result) {
    // Send message to content script to show overlay
    chrome.tabs.sendMessage(tabId, {
        action: 'SHOW_WARNING',
        data: result
    });
}

// Clear cache every hour
chrome.alarms.create('clearCache', { periodInMinutes: 60 });
chrome.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === 'clearCache') scanCache.clear();
});
