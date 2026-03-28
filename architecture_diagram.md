# AI Image Workbench Architecture

## Component Overview

```mermaid
graph TB
    subgraph "User Interface Layer"
        UI[Main Application<br/>main.py]
        MSF[Model Selection Frame<br/>ModelSelectionFrame]
        PIF[Prompt Input Frame<br/>PromptInputFrame]
        IDM[Image Display Manager<br/>ImageDisplayManager]
        CP[Control Panel<br/>UI Components]
    end
    
    subgraph "Business Logic Layer"
        GM[Generation Manager<br/>GenerationManager]
        SM[Settings Manager<br/>SettingsManager]
        TM[Threading Manager<br/>UpdateThreadManager]
        SA[Spinner Animator<br/>SpinnerAnimator]
        CM[Clipboard Manager<br/>ClipboardManager]
    end
    
    subgraph "API Integration Layer"
        IGA[Image Gen API<br/>image_gen_api.py]
        AIA[AI API<br/>ai_api.py]
    end
    
    subgraph "External Services"
        FAL[Fal.ai API<br/>Image Generation]
        OPENAI[OpenRouter<br/>Grok 4.1 Fast<br/>Prompt Enhancement]
    end
    
    subgraph "Data & Utilities"
        CONF[Configuration<br/>config.py]
        IH[Image Handler<br/>image_handler.py]
        UTIL[Utilities<br/>threading_utils.py]
    end
    
    %% User Flow
    UI --> MSF
    UI --> PIF
    UI --> CP
    UI --> IDM
    
    %% Business Logic
    MSF --> GM
    PIF --> GM
    CP --> GM
    
    GM --> TM
    TM --> IGA
    TM --> AIA
    
    IGA --> FAL
    AIA --> OPENAI
    
    %% Settings & State
    UI --> SM
    SM --> CONF
    
    %% Image Processing
    IGA --> IH
    IH --> IDM
    
    %% Clipboard
    CP --> CM
    IDM --> CM
    
    %% UI Updates
    TM --> UI
    SA --> UI
    
    %% Configuration
    CONF --> MSF
    CONF --> PIF
    CONF --> IGA
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant UI as UI Layer
    participant GM as Generation Manager
    participant TM as Threading Manager
    participant API as Image Gen API
    participant AI as AI API
    participant FAL as Fal.ai
    participant OPENAI as OpenRouter
    participant IH as Image Handler
    participant DISP as Display
    
    User->>UI: Enter Prompt + Select Model
    UI->>GM: Create Generation Request
    GM->>TM: Queue Request
    TM->>API: Call generate_image()
    
    alt Prompt Enhancement Needed
        API->>AI: enhance_prompt()
        AI->>OPENAI: API Call
        OPENAI-->>AI: Enhanced Prompt
        AI-->>API: Return Enhanced Prompt
    end
    
    API->>FAL: API Call with Model & Prompt
    FAL-->>API: Image URL/Data
    API->>IH: Process Image
    IH-->>API: PIL Image
    
    API-->>TM: Return Image
    TM-->>GM: Update Request Status
    GM-->>UI: Signal Completion
    UI->>DISP: Show Image
    DISP-->>User: Display Result
    
    User->>UI: Click Copy/Zoom/Pan
    UI->>CM: Copy to Clipboard
    UI->>IH: Zoom/Pan Operations
```

## Module Dependencies

```mermaid
graph TD
    main --> config
    main --> ui_components
    main --> image_gen_api
    main --> ai_api
    main --> image_handler
    main --> clipboard_manager
    main --> threading_utils
    main --> generation_manager
    main --> settings_manager
    
    ui_components --> config
    ui_components --> image_handler
    
    image_gen_api --> config
    
    generation_manager --> image_gen_api
    
    image_handler --> config
    
    threading_utils --> generation_manager
    
    settings_manager --> config
```

## Key Features Architecture

### 1. Model Memory System
```mermaid
graph LR
    subgraph "Model Memory Cache"
        MM[Model Memory<br/>In-Memory Cache]
        MC[Model Cache<br/>per Model]
        TI[Tick Indicator<br/>✓]
        HG[Hourglass<br/>Generating]
        VI[Viewed Indicator<br/>👁]
    end
    
    GM[Generation Manager] --> MM
    MM --> MC
    MC --> TI
    MC --> HG
    MC --> VI
    
    MSF[Model Selection] --> TI
    MSF --> HG
    MSF --> VI
```

### 2. Threading & Background Processing
```mermaid
graph TB
    subgraph "Main Thread (UI)"
        UI[UI Events]
        QM[Queue Manager]
        UP[Update Processor]
    end
    
    subgraph "Background Threads"
        GT[Generation Thread<br/>ThreadPoolExecutor]
        UT[Update Thread<br/>Queue Processor]
        SA[Spinner Thread<br/>Animator]
    end
    
    UI --> QM
    QM --> GT
    GT --> QM
    QM --> UP
    UP --> UI
    
    UI --> SA
    SA --> UI
    
    UT --> UI
```

### 3. Settings Persistence
```mermaid
graph LR
    subgraph "Runtime"
        APP[Application]
        WS[Window Settings]
    end
    
    subgraph "Storage"
        FILE[Settings File<br/>~/.image_generator/<br/>window_state.json]
    end
    
    APP --> WS
    WS -->|Save| FILE
    FILE -->|Load| WS
    WS -->|Apply| APP
```

## Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **main.py** | Main application coordinator, event handling |
| **config.py** | Constants, model definitions, UI settings |
| **ui_components.py** | Specialized UI widgets (model selection, prompt input) |
| **image_gen_api.py** | Fal.ai API integration, response parsing |
| **ai_api.py** | OpenRouter API for prompt enhancement |
| **image_handler.py** | Image processing, zoom/pan, display management |
| **clipboard_manager.py** | Cross-platform clipboard operations |
| **threading_utils.py** | Background thread management, queue processing |
| **generation_manager.py** | Request queueing, status tracking, execution |
| **settings_manager.py** | Window state persistence |

## External Dependencies

- **Fal.ai API**: Image generation service
- **OpenRouter API**: Grok 4.1 Fast for prompt enhancement
- **Pillow (PIL)**: Image processing
- **Tkinter**: GUI framework
- **Requests**: HTTP client for API calls
