using System;
using System.ComponentModel;
using System.Text;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;
using ImageGenDotNet.ViewModels;

namespace ImageGenDotNet;

/// <summary>
/// Interaction logic for MainWindow.xaml
/// </summary>
public partial class MainWindow : Window
{
    private bool _isDragging = false;
    private Point _lastMousePosition;
    private const double ZoomFactor = 1.2;
    private const double MinZoom = 0.1;
    private const double MaxZoom = 10.0;
    private double _currentZoom = 1.0;

    public MainWindow()
    {
        InitializeComponent();
        DataContext = new MainViewModel();
        
        // Subscribe to property changes to reset zoom when image changes
        if (DataContext is MainViewModel viewModel)
        {
            viewModel.PropertyChanged += ViewModel_PropertyChanged;
        }
        
        // Add keyboard shortcut for running tests (Ctrl+T)
        KeyDown += MainWindow_KeyDown;
    }

    /// <summary>
    /// Handles keyboard shortcuts
    /// </summary>
    private async void MainWindow_KeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key == Key.T && (Keyboard.Modifiers & ModifierKeys.Control) == ModifierKeys.Control)
        {
            await RunIntegrationTests();
            e.Handled = true;
        }
    }

    /// <summary>
    /// Runs the integration tests
    /// </summary>
    private async System.Threading.Tasks.Task RunIntegrationTests()
    {
        var result = MessageBox.Show(
            "This will run comprehensive integration tests that will:\n\n" +
            "• Test all features with real API calls\n" +
            "• Generate multiple test images\n" +
            "• Save test results to your Desktop\n" +
            "• May take several minutes to complete\n\n" +
            "Make sure you have FAL_KEY and OPENAI_API_KEY environment variables set.\n\n" +
            "Continue with testing?",
            "Run Integration Tests",
            MessageBoxButton.YesNo,
            MessageBoxImage.Question);

        if (result == MessageBoxResult.Yes)
        {
            try
            {
                var integrationTests = new IntegrationTests();
                
                // Show progress dialog
                var progressWindow = new Window
                {
                    Title = "Running Integration Tests",
                    Width = 400,
                    Height = 200,
                    WindowStartupLocation = WindowStartupLocation.CenterOwner,
                    Owner = this,
                    ResizeMode = ResizeMode.NoResize
                };
                
                var progressContent = new StackPanel
                {
                    Margin = new Thickness(20),
                    VerticalAlignment = VerticalAlignment.Center
                };
                
                progressContent.Children.Add(new TextBlock
                {
                    Text = "Running integration tests...",
                    FontSize = 16,
                    HorizontalAlignment = HorizontalAlignment.Center,
                    Margin = new Thickness(0, 0, 0, 20)
                });
                
                var progressBar = new ProgressBar
                {
                    IsIndeterminate = true,
                    Height = 20,
                    Margin = new Thickness(0, 0, 0, 20)
                };
                progressContent.Children.Add(progressBar);
                
                progressContent.Children.Add(new TextBlock
                {
                    Text = "This may take several minutes. Please wait...",
                    FontSize = 12,
                    HorizontalAlignment = HorizontalAlignment.Center,
                    Foreground = Brushes.Gray
                });
                
                progressWindow.Content = progressContent;
                progressWindow.Show();
                
                // Run tests asynchronously
                var testsPassed = await integrationTests.RunAllTestsAsync();
                
                progressWindow.Close();
                
                // Show results
                var resultMessage = testsPassed 
                    ? "✅ All integration tests PASSED!\n\nTest results and generated images have been saved to your Desktop in the 'ImageGenTests' folder."
                    : "❌ Some integration tests FAILED.\n\nPlease check the test results file on your Desktop for details.";
                
                var resultIcon = testsPassed ? MessageBoxImage.Information : MessageBoxImage.Warning;
                
                MessageBox.Show(resultMessage, "Integration Test Results", MessageBoxButton.OK, resultIcon);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error running integration tests:\n\n{ex.Message}", "Test Error", 
                    MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }
    }

    /// <summary>
    /// Handles property changes from the ViewModel
    /// </summary>
    private void ViewModel_PropertyChanged(object? sender, System.ComponentModel.PropertyChangedEventArgs e)
    {
        if (e.PropertyName == nameof(MainViewModel.GeneratedImage))
        {
            ResetZoom();
        }
    }

    /// <summary>
    /// Resets the zoom to fit the image in the viewer
    /// </summary>
    private void ResetZoom()
    {
        _currentZoom = 1.0;
        ImageScaleTransform.ScaleX = 1.0;
        ImageScaleTransform.ScaleY = 1.0;
        ImageScrollViewer.ScrollToHorizontalOffset(0);
        ImageScrollViewer.ScrollToVerticalOffset(0);
    }

    /// <summary>
    /// Handles double-click to reset zoom
    /// </summary>
    private void ImageScrollViewer_MouseDoubleClick(object sender, MouseButtonEventArgs e)
    {
        if (GeneratedImage.Source != null)
        {
            ResetZoom();
            e.Handled = true;
        }
    }

    #region Zoom and Pan Event Handlers

    /// <summary>
    /// Handles mouse wheel events for zooming
    /// </summary>
    private void ImageScrollViewer_PreviewMouseWheel(object sender, MouseWheelEventArgs e)
    {
        if (GeneratedImage.Source == null)
            return;

        // Calculate new zoom factor
        double newZoom;
        if (e.Delta > 0)
        {
            // Zoom in
            newZoom = _currentZoom * ZoomFactor;
        }
        else
        {
            // Zoom out
            newZoom = _currentZoom / ZoomFactor;
        }

        // Clamp zoom to min/max values
        newZoom = Math.Max(MinZoom, Math.Min(MaxZoom, newZoom));

        // Get mouse position relative to the image
        var mousePosition = e.GetPosition(GeneratedImage);
        
        // Store the current scroll position
        var horizontalOffset = ImageScrollViewer.HorizontalOffset;
        var verticalOffset = ImageScrollViewer.VerticalOffset;

        // Apply the zoom transform
        ImageScaleTransform.ScaleX = newZoom;
        ImageScaleTransform.ScaleY = newZoom;
        _currentZoom = newZoom;

        // Calculate the zoom ratio
        var zoomRatio = newZoom / _currentZoom;
        
        // Update the current zoom before calculating offsets
        _currentZoom = newZoom;

        // Update the scroll position to keep the zoom centered on the mouse position
        var newHorizontalOffset = (horizontalOffset + mousePosition.X) * zoomRatio - mousePosition.X;
        var newVerticalOffset = (verticalOffset + mousePosition.Y) * zoomRatio - mousePosition.Y;

        // Force the ScrollViewer to update its layout
        ImageScrollViewer.UpdateLayout();

        // Set the new scroll position
        ImageScrollViewer.ScrollToHorizontalOffset(newHorizontalOffset);
        ImageScrollViewer.ScrollToVerticalOffset(newVerticalOffset);

        e.Handled = true;
    }

    /// <summary>
    /// Handles mouse left button down for starting drag operation
    /// </summary>
    private void ImageScrollViewer_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    {
        if (GeneratedImage.Source == null)
            return;

        // Only start dragging if we're not double-clicking
        if (e.ClickCount == 1)
        {
            _isDragging = true;
            _lastMousePosition = e.GetPosition(ImageScrollViewer);
            ImageScrollViewer.CaptureMouse();
            ImageScrollViewer.Cursor = Cursors.Hand;
            e.Handled = true;
        }
    }

    /// <summary>
    /// Handles mouse left button up for ending drag operation
    /// </summary>
    private void ImageScrollViewer_MouseLeftButtonUp(object sender, MouseButtonEventArgs e)
    {
        if (_isDragging)
        {
            _isDragging = false;
            ImageScrollViewer.ReleaseMouseCapture();
            ImageScrollViewer.Cursor = Cursors.Arrow;
            e.Handled = true;
        }
    }

    /// <summary>
    /// Handles mouse move events for panning
    /// </summary>
    private void ImageScrollViewer_MouseMove(object sender, MouseEventArgs e)
    {
        if (!_isDragging || GeneratedImage.Source == null)
            return;

        var currentPosition = e.GetPosition(ImageScrollViewer);
        var deltaX = _lastMousePosition.X - currentPosition.X;
        var deltaY = _lastMousePosition.Y - currentPosition.Y;

        // Update scroll position
        ImageScrollViewer.ScrollToHorizontalOffset(ImageScrollViewer.HorizontalOffset + deltaX);
        ImageScrollViewer.ScrollToVerticalOffset(ImageScrollViewer.VerticalOffset + deltaY);

        _lastMousePosition = currentPosition;
        e.Handled = true;
    }

    #endregion

    #region Menu Event Handlers

    /// <summary>
    /// Handles the Run Integration Tests menu click
    /// </summary>
    private async void RunIntegrationTests_Click(object sender, RoutedEventArgs e)
    {
        await RunIntegrationTests();
    }

    /// <summary>
    /// Handles the About menu click
    /// </summary>
    private void About_Click(object sender, RoutedEventArgs e)
    {
        MessageBox.Show(
            "AI Image Generator\n" +
            "Version 1.0\n\n" +
            "A WPF application for generating images using various AI models.\n\n" +
            "Features:\n" +
            "• Multiple AI model support\n" +
            "• Prompt enhancement with OpenAI\n" +
            "• Auto-generation capabilities\n" +
            "• Image zoom and pan\n" +
            "• Save functionality\n\n" +
            "Keyboard Shortcuts:\n" +
            "• Ctrl+T: Run Integration Tests\n" +
            "• Double-click image: Reset zoom\n" +
            "• Mouse wheel: Zoom in/out\n" +
            "• Click and drag: Pan image",
            "About AI Image Generator",
            MessageBoxButton.OK,
            MessageBoxImage.Information);
    }

    #endregion
}