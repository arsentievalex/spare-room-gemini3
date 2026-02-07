"""
User wardrobe data fetched from Google Cloud Storage.

Each user has a folder at:
  https://storage.googleapis.com/gemini3-hackathon-demo-wardrobe/{username}/

Containing:
  - user_info.json (profile + wardrobe items)
  - user_photo.jpg
  - wardrobe/item_{id}.jpg
"""

import httpx
from typing import Optional
from pydantic import BaseModel


GCS_BASE_URL = 'https://storage.googleapis.com/gemini3-hackathon-demo-wardrobe'


class WardrobeItem(BaseModel):
    """A single item in the user's wardrobe."""
    id: str
    name: str
    type: str
    color: str
    color_hex: str
    style: str
    description: str
    image_path: Optional[str] = None  # URL to the item image on GCS


class UserProfile(BaseModel):
    """User profile with body measurements and style preferences."""
    username: str
    gender: Optional[str] = None
    height_cm: int = 175
    weight_kg: Optional[int] = None
    usual_sizes: Optional[dict] = None
    style_preferences: Optional[dict] = None
    profile_image_url: Optional[str] = None


async def fetch_user_info(username: str) -> Optional[dict]:
    """Fetch user_info.json from GCS for the given username."""
    url = f"{GCS_BASE_URL}/{username}/user_info.json"
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                return response.json()
            print(f"Failed to fetch user info: {response.status_code}")
            return None
        except Exception as e:
            print(f"Error fetching user info: {e}")
            return None


def parse_user_profile(user_info: dict) -> UserProfile:
    """Parse user_info.json into a UserProfile."""
    measurements = user_info.get('measurements', {})
    return UserProfile(
        username=user_info['username'],
        gender=user_info.get('gender', ''),
        height_cm=measurements.get('height_cm', 175),
        weight_kg=measurements.get('weight_kg'),
        usual_sizes=user_info.get('usual_sizes'),
        style_preferences=user_info.get('style_preferences'),
        profile_image_url=user_info.get('profile_image_url'),
    )


def parse_wardrobe_items(user_info: dict) -> list[WardrobeItem]:
    """Parse wardrobe_items from user_info.json into WardrobeItem list."""
    items = []
    for item_data in user_info.get('wardrobe_items', []):
        items.append(WardrobeItem(
            id=item_data['id'],
            name=item_data['name'],
            type=item_data['type'],
            color=item_data['color'],
            color_hex=item_data.get('color_hex', '#9ca3af'),
            style=item_data.get('style', 'casual'),
            description=item_data.get('description', ''),
            image_path=item_data.get('image_path'),
        ))
    return items


def get_user_context(profile: UserProfile, wardrobe: list[WardrobeItem]) -> str:
    """Build user context string for AI prompts."""
    sizes = profile.usual_sizes or {}
    style_prefs = profile.style_preferences or {}
    raw_style = style_prefs.get('raw_text', '')
    constraints = style_prefs.get('parsed_constraints', [])

    context = f"""User Profile:
- Username: {profile.username}
- Gender: {profile.gender or 'Not specified'}
- Height: {profile.height_cm}cm"""

    if profile.weight_kg:
        context += f"\n- Weight: {profile.weight_kg}kg"

    if sizes:
        size_parts = []
        for key, val in sizes.items():
            size_parts.append(f"{key}: {val}")
        context += f"\n- Usual sizes: {', '.join(size_parts)}"

    if raw_style:
        context += f"\n- Style preferences: {raw_style}"

    if constraints:
        context += f"\n- Style constraints: {', '.join(constraints)}"

    # Wardrobe summary
    context += "\n\nUser's current wardrobe:"
    for item in wardrobe:
        context += f"\n- {item.name} ({item.type}): {item.color}, {item.style} style. {item.description}"

    return context
