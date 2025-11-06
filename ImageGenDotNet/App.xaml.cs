using System.Configuration;
using System.Data;
using System.Windows;
using ImageGenDotNet.Utilities;

namespace ImageGenDotNet;

/// <summary>
/// Interaction logic for App.xaml
/// </summary>
public partial class App : Application
{
    protected override void OnStartup(StartupEventArgs e)
    {
        try
        {
            // Validate environment variables before starting the application
            var validationResult = EnvironmentValidator.ValidateEnvironment();
            
            // If FAL_KEY is missing, show error and exit (core functionality won't work)
            if (validationResult.MissingKeys.Contains("FAL_KEY"))
            {
                var errorMessage = "Image Generation Application - Configuration Error\n\n" +
                                 validationResult.ErrorMessage + "\n\n" +
                                 validationResult.SetupInstructions;
                
                MessageBox.Show(errorMessage, "Configuration Error", 
                    MessageBoxButton.OK, MessageBoxImage.Error);
                
                // Exit the application
                Shutdown(1);
                return;
            }
            
            // If there are warnings (like missing OPENAI_API_KEY or invalid formats), show them but continue
            if (validationResult.Warnings.Count > 0 || validationResult.InvalidKeys.Count > 0)
            {
                var warningMessage = "Image Generation Application - Configuration Warnings\n\n";
                
                if (validationResult.InvalidKeys.Count > 0)
                {
                    warningMessage += validationResult.ErrorMessage + "\n\n";
                }
                
                if (validationResult.Warnings.Count > 0)
                {
                    warningMessage += string.Join("\n", validationResult.Warnings) + "\n\n";
                }
                
                warningMessage += "The application will start, but some features may be limited.\n\n" +
                                "Setup Instructions:\n" + validationResult.SetupInstructions;
                
                MessageBox.Show(warningMessage, "Configuration Warnings", 
                    MessageBoxButton.OK, MessageBoxImage.Warning);
            }
            
            base.OnStartup(e);
        }
        catch (Exception ex)
        {
            MessageBox.Show($"Startup Error: {ex.Message}\n\nStack Trace:\n{ex.StackTrace}", 
                "Application Startup Error", MessageBoxButton.OK, MessageBoxImage.Error);
            Shutdown(1);
        }
    }
}

