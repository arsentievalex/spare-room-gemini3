# Spare Room - Technical Architecture

## System Overview

```mermaid
flowchart TB
    subgraph User["User"]
        U1[Browse Online Store]
        U2[Trigger Extension]
        U3[View Results]
    end

    subgraph WebApp["Web App - Profile Setup (AI Studio)"]
        O1[Upload Photo]
        O2[Enter Measurements & Sizes]
        O3[Set Style Preferences]
        O4[Upload Wardrobe Item Photos]
        O5["AI Analysis<br/>(Gemini 3 Flash)"]
    end

    subgraph GCS["Google Cloud Storage"]
        G1["user_info.json<br/>(profile + wardrobe metadata)"]
        G2["user_photo.jpg"]
        G3["wardrobe/item_{id}.jpg"]
    end

    subgraph Extension["Chrome Extension"]
        E0[Setup: Username + API Key]
        E1[Capture Screenshot]
        E2[Extract Page HTML]
        E3[Display Try-On Images]
        E4[Show Fit Score & Matches]
    end

    subgraph Backend["FastAPI Backend (Local)"]
        B1[/POST /analyze-and-style/]
        B2[Fetch user_info.json from GCS]
        B3[Download wardrobe images from GCS]
    end

    subgraph Pipeline["AI Styling Pipeline"]
        subgraph Step1["Step 1: Extract"]
            S1[Product Extraction]
            M1["gemini-3-flash-preview<br/>thinking: low"]
        end

        subgraph Step2["Step 2: Analyze"]
            S2[Styling Analysis]
            M2["gemini-3-flash-preview<br/>thinking: medium"]
        end

        subgraph Step3["Step 3: Generate"]
            S3[Virtual Try-On]
            M3["gemini-3-pro-image-preview<br/>+ gemini-2.5-flash-image"]
        end
    end

    subgraph Output["Results"]
        R1[Try-On Images<br/>Front + 3 Angles]
        R2[Fit Score 0-100]
        R3[Matching Wardrobe Items]
        R4[Styling Tips]
    end

    %% Onboarding: Web App writes to GCS
    O1 --> O5
    O4 --> O5
    O5 -->|"Analyze & catalog<br/>wardrobe items"| G1
    O1 --> G2
    O4 --> G3
    O2 --> G1
    O3 --> G1

    %% Extension setup
    U1 --> U2
    U2 --> E0
    E0 -->|"Validate username<br/>(fetch user_info.json)"| GCS

    %% Main shopping flow
    E0 --> E1
    E0 --> E2
    E1 --> B1
    E2 --> B1

    %% Backend fetches from GCS
    B1 --> B2
    B2 --> GCS
    B1 --> B3
    B3 --> GCS

    %% Backend to Pipeline
    B2 -.->|User profile + wardrobe metadata| S2
    B2 -.->|User photo URL| S3
    B3 -.->|Wardrobe item images| S3

    %% Pipeline Flow
    S1 --> M1
    M1 -->|"Product: name, color,<br/>brand, price, category"| S2
    S2 --> M2
    M2 -->|"Fit Score +<br/>Matching Items"| S3
    S3 --> M3

    %% Output
    M3 --> R1
    M2 --> R2
    M2 --> R3
    M2 --> R4

    %% Results to Extension
    R1 --> E3
    R2 --> E4
    R3 --> E4
    R4 --> E4
    E3 --> U3
    E4 --> U3
```

## Data Flow

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant WA as Web App (AI Studio)
    participant GCS as Google Cloud Storage
    participant Ext as Chrome Extension
    participant API as FastAPI Backend (Local)
    participant Flash as Gemini 3 Flash
    participant ProImg as Gemini 3 Pro Image
    participant Nano as Gemini 2.5 Flash Image

    Note over U,GCS: Profile Setup Phase (One-time, in Web App)
    U->>WA: Upload photo, measurements, preferences
    U->>WA: Upload wardrobe item photos
    WA->>Flash: Analyze each wardrobe item photo<br/>(extract name, type, color, style, description)
    Flash-->>WA: Structured item metadata
    WA->>GCS: Write user_info.json (profile + all wardrobe items)
    WA->>GCS: Upload user_photo.jpg
    WA->>GCS: Upload wardrobe/item_{id}.jpg for each item

    Note over U,Nano: Extension Setup (One-time)
    U->>Ext: Enter username + Gemini API key
    Ext->>GCS: Validate username (fetch user_info.json)
    GCS-->>Ext: 200 OK (username valid)
    Ext->>Ext: Cache credentials in chrome.storage.local

    Note over U,Nano: Shopping Phase (Per Product)
    U->>Ext: Click extension on product page
    Ext->>Ext: Capture screenshot + extract HTML
    Ext->>API: POST /analyze-and-style<br/>{username, gemini_api_key, screenshot, html}

    API->>GCS: Fetch user_info.json for username
    GCS-->>API: User profile + wardrobe items metadata

    rect rgb(240, 248, 255)
        Note over API,Flash: Step 1: Product Extraction
        API->>Flash: Screenshot + HTML (thinking: low)
        Flash-->>API: {name, color, brand, price, category, material}
    end

    rect rgb(255, 248, 240)
        Note over API,Flash: Step 2: Styling Analysis
        API->>Flash: Product info + User profile + Wardrobe list<br/>(thinking: medium)
        Flash-->>API: {fit_score, matching_items[], styling_tip}
    end

    rect rgb(240, 255, 240)
        Note over API,Nano: Step 3: Image Generation
        API->>GCS: Download user photo + selected wardrobe item images
        GCS-->>API: Image files
        API->>ProImg: User photo + Product screenshot + Wardrobe item images
        ProImg-->>API: Front view try-on image

        loop For each angle: left, right, back
            API->>Nano: Front image + angle instruction
            Nano-->>API: Angle view image
        end
    end

    API-->>Ext: {try_on_images, fit_score, matches[], styling_tip}
    Ext-->>U: Display results in sidebar panel
```

## LLM Architecture

### Models Used

| Model | Step | Task | Thinking Level | Input | Output |
|-------|------|------|---------------|-------|--------|
| `gemini-3-flash-preview` | Onboarding (Web App) | Wardrobe item analysis | - | Item photo | Name, type, color, hex, style, description |
| `gemini-3-flash-preview` | Step 1: Extract | Product extraction | `low` | Screenshot + HTML | Product name, color, brand, price, category, material |
| `gemini-3-flash-preview` | Step 2: Analyze | Styling analysis | `medium` | Product info + user profile + wardrobe list | Fit score, best matches (1 per category), styling tip |
| `gemini-3-pro-image-preview` | Step 3a: Generate | Main virtual try-on | - | User photo + product screenshot + up to 3 wardrobe item images (max 5 images) | Photorealistic front-view try-on image |
| `gemini-2.5-flash-image` | Step 3b: Angles | Angle view generation | - | Front try-on image + angle instruction | Same outfit from left/right/back (3 calls) |

### Model Selection Strategy

```mermaid
graph LR
    subgraph Task["Task Type"]
        T0[Wardrobe Cataloging]
        T1[Text Extraction]
        T2[Reasoning & Analysis]
        T3[Primary Image Gen]
        T4[Angle Image Gen]
    end

    subgraph Model["Model"]
        M0["gemini-3-flash-preview"]
        M1["gemini-3-flash-preview<br/>thinking: low"]
        M2["gemini-3-flash-preview<br/>thinking: medium"]
        M3["gemini-3-pro-image-preview"]
        M4["gemini-2.5-flash-image"]
    end

    subgraph Why["Optimization Priority"]
        P0["Speed + structured output"]
        P1["Speed — simple extraction"]
        P2["Quality — nuanced styling reasoning"]
        P3["Quality — photorealistic generation"]
        P4["Cost — repeated angle generation"]
    end

    T0 --> M0 --> P0
    T1 --> M1 --> P1
    T2 --> M2 --> P2
    T3 --> M3 --> P3
    T4 --> M4 --> P4
```

### Image Pipeline Detail

```mermaid
flowchart LR
    subgraph Inputs["Image Inputs (max 5)"]
        I1["IMAGE 1<br/>User photo<br/>(from GCS)"]
        I2["IMAGE 2<br/>Product screenshot<br/>(from page capture)"]
        I3["IMAGES 3-5<br/>Wardrobe items<br/>(from GCS)"]
    end

    subgraph Main["Main Generation"]
        MG["gemini-3-pro-image-preview<br/>Prompt: Full-body studio try-on<br/>preserving user identity"]
    end

    subgraph Angles["Angle Generation (x3)"]
        A1["gemini-2.5-flash-image<br/>Left view"]
        A2["gemini-2.5-flash-image<br/>Right view"]
        A3["gemini-2.5-flash-image<br/>Back view"]
    end

    subgraph Result["Output"]
        R["4 images:<br/>Front + Left + Right + Back"]
    end

    I1 --> MG
    I2 --> MG
    I3 --> MG
    MG -->|Front image| A1
    MG -->|Front image| A2
    MG -->|Front image| A3
    MG --> Result
    A1 --> Result
    A2 --> Result
    A3 --> Result
```

## Component Architecture

```mermaid
graph TB
    subgraph Client["Client Layer"]
        WA["Web App (AI Studio)<br/>Profile setup + wardrobe cataloging"]
        CE["Chrome Extension<br/>Product analysis + try-on"]
    end

    subgraph Storage["Storage Layer"]
        GCS["Google Cloud Storage<br/>(Public Bucket)"]
        CS["chrome.storage.local<br/>(Username + API Key)"]
    end

    subgraph Server["Server Layer (Local)"]
        FA["FastAPI Backend"]
        subgraph Services["Services"]
            PS["Product Service<br/>(extract_product_info)"]
            SS["Styling Service<br/>(analyze_styling)"]
            IS["Image Service<br/>(generate_tryon_image<br/>generate_angle_image)"]
        end
    end

    subgraph AI["AI Layer"]
        subgraph Gemini["Google Gemini API"]
            G3F["gemini-3-flash-preview"]
            G3P["gemini-3-pro-image-preview"]
            G25["gemini-2.5-flash-image"]
        end
    end

    WA -->|"Write user data<br/>+ wardrobe images"| GCS
    WA --> G3F

    CE -->|"Cache credentials"| CS
    CE -->|"Validate username"| GCS
    CE -->|"POST /analyze-and-style"| FA

    FA -->|"Fetch user_info.json<br/>+ wardrobe images"| GCS

    FA --> PS
    FA --> SS
    FA --> IS

    PS --> G3F
    SS --> G3F
    IS --> G3P
    IS --> G25
```

## Key Design Decisions

- **API key stays local**: The Gemini API key is stored in chrome.storage.local and passed per-request to the local backend. It never leaves the user's machine.
- **GCS as data layer**: All user data lives in a public GCS bucket, keyed by username. No database needed.
- **Per-request Gemini client**: The backend creates a new Gemini client for each request using the user's API key, rather than a singleton.
- **Web App handles onboarding AI**: Wardrobe item analysis (photo → structured metadata) happens once during profile setup in the AI Studio web app, not in the extension flow.
- **Extension flow is read-only**: The extension only reads from GCS (never writes). All profile/wardrobe mutations happen in the web app.
