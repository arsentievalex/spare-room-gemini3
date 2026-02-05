# Spare Room

**The Portal Between the Store and Your Wardrobe**

Spare Room is an AI-powered shopping companion that connects online stores directly to your personal wardrobe. See how clothes look on you before buying, get outfit recommendations based on what you already own, and reduce returns.

## Features

- **Virtual Try-On** - See how garments look on your actual body from multiple angles
- **Wardrobe Matching** - Get instant suggestions for items in your closet that pair well with new pieces
- **Fit Score** - Receive a compatibility score (0-100) based on your existing wardrobe and style
- **Style Compatibility** - Get alerts if something conflicts with your stated preferences

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Chrome Extension                                │
│  (captures screenshot + HTML, sends to backend)                      │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                                 │
└─────────────────────────────────────────────────────────────────────┘
                                  │
            ┌─────────────────────┼─────────────────────┐
            ▼                     ▼                     ▼
   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
   │ STEP 1: Extract │   │ STEP 2: Analyze │   │ STEP 3: Generate│
   │ Product Info    │   │ Styling & Fit   │   │ Try-On Images   │
   │                 │   │                 │   │                 │
   │ gemini-3-flash  │   │ gemini-3-flash  │   │ gemini-3-pro-   │
   │ thinking: low   │   │ thinking: medium│   │ image-preview   │
   └─────────────────┘   └─────────────────┘   └─────────────────┘
```

## Tech Stack

- **Backend**: Python, FastAPI
- **Extension**: JavaScript, Chrome Extension Manifest V3
- **AI**: Google Gemini 3 API
  - `gemini-3-flash-preview` - Product extraction & styling analysis
  - `gemini-3-pro-image-preview` - Primary try-on image generation
  - `gemini-2.5-flash-image` - Additional angle generation

## Setup

### Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your Gemini API key:
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

4. Start the server:
   ```bash
   python server.py
   ```

### Chrome Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `extension` folder

## How It Works

1. **Onboarding**: Users upload a photo, enter measurements, set style preferences, and upload wardrobe photos
2. **Shopping**: When browsing any online store, click the extension to analyze a product
3. **Analysis**: The AI extracts product info, analyzes fit with your wardrobe, and generates try-on images
4. **Decision**: View the fit score, matching items, and styling tips to make informed purchases

## Project Structure

```
├── backend/
│   ├── server.py          # FastAPI server
│   ├── gemini_client.py   # Gemini API integration
│   ├── wardrobe.py        # Wardrobe management
│   └── requirements.txt
├── extension/
│   ├── manifest.json      # Extension config
│   ├── popup.html/js      # Extension popup
│   ├── sidebar.html/js    # Side panel UI
│   ├── content_script.js  # Page content capture
│   └── background.js      # Service worker
└── architecture.md        # Detailed architecture docs
```

## License

MIT
