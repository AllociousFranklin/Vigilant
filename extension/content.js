// VIGILANT Extension - Content Script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'SHOW_WARNING') {
        injectWarning(message.data);
    }
});

function injectWarning(data) {
    // Check if warning already exists
    if (document.getElementById('vigilant-protection-layer')) return;

    const layer = document.createElement('div');
    layer.id = 'vigilant-protection-layer';
    layer.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: #030712;
    z-index: 2147483647;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Inter', sans-serif;
    color: #f8fafc;
    padding: 2rem;
  `;

    const card = document.createElement('div');
    card.style.cssText = `
    max-width: 600px;
    width: 100%;
    background: rgba(15, 23, 42, 0.8);
    backdrop-filter: blur(12px);
    border: 1px solid #f43f5e;
    border-radius: 1.5rem;
    padding: 3rem;
    text-align: center;
    box-shadow: 0 0 50px rgba(244, 63, 94, 0.3);
  `;

    const reasonsHtml = data.reasons.map(r => `
    <div style="background: rgba(244, 63, 94, 0.1); border: 1px solid rgba(244, 63, 94, 0.2); border-radius: 0.75rem; padding: 1rem; margin-bottom: 0.75rem; text-align: left;">
      <div style="font-size: 0.7rem; color: #f43f5e; font-weight: 700; text-transform: uppercase;">${r.category}</div>
      <div style="font-size: 0.95rem;">${r.reason}</div>
    </div>
  `).join('');

    card.innerHTML = `
    <div style="margin-bottom: 2rem;">
      <div style="display: inline-flex; align-items: center; justify-content: center; width: 80px; height: 80px; background: rgba(244, 63, 94, 0.15); border-radius: 50%; color: #f43f5e; margin-bottom: 1.5rem;">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/><path d="m14.5 9-5 5"/><path d="m9.5 9 5 5"/></svg>
      </div>
      <h1 style="font-size: 2rem; font-weight: 700; margin-bottom: 0.75rem; font-family: 'Outfit', sans-serif;">PHISHING DETECTED</h1>
      <p style="color: #94a3b8; font-size: 1.1rem;">VIGILANT AI has identified this page as high-risk.</p>
    </div>

    <div style="margin-bottom: 2.5rem;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
        <span style="font-size: 0.9rem; font-weight: 600; color: #94a3b8;">RISK SCORE: ${data.risk_score}/100</span>
        <span style="font-size: 0.9rem; font-weight: 700; color: #f43f5e;">${data.severity} SEVERITY</span>
      </div>
      <div style="max-height: 300px; overflow-y: auto; padding-right: 0.5rem;">
        ${reasonsHtml}
      </div>
    </div>

    <div style="display: flex; gap: 1rem;">
      <button id="vigilant-go-back" style="flex: 2; padding: 1rem; background: #f43f5e; color: #030712; border: none; border-radius: 0.75rem; font-weight: 700; cursor: pointer;">GO BACK TO SAFETY</button>
      <button id="vigilant-ignore" style="flex: 1; padding: 1rem; background: transparent; border: 1px solid #334155; color: #64748b; border-radius: 0.75rem; font-weight: 600; cursor: pointer; font-size: 0.8rem;">IGNORE WARNING</button>
    </div>
    
    <div style="margin-top: 2rem; font-size: 0.75rem; color: #475569;">
      VIGILANT ID: ${data.scan_id} | Analysis Latency: ${data.latency_ms}ms
    </div>
  `;

    layer.appendChild(card);
    document.documentElement.appendChild(layer);

    document.getElementById('vigilant-go-back').addEventListener('click', () => {
        window.location.href = 'about:newtab';
    });

    document.getElementById('vigilant-ignore').addEventListener('click', () => {
        layer.remove();
    });
}
