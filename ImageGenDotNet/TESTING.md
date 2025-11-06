# Integration Testing Guide

This document describes the comprehensive integration testing implemented for the WPF Image Generator application.

## Overview

The integration tests verify all features end-to-end with real API calls, ensuring the application works correctly in a production-like environment.

## Test Coverage

### Test 1: Environment Validation
- **Requirements**: 6.6
- **Purpose**: Validates API key configuration and environment setup
- **Tests**:
  - Checks for FAL_KEY environment variable
  - Checks for OPENAI_API_KEY environment variable
  - Validates environment status reporting
  - Verifies setup instructions are provided

### Test 2: Model Availability
- **Requirements**: 1.1
- **Purpose**: Ensures all AI models are available and selectable
- **Tests**:
  - Retrieves list of available models
  - Verifies model count is greater than zero
  - Tests model selection functionality
  - Lists all available models for verification

### Test 3: Image Generation with Multiple Models
- **Requirements**: 1.1, 1.2, 1.3, 1.4
- **Purpose**: Tests image generation with different AI models
- **Tests**:
  - Tests generation with fast models (flux/schnell)
  - Tests generation with pro models (flux-pro/v1.1)
  - Tests generation with specialized models (ideogram/v2)
  - Verifies generated images are valid
  - Saves test images for manual verification
  - Tests error handling for failed generations

### Test 4: Prompt Enhancement (Basic)
- **Requirements**: 2.1, 2.2
- **Purpose**: Tests prompt enhancement without directions
- **Tests**:
  - Enhances a simple prompt using OpenAI
  - Verifies enhanced prompt is longer and different
  - Tests command availability based on API key presence
  - Handles missing API key gracefully

### Test 5: Prompt Enhancement with Directions
- **Requirements**: 2.1, 2.3
- **Purpose**: Tests prompt enhancement with user directions
- **Tests**:
  - Verifies command availability
  - Tests that the feature requires user input dialog
  - Handles missing API key gracefully
  - Note: Full automation limited due to user input requirement

### Test 6: Save Functionality
- **Requirements**: 5.1, 5.2, 5.3, 5.4
- **Purpose**: Tests image saving and file dialog behavior
- **Tests**:
  - Tests save command availability
  - Performs programmatic save operation
  - Verifies saved file exists and has correct size
  - Tests save without image (should be disabled)
  - Tests different file formats (JPEG, PNG)

### Test 7: Auto-Generation Feature
- **Requirements**: 4.1, 4.2, 4.3, 4.4
- **Purpose**: Tests automatic image generation functionality
- **Tests**:
  - Tests auto-generation toggle
  - Verifies prompt changes trigger auto-generation
  - Tests model-specific auto-generation rules
  - Verifies slow models disable auto-generation
  - Tests auto-generate after enhancement feature

### Test 8: UI Responsiveness
- **Requirements**: 6.3, 6.4
- **Purpose**: Ensures UI remains responsive during operations
- **Tests**:
  - Monitors status text updates during operations
  - Verifies command availability changes during generation
  - Tests loading indicators and progress feedback
  - Ensures UI doesn't freeze during API calls

### Test 9: Error Handling
- **Requirements**: 1.4, 2.5, 5.4, 6.6
- **Purpose**: Tests error handling and user feedback
- **Tests**:
  - Tests empty prompt validation
  - Tests invalid model handling
  - Tests save without image
  - Tests environment status error handling
  - Verifies user-friendly error messages

## Running the Tests

### Method 1: Using the Application Menu
1. Start the application: `dotnet run --configuration Release`
2. Go to **Tools > Run Integration Tests**
3. Click **Yes** to confirm
4. Wait for tests to complete (may take several minutes)
5. Review results in the popup dialog

### Method 2: Using Keyboard Shortcut
1. Start the application
2. Press **Ctrl+T**
3. Follow the same process as Method 1

### Method 3: Using PowerShell Script
1. Run `./run_tests.ps1` from the ImageGenDotNet directory
2. The script will build and start the application
3. Use Method 1 or 2 to run the tests

## Prerequisites

### Required Environment Variables
- **FAL_KEY**: Your FAL API key for image generation
- **OPENAI_API_KEY**: Your OpenAI API key for prompt enhancement

### Setting Environment Variables (Windows)
```powershell
# PowerShell
$env:FAL_KEY = "your-fal-api-key-here"
$env:OPENAI_API_KEY = "your-openai-api-key-here"

# Or permanently via System Properties
# 1. Right-click "This PC" > Properties
# 2. Advanced system settings > Environment Variables
# 3. Add new user variables for FAL_KEY and OPENAI_API_KEY
```

### Setting Environment Variables (Command Prompt)
```cmd
set FAL_KEY=your-fal-api-key-here
set OPENAI_API_KEY=your-openai-api-key-here
```

## Test Output

### Test Results File
- Location: `Desktop/ImageGenTests/integration_test_results_[timestamp].txt`
- Contains: Detailed log of all test operations and results
- Format: Timestamped entries with test status

### Generated Test Images
- Location: `Desktop/ImageGenTests/`
- Files: Various test images generated during testing
- Purpose: Manual verification of image generation quality

### Test Summary
The tests provide a comprehensive PASS/FAIL result for each test category and an overall result.

## Interpreting Results

### PASSED Tests
- ✅ All functionality working correctly
- API keys configured properly
- All features operational

### FAILED Tests
- ❌ Check test results file for specific errors
- Common issues:
  - Missing API keys
  - Network connectivity problems
  - API rate limiting
  - Invalid API responses

### SKIPPED Tests
- ⚠️ Tests skipped due to missing prerequisites
- Usually due to missing API keys
- Application will still function with limited features

## Troubleshooting

### Common Issues

1. **"FAL_KEY environment variable is not set"**
   - Set the FAL_KEY environment variable
   - Restart the application after setting

2. **"OPENAI_API_KEY environment variable is not set"**
   - Set the OPENAI_API_KEY environment variable
   - Prompt enhancement features will be disabled without this

3. **Network/API Errors**
   - Check internet connectivity
   - Verify API keys are valid and have sufficient credits
   - Check for API service outages

4. **File Permission Errors**
   - Ensure write permissions to Desktop folder
   - Check antivirus software isn't blocking file operations

### Getting Help

1. Check the test results file for detailed error messages
2. Use the **Tools > Environment Status** menu to check configuration
3. Verify API keys are correctly set and valid
4. Check the application logs for additional details

## Manual Testing Checklist

In addition to automated tests, perform these manual verifications:

### Image Viewing and Zoom/Pan (Requirements: 3.1, 3.2, 3.3, 3.5)
- [ ] Generated image displays correctly
- [ ] Mouse wheel zooms in/out smoothly
- [ ] Click and drag pans the image
- [ ] Double-click resets zoom
- [ ] Image maintains aspect ratio
- [ ] Zoom centers on cursor position

### User Interface Responsiveness (Requirements: 6.1, 6.2, 6.3, 6.4)
- [ ] Window resizes properly
- [ ] Controls remain accessible during operations
- [ ] Status updates appear in real-time
- [ ] Loading indicators animate smoothly
- [ ] Buttons provide visual feedback on hover/click

### File Dialog Behavior (Requirements: 5.1, 5.2)
- [ ] Save dialog opens with appropriate filters
- [ ] Default filename includes timestamp
- [ ] File saves to selected location
- [ ] Confirmation message appears after save

This comprehensive testing approach ensures all requirements are verified and the application functions correctly in real-world scenarios.