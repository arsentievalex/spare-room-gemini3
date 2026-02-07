// Sidebar script for Spare Room - Personal AI Stylist

// State elements
const loadingState = document.getElementById('loading-state');
const errorState = document.getElementById('error-state');
const successState = document.getElementById('success-state');
const emptyState = document.getElementById('empty-state');

// Loading elements
const loadingDetails = document.getElementById('loading-details');

// Track current analysis to prevent stale updates
let currentAnalysisStartTime = null;
let loadingTimeoutId = null;

// Error elements
const errorMessage = document.getElementById('error-message');
const retryBtn = document.getElementById('retry-btn');

// Success elements
const productName = document.getElementById('product-name');
const productDetails = document.getElementById('product-details');
const wardrobeItemsList = document.getElementById('wardrobe-items-list');
const stylingNotes = document.getElementById('styling-notes');
const stylingNotesSection = document.getElementById('styling-notes-section');
const styledImage = document.getElementById('styled-image');
const imagePlaceholder = document.getElementById('image-placeholder');

// Carousel elements
const carouselLeft = document.getElementById('carousel-left');
const carouselRight = document.getElementById('carousel-right');
const carouselIndicators = document.getElementById('carousel-indicators');
const angleLabel = document.getElementById('angle-label');

// Carousel state
let carouselImages = [];
let currentAngleIndex = 0;
const angleNames = ['Front', 'Left', 'Right', 'Back'];
const angleKeys = ['front', 'left', 'right', 'back'];

// Initialize sidebar
document.addEventListener('DOMContentLoaded', async () => {
  // Check for existing analysis state
  try {
    const response = await chrome.runtime.sendMessage({ action: 'getAnalysisStatus' });
    if (response && response.analysis) {
      updateUI(response.analysis);
    } else {
      showEmptyState();
    }
  } catch (error) {
    showEmptyState();
  }
});

// Listen for analysis updates from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'analysisUpdate') {
    updateUI(message.analysis);
  }
});

// Retry button handler
retryBtn.addEventListener('click', () => {
  // Close sidebar - user needs to click the extension button again
  showEmptyState();
});

// Carousel handlers
carouselLeft.addEventListener('click', () => {
  if (carouselImages.length > 0) {
    currentAngleIndex = (currentAngleIndex - 1 + carouselImages.length) % carouselImages.length;
    updateCarouselDisplay();
  }
});

carouselRight.addEventListener('click', () => {
  if (carouselImages.length > 0) {
    currentAngleIndex = (currentAngleIndex + 1) % carouselImages.length;
    updateCarouselDisplay();
  }
});

function updateCarouselDisplay() {
  if (carouselImages.length === 0) return;

  const currentImage = carouselImages[currentAngleIndex];
  styledImage.src = `data:image/png;base64,${currentImage.data}`;
  angleLabel.textContent = currentImage.name;

  // Update indicators
  const dots = carouselIndicators.querySelectorAll('.carousel-dot');
  dots.forEach((dot, idx) => {
    dot.classList.toggle('active', idx === currentAngleIndex);
  });
}

function initCarousel(images) {
  carouselImages = [];
  currentAngleIndex = 0;

  // Build array of available images
  angleKeys.forEach((key, idx) => {
    if (images && images[key]) {
      carouselImages.push({
        key: key,
        name: angleNames[idx],
        data: images[key]
      });
    }
  });

  // Create indicator dots
  carouselIndicators.innerHTML = '';
  carouselImages.forEach((_, idx) => {
    const dot = document.createElement('span');
    dot.className = 'carousel-dot' + (idx === 0 ? ' active' : '');
    dot.addEventListener('click', () => {
      currentAngleIndex = idx;
      updateCarouselDisplay();
    });
    carouselIndicators.appendChild(dot);
  });

  // Show/hide arrows based on image count
  const hasMultiple = carouselImages.length > 1;
  carouselLeft.style.display = hasMultiple ? 'flex' : 'none';
  carouselRight.style.display = hasMultiple ? 'flex' : 'none';
  carouselIndicators.style.display = hasMultiple ? 'flex' : 'none';
  angleLabel.style.display = hasMultiple ? 'block' : 'none';

  // Display first image
  if (carouselImages.length > 0) {
    updateCarouselDisplay();
  }
}

/**
 * Update UI based on analysis state
 */
function updateUI(analysis) {
  if (!analysis) {
    showEmptyState();
    return;
  }

  // Clear any pending loading timeout
  if (loadingTimeoutId) {
    clearTimeout(loadingTimeoutId);
    loadingTimeoutId = null;
  }

  // Track the current analysis
  currentAnalysisStartTime = analysis.startTime;

  switch (analysis.status) {
    case 'loading':
      showLoadingState(analysis);
      break;
    case 'success':
      showSuccessState(analysis);
      break;
    case 'error':
      showErrorState(analysis);
      break;
    default:
      showEmptyState();
  }
}

/**
 * Show loading state
 */
function showLoadingState(analysis) {
  hideAllStates();
  loadingState.classList.remove('hidden');

  // Update loading message based on time elapsed
  const elapsed = Date.now() - analysis.startTime;
  if (elapsed < 3000) {
    loadingDetails.textContent = 'Looking at this piece...';
  } else if (elapsed < 8000) {
    loadingDetails.textContent = 'Checking your closet...';
  } else {
    loadingDetails.textContent = 'Creating your styled look...';
  }

  // Continue updating loading message, but only if still in loading state
  if (analysis.status === 'loading') {
    const analysisStartTime = analysis.startTime;
    loadingTimeoutId = setTimeout(() => {
      // Only update if this is still the current analysis
      if (currentAnalysisStartTime === analysisStartTime) {
        // Fetch fresh status from background
        chrome.runtime.sendMessage({ action: 'getAnalysisStatus' })
          .then(response => {
            if (response && response.analysis &&
                response.analysis.startTime === analysisStartTime) {
              updateUI(response.analysis);
            }
          })
          .catch(() => {});
      }
    }, 2000);
  }
}

/**
 * Show error state
 */
function showErrorState(analysis) {
  hideAllStates();
  errorState.classList.remove('hidden');
  errorMessage.textContent = analysis.error || 'An unexpected error occurred';
}

/**
 * Show success state with results
 */
function showSuccessState(analysis) {
  hideAllStates();
  successState.classList.remove('hidden');

  const result = analysis.result;
  if (!result) return;

  // Product info - minimal display
  if (result.product) {
    productName.textContent = result.product.name || 'Unknown Product';
    const details = [];
    if (result.product.brand) details.push(result.product.brand);
    if (result.product.color) details.push(result.product.color);
    productDetails.textContent = details.join(' • ');
  }

  // Wardrobe items with thumbnails
  if (result.selected_items && result.selected_items.length > 0) {
    wardrobeItemsList.innerHTML = '';
    const stylingNotesContent = [];

    result.selected_items.forEach(item => {
      const itemEl = document.createElement('div');
      itemEl.className = 'wardrobe-item';
      const colorHex = item.color_hex || getColorCode(item.color);

      // Use image URL, base64, or fall back to color swatch
      let imageContent;
      if (item.image_url) {
        imageContent = `<img src="${item.image_url}" alt="${item.name}" class="item-thumbnail">`;
      } else if (item.image_base64) {
        imageContent = `<img src="data:image/png;base64,${item.image_base64}" alt="${item.name}" class="item-thumbnail">`;
      } else {
        imageContent = `<div class="item-color" style="background-color: ${colorHex}"></div>`;
      }

      itemEl.innerHTML = `
        <div class="item-image-wrapper">
          ${imageContent}
        </div>
        <div class="item-info">
          <p class="item-name">${item.name}</p>
          <p class="item-meta">${item.type} · <span class="color-hex">${colorHex}</span></p>
        </div>
      `;
      wardrobeItemsList.appendChild(itemEl);

      // Collect styling notes
      if (item.match_reason) {
        stylingNotesContent.push({
          name: item.name,
          reason: item.match_reason
        });
      }
    });

    // Display styling notes (why each item was chosen)
    if (stylingNotesContent.length > 0) {
      stylingNotes.innerHTML = '';
      stylingNotesContent.forEach(note => {
        const noteEl = document.createElement('div');
        noteEl.className = 'styling-note';
        noteEl.innerHTML = `
          <span class="note-item">${note.name}:</span>
          <span class="note-reason">${note.reason}</span>
        `;
        stylingNotes.appendChild(noteEl);
      });
      stylingNotesSection.classList.remove('hidden');
    } else {
      stylingNotesSection.classList.add('hidden');
    }
  } else {
    wardrobeItemsList.innerHTML = '<p class="no-items">No matching items found</p>';
    stylingNotesSection.classList.add('hidden');
  }

  // Generated images - use carousel for multiple angles
  if (result.generated_images || result.generated_image_base64) {
    // Build images object from new format or fallback to old format
    let images = result.generated_images || {};

    // Fallback: if only old format exists, use it as front
    if (!images.front && result.generated_image_base64) {
      images = { front: result.generated_image_base64 };
    }

    // Check if we have at least one image
    const hasAnyImage = images.front || images.left || images.right || images.back;

    if (hasAnyImage) {
      initCarousel(images);
      styledImage.classList.remove('hidden');
      imagePlaceholder.classList.add('hidden');
    } else {
      styledImage.classList.add('hidden');
      imagePlaceholder.classList.remove('hidden');
      imagePlaceholder.textContent = 'Image unavailable';
      carouselLeft.style.display = 'none';
      carouselRight.style.display = 'none';
      carouselIndicators.style.display = 'none';
      angleLabel.style.display = 'none';
    }
  } else {
    styledImage.classList.add('hidden');
    imagePlaceholder.classList.remove('hidden');
    imagePlaceholder.textContent = 'Image unavailable';
    carouselLeft.style.display = 'none';
    carouselRight.style.display = 'none';
    carouselIndicators.style.display = 'none';
    angleLabel.style.display = 'none';
  }
}

/**
 * Show empty state
 */
function showEmptyState() {
  hideAllStates();
  emptyState.classList.remove('hidden');
}

/**
 * Hide all state containers
 */
function hideAllStates() {
  loadingState.classList.add('hidden');
  errorState.classList.add('hidden');
  successState.classList.add('hidden');
  emptyState.classList.add('hidden');
}

/**
 * Get CSS color code from color name
 */
function getColorCode(colorName) {
  const colors = {
    'black': '#1a1a1a',
    'white': '#f5f5f5',
    'navy': '#1e3a5f',
    'blue': '#3b82f6',
    'red': '#ef4444',
    'green': '#22c55e',
    'brown': '#8b4513',
    'beige': '#d4c4a8',
    'gray': '#6b7280',
    'grey': '#6b7280',
    'tan': '#d2b48c',
    'cream': '#fffdd0',
    'burgundy': '#722f37',
    'olive': '#808000',
    'khaki': '#c3b091',
    'denim': '#1560bd',
    'pink': '#ec4899',
    'purple': '#9333ea',
    'yellow': '#eab308',
    'orange': '#f97316'
  };

  const lowerColor = (colorName || '').toLowerCase();
  return colors[lowerColor] || '#9ca3af';
}
