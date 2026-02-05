"""
FastAPI backend server for the Wardrobe Styling Assistant.

Endpoints:
- POST /analyze-and-style: Analyze a product page and return styling recommendations
- GET /health: Health check endpoint
"""

import os
import json
import base64
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from wardrobe import get_user_profile, get_wardrobe, get_user_context
from gemini_client import full_product_analysis


def load_image_thumbnail(file_path: str) -> Optional[str]:
    """Load an image and return as base64 string."""
    try:
        if not file_path or not os.path.exists(file_path):
            return None
        with open(file_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception:
        return None

# Helper function for debug logging
def debug_log(location, message, data, hypothesis_id="G"):
    log_file = '/Users/olek.arsentiev/Documents/gemini3_hack/.cursor/debug.log'
    try:
        with open(log_file, 'a') as f:
            import time
            f.write(json.dumps({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": hypothesis_id,
                "location": location,
                "message": message,
                "data": data,
                "timestamp": int(time.time() * 1000)
            }) + '\n')
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        print(f"Debug log error: {e}")


# Initialize FastAPI app
app = FastAPI(
    title="Wardrobe Styling Assistant API",
    description="AI-powered styling recommendations using Gemini 3",
    version="1.0.0"
)

# Configure CORS for Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for extension
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Request/Response Models ====================

class AnalyzeRequest(BaseModel):
    """Request body for product analysis."""
    user_id: str
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
    image_base64: Optional[str] = None  # Thumbnail of the actual item


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
    generated_image_base64: Optional[str] = None  # Backwards compatibility
    generated_images: Optional[GeneratedImages] = None  # Multi-angle images


# ==================== Endpoints ====================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    api_key_set = bool(os.environ.get("GEMINI_API_KEY"))
    return {
        "status": "healthy",
        "gemini_api_key_configured": api_key_set
    }


@app.post("/analyze-and-style", response_model=AnalyzeResponse)
async def analyze_and_style(request: AnalyzeRequest):
    """
    Analyze a product page and return styling recommendations.

    Flow:
    1. Extract product info from screenshot + HTML using Gemini
    2. Match with user's wardrobe items
    3. Generate styled outfit visualization
    4. Return fit score, selected items, and commentary
    """
    # #region agent log
    debug_log("server.py:88", "analyze_and_style endpoint called", {"user_id": request.user_id})
    # #endregion
    # Validate user exists
    user_profile = get_user_profile(request.user_id)
    if not user_profile:
        raise HTTPException(status_code=404, detail=f"User not found: {request.user_id}")

    # Get user's wardrobe
    wardrobe = get_wardrobe(request.user_id)
    if not wardrobe:
        raise HTTPException(status_code=404, detail=f"No wardrobe found for user: {request.user_id}")

    # Convert wardrobe items to dicts for the AI
    wardrobe_dicts = [item.model_dump() for item in wardrobe]

    # Get user context for AI prompts
    user_context = get_user_context(request.user_id)

    try:
        # #region agent log
        import json
        with open('/Users/olek.arsentiev/Documents/gemini3_hack/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"G","location":"server.py:114","message":"Starting full_product_analysis","data":{"user_id":request.user_id},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
        # Run full analysis
        result = await full_product_analysis(
            screenshot_base64=request.screenshot_base64,
            html_content=request.html_content,
            page_url=request.page_url,
            page_title=request.page_title,
            user_context=user_context,
            wardrobe_items=wardrobe_dicts,
            user_profile=user_profile.model_dump()
        )
        # #region agent log
        with open('/Users/olek.arsentiev/Documents/gemini3_hack/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"G","location":"server.py:125","message":"full_product_analysis completed","data":{"has_generated_image":bool(result.get("generated_image_base64"))},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion

        # Format response
        # #region agent log
        import json
        with open('/Users/olek.arsentiev/Documents/gemini3_hack/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"G","location":"server.py:127","message":"Formatting response","data":{"has_generated_image":bool(result.get("generated_image_base64")),"image_length":len(result.get("generated_image_base64","")) if result.get("generated_image_base64") else 0},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
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
            image_b64 = load_image_thumbnail(item.get("image_path"))
            selected_items_response.append(
                WardrobeItemResponse(
                    id=item["id"],
                    name=item["name"],
                    type=item["type"],
                    color=item["color"],
                    color_hex=item.get("color_hex"),
                    match_reason=item.get("match_reason"),
                    image_base64=image_b64
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
        # #region agent log
        import json
        import traceback
        with open('/Users/olek.arsentiev/Documents/gemini3_hack/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"F","location":"server.py:148","message":"Exception in analyze_and_style","data":{"error_type":type(e).__name__,"error_message":str(e),"traceback":traceback.format_exc()},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Development Server ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
