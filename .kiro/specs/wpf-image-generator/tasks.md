# Implementation Plan

- [x] 1. Set up WPF project structure and dependencies





  - Create new WPF project targeting .NET 8.0 in ../ImageGenDotNet directory
  - Add CommunityToolkit.Mvvm NuGet package for MVVM support
  - Add Newtonsoft.Json and Microsoft.Extensions.Http packages
  - Set up basic project structure with ViewModels and Utilities folders
  - _Requirements: 6.1, 7.1_

- [x] 2. Create basic MainWindow UI layout






  - Design MainWindow.xaml with model selector, prompt input, generate button, and image display area
  - Implement basic layout with Grid and proper sizing
  - Add status bar for user feedback
  - Set up data binding placeholders for ViewModel properties
  - _Requirements: 6.1, 6.2_

- [x] 3. Implement MainViewModel with basic MVVM structure





  - Create MainViewModel inheriting from ObservableObject
  - Add properties for SelectedModel, AvailableModels, PromptText, GeneratedImage, IsGenerating, StatusText
  - Add boolean properties for AutoGenerate and AutoGenerateAfterEnhance
  - Implement INotifyPropertyChanged through CommunityToolkit.Mvvm
  - _Requirements: 7.2, 7.4_

- [x] 4. Create ImageGenerator utility class





  - Implement ImageGenerator class with GenerateAsync method
  - Add GetAvailableModels method returning the same model list as Python version
  - Set up basic HTTP client for API calls
  - Add placeholder for FAL API integration (will implement actual API calls later)
  - _Requirements: 1.1, 1.2_

- [x] 5. Create PromptEnhancer utility class





  - Implement PromptEnhancer class with EnhanceAsync method
  - Add support for optional directions parameter
  - Set up OpenAI API client using environment variable for API key
  - Add basic error handling for API failures
  - _Requirements: 2.1, 2.2, 2.5_

- [x] 6. Create FileHelper utility class





  - Implement SaveImageAsync method to save BitmapImage to file
  - Add ShowSaveDialog method using SaveFileDialog
  - Handle basic file I/O errors with user-friendly messages
  - Support JPEG format for image saving
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 7. Implement command handlers in MainViewModel





  - Create GenerateImageCommand using RelayCommand from CommunityToolkit.Mvvm
  - Add EnhancePromptCommand and EnhancePromptWithDirectionsCommand
  - Implement SaveImageCommand with proper error handling
  - Add async command support for long-running operations
  - _Requirements: 1.3, 2.3, 5.1, 7.3_

- [x] 8. Add image generation functionality






  - Connect ImageGenerator to actual FAL API calls
  - Implement model-specific request formatting based on Python version
  - Add response parsing for different API formats
  - Handle API errors and display appropriate status messages
  - _Requirements: 1.2, 1.4, 6.6_

- [x] 9. Implement prompt enhancement with OpenAI integration





  - Connect PromptEnhancer to OpenAI API using OPENAI_API_KEY environment variable
  - Add input dialog for enhancement directions
  - Implement auto-generate after enhancement feature
  - Add proper error handling for missing API keys
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 10. Add basic image zoom and pan functionality





  - Implement ScrollViewer-based image viewing with zoom support
  - Add mouse wheel zoom functionality
  - Implement click-and-drag panning
  - Ensure proper image fitting and aspect ratio maintenance
  - _Requirements: 3.1, 3.2, 3.3, 3.5_

- [x] 11. Implement auto-generation feature





  - Add text change detection for prompt input
  - Implement debounced auto-generation to avoid excessive API calls
  - Add model-specific auto-generation rules (disable for slower models)
  - Handle concurrent generation requests with proper queuing
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 12. Add visual feedback and status indicators





  - Implement loading spinner or progress indicator during generation
  - Add status text updates for different operation states
  - Ensure UI remains responsive during async operations
  - Add visual feedback for button clicks and user interactions
  - _Requirements: 4.5, 6.3, 6.4_

- [x] 13. Handle environment variable configuration






  - Add startup checks for required API keys (OPENAI_API_KEY, FAL_KEY)
  - Display helpful error messages if API keys are missing
  - Add basic validation for API key format
  - Provide clear instructions for setting up environment variables
  - _Requirements: 6.6_

- [x] 14. Final integration and testing





  - Test all features end-to-end with real API calls
  - Verify image generation works with multiple models
  - Test prompt enhancement with and without directions
  - Verify save functionality and file dialog behavior
  - Test zoom/pan functionality and UI responsiveness
  - _Requirements: 1.1, 2.1, 3.1, 4.1, 5.1, 6.1_