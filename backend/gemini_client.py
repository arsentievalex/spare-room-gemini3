"""
Gemini 3 API client for the Styling Assistant.

Provides wrapper functions for:
1. Product extraction from screenshots/HTML
2. Wardrobe matching and styling recommendations
3. Image generation for outfit visualization (virtual try-on)
"""

import os
import base64
import json
import httpx
from typing import Optional
from pydantic import BaseModel
from google import genai
from google.genai import types
from dotenv import load_dotenv
import PIL.Image
from io import BytesIO

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not set. Set it before making API calls.")

# Initialize client (will be None if no API key)
client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)


# ==================== Data Models ====================

class ProductInfo(BaseModel):
    """Extracted product information."""
    name: str
    type: str  # e.g., "shirt", "pants", "dress", "jacket"
    color: str
    style: str  # e.g., "casual", "formal", "streetwear"
    category: str  # "top", "bottom", "outerwear", "shoes", "accessory"
    brand: Optional[str] = None
    price: Optional[str] = None
    material: Optional[str] = None
    description: str


class WardrobeMatch(BaseModel):
    """A single wardrobe item match with fit score."""
    item_id: str
    fit_score: int  # 0-100 for this specific pairing
    reason: str  # Brief reason why this item pairs well


class StylingResult(BaseModel):
    """Result of styling analysis."""
    overall_fit_score: int  # 0-100
    best_matches: list[WardrobeMatch]  # One per category, ranked by fit
    styling_tip: str  # Short, formatted tip


# ==================== Helper Functions ====================

def get_product_category(product_type: str) -> str:
    """Map product type to category for filtering."""
    type_lower = product_type.lower()

    tops = ["shirt", "t-shirt", "tshirt", "blouse", "polo", "sweater", "hoodie", "top", "tank"]
    bottoms = ["pants", "jeans", "trousers", "shorts", "skirt"]
    outerwear = ["jacket", "coat", "blazer", "cardigan", "vest", "parka", "windbreaker"]
    shoes = ["shoes", "sneakers", "boots", "loafers", "sandals", "heels"]
    accessories = ["hat", "cap", "scarf", "belt", "bag", "watch", "jewelry", "sunglasses"]

    for word in tops:
        if word in type_lower:
            return "top"
    for word in bottoms:
        if word in type_lower:
            return "bottom"
    for word in outerwear:
        if word in type_lower:
            return "outerwear"
    for word in shoes:
        if word in type_lower:
            return "shoes"
    for word in accessories:
        if word in type_lower:
            return "accessory"

    return "other"


def get_visible_categories(product_category: str) -> list[str]:
    """
    Determine which wardrobe categories would be visible when wearing a product.
    E.g., if wearing a winter jacket, a t-shirt underneath won't be visible.
    """
    if product_category == "outerwear":
        # Jacket/coat: show pants, shoes, accessories (not shirts underneath)
        return ["bottom", "shoes", "accessory"]
    elif product_category == "top":
        # Shirt/top: show pants, shoes, maybe outerwear
        return ["bottom", "shoes", "outerwear", "accessory"]
    elif product_category == "bottom":
        # Pants/skirt: show tops, shoes, outerwear
        return ["top", "shoes", "outerwear", "accessory"]
    elif product_category == "shoes":
        # Shoes: show pants, tops, outerwear
        return ["bottom", "top", "outerwear", "accessory"]
    else:
        # Default: show everything
        return ["top", "bottom", "outerwear", "shoes", "accessory"]


def load_image_as_base64(file_path: str) -> Optional[str]:
    """Load an image from local file path and return as base64."""
    try:
        import os
        # #region agent log
        import json
        with open('/Users/olek.arsentiev/Documents/gemini3_hack/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"gemini_client.py:113","message":"load_image_as_base64 entry","data":{"file_path":file_path,"file_exists":os.path.exists(file_path) if file_path else False},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
        
        if not file_path or not os.path.exists(file_path):
            print(f"Image file not found: {file_path}")
            # #region agent log
            with open('/Users/olek.arsentiev/Documents/gemini3_hack/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"gemini_client.py:120","message":"Image file not found","data":{"file_path":file_path},"timestamp":int(__import__('time').time()*1000)})+'\n')
            # #endregion
            return None
        
        with open(file_path, 'rb') as f:
            image_data = f.read()
            print(f"Loaded image from {file_path}: {len(image_data)} bytes")
            # #region agent log
            with open('/Users/olek.arsentiev/Documents/gemini3_hack/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"gemini_client.py:127","message":"Image loaded successfully","data":{"file_path":file_path,"content_length":len(image_data)},"timestamp":int(__import__('time').time()*1000)})+'\n')
            # #endregion
            return base64.b64encode(image_data).decode('utf-8')
    except Exception as e:
        print(f"Failed to load image from {file_path}: {e}")
        # #region agent log
        import json
        with open('/Users/olek.arsentiev/Documents/gemini3_hack/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"gemini_client.py:133","message":"Exception in load_image_as_base64","data":{"error_type":type(e).__name__,"error_message":str(e)},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
    return None


# ==================== Product Extraction ====================

async def extract_product_info(
    screenshot_base64: str,
    html_content: str,
    page_url: str,
    page_title: str
) -> ProductInfo:
    """
    Extract product information from a page screenshot and HTML.
    """
    if not client:
        raise RuntimeError("GEMINI_API_KEY not configured")

    # Prepare the image
    image_data = base64.b64decode(screenshot_base64)
    image_part = types.Part.from_bytes(data=image_data, mime_type="image/png")

    # Truncate HTML to avoid token limits
    truncated_html = html_content[:30000] if len(html_content) > 30000 else html_content

    prompt = f"""You are an expert fashion product analyst with deep knowledge of clothing, brands, and retail. Your task is to extract precise product information from an e-commerce product page.

## CONTEXT
You are provided with:
1. A screenshot of the product page (analyze visuals: product image, color, style cues)
2. HTML content containing structured product data
3. Page metadata

Page URL: {page_url}
Page Title: {page_title}

## HTML CONTENT (for structured data extraction)
{truncated_html}

## EXTRACTION INSTRUCTIONS

Analyze BOTH the visual screenshot AND the HTML to extract accurate product details. Cross-reference visual information with text data for accuracy.

### Required Fields:

**name**: Extract the exact product name as displayed (e.g., "Oversized Linen Blend Shirt", "Classic Straight Leg Jeans")

**type**: Identify the specific garment type. Be precise:
- Tops: "t-shirt", "polo", "blouse", "sweater", "hoodie", "tank top", "crop top", "cardigan"
- Bottoms: "jeans", "chinos", "trousers", "shorts", "skirt", "joggers", "leggings"
- Outerwear: "jacket", "blazer", "coat", "parka", "bomber", "denim jacket", "leather jacket"
- Shoes: "sneakers", "boots", "loafers", "sandals", "heels", "oxford shoes"
- Accessories: "hat", "scarf", "belt", "bag", "watch", "sunglasses", "jewelry"

**color**: Describe the primary color(s) accurately. Use specific color names when possible:
- Instead of "blue" → "navy blue", "sky blue", "cobalt", "indigo"
- Instead of "brown" → "tan", "camel", "chocolate", "cognac"
- For patterns: "black and white striped", "floral print", "plaid"

**style**: Categorize the aesthetic style:
- "casual" - everyday relaxed wear
- "smart casual" - polished but not formal
- "formal" - business/dressy occasions
- "streetwear" - urban, trendy, often logo-heavy
- "athleisure" - sporty but fashionable
- "bohemian" - flowy, artistic, earthy
- "minimalist" - clean lines, neutral colors
- "vintage" - retro-inspired designs

**category**: MUST be exactly one of: "top", "bottom", "outerwear", "shoes", "accessory"

**brand**: Extract brand name from logo, URL, or HTML. Use proper capitalization (e.g., "Zara", "H&M", "Nike")

**price**: Include currency symbol and full price (e.g., "$49.99", "€79.00", "£65")

**material**: Extract fabric composition if available (e.g., "100% cotton", "polyester blend", "genuine leather")

**description**: Write ONE concise sentence capturing the product's key selling points and aesthetic appeal.

## OUTPUT
Return valid JSON matching the schema exactly. Ensure all string values are properly escaped."""

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=[image_part, prompt],
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level="low"),
            response_mime_type="application/json",
            response_schema=ProductInfo,
            temperature=0.5
        )
    )

    try:
        result_text = response.text
        result_dict = json.loads(result_text)
        product = ProductInfo(**result_dict)
        # Ensure category is set correctly
        if not product.category or product.category == "other":
            product.category = get_product_category(product.type)
        return product
    except Exception as e:
        return ProductInfo(
            name=page_title or "Unknown Product",
            type="clothing",
            color="unknown",
            style="casual",
            category="other",
            description="Could not extract product details"
        )


# ==================== Styling Analysis ====================

async def analyze_styling(
    product: ProductInfo,
    user_context: str,
    wardrobe_items: list[dict]
) -> StylingResult:
    """
    Analyze how well a product fits with the user's wardrobe.
    Returns ONE best match per visible category.
    """
    if not client:
        raise RuntimeError("GEMINI_API_KEY not configured")

    # Get categories that would be visible with this product
    visible_categories = get_visible_categories(product.category)

    # Filter wardrobe to only items in visible categories
    filtered_items = []
    for item in wardrobe_items:
        item_category = get_product_category(item['type'])
        if item_category in visible_categories:
            filtered_items.append({**item, 'category': item_category})

    if not filtered_items:
        return StylingResult(
            overall_fit_score=50,
            best_matches=[],
            styling_tip="Add more items to your wardrobe for better recommendations."
        )

    # Build wardrobe list with IDs clearly marked
    wardrobe_text = "\n".join([
        f"- ID=\"{item['id']}\" | {item['name']} | Type: {item['type']} | Color: {item['color']} | Category: {item['category']}"
        for item in filtered_items
    ])

    # Build valid IDs list for the prompt
    valid_ids = [item['id'] for item in filtered_items]

    prompt = f"""You are a world-renowned personal stylist who has dressed celebrities, styled editorial shoots for Vogue, and served as creative director at luxury fashion houses. You possess encyclopedic knowledge of fashion theory, color science, and the subtle art of creating outfits that make people feel confident and look exceptional.

## YOUR MISSION
A client is considering purchasing a new item. Analyze whether it will integrate beautifully with their existing wardrobe, and if so, which specific pieces create the most stunning combinations.

## THE NEW PIECE UNDER CONSIDERATION
- **Item**: {product.name}
- **Garment Type**: {product.type}
- **Color**: {product.color}
- **Style Aesthetic**: {product.style}
- **Category**: {product.category}

## CLIENT PROFILE
{user_context}

## CLIENT'S CURRENT WARDROBE
{wardrobe_text}

**Available Item IDs**: {valid_ids}

---

## EXPERT STYLING FRAMEWORK

### 1. COLOR THEORY & HARMONY

**The 60-30-10 Rule**:
- 60% dominant color (usually neutral: black, white, navy, gray, beige)
- 30% secondary color (complementary or analogous)
- 10% accent color (bold pop, accessories)
- Evaluate if the new piece fits as a 60%, 30%, or 10% element

**Color Temperature**:
- WARM undertones: red, orange, yellow, coral, rust, camel, olive, warm brown
- COOL undertones: blue, green, purple, pink, silver, charcoal, cool gray
- Mixing temperatures CAN work but requires sophistication
- Same-temperature outfits feel naturally cohesive

**Advanced Color Pairings**:
- **Monochromatic**: Same color, different shades (elegant, elongating)
- **Analogous**: Adjacent colors (blue + teal + green = harmonious)
- **Complementary**: Opposites (navy + burnt orange = striking)
- **Triadic**: Three equidistant colors (sophisticated when balanced)
- **Neutral + Pop**: Safe foundation + one statement color

**Color Clashes to Avoid**:
- Competing brights (red + orange + pink together)
- Clashing undertones (cool pink + warm orange)
- Too many patterns with different color stories

### 2. SILHOUETTE & PROPORTION

**The Golden Rule of Balance**:
- Volume on top → fitted on bottom (oversized sweater + slim jeans)
- Fitted on top → volume on bottom (bodysuit + wide-leg trousers)
- NEVER volume + volume (looks shapeless) unless intentionally avant-garde

**Waistline Strategies**:
- High-waisted bottoms + tucked top = legs appear longer
- Cropped top + high-waisted = shows sliver of skin, modern
- Dropped waist = relaxed, '90s aesthetic (harder to pull off)

**Layering Hierarchy**:
- Thinnest layer closest to body, progressively heavier outward
- Each layer should be visible at edges (collar, hem, cuffs)
- Odd numbers of layers (1, 3) often look more intentional than even

**Length Relationships**:
- Jacket hem should NOT hit at widest part of hips
- Midi skirts work best with heels or sleek boots
- Cropped pants need the right shoe (loafers, ankle boots, not chunky sneakers)

### 3. TEXTURE & FABRIC INTERPLAY

**Texture Mixing Mastery**:
- Contrast creates visual interest: matte + shiny, rough + smooth
- Leather + knit = edgy sophistication
- Denim + silk = casual elegance
- Wool + cotton = textural depth
- Velvet + linen = generally avoid (seasonal clash)

**Fabric Weight Consistency**:
- Heavy fabrics (wool coat) pair with substantial pieces (thick knits, denim)
- Light fabrics (linen shirt) pair with breathable pieces (cotton, chambray)
- Mixing weights requires intentionality

**Pattern Mixing Rules**:
- Vary the SCALE: large floral + thin stripe = works
- Same scale patterns compete and clash
- Keep one pattern dominant, others subtle
- Solid "rest" pieces between patterns
- Patterns should share at least one color

### 4. STYLE COHERENCE & OCCASION

**Style Spectrum Compatibility**:
- Athleisure ←→ Casual ←→ Smart Casual ←→ Business Casual ←→ Formal
- Items can move 1-2 steps on the spectrum, not more
- A hoodie (athleisure) can dress up to casual, NOT to business casual
- A blazer (business casual) can dress down to smart casual with jeans

**Occasion Versatility Score**:
- How many different occasions can this outfit serve?
- Work-to-dinner transitions are valuable
- Weekend-to-brunch flexibility matters

**Aesthetic Tribes** (don't mix across tribes without expertise):
- Minimalist: Clean lines, neutral palette, quality over quantity
- Classic: Timeless pieces, navy/camel/white, preppy influences
- Streetwear: Logos, sneakers, oversized fits, graphic elements
- Bohemian: Flowy fabrics, earth tones, artisanal details
- Edgy: Black, leather, asymmetry, hardware details
- Romantic: Soft fabrics, florals, delicate details, pastels

### 5. WARDROBE GAPS & REDUNDANCY

**Capsule Wardrobe Thinking**:
- Does this piece fill a GAP in the wardrobe? (High value)
- Does it DUPLICATE something already owned? (Low value unless upgrade)
- How many existing pieces can it pair with? (Versatility multiplier)

**The "Cost Per Wear" Mindset**:
- Versatile pieces that match 5+ items = excellent investment
- Pieces that only match 1-2 items = consider carefully
- Statement pieces that create 0 new outfit options = likely pass

---

## SCORING METHODOLOGY

**Overall Fit Score (0-100)**:

| Score | Meaning | Criteria |
|-------|---------|----------|
| 95-100 | Wardrobe Essential | Fills critical gap, matches 5+ pieces, elevates multiple outfits |
| 85-94 | Excellent Addition | Versatile, strong color/style harmony, creates 3-4 new outfits |
| 75-84 | Good Purchase | Solid matches exist, complements aesthetic, adds variety |
| 65-74 | Decent Option | Works with a few pieces, some styling limitations |
| 50-64 | Marginal Fit | Limited pairing options, may feel disconnected from wardrobe |
| 35-49 | Poor Fit | Style/color conflicts, few viable combinations |
| 0-34 | Does Not Belong | Clashes with wardrobe aesthetic, no good pairings |

**Individual Item Pairing Score (0-100)**:
- 90+: Perfect harmony across color, style, silhouette, occasion
- 80-89: Strong pairing with minor considerations
- 70-79: Good match, works well together
- 60-69: Acceptable pairing, not optimal
- Below 60: Weak pairing, styling challenges

---

## STRICT CONSTRAINTS
1. **ONLY** select from these IDs: {valid_ids} — never hallucinate items
2. **ONE item per category** maximum (one bottom, one top, etc.)
3. Select only items that would be **VISIBLE** in the final outfit
4. If new piece is outerwear → tops are hidden underneath, don't select them
5. If new piece is a top → don't select another top
6. Do not select accessories (caps, hats, scarves, etc.) for all outfites, select only where it fits best (e.g. a hat for a casual outfit, a scarf for a formal outfit, etc.) Do not select caps for winter outfits.

---

## REQUIRED OUTPUT

Return JSON with:
1. **overall_fit_score**: Integer 0-100 using the scoring methodology above
2. **best_matches**: Array with ONE match per visible category:
   - item_id: Must be exactly from {valid_ids}
   - fit_score: 0-100 for this specific pairing
   - reason: 10 words max - cite specific styling principles (e.g., "Complementary colors: navy + camel create classic contrast")
3. **styling_tip**: One expert tip (max 15 words) that a real stylist would give - be specific, not generic

Return valid JSON only."""

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level="medium"),
            response_mime_type="application/json",
            response_schema=StylingResult,
            temperature=0.5
        )
    )

    try:
        result_text = response.text
        result_dict = json.loads(result_text)
        result = StylingResult(**result_dict)

        # CRITICAL: Filter out any hallucinated items that aren't in the wardrobe
        valid_id_set = set(valid_ids)
        validated_matches = []
        seen_categories = set()

        for match in result.best_matches:
            if match.item_id in valid_id_set:
                # Find the item to get its category
                item = next((i for i in filtered_items if i['id'] == match.item_id), None)
                if item:
                    category = item['category']
                    # Only keep ONE item per category
                    if category not in seen_categories:
                        seen_categories.add(category)
                        validated_matches.append(match)

        result.best_matches = validated_matches
        return result

    except Exception as e:
        print(f"Styling analysis error: {e}")
        return StylingResult(
            overall_fit_score=50,
            best_matches=[],
            styling_tip="This piece could work with neutral basics."
        )


# ==================== Image Generation (Virtual Try-On) ====================

def _load_pil_image(file_path: str) -> Optional[PIL.Image.Image]:
    """Load an image file as a PIL Image object."""
    try:
        if not file_path or not os.path.exists(file_path):
            print(f"Image file not found: {file_path}")
            return None
        img = PIL.Image.open(file_path)
        print(f"Loaded PIL image from {file_path}: {img.size}")
        return img
    except Exception as e:
        print(f"Failed to load PIL image from {file_path}: {e}")
        return None


def _base64_to_pil_image(base64_str: str) -> Optional[PIL.Image.Image]:
    """Convert a base64 string to a PIL Image object."""
    try:
        image_data = base64.b64decode(base64_str)
        img = PIL.Image.open(BytesIO(image_data))
        print(f"Converted base64 to PIL image: {img.size}")
        return img
    except Exception as e:
        print(f"Failed to convert base64 to PIL image: {e}")
        return None


async def generate_tryon_image(
    product: ProductInfo,
    product_screenshot_base64: str,
    selected_items: list[dict],
    user_profile: dict
) -> Optional[str]:
    """
    Generate a virtual try-on image showing the user wearing the outfit.

    Uses gemini-3-pro-image-preview which accepts up to 6 images.
    We pass: 1) user reference photo, 2) product image, 3-5) up to 3 wardrobe items.
    """
    # #region agent log
    import json
    with open('/Users/olek.arsentiev/Documents/gemini3_hack/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"gemini_client.py:342","message":"generate_tryon_image entry","data":{"has_client":bool(client),"product_name":product.name,"selected_items_count":len(selected_items)},"timestamp":int(__import__('time').time()*1000)})+'\n')
    # #endregion
    if not client:
        # #region agent log
        with open('/Users/olek.arsentiev/Documents/gemini3_hack/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"gemini_client.py:343","message":"Client not initialized","data":{"error":"GEMINI_API_KEY not configured"},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
        raise RuntimeError("GEMINI_API_KEY not configured")

    # User body info
    height = user_profile.get('height_cm', 175)
    size_top = user_profile.get('typical_size_top', 'M')
    size_bottom = user_profile.get('typical_size_bottom', '32')

    # Load user photo as PIL Image (IMAGE 1)
    user_photo_path = user_profile.get('photo_path')
    # #region agent log
    with open('/Users/olek.arsentiev/Documents/gemini3_hack/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"gemini_client.py:388","message":"Checking user photo path","data":{"user_photo_path":user_photo_path},"timestamp":int(__import__('time').time()*1000)})+'\n')
    # #endregion

    user_photo_pil = _load_pil_image(user_photo_path) if user_photo_path else None
    if not user_photo_pil:
        print("ERROR: Cannot generate try-on without user photo")
        # #region agent log
        with open('/Users/olek.arsentiev/Documents/gemini3_hack/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"gemini_client.py:406","message":"Returning None - no user photo","data":{},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
        return None

    # Load product screenshot as PIL Image (IMAGE 2)
    product_pil = _base64_to_pil_image(product_screenshot_base64)
    if not product_pil:
        print("ERROR: Cannot generate try-on without product image")
        return None

    # Load up to 3 wardrobe items as PIL Images (IMAGES 3-5)
    wardrobe_images = []  # List of (pil_image, item_dict) tuples
    for item in selected_items[:3]:  # Max 3 wardrobe items
        if item.get('image_path'):
            item_pil = _load_pil_image(item['image_path'])
            if item_pil:
                wardrobe_images.append((item_pil, item))
                print(f"Loaded wardrobe item for image: {item['name']}")

    # Get additional user measurements if available
    weight = user_profile.get('weight_kg', '')
    body_type = user_profile.get('body_type', 'average')
    skin_tone = user_profile.get('skin_tone', '')
    hair_color = user_profile.get('hair_color', '')

    # Build wardrobe items description for the prompt
    wardrobe_descriptions = []
    for idx, (_, item) in enumerate(wardrobe_images):
        img_num = idx + 3
        wardrobe_descriptions.append(f"**IMAGE {img_num} - {item['name'].upper()}**: {item['color']} {item['type']}")

    wardrobe_section = "\n".join(wardrobe_descriptions) if wardrobe_descriptions else "No additional wardrobe items provided."

    # Build the prompt text
    prompt_text = f"""You are a world-class fashion photographer and virtual try-on specialist. Create a photorealistic virtual try-on image for a high-end retail e-commerce store (Zara, COS, H&M premium style).

## CRITICAL: USE THE PERSON FROM IMAGE 1
**IMAGE 1 is the ACTUAL USER.** You MUST:
- Use their EXACT face, facial features, skin tone, and hair
- Preserve their identity - the result must look like THE SAME PERSON
- Match their body proportions accurately
- This is NOT a generic model - it must be THIS specific person

## USER'S MEASUREMENTS
- Height: {height} cm | Top: {size_top} | Bottom: {size_bottom}
{f"- Weight: {weight} kg" if weight else ""}{f" | Body type: {body_type}" if body_type else ""}

## IMAGE REFERENCES

**IMAGE 1 - THE USER (MANDATORY)**
Use their face, skin tone, hair, body shape, and proportions.

**IMAGE 2 - NEW PRODUCT: {product.name}**
- {product.color} {product.type} - this is the HERO piece being tried on
- Extract ONLY the garment, IGNORE any model in this image
- This item MUST appear in the final image

{wardrobe_section}

## MANDATORY: INCLUDE ALL PROVIDED ITEMS

**You MUST include EVERY wardrobe item shown in the reference images.**
These items have been specifically selected by our styling AI as the best matches - they ARE the recommended outfit.

- The new product (IMAGE 2) MUST be worn
- ALL wardrobe items from IMAGES 3-5 MUST appear in the final image
- Accessories like caps, hats, scarves MUST be worn if provided
- Do NOT skip any item - each one was chosen for a reason

**Your job is to make ALL items look cohesive together**, not to decide which items to include.

## PHOTOGRAPHY REQUIREMENTS

**Composition**: Full body, head to feet, centered, studio backdrop (light gray #F5F5F5)

**Pose**: Natural confident standing pose, relaxed shoulders, slight weight shift

**Lighting**: Soft diffused studio lighting, no harsh shadows

**Quality**: Sharp focus, visible fabric textures, accurate colors, professional e-commerce grade

**Orientation**: Vertical full body shot, no cropped or partial body shots, no horizontal shots, no extra blank space on the sides.

## OUTPUT REQUIREMENTS
✓ Person's face matches IMAGE 1 exactly
✓ The new product ({product.name}) is the focal point and MUST be worn
✓ ALL wardrobe items from provided images MUST appear (no exceptions)
✓ Full body visible, professional retail photography quality
✓ Every accessory (caps, hats, etc.) MUST be worn if provided
✓ No extra blank space on the sides.

Generate the image now."""

    # Build contents list: prompt + user photo + product + up to 3 wardrobe items
    # Total max: 5 images (1 user + 1 product + 3 wardrobe)
    contents = [prompt_text, user_photo_pil, product_pil]
    for wardrobe_pil, _ in wardrobe_images:
        contents.append(wardrobe_pil)

    images_count = 2 + len(wardrobe_images)
    print(f"Sending {images_count} images to Gemini Pro Image (max 5)")

    # #region agent log
    with open('/Users/olek.arsentiev/Documents/gemini3_hack/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"gemini_client.py:437","message":"Before API call","data":{"images_count":images_count,"wardrobe_items_count":len(wardrobe_images)},"timestamp":int(__import__('time').time()*1000)})+'\n')
    # #endregion

    try:
        # #region agent log
        with open('/Users/olek.arsentiev/Documents/gemini3_hack/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"gemini_client.py:439","message":"Calling Gemini API","data":{"model":"gemini-3-pro-image-preview"},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=['Text', 'Image']
            )
        )
        # #region agent log
        with open('/Users/olek.arsentiev/Documents/gemini3_hack/.cursor/debug.log', 'a') as f:
            candidate = response.candidates[0] if response.candidates else None
            has_content = bool(candidate and candidate.content)
            parts_count = len(candidate.content.parts) if (candidate and candidate.content and hasattr(candidate.content, 'parts')) else 0
            finish_reason = getattr(candidate, 'finish_reason', None) if candidate else None
            # Log prompt_feedback if available
            prompt_feedback = getattr(response, 'prompt_feedback', None)
            prompt_feedback_data = None
            if prompt_feedback:
                prompt_feedback_data = {
                    "block_reason": str(getattr(prompt_feedback, 'block_reason', None)) if hasattr(prompt_feedback, 'block_reason') else None,
                    "safety_ratings": [{"category": str(r.category) if hasattr(r, 'category') else None, "probability": str(r.probability) if hasattr(r, 'probability') else None} for r in (getattr(prompt_feedback, 'safety_ratings', []) or [])] if hasattr(prompt_feedback, 'safety_ratings') else []
                }
            # Log response structure details
            response_structure = {
                "has_candidates": bool(response.candidates),
                "candidates_count": len(response.candidates) if response.candidates else 0,
                "has_content": has_content,
                "parts_count": parts_count,
                "candidate_type": type(candidate).__name__ if candidate else None,
                "content_type": type(candidate.content).__name__ if (candidate and candidate.content) else None,
                "finish_reason": str(finish_reason) if finish_reason else None,
                "prompt_feedback": prompt_feedback_data
            }
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"gemini_client.py:447","message":"API call succeeded","data":response_structure,"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion

        # Extract image from response
        if not response.candidates or len(response.candidates) == 0:
            print("No candidates in response")
            # #region agent log
            with open('/Users/olek.arsentiev/Documents/gemini3_hack/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"gemini_client.py:540","message":"No candidates in response","data":{},"timestamp":int(__import__('time').time()*1000)})+'\n')
            # #endregion
            return None

        candidate = response.candidates[0]
        # #region agent log
        with open('/Users/olek.arsentiev/Documents/gemini3_hack/.cursor/debug.log', 'a') as f:
            finish_reason = getattr(candidate, 'finish_reason', None) if candidate else None
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"gemini_client.py:548","message":"Checking candidate","data":{"has_candidate":bool(candidate),"has_content":bool(candidate.content if candidate else None),"finish_reason":str(finish_reason) if finish_reason else None},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion

        if not candidate or not candidate.content:
            print(f"Candidate has no content (finish_reason: {getattr(candidate, 'finish_reason', 'unknown') if candidate else 'no candidate'})")
            # #region agent log
            with open('/Users/olek.arsentiev/Documents/gemini3_hack/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"gemini_client.py:555","message":"Candidate has no content","data":{"has_candidate":bool(candidate),"has_content":bool(candidate.content if candidate else None),"finish_reason":str(getattr(candidate, 'finish_reason', None)) if candidate else None},"timestamp":int(__import__('time').time()*1000)})+'\n')
            # #endregion
            return None

        if not hasattr(candidate.content, 'parts') or not candidate.content.parts:
            print("Content has no parts")
            # #region agent log
            with open('/Users/olek.arsentiev/Documents/gemini3_hack/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"gemini_client.py:543","message":"Content has no parts","data":{},"timestamp":int(__import__('time').time()*1000)})+'\n')
            # #endregion
            return None

        for part in candidate.content.parts:
            # #region agent log
            with open('/Users/olek.arsentiev/Documents/gemini3_hack/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"gemini_client.py:451","message":"Checking response part","data":{"has_inline_data":hasattr(part,'inline_data'),"inline_data_exists":bool(hasattr(part,'inline_data') and part.inline_data)},"timestamp":int(__import__('time').time()*1000)})+'\n')
            # #endregion
            if hasattr(part, 'inline_data') and part.inline_data:
                print(f"Generated try-on image: {len(part.inline_data.data)} bytes")
                # #region agent log
                with open('/Users/olek.arsentiev/Documents/gemini3_hack/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"gemini_client.py:454","message":"Image found in response","data":{"image_size_bytes":len(part.inline_data.data)},"timestamp":int(__import__('time').time()*1000)})+'\n')
                # #endregion
                return base64.b64encode(part.inline_data.data).decode('utf-8')

        print("No image in response")
        # #region agent log
        with open('/Users/olek.arsentiev/Documents/gemini3_hack/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"gemini_client.py:460","message":"No image in response","data":{"parts_count":len(response.candidates[0].content.parts) if response.candidates else 0},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
        return None

    except Exception as e:
        print(f"Image generation error: {e}")
        # #region agent log
        with open('/Users/olek.arsentiev/Documents/gemini3_hack/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"F","location":"gemini_client.py:465","message":"Exception during image generation","data":{"error_type":type(e).__name__,"error_message":str(e)},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
        return None


async def generate_angle_image(
    main_image_base64: str,
    angle: str,
    product_name: str,
    max_retries: int = 2
) -> Optional[str]:
    """
    Generate the same outfit image from a different angle.

    Args:
        main_image_base64: The main front-view image
        angle: One of "left", "right", "back"
        product_name: Name of the product for context
        max_retries: Number of retry attempts if generation fails

    Returns:
        Base64 encoded image from the requested angle
    """
    import asyncio

    if not client:
        return None

    # Convert main image to PIL
    main_image_pil = _base64_to_pil_image(main_image_base64)
    if not main_image_pil:
        print(f"ERROR: Cannot generate {angle} angle - failed to load main image")
        return None

    angle_descriptions = {
        "left": "LEFT SIDE view (90 degrees rotated, showing the left profile)",
        "right": "RIGHT SIDE view (90 degrees rotated, showing the right profile)",
        "back": "BACK view (180 degrees rotated, showing from behind)"
    }

    angle_desc = angle_descriptions.get(angle, angle)

    prompt_text = f"""You are given IMAGE 1 which shows a fashion model wearing an outfit (front view).

Your task: Generate the EXACT SAME image but from a {angle_desc}.

## CRITICAL REQUIREMENTS - PRESERVE EVERYTHING:
- **SAME PERSON**: Identical face, hair, skin tone, body proportions
- **SAME OUTFIT**: Every clothing item must be identical - same colors, patterns, fit, draping
- **SAME POSE ENERGY**: Similar confident stance, just rotated to show the {angle} view
- **SAME LIGHTING**: Identical studio lighting setup and shadows
- **SAME BACKGROUND**: Clean light gray (#F5F5F5) studio backdrop
- **SAME QUALITY**: Professional e-commerce photography grade

## ANGLE SPECIFICATION: {angle.upper()} VIEW
- Rotate the camera {angle_desc}
- The person should appear naturally turned, as if photographed from this angle
- All clothing details visible from this angle should be accurate
- Maintain the same distance and framing

## DO NOT:
- Change any clothing items or colors
- Alter the person's appearance
- Modify the lighting or background
- Add or remove any elements

Generate the {angle} view image now."""

    for attempt in range(max_retries + 1):
        try:
            # Add small delay between retries to avoid rate limiting
            if attempt > 0:
                delay = 2 * attempt  # 2s, 4s delays
                print(f"Retry {attempt} for {angle} angle after {delay}s delay...")
                await asyncio.sleep(delay)

            response = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[prompt_text, main_image_pil],
                config=types.GenerateContentConfig(
                    response_modalities=['Text', 'Image']
                )
            )

            # Extract image from response
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]

                # Check for finish reason issues
                finish_reason = getattr(candidate, 'finish_reason', None)
                if finish_reason and 'SAFETY' in str(finish_reason):
                    print(f"Safety filter triggered for {angle} angle, retrying...")
                    continue

                if candidate and candidate.content and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            print(f"Generated {angle} angle image: {len(part.inline_data.data)} bytes")
                            return base64.b64encode(part.inline_data.data).decode('utf-8')

            print(f"No image in {angle} angle response (attempt {attempt + 1}/{max_retries + 1})")

        except Exception as e:
            print(f"Angle image generation error ({angle}, attempt {attempt + 1}): {e}")
            if attempt < max_retries:
                continue

    print(f"Failed to generate {angle} angle after {max_retries + 1} attempts")
    return None


async def generate_all_tryon_images(
    product: ProductInfo,
    product_screenshot_base64: str,
    selected_items: list[dict],
    user_profile: dict
) -> dict:
    """
    Generate main try-on image and additional angle views.

    Returns:
        Dict with keys: front, left, right, back (base64 images)
    """
    import asyncio

    result = {
        "front": None,
        "left": None,
        "right": None,
        "back": None
    }

    # Step 1: Generate main front image with Pro model
    print("Generating main front image with gemini-3-pro-image-preview...")
    main_image = await generate_tryon_image(
        product=product,
        product_screenshot_base64=product_screenshot_base64,
        selected_items=selected_items,
        user_profile=user_profile
    )

    if not main_image:
        print("Failed to generate main image")
        return result

    result["front"] = main_image
    print("Main front image generated successfully")

    # Step 2: Generate angle views with Flash model (sequentially with delays)
    angles = ["left", "right", "back"]

    for i, angle in enumerate(angles):
        # Add delay between requests to avoid rate limiting
        if i > 0:
            print(f"Waiting 1s before next angle to avoid rate limiting...")
            await asyncio.sleep(1)

        print(f"Generating {angle} angle view with gemini-2.5-flash-image...")
        angle_image = await generate_angle_image(
            main_image_base64=main_image,
            angle=angle,
            product_name=product.name
        )
        if angle_image:
            result[angle] = angle_image
            print(f"{angle.capitalize()} angle generated successfully")
        else:
            print(f"Failed to generate {angle} angle")

    return result


# ==================== Combined Analysis ====================

async def full_product_analysis(
    screenshot_base64: str,
    html_content: str,
    page_url: str,
    page_title: str,
    user_context: str,
    wardrobe_items: list[dict],
    user_profile: dict
) -> dict:
    """
    Perform full product analysis pipeline:
    1. Extract product info from screenshot/HTML
    2. Analyze styling fit with wardrobe (one item per category)
    3. Generate virtual try-on image
    """
    # #region agent log
    import json
    with open('/Users/olek.arsentiev/Documents/gemini3_hack/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"G","location":"gemini_client.py:471","message":"full_product_analysis entry","data":{"wardrobe_items_count":len(wardrobe_items)},"timestamp":int(__import__('time').time()*1000)})+'\n')
    # #endregion
    # Step 1: Extract product info
    product = await extract_product_info(
        screenshot_base64=screenshot_base64,
        html_content=html_content,
        page_url=page_url,
        page_title=page_title
    )

    # Step 2: Analyze styling
    styling = await analyze_styling(
        product=product,
        user_context=user_context,
        wardrobe_items=wardrobe_items
    )

    # Get selected wardrobe items (only validated ones from best_matches)
    selected_item_ids = [match.item_id for match in styling.best_matches]
    selected_items = [
        item for item in wardrobe_items
        if item['id'] in selected_item_ids
    ]

    # Add fit scores to selected items for display
    for item in selected_items:
        match = next((m for m in styling.best_matches if m.item_id == item['id']), None)
        if match:
            item['fit_score'] = match.fit_score
            item['match_reason'] = match.reason

    # Step 3: Generate virtual try-on images (front + angles)
    generated_images = await generate_all_tryon_images(
        product=product,
        product_screenshot_base64=screenshot_base64,
        selected_items=selected_items,
        user_profile=user_profile
    )
    # #region agent log
    import json
    with open('/Users/olek.arsentiev/Documents/gemini3_hack/.cursor/debug.log', 'a') as f:
        angles_generated = [k for k, v in generated_images.items() if v]
        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"G","location":"gemini_client.py:513","message":"full_product_analysis returning result","data":{"angles_generated":angles_generated,"count":len(angles_generated)},"timestamp":int(__import__('time').time()*1000)})+'\n')
    # #endregion

    return {
        "product": product.model_dump(),
        "fit_score": styling.overall_fit_score,
        "selected_items": selected_items,
        "commentary": styling.styling_tip,
        "generated_image_base64": generated_images.get("front"),  # Keep for backwards compatibility
        "generated_images": generated_images  # New: all angles
    }
