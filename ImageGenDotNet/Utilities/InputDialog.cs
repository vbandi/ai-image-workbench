using System.Windows;
using System.Windows.Controls;

namespace ImageGenDotNet.Utilities
{
    /// <summary>
    /// Simple input dialog for getting text input from user
    /// </summary>
    public static class InputDialog
    {
        /// <summary>
        /// Shows a simple input dialog
        /// </summary>
        /// <param name="title">Dialog title</param>
        /// <param name="message">Message to display</param>
        /// <param name="defaultValue">Default input value</param>
        /// <returns>User input or null if cancelled</returns>
        public static string? ShowDialog(string title, string message, string defaultValue = "")
        {
            var dialog = new Window
            {
                Title = title,
                Width = 400,
                Height = 200,
                WindowStartupLocation = WindowStartupLocation.CenterOwner,
                ResizeMode = ResizeMode.NoResize,
                WindowStyle = WindowStyle.ToolWindow
            };

            var grid = new Grid();
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

            var messageLabel = new Label
            {
                Content = message,
                Margin = new Thickness(10),
                HorizontalAlignment = HorizontalAlignment.Left
            };
            Grid.SetRow(messageLabel, 0);

            var textBox = new TextBox
            {
                Text = defaultValue,
                Margin = new Thickness(10),
                Height = 25
            };
            Grid.SetRow(textBox, 1);

            var buttonPanel = new StackPanel
            {
                Orientation = Orientation.Horizontal,
                HorizontalAlignment = HorizontalAlignment.Right,
                Margin = new Thickness(10)
            };

            var okButton = new Button
            {
                Content = "OK",
                Width = 75,
                Height = 25,
                Margin = new Thickness(5, 0, 0, 0),
                IsDefault = true
            };

            var cancelButton = new Button
            {
                Content = "Cancel",
                Width = 75,
                Height = 25,
                IsCancel = true
            };

            buttonPanel.Children.Add(cancelButton);
            buttonPanel.Children.Add(okButton);
            Grid.SetRow(buttonPanel, 2);

            grid.Children.Add(messageLabel);
            grid.Children.Add(textBox);
            grid.Children.Add(buttonPanel);

            dialog.Content = grid;

            string? result = null;
            okButton.Click += (s, e) =>
            {
                result = textBox.Text;
                dialog.DialogResult = true;
            };

            textBox.Focus();
            textBox.SelectAll();

            return dialog.ShowDialog() == true ? result : null;
        }
    }
}