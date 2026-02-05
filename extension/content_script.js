// Content script for Wardrobe Styling Assistant
// Extracts page content for AI analysis

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'ping') {
    // Respond to ping to confirm content script is loaded
    sendResponse({ status: 'ok' });
    return true;
  }

  if (request.action === 'getPageContent') {
    try {
      // Extract relevant page information
      const pageContent = {
        html: getCleanedHtml(),
        url: window.location.href,
        title: document.title,
        metadata: extractMetadata()
      };

      sendResponse(pageContent);
    } catch (error) {
      console.error('Content script error:', error);
      sendResponse({ error: error.message });
    }
  }

  // Return true to indicate async response
  return true;
});

/**
 * Get cleaned HTML content (remove scripts and limit size)
 */
function getCleanedHtml() {
  // Clone the document to avoid modifying the actual page
  const docClone = document.cloneNode(true);

  // Remove script and style tags to reduce noise
  const scriptsAndStyles = docClone.querySelectorAll('script, style, noscript, iframe');
  scriptsAndStyles.forEach(el => el.remove());

  // Get the HTML content
  let html = docClone.documentElement.outerHTML;

  // Limit size to avoid overwhelming the API (max ~100KB)
  const maxLength = 100000;
  if (html.length > maxLength) {
    // Try to get just the main content area
    const mainContent = findMainContent();
    if (mainContent && mainContent.length < maxLength) {
      html = mainContent;
    } else {
      html = html.substring(0, maxLength);
    }
  }

  return html;
}

/**
 * Try to find the main product content area
 */
function findMainContent() {
  // Common selectors for product content
  const selectors = [
    '[data-testid="product-detail"]',
    '[class*="product-detail"]',
    '[class*="pdp-"]',
    'main',
    '[role="main"]',
    '#main-content',
    '.product-page',
    '.product-container'
  ];

  for (const selector of selectors) {
    const el = document.querySelector(selector);
    if (el) {
      return el.outerHTML;
    }
  }

  return null;
}

/**
 * Extract useful metadata from the page
 */
function extractMetadata() {
  const metadata = {};

  // Get Open Graph data
  const ogTags = document.querySelectorAll('meta[property^="og:"]');
  ogTags.forEach(tag => {
    const property = tag.getAttribute('property').replace('og:', '');
    metadata[`og_${property}`] = tag.getAttribute('content');
  });

  // Get product-specific meta tags
  const productMeta = document.querySelectorAll('meta[property^="product:"]');
  productMeta.forEach(tag => {
    const property = tag.getAttribute('property').replace('product:', '');
    metadata[`product_${property}`] = tag.getAttribute('content');
  });

  // Get JSON-LD structured data (often contains product info)
  const jsonLdScripts = document.querySelectorAll('script[type="application/ld+json"]');
  const jsonLdData = [];
  jsonLdScripts.forEach(script => {
    try {
      const data = JSON.parse(script.textContent);
      jsonLdData.push(data);
    } catch (e) {
      // Ignore invalid JSON
    }
  });

  if (jsonLdData.length > 0) {
    metadata.jsonLd = jsonLdData;
  }

  // Get any visible price elements
  const priceSelectors = [
    '[class*="price"]',
    '[data-testid*="price"]',
    '[itemprop="price"]'
  ];

  for (const selector of priceSelectors) {
    const priceEl = document.querySelector(selector);
    if (priceEl && priceEl.textContent) {
      const priceText = priceEl.textContent.trim();
      if (priceText.match(/[\$\€\£]/)) {
        metadata.price = priceText;
        break;
      }
    }
  }

  return metadata;
}
