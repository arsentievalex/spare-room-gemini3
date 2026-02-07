"""
FastAPI backend server for the Wardrobe Styling Assistant.

Endpoints:
- POST /analyze-and-style: Analyze a product page and return styling recommendations
- GET /health: Health check endpoint
"""

import base64
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from wardrobe import fetch_user_info, parse_user_profile, parse_wardrobe_items, get_user_context
from gemini_client import full_product_analysis


async def load_image_thumbnail_from_url(url: str) -> Optional[str]:
    """Download an image from URL and return as base64 string."""
    try:
        if not url:
            return None
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return base64.b64encode(response.content).decode('utf-8')
        return None
    except Exception:
        return None


# Initialize FastAPI app
app = FastAPI(
    title="Wardrobe Styling Assistant API",
    description="AI-powered styling recommendations using Gemini 3",
    version="1.0.0"
)

# Configure CORS for Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Request/Response Models ====================

class AnalyzeRequest(BaseModel):
    """Request body for product analysis."""
    username: str
    gemini_api_key: str
    page_url: str
    page_title: str
    html_content: str
    screenshot_base64: str


class ProductInfo(BaseModel):
    """Product information in response."""
    name: str
    type: str
    color: str
    style: str
    brand: Optional[str] = None
    price: Optional[str] = None
    description: str


class WardrobeItemResponse(BaseModel):
    """Wardrobe item in response."""
    id: str
    name: str
    type: str
    color: str
    color_hex: Optional[str] = None
    match_reason: Optional[str] = None
    image_base64: Optional[str] = None
    image_url: Optional[str] = None


class GeneratedImages(BaseModel):
    """Generated try-on images from multiple angles."""
    front: Optional[str] = None
    left: Optional[str] = None
    right: Optional[str] = None
    back: Optional[str] = None


class AnalyzeResponse(BaseModel):
    """Response body for product analysis."""
    product: ProductInfo
    fit_score: int
    selected_items: list[WardrobeItemResponse]
    commentary: str
    generated_image_base64: Optional[str] = None
    generated_images: Optional[GeneratedImages] = None


# ==================== Endpoints ====================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/analyze-and-style", response_model=AnalyzeResponse)
async def analyze_and_style(request: AnalyzeRequest):
    """
    Analyze a product page and return styling recommendations.

    Flow:
    1. Fetch user data from GCS
    2. Extract product info from screenshot + HTML using Gemini
    3. Match with user's wardrobe items
    4. Generate styled outfit visualization
    5. Return fit score, selected items, and commentary
    """
    # Fetch user info from GCS
    user_info = await fetch_user_info(request.username)
    if not user_info:
        raise HTTPException(status_code=404, detail=f"User not found: {request.username}")

    # Parse user data
    user_profile = parse_user_profile(user_info)
    wardrobe = parse_wardrobe_items(user_info)

    if not wardrobe:
        raise HTTPException(status_code=404, detail=f"No wardrobe items found for user: {request.username}")

    # Convert wardrobe items to dicts for the AI
    wardrobe_dicts = [item.model_dump() for item in wardrobe]

    # Get user context for AI prompts
    user_context = get_user_context(user_profile, wardrobe)

    # Build user profile dict for image generation
    user_profile_dict = {
        'username': user_profile.username,
        'height_cm': user_profile.height_cm,
        'weight_kg': user_profile.weight_kg,
        'gender': user_profile.gender,
        'typical_size_top': (user_profile.usual_sizes or {}).get('tshirts', 'M'),
        'typical_size_bottom': (user_profile.usual_sizes or {}).get('pants', 'M'),
        'shoe_size': (user_profile.usual_sizes or {}).get('shoes', ''),
        'profile_image_url': user_profile.profile_image_url,
    }

    try:
        # Run full analysis with user's API key
        result = await full_product_analysis(
            screenshot_base64=request.screenshot_base64,
            html_content=request.html_content,
            page_url=request.page_url,
            page_title=request.page_title,
            user_context=user_context,
            wardrobe_items=wardrobe_dicts,
            user_profile=user_profile_dict,
            gemini_api_key=request.gemini_api_key
        )

        # Build generated images response
        gen_images = result.get("generated_images", {})
        generated_images_response = GeneratedImages(
            front=gen_images.get("front"),
            left=gen_images.get("left"),
            right=gen_images.get("right"),
            back=gen_images.get("back")
        ) if gen_images else None

        # Build selected items with image thumbnails
        selected_items_response = []
        for item in result["selected_items"]:
            image_url = item.get("image_path")
            image_b64 = await load_image_thumbnail_from_url(image_url) if image_url else None
            selected_items_response.append(
                WardrobeItemResponse(
                    id=item["id"],
                    name=item["name"],
                    type=item["type"],
                    color=item["color"],
                    color_hex=item.get("color_hex"),
                    match_reason=item.get("match_reason"),
                    image_base64=image_b64,
                    image_url=image_url,
                )
            )

        return AnalyzeResponse(
            product=ProductInfo(**result["product"]),
            fit_score=result["fit_score"],
            selected_items=selected_items_response,
            commentary=result["commentary"],
            generated_image_base64=result.get("generated_image_base64"),
            generated_images=generated_images_response
        )

    except Exception as e:
        print(f"Analysis error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Development Server ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
