# Design Document

## Overview

The WPF C# Image Generator application will be built using modern WPF practices with MVVM architecture, async/await patterns, and proper separation of concerns. The application will replicate the functionality of the existing Python tkinter application while providing a native Windows experience.

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Presentation  │    │    Business     │    │   Utilities     │
│     Layer       │    │     Logic       │    │                 │
│                 │    │                 │    │                 │
│ - MainWindow    │◄──►│ - ViewModels    │◄──►│ - API Classes   │
│ - UserControls  │    │ - Commands      │    │ - File Helper   │
│ - Converters    │    │ - Models        │    │ - Settings      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Project Structure

```
ImageGenDotNet/
├── ImageGenDotNet.csproj
├── App.xaml
├── App.xaml.cs
├── MainWindow.xaml
├── MainWindow.xaml.cs
├── ViewModels/
│   └── MainViewModel.cs
└── Utilities/
    ├── ImageGenerator.cs
    ├── PromptEnhancer.cs
    └── FileHelper.cs
```

## Components and Interfaces

### 1. MainViewModel

The primary ViewModel that orchestrates the application logic:

**Properties:**
- `SelectedModel`: Currently selected AI model (string)
- `AvailableModels`: Collection of available AI models (List<string>)
- `PromptText`: Current prompt text
- `GeneratedImage`: Currently displayed image (BitmapImage)
- `IsGenerating`: Boolean indicating if generation is in progress
- `StatusText`: Status message for user feedback
- `AutoGenerate`: Boolean for auto-generation toggle
- `AutoGenerateAfterEnhance`: Boolean for post-enhancement auto-generation

**Commands:**
- `GenerateImageCommand`: Manually trigger image generation
- `EnhancePromptCommand`: Enhance the current prompt
- `EnhancePromptWithDirectionsCommand`: Enhance with user-provided directions
- `SaveImageCommand`: Save the current image to disk

### 2. ImageGenerator

Simple class for image generation API calls:

```csharp
public class ImageGenerator
{
    public async Task<BitmapImage> GenerateAsync(string model, string prompt);
    public List<string> GetAvailableModels();
}
```

### 3. PromptEnhancer

Simple class for prompt enhancement:

```csharp
public class PromptEnhancer
{
    public async Task<string> EnhanceAsync(string prompt, string directions = null);
}
```

### 4. FileHelper

Simple class for file operations:

```csharp
public class FileHelper
{
    public async Task<bool> SaveImageAsync(BitmapImage image, string filePath);
    public string ShowSaveDialog();
}
```

## Data Models

Simple approach - use basic types directly in ViewModel:
- `BitmapImage` for images
- `string` for prompts and models
- `bool` for flags
- `List<string>` for model collections

## Error Handling

### Exception Handling Strategy

1. **API Errors**: Catch HTTP exceptions and API-specific errors, display user-friendly messages
2. **Network Errors**: Handle timeout and connectivity issues with retry suggestions
3. **File I/O Errors**: Manage file access permissions and disk space issues
4. **Validation Errors**: Validate user input and provide immediate feedback

### Error Display

- Status bar for non-critical errors and information
- Message boxes for critical errors requiring user attention
- Inline validation for form inputs
- Progress indicators with cancellation options

## Testing Strategy

Simple manual testing - this is a hobby project, no need for formal unit tests.

## Performance Considerations

### Image Handling

- Use `BitmapImage` with appropriate caching settings
- Implement image disposal to prevent memory leaks
- Consider image compression for large generated images
- Lazy loading for image thumbnails if implementing history

### Async Operations

- All API calls use async/await patterns
- Proper cancellation token usage for long-running operations
- UI thread marshaling for property updates
- Background thread usage for image processing

### Memory Management

- Proper disposal of HTTP clients and image resources
- Weak event patterns where appropriate
- Monitoring for memory leaks in long-running sessions

## Security Considerations

### API Key Management

- Read API keys from environment variables (consistent with Python version)
- Never hardcode API keys in source code
- Check for required environment variables (`OPENAI_API_KEY`, `FAL_KEY`) on startup
- Provide clear error messages and setup instructions if keys are missing

### Input Validation

- Sanitize user prompts before sending to APIs
- Validate file paths for save operations
- Implement reasonable limits on prompt length and generation frequency

### Network Security

- Use HTTPS for all API communications
- Implement proper certificate validation
- Handle network timeouts gracefully

## Dependencies

### NuGet Packages

- **CommunityToolkit.Mvvm**: Modern MVVM framework with ObservableObject, RelayCommand, etc.
- **Newtonsoft.Json**: JSON serialization for API communication
- **Microsoft.Extensions.Http**: HTTP client factory and management

### Target Framework

- **.NET 8.0** (latest LTS) for modern C# features and performance
- **Windows-specific**: WPF is fully supported in modern .NET (not just .NET Framework)

## Deployment Considerations

### Build Configuration

- Release builds with optimizations enabled
- Proper assembly versioning
- Code signing for distribution (if required)

### Installation

- Self-contained deployment to avoid .NET runtime dependencies
- Single-file publishing for easy distribution
- Desktop shortcut creation during installation

### Configuration

**Application Settings (appsettings.json):**
- Default image generation models list
- API endpoints and timeout configurations
- Default image save formats and quality settings
- Application-wide constants (max prompt length, etc.)

**User Settings:**
- Keep it simple - no persistence between sessions (like Python version)
- Use default values on startup

**API Key Management:**
- API keys are read from environment variables (matching Python version approach):
  - `OPENAI_API_KEY` for prompt enhancement
  - `FAL_KEY` for image generation (FAL client handles this automatically)
- Application will check for required environment variables on startup
- Provide clear error messages if API keys are missing

