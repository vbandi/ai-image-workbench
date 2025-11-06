#!/usr/bin/env python3
"""
Test script to verify status text behavior across all generation scenarios.
This script tests the requirements specified in the fix-generating-text-bug spec.
"""

import tkinter as tk
import threading
import time
import sys
from unittest.mock import patch, MagicMock
from ui_app import ImageGeneratorApp
from PIL import Image


class StatusTestRunner:
    def __init__(self):
        self.test_results = []
        self.app = None
        self.root = None
        
    def setup_test_app(self):
        """Setup a test instance of the application"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        self.app = ImageGeneratorApp(self.root)
        # Process any pending events
        self.root.update()
        
    def teardown_test_app(self):
        """Clean up the test application"""
        if self.root:
            self.root.destroy()
            self.root = None
            self.app = None
            
    def log_test(self, test_name, passed, message=""):
        """Log test results"""
        status = "PASS" if passed else "FAIL"
        result = f"[{status}] {test_name}"
        if message:
            result += f": {message}"
        print(result)
        self.test_results.append((test_name, passed, message))
        
    def wait_for_generation_complete(self, timeout=10):
        """Wait for generation to complete or timeout"""
        start_time = time.time()
        while self.app.is_generating and (time.time() - start_time) < timeout:
            self.root.update()
            time.sleep(0.1)
        return not self.app.is_generating
        
    def get_status_text(self):
        """Get current status text"""
        return self.app.status_label.cget("text")
        
    def test_manual_generation_status_clearing(self):
        """Test manual generation via Generate button ensures status clears properly"""
        test_name = "Manual Generation Status Clearing"
        
        try:
            # Set up a test prompt
            self.app.text_input.insert("1.0", "test prompt")
            
            # Mock the generate_image function to return quickly
            with patch('ui_app.generate_image') as mock_generate:
                mock_generate.return_value = Image.new('RGB', (512, 512), color='red')
                
                # Trigger manual generation
                initial_status = self.get_status_text()
                self.app.manual_generate()
                
                # Check that status shows "Generating image..."
                self.root.update()
                time.sleep(0.1)  # Allow status to update
                generating_status = self.get_status_text()
                
                # Wait for generation to complete
                completed = self.wait_for_generation_complete()
                
                if not completed:
                    self.log_test(test_name, False, "Generation did not complete within timeout")
                    return
                    
                # Check final status
                final_status = self.get_status_text()
                
                # Verify status progression
                status_shows_generating = "Generating" in generating_status
                status_cleared = final_status in ["Ready", ""]
                
                passed = status_shows_generating and status_cleared
                message = f"Initial: '{initial_status}' -> Generating: '{generating_status}' -> Final: '{final_status}'"
                self.log_test(test_name, passed, message)
                
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {str(e)}")
            
    def test_auto_generation_keypress_status(self):
        """Test auto-generation on keypress ensures status updates correctly"""
        test_name = "Auto-Generation Keypress Status"
        
        try:
            # Enable auto-generation
            self.app.auto_generate.set(True)
            
            # Mock the generate_image function
            with patch('ui_app.generate_image') as mock_generate:
                mock_generate.return_value = Image.new('RGB', (512, 512), color='blue')
                
                # Clear any existing text and add new text
                self.app.text_input.delete("1.0", tk.END)
                self.app.text_input.insert("1.0", "auto test prompt")
                
                # Simulate key release event
                event = MagicMock()
                event.keysym = 'a'
                
                initial_status = self.get_status_text()
                self.app.on_key_release(event)
                
                # Allow status to update
                self.root.update()
                time.sleep(0.1)
                generating_status = self.get_status_text()
                
                # Wait for completion
                completed = self.wait_for_generation_complete()
                
                if not completed:
                    self.log_test(test_name, False, "Auto-generation did not complete within timeout")
                    return
                    
                final_status = self.get_status_text()
                
                # Verify status updates
                status_shows_generating = "Generating" in generating_status
                status_cleared = final_status in ["Ready", ""]
                
                passed = status_shows_generating and status_cleared
                message = f"Initial: '{initial_status}' -> Generating: '{generating_status}' -> Final: '{final_status}'"
                self.log_test(test_name, passed, message)
                
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {str(e)}")
            
    def test_queued_operations_status(self):
        """Test queued operations ensure status reflects current operation state"""
        test_name = "Queued Operations Status"
        
        try:
            # Mock generate_image to take some time
            def slow_generate(model, prompt):
                time.sleep(0.5)  # Simulate slow generation
                return Image.new('RGB', (512, 512), color='green')
                
            with patch('ui_app.generate_image', side_effect=slow_generate):
                # Start first generation
                self.app.text_input.delete("1.0", tk.END)
                self.app.text_input.insert("1.0", "first prompt")
                self.app.manual_generate()
                
                # Allow first generation to start
                self.root.update()
                time.sleep(0.1)
                first_status = self.get_status_text()
                
                # Queue second generation while first is running
                self.app.text_input.delete("1.0", tk.END)
                self.app.text_input.insert("1.0", "second prompt")
                self.app.manual_generate()
                
                # Status should still show generating for current operation
                self.root.update()
                time.sleep(0.1)
                queued_status = self.get_status_text()
                
                # Wait for all operations to complete
                completed = self.wait_for_generation_complete(timeout=15)
                
                if not completed:
                    self.log_test(test_name, False, "Queued operations did not complete within timeout")
                    return
                    
                final_status = self.get_status_text()
                
                # Verify status behavior
                shows_generating = "Generating" in first_status and "Generating" in queued_status
                final_cleared = final_status in ["Ready", ""]
                
                passed = shows_generating and final_cleared
                message = f"First: '{first_status}' -> Queued: '{queued_status}' -> Final: '{final_status}'"
                self.log_test(test_name, passed, message)
                
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {str(e)}")
            
    def test_error_scenarios_status_persistence(self):
        """Test error scenarios confirm error messages display and persist appropriately"""
        test_name = "Error Scenarios Status Persistence"
        
        try:
            # Mock generate_image to raise an exception
            with patch('ui_app.generate_image') as mock_generate:
                mock_generate.side_effect = Exception("Test error message")
                
                # Set up prompt and trigger generation
                self.app.text_input.delete("1.0", tk.END)
                self.app.text_input.insert("1.0", "error test prompt")
                
                initial_status = self.get_status_text()
                self.app.manual_generate()
                
                # Allow status to update to generating
                self.root.update()
                time.sleep(0.1)
                generating_status = self.get_status_text()
                
                # Wait for error to occur
                completed = self.wait_for_generation_complete()
                
                if not completed:
                    self.log_test(test_name, False, "Error generation did not complete within timeout")
                    return
                    
                error_status = self.get_status_text()
                
                # Wait a bit more to ensure error persists
                time.sleep(0.5)
                self.root.update()
                persistent_status = self.get_status_text()
                
                # Verify error handling
                shows_generating = "Generating" in generating_status
                shows_error = "Error" in error_status and "Test error message" in error_status
                error_persists = error_status == persistent_status
                
                passed = shows_generating and shows_error and error_persists
                message = f"Initial: '{initial_status}' -> Generating: '{generating_status}' -> Error: '{error_status}' -> Persistent: '{persistent_status}'"
                self.log_test(test_name, passed, message)
                
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {str(e)}")
            
    def test_rapid_successive_operations_status(self):
        """Test rapid successive operations show correct status for each operation"""
        test_name = "Rapid Successive Operations Status"
        
        try:
            # Mock generate_image with different responses
            call_count = 0
            def varying_generate(model, prompt):
                nonlocal call_count
                call_count += 1
                time.sleep(0.2)  # Short delay
                return Image.new('RGB', (512, 512), color=['red', 'blue', 'green'][call_count % 3])
                
            with patch('ui_app.generate_image', side_effect=varying_generate):
                status_history = []
                
                # Perform rapid successive operations
                for i in range(3):
                    self.app.text_input.delete("1.0", tk.END)
                    self.app.text_input.insert("1.0", f"rapid test {i}")
                    self.app.manual_generate()
                    
                    # Capture status immediately after each operation
                    self.root.update()
                    time.sleep(0.05)
                    status = self.get_status_text()
                    status_history.append(status)
                    
                    time.sleep(0.1)  # Small delay between operations
                
                # Wait for all operations to complete
                completed = self.wait_for_generation_complete(timeout=10)
                
                if not completed:
                    self.log_test(test_name, False, "Rapid operations did not complete within timeout")
                    return
                    
                final_status = self.get_status_text()
                
                # Verify that status showed generating for each operation
                all_show_generating = all("Generating" in status for status in status_history if status)
                final_cleared = final_status in ["Ready", ""]
                
                passed = all_show_generating and final_cleared
                message = f"Status history: {status_history} -> Final: '{final_status}'"
                self.log_test(test_name, passed, message)
                
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {str(e)}")
            
    def test_error_clearing_on_new_operation(self):
        """Test that error messages are cleared when new operations begin"""
        test_name = "Error Clearing on New Operation"
        
        try:
            # First, cause an error
            with patch('ui_app.generate_image') as mock_generate:
                mock_generate.side_effect = Exception("First error")
                
                self.app.text_input.delete("1.0", tk.END)
                self.app.text_input.insert("1.0", "error prompt")
                self.app.manual_generate()
                
                # Wait for error
                self.wait_for_generation_complete()
                error_status = self.get_status_text()
                
                # Now perform successful operation
                mock_generate.side_effect = None
                mock_generate.return_value = Image.new('RGB', (512, 512), color='yellow')
                
                self.app.text_input.delete("1.0", tk.END)
                self.app.text_input.insert("1.0", "success prompt")
                self.app.manual_generate()
                
                # Check that status changes to generating (clearing error)
                self.root.update()
                time.sleep(0.1)
                new_generating_status = self.get_status_text()
                
                # Wait for completion
                self.wait_for_generation_complete()
                final_status = self.get_status_text()
                
                # Verify error was cleared and new operation proceeded normally
                had_error = "Error" in error_status
                error_cleared = "Generating" in new_generating_status
                final_success = final_status in ["Ready", ""]
                
                passed = had_error and error_cleared and final_success
                message = f"Error: '{error_status}' -> New Gen: '{new_generating_status}' -> Final: '{final_status}'"
                self.log_test(test_name, passed, message)
                
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {str(e)}")
            
    def run_all_tests(self):
        """Run all status behavior tests"""
        print("Starting Status Text Behavior Tests")
        print("=" * 50)
        
        try:
            self.setup_test_app()
            
            # Run all test methods
            self.test_manual_generation_status_clearing()
            self.test_auto_generation_keypress_status()
            self.test_queued_operations_status()
            self.test_error_scenarios_status_persistence()
            self.test_rapid_successive_operations_status()
            self.test_error_clearing_on_new_operation()
            
        finally:
            self.teardown_test_app()
            
        # Print summary
        print("\n" + "=" * 50)
        print("Test Summary:")
        
        passed_tests = sum(1 for _, passed, _ in self.test_results if passed)
        total_tests = len(self.test_results)
        
        print(f"Passed: {passed_tests}/{total_tests}")
        
        if passed_tests < total_tests:
            print("\nFailed Tests:")
            for test_name, passed, message in self.test_results:
                if not passed:
                    print(f"  - {test_name}: {message}")
                    
        return passed_tests == total_tests


def main():
    """Main test runner"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Status Text Behavior Test Suite")
        print("Tests the status text behavior across all generation scenarios")
        print("Usage: python test_status_behavior.py")
        return
        
    runner = StatusTestRunner()
    success = runner.run_all_tests()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()