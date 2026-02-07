# Testing Instructions

## Prerequisites

- Google Chrome browser
- Python 3.10+
- A Gemini API key (get one at [aistudio.google.com](https://aistudio.google.com/apikey))

---

## Quick Start (Demo Account)

If you want to skip profile setup, use the pre-configured demo account:

- **Username:** `stylish-fashion-juumv`

This account already has a photo and wardrobe items uploaded. Jump straight to **Step 2** and use this username in **Step 4**.

---

## Step 1: Set Up Your Profile (Web App)

1. Open the Spare Room web app: [https://ai.studio/apps/drive/1GwKJawRP47872cGIrVNk6aSj8A5ElyZs](https://ai.studio/apps/drive/1GwKJawRP47872cGIrVNk6aSj8A5ElyZs)
2. Upload your photo, enter your measurements, and set your style preferences.
3. Upload photos of your wardrobe items — the AI will analyze each one automatically.
4. Once your profile is created, the app will display a **unique username** (e.g. `bold-mode-zmb12`). **Note it down** — you will need it for the extension.

## Step 2: Install the Extension

1. Clone the repo:
   ```bash
   git clone https://github.com/arsentievalex/spare-room-gemini3.git
   cd spare-room-gemini3
   ```
2. Open Chrome and navigate to `chrome://extensions/`
3. Enable **Developer mode** (toggle in the top-right corner).
4. Click **Load unpacked**.
5. Select the `extension` folder inside the cloned repo.
6. You should see the **Spare Room** extension appear in your extensions list. Pin it to the toolbar for easy access.

## Step 3: Start the Backend

1. In a terminal, navigate to the backend folder:
   ```bash
   cd backend
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Start the server:
   ```bash
   python server.py
   ```
4. Keep this terminal running. The server listens on `http://localhost:8000`.

## Step 4: Configure the Extension

1. Click the **Spare Room** extension icon in the Chrome toolbar.
2. Enter your **username** from Step 1.
3. Enter your **Gemini API key**.
4. Click **Save & Continue**. The extension will validate your username against the cloud storage.

## Step 5: Try It Out

1. Go to any retail product page. For example: [The North Face Jacket on Zalando](https://www.zalando.pl/the-north-face-m-hydrenalite-down-jacket-kurtka-puchowa-woodland-green-th322t090-m11.html)
2. **Make sure the product image is visible on screen** — the extension takes a screenshot of the current view, so if the product is scrolled out of sight, the analysis will fail.
3. Click the **Spare Room** extension icon, then click **Style this item**.
4. A sidebar will open showing a loading spinner. Wait for the AI to finish (this takes ~30-60 seconds as it runs multiple Gemini model calls).
5. Once complete, you will see:
   - A **virtual try-on image** of you wearing the product styled with your wardrobe items (front + 3 angle views).
   - A **fit score** (0-100) indicating how well the product fits your existing wardrobe.
   - **Matching wardrobe items** from your closet that pair well with the product.
   - A **styling tip** explaining why the combination works.
