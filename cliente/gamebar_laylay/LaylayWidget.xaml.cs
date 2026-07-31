using Microsoft.Gaming.XboxGameBar;
using System;
using System.Collections.Generic;
using Windows.Foundation;
using Windows.UI;
using Windows.UI.Xaml;
using Windows.UI.Xaml.Controls;
using Windows.UI.Xaml.Media;
using Windows.UI.Xaml.Media.Imaging;
using Windows.UI.Xaml.Navigation;

namespace LaylayGameBar
{
    public sealed partial class LaylayWidget : Page
    {
        private readonly DispatcherTimer _animationTimer;
        private readonly LocalBridgeClient _bridge;
        private XboxGameBarWidget _widget;
        private DateTimeOffset _animationStarted = DateTimeOffset.Now;
        private bool _speaking;
        private bool _connected;
        private bool _pinned;
        private bool _clickThrough;
        private bool _commandVisible;
        private string _emotion = "calma";
        private string _activity = "idle";
        private string _reactionId = "";
        private double _intensity = 0.33;
        private DateTimeOffset _reactionStarted = DateTimeOffset.MinValue;
        private DateTimeOffset _imageChangedAt = DateTimeOffset.MinValue;
        private int _animationFrame;
        private WidgetPreferences _preferences = WidgetPreferences.Load();
        private double _lastConfiguredAvatarSize;
        private Size _idleWindowSize;

        private static readonly Dictionary<string, string[]> Assets = new Dictionary<string, string[]>
        {
            { "animada", new [] { "animada/laylay_animada_512_transparente_real.png", "animada/laylay_animada_falando_512_transparente_real.png" } },
            { "brava", new [] { "brava/laylay_brava_512_transparente_real.png", "brava/laylay_brava_falando_512_transparente_real.png" } },
            { "calma", new [] { "calma/laylay_calma_512_transparente_real_corrigida.png", "calma/laylay_calma_falando_512_transparente_real.png" } },
            { "envergonhada", new [] { "envergonhada/laylay_envergonhada_512_transparente.png", "envergonhada/laylay_envergonhada_falando_512_transparente_real.png" } },
            { "feliz", new [] { "feliz/laylay_feliz_boca_fechada_512_RGBA.png", "feliz/laylay_feliz_falando_512_transparente_real.png" } },
            { "surpresa", new [] { "surpresa/laylay_surpresa_512_transparente_real.png", "surpresa/laylay_surpresa_falando_512_transparente_real.png" } },
            { "triste", new [] { "triste/laylay_triste_512_transparente_real.png", "triste/laylay_triste_falando_512_transparente_real.png" } },
        };

        public LaylayWidget()
        {
            InitializeComponent();
            _bridge = new LocalBridgeClient(18766, ApplyState, SetConnected);
            _animationTimer = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(1000.0 / 30.0) };
            _animationTimer.Tick += Animate;
            _lastConfiguredAvatarSize = _preferences.AvatarSize;
            _idleWindowSize = SquareWindowSize(_preferences.AvatarSize);
            Root.SizeChanged += RootSizeChanged;
            ApplyPreferences();
            SetAvatarImage();
        }

        protected override void OnNavigatedTo(NavigationEventArgs e)
        {
            _widget = e.Parameter as XboxGameBarWidget;
            if (_widget != null)
            {
                _pinned = _widget.Pinned;
                _clickThrough = _widget.ClickThroughEnabled;
                _bridge.SetPinned(_pinned);
                _widget.PinnedChanged += WidgetPinnedChanged;
                _widget.ClickThroughEnabledChanged += WidgetClickThroughChanged;
                _widget.SettingsSupported = true;
                _widget.SettingsClicked += WidgetSettingsClicked;
                _widget.MinWindowSize = new Size(160, 160);
                RequestWindowSize(_idleWindowSize);
            }
            _animationStarted = DateTimeOffset.Now;
            _animationTimer.Start();
            _bridge.Start();
        }

        protected override void OnNavigatedFrom(NavigationEventArgs e)
        {
            if (_widget != null)
            {
                _widget.PinnedChanged -= WidgetPinnedChanged;
                _widget.ClickThroughEnabledChanged -= WidgetClickThroughChanged;
                _widget.SettingsClicked -= WidgetSettingsClicked;
            }
            Root.SizeChanged -= RootSizeChanged;
            _animationTimer.Stop();
            _bridge.Dispose();
            base.OnNavigatedFrom(e);
        }

        private void WidgetPinnedChanged(XboxGameBarWidget sender, object args)
        {
            _pinned = sender.Pinned;
            _bridge.SetPinned(_pinned);
            UpdateConnectionBadge();
        }

        private void WidgetClickThroughChanged(XboxGameBarWidget sender, object args)
        {
            _clickThrough = sender.ClickThroughEnabled;
            UpdateConnectionBadge();
        }

        private async void WidgetSettingsClicked(XboxGameBarWidget sender, object args)
        {
            try
            {
                await sender.ActivateSettingsAsync();
            }
            catch
            {
                ConnectionText.Text = "não consegui abrir as configurações";
                ConnectionBadge.Visibility = Visibility.Visible;
            }
        }

        private async void ApplyState(WidgetState state)
        {
            await Dispatcher.RunAsync(Windows.UI.Core.CoreDispatcherPriority.Normal, () =>
            {
                var emotion = Assets.ContainsKey(state.Emotion) ? state.Emotion : "calma";
                if (emotion != _emotion || state.Speaking != _speaking)
                {
                    _emotion = emotion;
                    _speaking = state.Speaking;
                    SetAvatarImage();
                }
                var activity = state.Speaking ? "speaking" : (state.Activity ?? "idle");
                if ((!String.IsNullOrEmpty(state.ReactionId) && state.ReactionId != _reactionId)
                    || (activity != _activity && (activity == "success" || activity == "error")))
                {
                    _reactionStarted = DateTimeOffset.Now;
                    _reactionId = state.ReactionId ?? "";
                }
                _activity = activity;
                _intensity = Math.Max(0.0, Math.Min(1.0, state.Intensity));
                UpdateActivityIndicator();
                if (state.CommandBar.Visible != _commandVisible)
                {
                    SetCommandBarVisible(state.CommandBar.Visible);
                }
                CommandText.Text = state.CommandBar.Text;
            });
        }

        private async void SetConnected(bool connected)
        {
            await Dispatcher.RunAsync(Windows.UI.Core.CoreDispatcherPriority.Normal, () =>
            {
                ConnectionText.Text = connected ? "conectada" : "aguardando Laylay";
                _connected = connected;
                UpdateConnectionBadge();
            });
        }

        private void UpdateConnectionBadge()
        {
            if (!_preferences.ConnectionBadge)
            {
                ConnectionBadge.Visibility = Visibility.Collapsed;
                return;
            }
            if (!_connected)
            {
                ConnectionText.Text = "aguardando Laylay";
                ConnectionBadge.Visibility = Visibility.Visible;
            }
            else if (!_pinned)
            {
                ConnectionText.Text = "fixe no alfinete para usar no jogo";
                ConnectionBadge.Visibility = Visibility.Visible;
            }
            else if (!_clickThrough)
            {
                ConnectionText.Text = "ative o click-through para liberar o mouse";
                ConnectionBadge.Visibility = Visibility.Visible;
            }
            else
            {
                ConnectionBadge.Visibility = Visibility.Collapsed;
            }
        }

        private void ApplyPreferences()
        {
            var updated = WidgetPreferences.Load();
            var sizeChanged = Math.Abs(updated.AvatarSize - _lastConfiguredAvatarSize) >= 1;
            _preferences = updated;
            if (sizeChanged && !_commandVisible)
            {
                _lastConfiguredAvatarSize = updated.AvatarSize;
                _idleWindowSize = SquareWindowSize(updated.AvatarSize);
                RequestWindowSize(_idleWindowSize);
            }
            AvatarContainer.HorizontalAlignment = _preferences.AvatarSide == "left"
                ? HorizontalAlignment.Left : HorizontalAlignment.Right;
            CommandBar.VerticalAlignment = _preferences.CommandPosition == "bottom"
                ? VerticalAlignment.Bottom : VerticalAlignment.Top;
            UpdateConnectionBadge();
            UpdateActivityIndicator();
            LayoutAvatar();
        }

        private static Size SquareWindowSize(double avatarSize)
        {
            var side = Math.Max(160, Math.Min(400, avatarSize + 16));
            return new Size(side, side);
        }

        private async void RequestWindowSize(Size size)
        {
            if (_widget == null) return;
            try
            {
                await _widget.TryResizeWindowAsync(size);
            }
            catch
            {
                // A Game Bar pode negar um resize enquanto troca de modo. O
                // SizeChanged seguinte ainda mantém o PNG ajustado à janela.
            }
        }

        private void SetCommandBarVisible(bool visible)
        {
            // Redimensionar o widget fazia a Game Bar recentralizar toda a
            // janela. A faixa agora vive dentro da área já fixada: o avatar
            // permanece exatamente no canto escolhido pelo usuário.
            _commandVisible = visible;
            CommandBar.Visibility = visible ? Visibility.Visible : Visibility.Collapsed;
        }

        private void RootSizeChanged(object sender, SizeChangedEventArgs e)
        {
            if (!_commandVisible && e.NewSize.Width >= 150 && e.NewSize.Height >= 150)
            {
                // O usuário continua soberano: se redimensionar pela Game Bar,
                // o avatar passa a acompanhar esse novo quadrado/retângulo.
                _idleWindowSize = e.NewSize;
            }
            LayoutAvatar();
        }

        private void LayoutAvatar()
        {
            if (Root.ActualWidth <= 0 || Root.ActualHeight <= 0) return;
            var availableWidth = Math.Max(120, Root.ActualWidth - 12);
            var availableHeight = Math.Max(120, Root.ActualHeight - 12);
            var side = Math.Min(availableWidth, availableHeight);
            AvatarContainer.Width = side;
            AvatarContainer.Height = side;
        }

        private void SetAvatarImage()
        {
            var pair = Assets.ContainsKey(_emotion) ? Assets[_emotion] : Assets["calma"];
            var relative = pair[_speaking ? 1 : 0];
            AvatarImage.Source = new BitmapImage(new Uri("ms-appx:///Assets/Avatar/" + relative));
            AvatarImage.Opacity = _preferences.SmoothTransitions
                ? _preferences.AvatarOpacity * 0.82
                : _preferences.AvatarOpacity;
            _imageChangedAt = DateTimeOffset.Now;
        }

        private static Color ActivityColor(string activity)
        {
            switch (activity)
            {
                case "listening": return Color.FromArgb(255, 96, 165, 250);
                case "thinking": return Color.FromArgb(255, 167, 139, 250);
                case "executing": return Color.FromArgb(255, 56, 189, 248);
                case "success": return Color.FromArgb(255, 52, 211, 153);
                case "error": return Color.FromArgb(255, 251, 113, 133);
                default: return Color.FromArgb(0, 0, 0, 0);
            }
        }

        private void UpdateActivityIndicator()
        {
            var color = ActivityColor(_activity);
            ActivityAura.Stroke = new SolidColorBrush(color);
            ActivityDot.Fill = new SolidColorBrush(color);
        }

        private void Animate(object sender, object e)
        {
            _animationFrame++;
            if (_animationFrame % 15 == 0)
            {
                ApplyPreferences();
            }
            var seconds = (DateTimeOffset.Now - _animationStarted).TotalSeconds;
            var transitionAge = (DateTimeOffset.Now - _imageChangedAt).TotalSeconds;
            var fade = _preferences.SmoothTransitions && transitionAge < 0.16
                ? 0.82 + transitionAge / 0.16 * 0.18
                : 1.0;
            AvatarImage.Opacity = _preferences.AvatarOpacity * fade;
            var intensity = _preferences.MotionIntensity;
            var activityStrength = 0.65 + _intensity * 0.35;
            AvatarMove.X = 0;
            if (_speaking && _preferences.SpeakingMotion)
            {
                AvatarMove.Y = (Math.Sin(seconds * Math.PI * 2.0 / 0.56) * 1.15
                             + Math.Sin(seconds * Math.PI * 2.0 / 1.70) * 0.55) * intensity;
                var pulse = 1.0 + Math.Sin(seconds * Math.PI * 2.0 / 0.38) * 0.003 * intensity;
                AvatarScale.ScaleX = pulse;
                AvatarScale.ScaleY = pulse;
            }
            else if (!_speaking && _preferences.IdleMotion)
            {
                AvatarMove.Y = Math.Sin(seconds * Math.PI * 2.0 / 3.8) * 1.5 * intensity;
                AvatarScale.ScaleX = 1.0;
                AvatarScale.ScaleY = 1.0;
                if (_activity == "listening")
                {
                    AvatarMove.Y += Math.Abs(Math.Sin(seconds * 3.0)) * 1.5 * intensity;
                }
                else if (_activity == "thinking")
                {
                    AvatarMove.X = Math.Sin(seconds * 2.1) * 1.4 * intensity;
                }
                else if (_activity == "executing")
                {
                    AvatarMove.Y += Math.Sin(seconds * 8.0) * 1.8 * intensity;
                }
                var reactionAge = (DateTimeOffset.Now - _reactionStarted).TotalSeconds;
                if (_preferences.ReactiveMotion && _activity == "success" && reactionAge < 0.75)
                {
                    AvatarMove.Y -= Math.Abs(Math.Sin(reactionAge * 8.4)) * 7 * intensity * activityStrength;
                    var pop = 1.0 + Math.Sin(Math.Min(1.0, reactionAge / 0.75) * Math.PI) * 0.025;
                    AvatarScale.ScaleX = pop;
                    AvatarScale.ScaleY = pop;
                }
                else if (_preferences.ReactiveMotion && _activity == "error" && reactionAge < 0.7)
                {
                    AvatarMove.X = Math.Sin(reactionAge * 38.0) * 5 * (1 - reactionAge / 0.7) * intensity;
                }
            }
            else
            {
                AvatarMove.Y = 0;
                AvatarMove.X = 0;
                AvatarScale.ScaleX = 1.0;
                AvatarScale.ScaleY = 1.0;
            }
            var active = _preferences.ActivityIndicator
                && _activity != "idle" && _activity != "speaking";
            ActivityAura.Opacity = active ? 0.32 + (Math.Sin(seconds * 5.0) + 1.0) * 0.16 : 0.0;
            ActivityDot.Opacity = active ? 0.88 : 0.0;
        }
    }
}
