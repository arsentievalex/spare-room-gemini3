# Spare Room: The Portal Between the Store and Your Wardrobe

## Inspiration

You know the feeling. You order clothes online that look amazing on the model, only to find they don't quite work with anything in your closet. Or worse, they don't fit right and end up in the returns pile. The fashion industry's return rate hovers around 30-40% for online purchases, with each return generating significant CO2 emissions from shipping, repackaging, and often ending up in landfills.

I kept asking myself: what if shoppers could see exactly how a piece would look on *them* and whether it actually complements what they already own, before clicking "buy"? That's how Spare Room was born. The name comes from Narnia, where the spare room holds a wardrobe that serves as a portal to another world. This app is a portal between online shopping and your wardrobe. I wanted to bridge the gap between the excitement of online shopping and the reality of what you actually own, enabling conscious buying decisions that are good for your wallet and the planet.

## What it does

Spare Room is an AI-powered shopping companion that connects online stores directly to your personal wardrobe. Here's how it works:

**Initial Setup (Web App):** Users start by creating their style profile through a web app built with Google AI Studio. They upload a photo of themselves, provide their measurements (height, weight, gender, and any specific dimensions), note any style preferences or restrictions (like "I don't wear skinny jeans"), and upload photos of their existing wardrobe.

**Shopping Experience (Chrome Extension):** The Chrome extension serves as the main control panel. When browsing any online clothing store, users can:
- **Virtual Try-On:** See how the garment would look on their actual body from multiple angles
- **Wardrobe Matching:** Get instant suggestions for items in their closet that would pair well with the new piece
- **Fit Score:** Receive a compatibility score (0-100) based on their existing wardrobe and style
- **Style Compatibility:** Get alerts if something conflicts with their stated preferences

The result? Shoppers make informed decisions, buy clothes they'll actually wear, and dramatically reduce the likelihood of returns.

## How I built it

I leveraged Google's Gemini 3 API as the backbone of all AI capabilities. The system uses three different models, each chosen for a specific job:

### Architecture Overview

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
   │                 │   │                 │   │        +        │
   │ → name, color,  │   │ → fit score     │   │ gemini-2.5-     │
   │   brand, price, │   │ → matching items│   │ flash-image     │
   │   category      │   │ → styling tips  │   │ (for angles)    │
   └─────────────────┘   └─────────────────┘   └─────────────────┘
```

### The Pipeline

**Step 1: Product Extraction** (`gemini-3-flash-preview`, thinking level: `low`)

When a user triggers the extension on a product page, the extension captures a screenshot and the page HTML. The Flash model parses this into structured product data: name, type, color, style, category, brand, price, material, and description. I use low thinking here because speed matters and the task is straightforward extraction.

**Step 2: Styling Analysis** (`gemini-3-flash-preview`, thinking level: `medium`)

With the product info in hand, the same Flash model (but with deeper reasoning enabled) analyzes how well the item fits with the user's existing wardrobe. It returns a fit score from 0-100, picks the best matching items from each wardrobe category (tops, bottoms, shoes, accessories), and generates styling tips. Medium thinking gives the model room to reason about color coordination, style coherence, and occasion appropriateness.

**Step 3: Image Generation** (`gemini-3-pro-image-preview` + `gemini-2.5-flash-image`)

This is where the magic happens. The Pro image model takes the user's photo, the product screenshot, and up to 3 selected wardrobe items, then generates a realistic front-view try-on image. For the additional angles (left, right, back), I use the faster Nano-Banana model (`gemini-2.5-flash-image`) which takes the front image as reference and generates rotated views.

### Why This Architecture Works

The key insight is using the right model for each job. Flash handles the text-heavy reasoning tasks quickly and cheaply. The Pro image model does the heavy lifting for the main visualization where quality matters most. And Nano-Banana fills in the supplementary angles without burning through the budget.

I used Pydantic schemas for structured output, which keeps the responses consistent and easy to parse. The Chrome extension itself makes no AI calls; it just captures page content and displays results. All the intelligence lives in the Python backend.

The onboarding web app was built using Google AI Studio for rapid prototyping and seamless Gemini integration.

## Challenges I ran into

**Wardrobe Recognition Complexity:** Teaching the AI to accurately categorize and understand diverse wardrobe items, from vintage jackets to athletic wear, required extensive prompt engineering and careful use of Gemini's multimodal capabilities.

**Real-Time Performance:** Users expect instant feedback while browsing. Balancing comprehensive analysis with speed meant strategically using different Gemini models and thinking levels for different tasks. This is why the architecture splits work across three model configurations.

**Body Representation:** Creating respectful, accurate virtual try-on experiences that work across all body types was both a technical and ethical challenge I took seriously.

**Cross-Site Compatibility:** Making the Chrome extension work seamlessly across different e-commerce platforms with varying page structures required robust content detection. The solution was to rely on screenshots plus raw HTML rather than trying to parse specific DOM structures.

## Accomplishments I'm proud of

- Built a fully functional prototype that actually helps people make smarter shopping decisions
- Got `gemini-3-pro-image-preview` to create realistic outfit visualizations combining user photos with wardrobe and product images
- Designed a three-model pipeline that balances speed, cost, and quality
- Developed an intuitive onboarding flow that makes wardrobe digitization painless
- Created multi-angle try-on views using Nano-Banana for the supplementary rotations
- Successfully leveraged Gemini 3's thinking levels to control reasoning depth per task

## What I learned

- **Gemini 3's thinking levels** are incredibly useful for balancing cost, speed, and quality. Low thinking for extraction, medium for analysis, and letting the image models handle generation separately.
- **Multimodal AI** has matured to the point where complex fashion understanding is genuinely possible
- **Structured output with Pydantic** makes working with LLM responses so much easier. No more parsing headaches.
- **Model selection matters.** Using Flash for text tasks and Pro-image for generation kept costs reasonable while maintaining quality where it counts.
- Building for **real-world shopping behavior** requires understanding the entire user journey, not just the transaction moment

## What's next for Spare Room

**Retail Partnerships:** I want to work directly with retailers to integrate Spare Room into their platforms, providing them with reduced return rates and happier customers.

**Social Features:** Allow users to get feedback from friends on potential purchases and share outfit combinations.

**Seasonal Intelligence:** Proactive suggestions when seasons change. "You have 3 items that would work great with a light spring jacket. Here are some options."

**Sustainability Dashboard:** Track how many returns users have avoided and visualize their personal CO2 savings over time.

**Mobile App:** Bring the full Spare Room experience to mobile shopping with AR try-on capabilities.

**Resale Integration:** When users add new items, suggest older pieces they might want to sell or donate, creating a circular fashion ecosystem.

The vision is a future where every clothing purchase is intentional, every item gets worn, and fashion retail contributes to sustainability rather than waste.
