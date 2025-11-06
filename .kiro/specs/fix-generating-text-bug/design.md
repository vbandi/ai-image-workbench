# Design Document

## Overview

The bug occurs in the `create_img` method where the status text is set to "Generating image..." at the start but is not properly cleared or updated when the operation completes. The current implementation only handles the spinner animation cleanup in the `finally` block but neglects the status text.

## Architecture

The fix involves modifying the status text management in the `ImageGeneratorApp` class to ensure proper status updates throughout the image generation lifecycle.

## Components and Interfaces

### Modified Components

1. **`create_img` method** - The main image generation method that needs proper status text management
2. **Status text handling** - Ensure consistent status updates across all operation states

### Current Flow Analysis

```
create_img() starts
├── Set status: "Generating image..."
├── Set is_generating = True
├── Start spinner animation
├── Call generate_image()
├── Update image display
└── finally block:
    ├── Set is_generating = False
    ├── Cancel spinner
    ├── Clear spinner text
    └── ❌ Status text remains "Generating image..."
```

### Proposed Flow

```
create_img() starts
├── Set status: "Generating image..."
├── Set is_generating = True
├── Start spinner animation
├── Call generate_image()
├── ✅ Clear status text (return to "Ready" state)
├── Update image display
└── finally block:
    ├── Set is_generating = False
    ├── Cancel spinner
    └── Clear spinner text
```

## Data Models

No new data models required. The existing status management uses:
- `self.status_label` - tkinter Label widget for displaying status
- `self.is_generating` - boolean flag for generation state
- `self.spinner_label` - separate label for spinner animation

## Error Handling

### Current Error Handling
- Errors are caught and displayed via `self.root.after(0, self.status_label.config, {"text": f"Error: {str(e)}"})`
- This works correctly and should be preserved

### Enhanced Error Handling
- Maintain existing error display mechanism
- Ensure error messages persist until next operation starts
- Clear error messages when new operations begin

## Testing Strategy

### Manual Testing
1. **Success Case**: Generate an image and verify status changes from "Generating image..." to "Ready" (or empty)
2. **Error Case**: Trigger an error (invalid model/prompt) and verify error message displays and persists
3. **Queue Case**: Start multiple generations and verify status updates correctly for each
4. **Cancellation Case**: Test rapid prompt changes and verify status updates appropriately

### Edge Cases
1. **Rapid Operations**: Multiple quick generations should show appropriate status for current operation
2. **Network Issues**: Connection errors should display proper error messages
3. **Invalid Inputs**: Empty prompts or invalid models should show appropriate errors

## Implementation Details

### Status Text Management Strategy

1. **Success Path**: Clear status text (return to "Ready" state) after successful image generation
2. **Error Path**: Preserve existing error handling mechanism
3. **Cleanup**: Ensure status is updated in all code paths (success, error, finally)

### Code Changes Required

1. **In `create_img` method**:
   - Clear status text after successful image generation
   - Ensure status is properly managed in all execution paths

2. **Status Message Standards**:
   - Loading: "Generating image..."
   - Success: "Ready" (or empty text)
   - Error: "Error: {specific error message}"
   - Ready: "Ready"

### Thread Safety Considerations

The current implementation uses `self.root.after(0, ...)` for thread-safe GUI updates, which should be maintained for all status updates.