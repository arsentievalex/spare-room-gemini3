# Spare Room

**The Portal Between the Store and Your Wardrobe**

Spare Room is an AI-powered shopping companion that connects online stores to your personal wardrobe. See how clothes look on you before buying, get outfit recommendations based on what you already own, and reduce returns.

## Features

- **Virtual Try-On** — See how garments look on your body from 4 angles (front, left, right, back)
- **Wardrobe Matching** — Get suggestions for items you own that pair well with new pieces
- **Fit Score** — 0-100 compatibility score based on your wardrobe and style
- **Styling Tips** — Short notes on why the combination works

## Architecture

```
Web App (AI Studio)                    Chrome Extension
┌──────────────────┐                  ┌──────────────────┐
│ Upload photo     │                  │ Capture page     │
│ Upload wardrobe  │──► GCS Bucket    │ screenshot + HTML│
│ Enter sizes      │    (user data)   └────────┬─────────┘
└──────────────────┘         │                 │
                             │                 ▼
                             │        ┌──────────────────┐
                             └───────►│ FastAPI Backend   │
                                      │ (runs locally)   │
                                      └────────┬─────────┘
                                               │
                         ┌─────────────────────┼──────────────────┐
                         ▼                     ▼                  ▼
                   Extract Product      Analyze Styling     Generate Try-On
                   (Flash, low)        (Flash, medium)     (Pro Image + Nano)
```

## Tech Stack

- **Web App**: Google AI Studio (profile setup + wardrobe cataloging)
- **Storage**: Google Cloud Storage (user profiles, wardrobe images)
- **Backend**: Python, FastAPI
- **Extension**: JavaScript, Chrome Extension Manifest V3
- **AI**: Google Gemini 3 API
  - `gemini-3-flash-preview` — Wardrobe analysis, product extraction, styling analysis
  - `gemini-3-pro-image-preview` — Primary try-on image generation
  - `gemini-2.5-flash-image` — Additional angle generation

## Setup

### 1. Profile Setup (Web App)

1. Open the [Spare Room web app](https://ai.studio/apps/drive/1GwKJawRP47872cGIrVNk6aSj8A5ElyZs)
2. Upload your photo, measurements, style preferences, and wardrobe item photos
3. Note your unique username — you'll need it for the extension

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python server.py
```

The server runs on `http://localhost:8000`.

### 3. Chrome Extension

1. Open Chrome → `chrome://extensions/`
2. Enable **Developer mode** (top right toggle)
3. Click **Load unpacked** → select the `extension` folder
4. Click the extension icon, enter your username and Gemini API key

## How It Works

1. **Profile Setup** (Web App): Upload your photo, measurements, and wardrobe photos. Gemini Flash analyzes each item and stores everything in Google Cloud Storage.
2. **Extension Setup** (one-time): Enter your username and Gemini API key in the extension.
3. **Shopping**: Browse any online store, click the extension on a product page.
4. **Results**: View try-on images, fit score, matching wardrobe items, and styling tips in the sidebar.

## Project Structure

```
├── backend/
│   ├── server.py            # FastAPI server
│   ├── gemini_client.py     # Gemini API integration (4 models)
│   ├── wardrobe.py          # User data fetching from GCS
│   └── requirements.txt
├── extension/
│   ├── manifest.json        # Extension config (Manifest V3)
│   ├── popup.html/js        # Setup + trigger UI
│   ├── sidebar.html/js      # Results display with image carousel
│   ├── content_script.js    # Page content extraction
│   ├── background.js        # Service worker
│   └── styles.css           # Shared styles
├── architecture.md          # Detailed architecture with diagrams
├── testing_instructions.md  # Step-by-step testing guide
└── DEVPOST.md               # Hackathon submission writeup
```

## License

MIT
