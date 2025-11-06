using Microsoft.Win32;
using System;
using System.IO;
using System.Threading.Tasks;
using System.Windows.Media.Imaging;

namespace ImageGenDotNet.Utilities
{
    public class FileHelper
    {
        /// <summary>
        /// Shows a save file dialog for image files
        /// </summary>
        /// <returns>Selected file path or null if cancelled</returns>
        public string? ShowSaveDialog()
        {
            try
            {
                var saveFileDialog = new SaveFileDialog
                {
                    Title = "Save Image",
                    Filter = "JPEG Image (*.jpg)|*.jpg|PNG Image (*.png)|*.png|All Files (*.*)|*.*",
                    DefaultExt = "jpg",
                    AddExtension = true,
                    FileName = $"generated_image_{DateTime.Now:yyyyMMdd_HHmmss}"
                };

                bool? result = saveFileDialog.ShowDialog();
                return result == true ? saveFileDialog.FileName : null;
            }
            catch (Exception ex)
            {
                throw new InvalidOperationException($"Failed to show save dialog: {ex.Message}", ex);
            }
        }

        /// <summary>
        /// Saves a BitmapImage to the specified file path
        /// </summary>
        /// <param name="image">The BitmapImage to save</param>
        /// <param name="filePath">The file path to save to</param>
        /// <returns>True if successful, false otherwise</returns>
        public async Task<bool> SaveImageAsync(BitmapImage image, string filePath)
        {
            if (image == null)
            {
                throw new ArgumentNullException(nameof(image), "Image cannot be null");
            }

            if (string.IsNullOrWhiteSpace(filePath))
            {
                throw new ArgumentException("File path cannot be null or empty", nameof(filePath));
            }

            try
            {
                return await Task.Run(() =>
                {
                    // Determine encoder based on file extension
                    BitmapEncoder encoder = GetEncoderFromExtension(filePath);
                    
                    // Create directory if it doesn't exist
                    string? directory = Path.GetDirectoryName(filePath);
                    if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
                    {
                        Directory.CreateDirectory(directory);
                    }

                    // Save the image
                    using var fileStream = new FileStream(filePath, FileMode.Create, FileAccess.Write);
                    encoder.Frames.Add(BitmapFrame.Create(image));
                    encoder.Save(fileStream);
                    
                    return true;
                });
            }
            catch (UnauthorizedAccessException ex)
            {
                throw new InvalidOperationException($"Access denied when saving to '{filePath}'. Please check file permissions.", ex);
            }
            catch (DirectoryNotFoundException ex)
            {
                throw new InvalidOperationException($"Directory not found: '{Path.GetDirectoryName(filePath)}'. Please ensure the directory exists.", ex);
            }
            catch (IOException ex)
            {
                throw new InvalidOperationException($"File I/O error when saving to '{filePath}': {ex.Message}", ex);
            }
            catch (Exception ex)
            {
                throw new InvalidOperationException($"Unexpected error when saving image to '{filePath}': {ex.Message}", ex);
            }
        }

        /// <summary>
        /// Gets the appropriate bitmap encoder based on file extension
        /// </summary>
        /// <param name="filePath">The file path</param>
        /// <returns>BitmapEncoder for the file type</returns>
        private static BitmapEncoder GetEncoderFromExtension(string filePath)
        {
            string extension = Path.GetExtension(filePath).ToLowerInvariant();
            
            return extension switch
            {
                ".jpg" or ".jpeg" => new JpegBitmapEncoder { QualityLevel = 95 },
                ".png" => new PngBitmapEncoder(),
                ".bmp" => new BmpBitmapEncoder(),
                ".gif" => new GifBitmapEncoder(),
                ".tiff" or ".tif" => new TiffBitmapEncoder(),
                _ => new JpegBitmapEncoder { QualityLevel = 95 } // Default to JPEG
            };
        }
    }
}