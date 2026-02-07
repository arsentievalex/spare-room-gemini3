// Popup script for Spare Room - Personal AI Stylist

const GCS_BASE_URL = 'https://storage.googleapis.com/gemini3-hackathon-demo-wardrobe';

document.addEventListener('DOMContentLoaded', async () => {
  const setupScreen = document.getElementById('setup-screen');
  const mainScreen = document.getElementById('main-screen');
  const usernameInput = document.getElementById('username-input');
  const apikeyInput = document.getElementById('apikey-input');
  const saveSetupBtn = document.getElementById('save-setup-btn');
  const setupError = document.getElementById('setup-error');
  const changeSettingsBtn = document.getElementById('change-settings-btn');
  const pageTitleEl = document.getElementById('page-title');
  const styleBtn = document.getElementById('style-btn');
  const statusEl = document.getElementById('status');

  // Check for saved credentials
  const stored = await chrome.storage.local.get(['username', 'geminiApiKey']);

  if (stored.username && stored.geminiApiKey) {
    showMainScreen(stored.username);
  } else {
    // Pre-fill if partially saved
    if (stored.username) usernameInput.value = stored.username;
    showSetupScreen();
  }

  function showSetupScreen() {
    setupScreen.style.display = 'block';
    mainScreen.style.display = 'none';
    setupError.style.display = 'none';
  }

  async function showMainScreen(username) {
    setupScreen.style.display = 'none';
    mainScreen.style.display = 'block';

    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
      pageTitleEl.textContent = tab.title || 'Unknown page';
    }
  }

  function showSetupError(msg) {
    setupError.textContent = msg;
    setupError.style.display = 'block';
  }

  // Save setup
  saveSetupBtn.addEventListener('click', async () => {
    const username = usernameInput.value.trim();
    const apiKey = apikeyInput.value.trim();

    if (!username) {
      showSetupError('Please enter your username.');
      return;
    }
    if (!apiKey) {
      showSetupError('Please enter your Gemini API key.');
      return;
    }

    saveSetupBtn.disabled = true;
    setupError.style.display = 'none';

    // Validate username by checking if user_info.json exists
    try {
      const url = `${GCS_BASE_URL}/${encodeURIComponent(username)}/user_info.json`;
      const response = await fetch(url);
      if (!response.ok) {
        showSetupError('Username not found. Please check your username and try again.');
        saveSetupBtn.disabled = false;
        return;
      }
      // Valid - save credentials
      await chrome.storage.local.set({ username, geminiApiKey: apiKey });
      showMainScreen(username);
    } catch (error) {
      showSetupError('Could not validate username. Check your connection and try again.');
      saveSetupBtn.disabled = false;
    }
  });

  // Change settings
  changeSettingsBtn.addEventListener('click', () => {
    chrome.storage.local.get(['username', 'geminiApiKey'], (stored) => {
      usernameInput.value = stored.username || '';
      apikeyInput.value = stored.geminiApiKey || '';
      showSetupScreen();
    });
  });

  // Handle style button click
  styleBtn.addEventListener('click', async () => {
    const stored = await chrome.storage.local.get(['username', 'geminiApiKey']);
    if (!stored.username || !stored.geminiApiKey) {
      showSetupScreen();
      return;
    }

    styleBtn.disabled = true;
    statusEl.textContent = 'Capturing page...';
    statusEl.className = 'status loading';

    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

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
          screenshotBase64: screenshotResponse.screenshot,
          username: stored.username,
          geminiApiKey: stored.geminiApiKey
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
    await chrome.tabs.sendMessage(tabId, { action: 'ping' });
  } catch (error) {
    await chrome.scripting.executeScript({
      target: { tabId: tabId },
      files: ['content_script.js']
    });
    await new Promise(resolve => setTimeout(resolve, 100));
  }
}
