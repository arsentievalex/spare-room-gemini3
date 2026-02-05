"""
Demo user's wardrobe data for the Styling Assistant POC.

This module contains hardcoded wardrobe items and user profile for demonstration.
In a production system, this would be fetched from a database.

Images are loaded from the temp_images folder.
"""

import os
from typing import Optional
from pydantic import BaseModel

# Base path for images (relative to this file's directory)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_IMAGES_DIR = os.path.join(os.path.dirname(BASE_DIR), 'temp_images')


class WardrobeItem(BaseModel):
    """A single item in the user's wardrobe."""
    id: str
    name: str
    type: str  # e.g., "pants", "shirt", "shoes", "accessory"
    color: str
    color_hex: str  # Hex color code for accurate display
    style: str  # e.g., "casual", "formal", "streetwear"
    description: str
    image_path: Optional[str] = None  # Local file path for the item image


class UserProfile(BaseModel):
    """User profile with body measurements and style preferences."""
    user_id: str
    name: str
    height_cm: int
    typical_size_top: str
    typical_size_bottom: str
    shoe_size: str
    style_preferences: list[str]
    photo_path: Optional[str] = None  # Local file path for user reference photo


# Demo user profile
DEMO_USER = UserProfile(
    user_id="demo_user",
    name="Alex Demo",
    height_cm=178,
    typical_size_top="M",
    typical_size_bottom="32",
    shoe_size="10 US",
    style_preferences=["smart casual", "minimalist"],
    photo_path=os.path.join(TEMP_IMAGES_DIR, "user_photo.jpg")
)

# Demo wardrobe items
DEMO_WARDROBE: list[WardrobeItem] = [
    # Hoodies & Sweaters
    WardrobeItem(
        id="top_01",
        name="White Hoodie",
        type="hoodie",
        color="white",
        color_hex="#F5F5F5",
        style="casual",
        description="White oversized hoodie with a logo.",
        image_path=os.path.join(TEMP_IMAGES_DIR, "hoodie white.png")
    ),
    WardrobeItem(
        id="top_02",
        name="Green Hoodie",
        type="hoodie",
        color="green",
        color_hex="#2D5A3D",
        style="casual",
        description="Forest green hoodie, relaxed fit.",
        image_path=os.path.join(TEMP_IMAGES_DIR, "hoodie green.png")
    ),
    WardrobeItem(
        id="top_03",
        name="Red Hoodie",
        type="hoodie",
        color="red",
        color_hex="#B42B2B",
        style="casual",
        description="Bold red hoodie, statement piece.",
        image_path=os.path.join(TEMP_IMAGES_DIR, "hoodie red.png")
    ),
    WardrobeItem(
        id="top_04",
        name="Stranger Things Hoodie",
        type="hoodie",
        color="black",
        color_hex="#1A1A1A",
        style="streetwear",
        description="Black Stranger Things graphic hoodie.",
        image_path=os.path.join(TEMP_IMAGES_DIR, "hoodie stranger things.png")
    ),
    WardrobeItem(
        id="top_05",
        name="Black Sweater",
        type="sweater",
        color="black",
        color_hex="#1C1C1C",
        style="smart casual",
        description="Classic black knit sweater.",
        image_path=os.path.join(TEMP_IMAGES_DIR, "sweater black.png")
    ),

    # Pants & Jeans
    WardrobeItem(
        id="bottom_01",
        name="Blue Jeans",
        type="jeans",
        color="blue",
        color_hex="#4A6FA5",
        style="casual",
        description="Classic blue jeans with a straight leg.",
        image_path=os.path.join(TEMP_IMAGES_DIR, "jeans blue.png")
    ),
    WardrobeItem(
        id="bottom_02",
        name="Gray Jeans",
        type="jeans",
        color="gray",
        color_hex="#6B6B6B",
        style="casual",
        description="Gray denim jeans, versatile neutral.",
        image_path=os.path.join(TEMP_IMAGES_DIR, "jeans gray.png")
    ),
    # WardrobeItem(
    #     id="bottom_03",
    #     name="Beige Chinos",
    #     type="chinos",
    #     color="beige",
    #     color_hex="#C9B896",
    #     style="smart casual",
    #     description="Versatile beige chino pants.",
    #     image_path=os.path.join(TEMP_IMAGES_DIR, "pants biege.png")
    # ),
    # WardrobeItem(
    #     id="bottom_04",
    #     name="Light Pants",
    #     type="trousers",
    #     color="cream",
    #     color_hex="#E8E4D9",
    #     style="smart casual",
    #     description="Light cream trousers, clean and minimal.",
    #     image_path=os.path.join(TEMP_IMAGES_DIR, "light pants.png")
    # ),
    WardrobeItem(
        id="bottom_05",
        name="Sport Pants",
        type="joggers",
        color="gray",
        color_hex="#4A4A4A",
        style="athleisure",
        description="Gray athletic jogger pants.",
        image_path=os.path.join(TEMP_IMAGES_DIR, "pants sport.png")
    ),

    # Shoes
    WardrobeItem(
        id="shoes_01",
        name="Black Sneakers",
        type="sneakers",
        color="black",
        color_hex="#1A1A1A",
        style="casual",
        description="Classic black sneakers.",
        image_path=os.path.join(TEMP_IMAGES_DIR, "black sneakers.png")
    ),
    WardrobeItem(
        id="shoes_02",
        name="White Sneakers",
        type="sneakers",
        color="white",
        color_hex="#FFFFFF",
        style="casual",
        description="Clean white sneakers.",
        image_path=os.path.join(TEMP_IMAGES_DIR, "white sneakers.png")
    ),
    # WardrobeItem(
    #     id="shoes_03",
    #     name="Gray & White Sneakers",
    #     type="sneakers",
    #     color="gray",
    #     color_hex="#9E9E9E",
    #     style="casual",
    #     description="Two-tone gray and white sneakers.",
    #     image_path=os.path.join(TEMP_IMAGES_DIR, "gray white sneakers.png")
    # ),

    # Accessories
    # WardrobeItem(
    #     id="acc_01",
    #     name="Dark Cap",
    #     type="cap",
    #     color="navy",
    #     color_hex="#1E2A3A",
    #     style="casual",
    #     description="Dark navy baseball cap.",
    #     image_path=os.path.join(TEMP_IMAGES_DIR, "dark cap.png")
    # ),
    # WardrobeItem(
    #     id="acc_02",
    #     name="Light Cap",
    #     type="cap",
    #     color="beige",
    #     color_hex="#D4C4A8",
    #     style="casual",
    #     description="Light beige baseball cap.",
    #     image_path=os.path.join(TEMP_IMAGES_DIR, "light cap.png")
    # ),
]


def get_user_profile(user_id: str) -> Optional[UserProfile]:
    """Get user profile by ID."""
    if user_id == "demo_user":
        return DEMO_USER
    return None


def get_wardrobe(user_id: str) -> list[WardrobeItem]:
    """Get wardrobe items for a user."""
    if user_id == "demo_user":
        return DEMO_WARDROBE
    return []


def get_wardrobe_summary(user_id: str) -> str:
    """Get a text summary of the user's wardrobe for AI prompts."""
    wardrobe = get_wardrobe(user_id)
    if not wardrobe:
        return "No wardrobe items found."

    summary_lines = ["User's current wardrobe:"]
    for item in wardrobe:
        summary_lines.append(
            f"- {item.name} ({item.type}): {item.color}, {item.style} style. {item.description}"
        )

    return "\n".join(summary_lines)


def get_user_context(user_id: str) -> str:
    """Get full user context including profile and wardrobe for AI prompts."""
    profile = get_user_profile(user_id)
    if not profile:
        return "Unknown user."

    context = f"""User Profile:
- Name: {profile.name}
- Height: {profile.height_cm}cm
- Typical top size: {profile.typical_size_top}
- Typical bottom size: {profile.typical_size_bottom}
- Shoe size: {profile.shoe_size}
- Style preferences: {', '.join(profile.style_preferences)}

{get_wardrobe_summary(user_id)}"""

    return context
