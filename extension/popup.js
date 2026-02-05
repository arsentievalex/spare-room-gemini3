// Popup script for Spare Room - Personal AI Stylist

document.addEventListener('DOMContentLoaded', async () => {
  const pageTitleEl = document.getElementById('page-title');
  const styleBtn = document.getElementById('style-btn');
  const statusEl = document.getElementById('status');

  // Get current tab info
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  if (tab) {
    pageTitleEl.textContent = tab.title || 'Unknown page';
  }

  // Handle style button click
  styleBtn.addEventListener('click', async () => {
    styleBtn.disabled = true;
    statusEl.textContent = 'Capturing page...';
    statusEl.className = 'status loading';

    try {
      // Step 1: Ensure content script is injected
      statusEl.textContent = 'Preparing...';
      await ensureContentScriptInjected(tab.id);

      // Step 2: Get HTML content from content script
      statusEl.textContent = 'Extracting page content...';
      const htmlResponse = await chrome.tabs.sendMessage(tab.id, { action: 'getPageContent' });

      if (!htmlResponse || !htmlResponse.html) {
        throw new Error('Failed to extract page content');
      }

      // Step 3: Capture screenshot via background script
      statusEl.textContent = 'Capturing screenshot...';
      const screenshotResponse = await chrome.runtime.sendMessage({
        action: 'captureScreenshot',
        tabId: tab.id
      });

      if (!screenshotResponse || !screenshotResponse.screenshot) {
        throw new Error('Failed to capture screenshot');
      }

      // Step 4: Open side panel
      statusEl.textContent = 'Opening styling panel...';
      await chrome.sidePanel.open({ windowId: tab.windowId });

      // Step 5: Send data to background for API call
      statusEl.textContent = 'Analyzing with AI...';
      await chrome.runtime.sendMessage({
        action: 'analyzeProduct',
        data: {
          pageUrl: htmlResponse.url,
          pageTitle: htmlResponse.title,
          htmlContent: htmlResponse.html,
          screenshotBase64: screenshotResponse.screenshot
        }
      });

      statusEl.textContent = 'Analysis started! Check the sidebar.';
      statusEl.className = 'status success';

      // Close popup after a short delay
      setTimeout(() => window.close(), 1500);

    } catch (error) {
      console.error('Error:', error);
      statusEl.textContent = `Error: ${error.message}`;
      statusEl.className = 'status error';
      styleBtn.disabled = false;
    }
  });
});

/**
 * Ensure content script is injected into the tab
 */
async function ensureContentScriptInjected(tabId) {
  try {
    // Try to ping the content script
    await chrome.tabs.sendMessage(tabId, { action: 'ping' });
  } catch (error) {
    // Content script not loaded, inject it
    await chrome.scripting.executeScript({
      target: { tabId: tabId },
      files: ['content_script.js']
    });
    // Wait a moment for the script to initialize
    await new Promise(resolve => setTimeout(resolve, 100));
  }
}
