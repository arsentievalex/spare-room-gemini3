// Background service worker for Wardrobe Styling Assistant

const BACKEND_URL = 'http://localhost:8000';

// Store current analysis state
let currentAnalysis = null;

// Listen for messages from popup and content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  handleMessage(request, sender)
    .then(sendResponse)
    .catch(error => {
      console.error('Background error:', error);
      sendResponse({ error: error.message });
    });

  // Return true to indicate async response
  return true;
});

async function handleMessage(request, sender) {
  switch (request.action) {
    case 'captureScreenshot':
      return await captureScreenshot(request.tabId);

    case 'analyzeProduct':
      return await analyzeProduct(request.data);

    case 'getAnalysisStatus':
      return { analysis: currentAnalysis };

    default:
      throw new Error(`Unknown action: ${request.action}`);
  }
}

/**
 * Capture visible tab screenshot
 */
async function captureScreenshot(tabId) {
  try {
    // Get the tab's window
    const tab = await chrome.tabs.get(tabId);

    // Capture the visible area
    const dataUrl = await chrome.tabs.captureVisibleTab(tab.windowId, {
      format: 'png',
      quality: 90
    });

    // Extract base64 data (remove data:image/png;base64, prefix)
    const base64Data = dataUrl.split(',')[1];

    return { screenshot: base64Data };
  } catch (error) {
    console.error('Screenshot capture error:', error);
    throw new Error('Failed to capture screenshot: ' + error.message);
  }
}

/**
 * Send product data to backend for analysis
 */
async function analyzeProduct(data) {
  // Update state to loading
  currentAnalysis = {
    status: 'loading',
    startTime: Date.now(),
    pageUrl: data.pageUrl,
    pageTitle: data.pageTitle
  };

  // Notify sidebar of loading state
  broadcastToSidebar({ type: 'analysisUpdate', analysis: currentAnalysis });

  try {
    const response = await fetch(`${BACKEND_URL}/analyze-and-style`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: 'demo_user',
        page_url: data.pageUrl,
        page_title: data.pageTitle,
        html_content: data.htmlContent,
        screenshot_base64: data.screenshotBase64
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Server error: ${response.status} - ${errorText}`);
    }

    const result = await response.json();
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/919e1697-663a-4cbf-839e-a17b5c33ec34',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'background.js:96',message:'Received result from backend',data:{has_generated_image:!!result.generated_image_base64,image_length:result.generated_image_base64?result.generated_image_base64.length:0},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'G'})}).catch(()=>{});
    // #endregion

    // Update state with results
    currentAnalysis = {
      status: 'success',
      startTime: currentAnalysis.startTime,
      endTime: Date.now(),
      pageUrl: data.pageUrl,
      pageTitle: data.pageTitle,
      result: result
    };

    // Notify sidebar of results
    broadcastToSidebar({ type: 'analysisUpdate', analysis: currentAnalysis });

    return { success: true, result };

  } catch (error) {
    console.error('Analysis error:', error);

    // Update state with error
    currentAnalysis = {
      status: 'error',
      startTime: currentAnalysis.startTime,
      endTime: Date.now(),
      pageUrl: data.pageUrl,
      pageTitle: data.pageTitle,
      error: error.message
    };

    // Notify sidebar of error
    broadcastToSidebar({ type: 'analysisUpdate', analysis: currentAnalysis });

    throw error;
  }
}

/**
 * Broadcast message to sidebar
 */
async function broadcastToSidebar(message) {
  try {
    // Send to all extension pages (sidebar will receive this)
    chrome.runtime.sendMessage(message).catch(() => {
      // Sidebar might not be open, that's ok
    });
  } catch (error) {
    // Ignore errors when sidebar isn't open
  }
}

// Handle side panel opening
chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: false }).catch(() => {});
