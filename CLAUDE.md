# Gemini 3 Hackathon Project

Hackathon project for building applications with Google's Gemini 3 API.

## Project Structure

- `gemini_docs/` - Reference documentation and example notebooks
  - `gemini_Get_started.ipynb` - Comprehensive SDK guide
  - `Get_Started_Nano_Banana.ipynb` - Native image generation guide
  - `gemini_api_reference.txt` - REST API reference

## Gemini 3 Models

| Model | Use Case |
|-------|----------|
| `gemini-3-pro-preview` | Most capable, deep reasoning (thinking levels: low/high) |
| `gemini-3-flash-preview` | Fast, cost-effective (thinking levels: minimal/low/medium/high) |
| `gemini-3-pro-image-preview` | Image generation with thinking & search grounding, up to 4K |
| `gemini-2.5-flash-image` | Fast image generation (Nano-Banana) |

## SDK Setup

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=GEMINI_API_KEY)

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Your prompt here",
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level="high"),
        temperature=1.0  # Recommended for Gemini 3
    )
)
```

## Key Gemini 3 Features

### Thinking Levels
Control reasoning depth via `thinking_config`:
- `minimal` (Flash only) - Fastest, effectively no thinking
- `low` - Low latency, simple tasks
- `medium` (Flash only) - Balanced
- `high` (default for Pro) - Maximum reasoning

### Thought Signatures
Required for multi-turn conversations to maintain reasoning context. The SDK handles this automatically.

### Media Resolution
Control image/PDF tokenization per file:
- `MEDIA_RESOLUTION_HIGH` - 1120 tokens (images default)
- `MEDIA_RESOLUTION_MEDIUM` - 560 tokens (PDFs default)
- `MEDIA_RESOLUTION_LOW` - 280 tokens

## Common Operations

### Multimodal Input
```python
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[image, "Describe this image"]
)
```

### Structured Output
```python
from pydantic import BaseModel

class MySchema(BaseModel):
    field: str

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="prompt",
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=MySchema
    )
)
```

### Google Search Grounding
```python
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Current weather in Tokyo?",
    config={"tools": [{"google_search": {}}]}
)
```

### Image Generation (Nano-Banana)
```python
response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents="Create an image of...",
    config=types.GenerateContentConfig(
        response_modalities=['Text', 'Image']
    )
)
```

## Requirements

```
google-genai>=1.51.0
```
