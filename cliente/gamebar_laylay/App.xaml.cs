using Microsoft.Gaming.XboxGameBar;
using System;
using Windows.ApplicationModel;
using Windows.ApplicationModel.Activation;
using Windows.UI.Xaml;
using Windows.UI.Xaml.Controls;
using Windows.UI.Xaml.Navigation;

namespace LaylayGameBar
{
    sealed partial class App : Application
    {
        private XboxGameBarWidget _widget;
        private XboxGameBarWidget _settingsWidget;

        public App()
        {
            InitializeComponent();
            Suspending += OnSuspending;
        }

        protected override void OnActivated(IActivatedEventArgs args)
        {
            XboxGameBarWidgetActivatedEventArgs widgetArgs = null;
            if (args.Kind == ActivationKind.Protocol)
            {
                var protocolArgs = args as IProtocolActivatedEventArgs;
                if (protocolArgs != null && protocolArgs.Uri.Scheme == "ms-gamebarwidget")
                {
                    widgetArgs = args as XboxGameBarWidgetActivatedEventArgs;
                }
            }

            if (widgetArgs == null || !widgetArgs.IsLaunchActivation)
            {
                return;
            }

            var frame = new Frame();
            frame.NavigationFailed += OnNavigationFailed;
            Window.Current.Content = frame;
            if (widgetArgs.AppExtensionId == "LaylayWidget")
            {
                _widget = new XboxGameBarWidget(widgetArgs, Window.Current.CoreWindow, frame);
                frame.Navigate(typeof(LaylayWidget), _widget);
                Window.Current.Closed += OnWidgetClosed;
            }
            else if (widgetArgs.AppExtensionId == "LaylaySettings")
            {
                _settingsWidget = new XboxGameBarWidget(widgetArgs, Window.Current.CoreWindow, frame);
                frame.Navigate(typeof(LaylaySettings), _settingsWidget);
                Window.Current.Closed += OnSettingsClosed;
            }
            else
            {
                return;
            }
            Window.Current.Activate();
        }

        protected override void OnLaunched(LaunchActivatedEventArgs e)
        {
            var frame = Window.Current.Content as Frame ?? new Frame();
            frame.NavigationFailed += OnNavigationFailed;
            Window.Current.Content = frame;
            if (frame.Content == null)
            {
                frame.Navigate(typeof(MainPage));
            }
            Window.Current.Activate();
        }

        private void OnWidgetClosed(object sender, Windows.UI.Core.CoreWindowEventArgs e)
        {
            _widget = null;
            Window.Current.Closed -= OnWidgetClosed;
        }

        private void OnSettingsClosed(object sender, Windows.UI.Core.CoreWindowEventArgs e)
        {
            _settingsWidget = null;
            Window.Current.Closed -= OnSettingsClosed;
        }

        private void OnNavigationFailed(object sender, NavigationFailedEventArgs e)
        {
            throw new InvalidOperationException("Falha ao abrir " + e.SourcePageType.FullName);
        }

        private void OnSuspending(object sender, SuspendingEventArgs e)
        {
            _widget = null;
            _settingsWidget = null;
        }
    }
}
