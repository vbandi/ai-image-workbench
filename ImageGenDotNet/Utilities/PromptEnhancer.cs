using OpenAI;
using OpenAI.Chat;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace ImageGenDotNet.Utilities
{
    public class PromptEnhancer
    {
        private readonly ChatClient _chatClient;

        public PromptEnhancer()
        {
            var apiKey = Environment.GetEnvironmentVariable("OPENAI_API_KEY");
            if (string.IsNullOrEmpty(apiKey))
            {
                throw new InvalidOperationException("OPENAI_API_KEY environment variable is not set. Please set this environment variable with your OpenAI API key.");
            }

            var openAIClient = new OpenAIClient(apiKey);
            _chatClient = openAIClient.GetChatClient("gpt-3.5-turbo");
        }

        /// <summary>
        /// Enhances a prompt using OpenAI's chat completion API
        /// </summary>
        /// <param name="prompt">The original prompt to enhance</param>
        /// <param name="directions">Optional directions for how to enhance the prompt</param>
        /// <returns>The enhanced prompt</returns>
        public async Task<string> EnhanceAsync(string prompt, string? directions = null)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(prompt))
                {
                    throw new ArgumentException("Prompt cannot be null or empty", nameof(prompt));
                }

                // Build the system message based on whether directions are provided
                string systemMessage;
                if (!string.IsNullOrWhiteSpace(directions))
                {
                    systemMessage = $"You are a helpful assistant that enhances image generation prompts. " +
                                  $"Take the user's prompt and make it more detailed and effective for AI image generation. " +
                                  $"Follow these specific directions: {directions}. " +
                                  $"Return only the enhanced prompt, no additional text or explanations.";
                }
                else
                {
                    systemMessage = "You are a helpful assistant that enhances image generation prompts. " +
                                  "Take the user's prompt and make it more detailed and effective for AI image generation. " +
                                  "Add descriptive details, artistic style suggestions, lighting, composition, and other elements " +
                                  "that would help create a better image. Return only the enhanced prompt, no additional text or explanations.";
                }

                var messages = new List<ChatMessage>
                {
                    ChatMessage.CreateSystemMessage(systemMessage),
                    ChatMessage.CreateUserMessage(prompt)
                };

                var options = new ChatCompletionOptions
                {
                    MaxOutputTokenCount = 500,
                    Temperature = 0.7f
                };

                var response = await _chatClient.CompleteChatAsync(messages, options);
                
                if (response?.Value?.Content?.Count > 0)
                {
                    var enhancedPrompt = response.Value.Content[0].Text?.Trim();
                    if (!string.IsNullOrWhiteSpace(enhancedPrompt))
                    {
                        return enhancedPrompt;
                    }
                }

                throw new InvalidOperationException("OpenAI API returned an empty or invalid response");
            }
            catch (Exception ex) when (!(ex is ArgumentException))
            {
                // Log the actual error for debugging but throw a user-friendly message
                throw new InvalidOperationException($"Failed to enhance prompt: {ex.Message}", ex);
            }
        }
    }
}