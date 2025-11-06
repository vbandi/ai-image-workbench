using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows.Media.Imaging;

namespace ImageGenDotNet.Utilities
{
    /// <summary>
    /// Utility class for generating images using various AI models via FAL API
    /// </summary>
    public class ImageGenerator
    {
        private static readonly HttpClient _httpClient = new HttpClient();
        private static readonly string? _falKey = Environment.GetEnvironmentVariable("FAL_KEY");
        
        static ImageGenerator()
        {
            _httpClient.DefaultRequestHeaders.Add("Authorization", $"Key {_falKey}");
            _httpClient.DefaultRequestHeaders.Add("User-Agent", "ImageGenDotNet/1.0");
        }
        
        // Available models - matching the Python version
        private static readonly List<string> _availableModels = new List<string>
        {
            "fal-ai/flux/schnell",
            "fal-ai/flux-pro/v1.1",
            "fal-ai/flux-pro/v1.1-ultra",
            "fal-ai/flux-pro/v1.1-ultra-finetuned",
            "fal-ai/imagen4/preview",
            "fal-ai/imagen4/preview/fast",
            "fal-ai/imagen4/preview/ultra",
            "fal-ai/hidream-i1-fast",
            "fal-ai/hidream-i1-dev",
            "fal-ai/hidream-i1-full",
            "fal-ai/stable-diffusion-v35-large",
            "fal-ai/stable-diffusion-v35-medium",
            "fal-ai/luma-photon",
            "fal-ai/ideogram/v2",
            "fal-ai/recraft-20b",
            "fal-ai/sana",
            "fal-ai/bytedance/seedream/v3/text-to-image",
            "fal-ai/wan/v2.2-5b/text-to-image"
        };

        /// <summary>
        /// Gets the list of available AI models for image generation
        /// </summary>
        /// <returns>List of available model names</returns>
        public List<string> GetAvailableModels()
        {
            return new List<string>(_availableModels);
        }

        /// <summary>
        /// Generates an image using the specified model and prompt
        /// </summary>
        /// <param name="model">The AI model to use for generation</param>
        /// <param name="prompt">The text prompt for image generation</param>
        /// <returns>Generated image as BitmapImage</returns>
        /// <exception cref="ArgumentException">Thrown when model is not supported or prompt is empty</exception>
        /// <exception cref="HttpRequestException">Thrown when API call fails</exception>
        /// <exception cref="InvalidOperationException">Thrown when FAL_KEY environment variable is not set</exception>
        public async Task<BitmapImage> GenerateAsync(string model, string prompt)
        {
            // Validate inputs
            if (string.IsNullOrWhiteSpace(model))
                throw new ArgumentException("Model cannot be null or empty", nameof(model));
            
            if (string.IsNullOrWhiteSpace(prompt))
                throw new ArgumentException("Prompt cannot be null or empty", nameof(prompt));
            
            if (!_availableModels.Contains(model))
                throw new ArgumentException($"Unsupported model: {model}", nameof(model));

            if (string.IsNullOrWhiteSpace(_falKey))
                throw new InvalidOperationException("FAL_KEY environment variable is not set. Please set your FAL API key.");

            try
            {
                // Submit the generation request and get result
                var result = await SubmitAndGetResult(model, prompt);
                
                // Parse the response based on model type
                var imageBytes = await ParseModelResponse(result, model);
                
                // Convert to BitmapImage
                return CreateBitmapImageFromBytes(imageBytes);
            }
            catch (HttpRequestException ex)
            {
                throw new HttpRequestException($"Failed to generate image with model {model}: {ex.Message}", ex);
            }
            catch (JsonException ex)
            {
                throw new InvalidOperationException($"Failed to parse API response: {ex.Message}", ex);
            }
        }

        /// <summary>
        /// Submits a generation request to the FAL API and gets the result
        /// </summary>
        private async Task<JsonElement> SubmitAndGetResult(string model, string prompt)
        {
            var requestBody = CreateRequestBody(model, prompt);
            var json = JsonSerializer.Serialize(requestBody);
            var content = new StringContent(json, Encoding.UTF8, "application/json");
            
            // For sync_mode models, we can get the result directly
            var isSyncMode = IsSyncModeModel(model);
            
            if (isSyncMode)
            {
                var response = await _httpClient.PostAsync($"https://fal.run/{model}", content);
                response.EnsureSuccessStatusCode();
                
                var responseJson = await response.Content.ReadAsStringAsync();
                var result = JsonSerializer.Deserialize<JsonElement>(responseJson);
                return result;
            }
            else
            {
                // For async models, submit and then poll for results
                var submitResponse = await _httpClient.PostAsync($"https://fal.run/{model}", content);
                submitResponse.EnsureSuccessStatusCode();
                
                var submitJson = await submitResponse.Content.ReadAsStringAsync();
                var submission = JsonSerializer.Deserialize<JsonElement>(submitJson);
                
                if (submission.TryGetProperty("request_id", out var requestIdProp))
                {
                    var requestId = requestIdProp.GetString()!;
                    return await PollForResult(model, requestId);
                }
                
                throw new InvalidOperationException("Failed to get request ID from submission");
            }
        }

        /// <summary>
        /// Polls for the result of an async generation request
        /// </summary>
        private async Task<JsonElement> PollForResult(string model, string requestId)
        {
            var statusUrl = $"https://fal.run/{model}/requests/{requestId}/status";
            
            // Poll for completion with timeout
            var maxAttempts = 60; // 60 seconds timeout
            var attempts = 0;
            
            while (attempts < maxAttempts)
            {
                var response = await _httpClient.GetAsync(statusUrl);
                response.EnsureSuccessStatusCode();
                
                var responseJson = await response.Content.ReadAsStringAsync();
                var statusResponse = JsonSerializer.Deserialize<JsonElement>(responseJson);
                
                if (statusResponse.TryGetProperty("status", out var status))
                {
                    var statusValue = status.GetString();
                    if (statusValue == "COMPLETED")
                    {
                        if (statusResponse.TryGetProperty("result", out var result))
                        {
                            return result;
                        }
                        throw new InvalidOperationException("Completed response missing result");
                    }
                    else if (statusValue == "FAILED")
                    {
                        var error = statusResponse.TryGetProperty("error", out var errorProp) 
                            ? errorProp.GetString() 
                            : "Unknown error";
                        throw new InvalidOperationException($"Generation failed: {error}");
                    }
                }
                
                // Wait before polling again
                await Task.Delay(1000);
                attempts++;
            }
            
            throw new TimeoutException($"Generation request timed out after {maxAttempts} seconds");
        }

        /// <summary>
        /// Determines if a model supports sync mode
        /// </summary>
        private bool IsSyncModeModel(string model)
        {
            // Most models support sync mode, but some may require async polling
            return model switch
            {
                "fal-ai/flux/schnell" => true,
                "fal-ai/flux-pro/v1.1" => true,
                "fal-ai/flux-pro/v1.1-ultra" => true,
                "fal-ai/flux-pro/v1.1-ultra-finetuned" => true,
                _ => true // Default to sync mode
            };
        }

        /// <summary>
        /// Creates the request body based on the model type
        /// </summary>
        private object CreateRequestBody(string model, string prompt)
        {
            return model switch
            {
                "fal-ai/ideogram/v2" => new
                {
                    prompt,
                    enable_safety_checker = false,
                    safety_tolerance = 5
                },
                
                "fal-ai/imagen4/preview" or "fal-ai/imagen4/preview/fast" or "fal-ai/imagen4/preview/ultra" => new
                {
                    prompt,
                    num_images = 1,
                    aspect_ratio = "4:3",
                    enable_safety_checker = false,
                    safety_tolerance = 5
                },
                
                "fal-ai/flux-pro/v1.1-ultra-finetuned" => new
                {
                    prompt,
                    num_images = 1,
                    enable_safety_checker = false,
                    aspect_ratio = "4:3",
                    sync_mode = true,
                    finetune_id = "",
                    finetune_strength = 0.75
                },
                
                "fal-ai/bytedance/seedream/v3/text-to-image" => new
                {
                    prompt,
                    num_images = 1,
                    enable_safety_checker = false,
                    safety_tolerance = 5
                },
                
                "fal-ai/wan/v2.2-5b/text-to-image" => new
                {
                    prompt,
                    num_inference_steps = 40,
                    enable_safety_checker = false,
                    enable_prompt_expansion = false,
                    guidance_scale = 3.5,
                    shift = 2,
                    image_size = "landscape_4_3"
                },
                
                _ => new
                {
                    prompt,
                    num_images = 1,
                    enable_safety_checker = false,
                    image_size = "landscape_4_3",
                    sync_mode = true,
                    safety_tolerance = 5
                }
            };
        }

        /// <summary>
        /// Parses the model response based on the specific model format
        /// </summary>
        private async Task<byte[]> ParseModelResponse(JsonElement result, string model)
        {
            return model switch
            {
                "fal-ai/ideogram/v2" => await ParseIdeogramResponse(result),
                "fal-ai/imagen4/preview" or "fal-ai/imagen4/preview/fast" or "fal-ai/imagen4/preview/ultra" => await ParseImagen4Response(result),
                "fal-ai/flux-pro/v1.1" or "fal-ai/flux-pro/v1.1-ultra" or "fal-ai/flux-pro/v1.1-ultra-finetuned" => await ParseFluxProResponse(result),
                "fal-ai/bytedance/seedream/v3/text-to-image" => await ParseSeedreamResponse(result),
                "fal-ai/wan/v2.2-5b/text-to-image" => await ParseWanResponse(result),
                _ => await ParseStandardResponse(result)
            };
        }

        /// <summary>
        /// Parses Ideogram v2 response format
        /// </summary>
        private async Task<byte[]> ParseIdeogramResponse(JsonElement result)
        {
            // Format 1: Direct array of image URLs or data URIs
            if (result.TryGetProperty("images", out var images) && images.ValueKind == JsonValueKind.Array)
            {
                var firstImage = images.EnumerateArray().FirstOrDefault();
                if (firstImage.ValueKind == JsonValueKind.String)
                {
                    var imageData = firstImage.GetString()!;
                    return await ProcessImageData(imageData);
                }
            }
            
            // Format 2: Object with image property
            if (result.TryGetProperty("image", out var image) && image.ValueKind == JsonValueKind.String)
            {
                var imageData = image.GetString()!;
                return await ProcessImageData(imageData);
            }
            
            throw new InvalidOperationException($"Could not extract image from Ideogram v2 response");
        }

        /// <summary>
        /// Parses Imagen 4 response format
        /// </summary>
        private async Task<byte[]> ParseImagen4Response(JsonElement result)
        {
            if (result.TryGetProperty("images", out var images) && images.ValueKind == JsonValueKind.Array)
            {
                var firstImage = images.EnumerateArray().FirstOrDefault();
                if (firstImage.TryGetProperty("url", out var url))
                {
                    var imageUrl = url.GetString()!;
                    return await DownloadImageFromUrl(imageUrl);
                }
            }
            
            throw new InvalidOperationException("Could not extract image from Imagen 4 response");
        }

        /// <summary>
        /// Parses FLUX Pro response format
        /// </summary>
        private async Task<byte[]> ParseFluxProResponse(JsonElement result)
        {
            if (result.TryGetProperty("images", out var images) && images.ValueKind == JsonValueKind.Array)
            {
                var firstImage = images.EnumerateArray().FirstOrDefault();
                if (firstImage.TryGetProperty("url", out var url))
                {
                    var imageUrl = url.GetString()!;
                    return await DownloadImageFromUrl(imageUrl);
                }
            }
            
            throw new InvalidOperationException("Could not extract image from FLUX Pro response");
        }

        /// <summary>
        /// Parses SeeDream v3 response format
        /// </summary>
        private async Task<byte[]> ParseSeedreamResponse(JsonElement result)
        {
            if (result.TryGetProperty("images", out var images) && images.ValueKind == JsonValueKind.Array)
            {
                var firstImage = images.EnumerateArray().FirstOrDefault();
                if (firstImage.TryGetProperty("url", out var url))
                {
                    var imageUrl = url.GetString()!;
                    return await DownloadImageFromUrl(imageUrl);
                }
            }
            
            throw new InvalidOperationException("Could not extract image from SeeDream v3 response");
        }

        /// <summary>
        /// Parses WAN v2.2-5b response format
        /// </summary>
        private async Task<byte[]> ParseWanResponse(JsonElement result)
        {
            if (result.TryGetProperty("image", out var image) && image.TryGetProperty("url", out var url))
            {
                var imageUrl = url.GetString()!;
                return await DownloadImageFromUrl(imageUrl);
            }
            
            throw new InvalidOperationException("Could not extract image from WAN v2.2-5b response");
        }

        /// <summary>
        /// Parses standard response format
        /// </summary>
        private async Task<byte[]> ParseStandardResponse(JsonElement result)
        {
            if (result.TryGetProperty("images", out var images) && images.ValueKind == JsonValueKind.Array)
            {
                var firstImage = images.EnumerateArray().FirstOrDefault();
                if (firstImage.TryGetProperty("url", out var url))
                {
                    var imageData = url.GetString()!;
                    return await ProcessImageData(imageData);
                }
            }
            
            throw new InvalidOperationException("Could not extract image from standard response");
        }

        /// <summary>
        /// Processes image data (either data URI or URL)
        /// </summary>
        private async Task<byte[]> ProcessImageData(string imageData)
        {
            if (imageData.StartsWith("data:"))
            {
                // Handle data URI
                var base64Data = imageData.Split(',')[1];
                return Convert.FromBase64String(base64Data);
            }
            else
            {
                // Handle URL
                return await DownloadImageFromUrl(imageData);
            }
        }

        /// <summary>
        /// Downloads image from URL
        /// </summary>
        private async Task<byte[]> DownloadImageFromUrl(string url)
        {
            var response = await _httpClient.GetAsync(url);
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadAsByteArrayAsync();
        }

        /// <summary>
        /// Creates a BitmapImage from byte array
        /// </summary>
        private BitmapImage CreateBitmapImageFromBytes(byte[] imageBytes)
        {
            var bitmap = new BitmapImage();
            bitmap.BeginInit();
            bitmap.StreamSource = new MemoryStream(imageBytes);
            bitmap.CacheOption = BitmapCacheOption.OnLoad;
            bitmap.EndInit();
            bitmap.Freeze(); // Make it thread-safe
            return bitmap;
        }

        /// <summary>
        /// Disposes of the HTTP client resources
        /// </summary>
        public static void Dispose()
        {
            _httpClient?.Dispose();
        }
    }
}