using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;

namespace ImageGenDotNet.Utilities
{
    /// <summary>
    /// Utility class for validating environment variables and API keys
    /// </summary>
    public static class EnvironmentValidator
    {
        /// <summary>
        /// Result of environment validation
        /// </summary>
        public class ValidationResult
        {
            public bool IsValid { get; set; }
            public List<string> MissingKeys { get; set; } = new List<string>();
            public List<string> InvalidKeys { get; set; } = new List<string>();
            public List<string> Warnings { get; set; } = new List<string>();
            public string ErrorMessage { get; set; } = string.Empty;
            public string SetupInstructions { get; set; } = string.Empty;
        }

        /// <summary>
        /// Validates all required environment variables for the application
        /// </summary>
        /// <returns>ValidationResult with details about missing or invalid keys</returns>
        public static ValidationResult ValidateEnvironment()
        {
            var result = new ValidationResult();
            
            // Check OPENAI_API_KEY
            var openAiKey = Environment.GetEnvironmentVariable("OPENAI_API_KEY");
            if (string.IsNullOrWhiteSpace(openAiKey))
            {
                result.MissingKeys.Add("OPENAI_API_KEY");
                result.Warnings.Add("Prompt enhancement features will be disabled without OPENAI_API_KEY");
            }
            else if (!IsValidOpenAiApiKey(openAiKey))
            {
                result.InvalidKeys.Add("OPENAI_API_KEY");
                result.Warnings.Add("OPENAI_API_KEY format appears invalid - should start with 'sk-'");
            }

            // Check FAL_KEY
            var falKey = Environment.GetEnvironmentVariable("FAL_KEY");
            if (string.IsNullOrWhiteSpace(falKey))
            {
                result.MissingKeys.Add("FAL_KEY");
            }
            else if (!IsValidFalApiKey(falKey))
            {
                result.InvalidKeys.Add("FAL_KEY");
                result.Warnings.Add("FAL_KEY format appears invalid");
            }

            // Determine overall validity
            // FAL_KEY is required for core functionality, OPENAI_API_KEY is optional
            // Invalid format warnings shouldn't prevent the app from starting
            result.IsValid = !result.MissingKeys.Contains("FAL_KEY");

            // Generate error message and setup instructions
            if (!result.IsValid || result.MissingKeys.Count > 0 || result.InvalidKeys.Count > 0)
            {
                result.ErrorMessage = GenerateErrorMessage(result);
                result.SetupInstructions = GenerateSetupInstructions(result);
            }

            return result;
        }

        /// <summary>
        /// Validates OpenAI API key format
        /// </summary>
        /// <param name="apiKey">The API key to validate</param>
        /// <returns>True if the format appears valid</returns>
        private static bool IsValidOpenAiApiKey(string apiKey)
        {
            if (string.IsNullOrWhiteSpace(apiKey))
                return false;

            // OpenAI API keys typically start with "sk-" and are followed by alphanumeric characters
            // They are usually around 51 characters total
            var pattern = @"^sk-[a-zA-Z0-9]{20,}$";
            return Regex.IsMatch(apiKey, pattern);
        }

        /// <summary>
        /// Validates FAL API key format
        /// </summary>
        /// <param name="apiKey">The API key to validate</param>
        /// <returns>True if the format appears valid</returns>
        private static bool IsValidFalApiKey(string apiKey)
        {
            if (string.IsNullOrWhiteSpace(apiKey))
                return false;

            // FAL API keys can contain alphanumeric characters, hyphens, underscores, and colons
            // Basic validation - at least 20 characters
            var pattern = @"^[a-zA-Z0-9_:-]{20,}$";
            return Regex.IsMatch(apiKey, pattern);
        }

        /// <summary>
        /// Generates a user-friendly error message based on validation results
        /// </summary>
        /// <param name="result">The validation result</param>
        /// <returns>Formatted error message</returns>
        private static string GenerateErrorMessage(ValidationResult result)
        {
            var messages = new List<string>();

            if (result.MissingKeys.Contains("FAL_KEY"))
            {
                messages.Add("FAL_KEY environment variable is required for image generation but is not set.");
            }

            if (result.MissingKeys.Contains("OPENAI_API_KEY"))
            {
                messages.Add("OPENAI_API_KEY environment variable is not set. Prompt enhancement features will be disabled.");
            }

            if (result.InvalidKeys.Count > 0)
            {
                messages.Add($"The following API keys have invalid formats: {string.Join(", ", result.InvalidKeys)}");
            }

            return string.Join("\n\n", messages);
        }

        /// <summary>
        /// Generates setup instructions for missing or invalid API keys
        /// </summary>
        /// <param name="result">The validation result</param>
        /// <returns>Formatted setup instructions</returns>
        private static string GenerateSetupInstructions(ValidationResult result)
        {
            var instructions = new List<string>();

            instructions.Add("To set up environment variables on Windows:");
            instructions.Add("");

            if (result.MissingKeys.Contains("FAL_KEY") || result.InvalidKeys.Contains("FAL_KEY"))
            {
                instructions.Add("For FAL_KEY (Required for image generation):");
                instructions.Add("1. Get your API key from https://fal.ai/dashboard");
                instructions.Add("2. Open Command Prompt as Administrator");
                instructions.Add("3. Run: setx FAL_KEY \"your-fal-api-key-here\" /M");
                instructions.Add("");
            }

            if (result.MissingKeys.Contains("OPENAI_API_KEY") || result.InvalidKeys.Contains("OPENAI_API_KEY"))
            {
                instructions.Add("For OPENAI_API_KEY (Optional - for prompt enhancement):");
                instructions.Add("1. Get your API key from https://platform.openai.com/api-keys");
                instructions.Add("2. Open Command Prompt as Administrator");
                instructions.Add("3. Run: setx OPENAI_API_KEY \"sk-your-openai-key-here\" /M");
                instructions.Add("");
            }

            instructions.Add("Alternative method using System Properties:");
            instructions.Add("1. Right-click 'This PC' → Properties → Advanced system settings");
            instructions.Add("2. Click 'Environment Variables'");
            instructions.Add("3. Under 'System variables', click 'New'");
            instructions.Add("4. Add the variable name and value");
            instructions.Add("");
            instructions.Add("After setting environment variables, restart the application.");

            return string.Join("\n", instructions);
        }

        /// <summary>
        /// Gets a summary of the current environment status
        /// </summary>
        /// <returns>Human-readable status summary</returns>
        public static string GetEnvironmentStatus()
        {
            var result = ValidateEnvironment();
            
            if (result.IsValid && result.MissingKeys.Count == 0 && result.InvalidKeys.Count == 0)
            {
                return "All environment variables are properly configured.";
            }

            var status = new List<string>();
            
            if (result.MissingKeys.Contains("FAL_KEY"))
            {
                status.Add("❌ FAL_KEY: Missing (Image generation disabled)");
            }
            else if (result.InvalidKeys.Contains("FAL_KEY"))
            {
                status.Add("⚠️ FAL_KEY: Invalid format");
            }
            else
            {
                status.Add("✅ FAL_KEY: Configured");
            }

            if (result.MissingKeys.Contains("OPENAI_API_KEY"))
            {
                status.Add("⚠️ OPENAI_API_KEY: Missing (Prompt enhancement disabled)");
            }
            else if (result.InvalidKeys.Contains("OPENAI_API_KEY"))
            {
                status.Add("⚠️ OPENAI_API_KEY: Invalid format");
            }
            else
            {
                status.Add("✅ OPENAI_API_KEY: Configured");
            }

            return string.Join("\n", status);
        }
    }
}