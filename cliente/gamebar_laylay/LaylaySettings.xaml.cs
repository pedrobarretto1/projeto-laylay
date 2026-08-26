using Windows.UI;
using Windows.UI.Xaml;
using Windows.UI.Xaml.Controls;
using Windows.UI.Xaml.Media;

namespace LaylayGameBar
{
    public sealed partial class LaylaySettings : Page
    {
        private readonly Slider _avatarSize = Slider(140, 380, 10);
        private readonly Slider _avatarOpacity = Slider(0.4, 1.0, 0.05);
        private readonly Slider _motionIntensity = Slider(0, 2, 0.1);
        private readonly ToggleSwitch _idleMotion = Toggle("Respiração quando está quieta");
        private readonly ToggleSwitch _speakingMotion = Toggle("Movimento enquanto fala");
        private readonly ToggleSwitch _reactiveMotion = Toggle("Reações ao concluir ou falhar comandos");
        private readonly ToggleSwitch _activityIndicator = Toggle("Aura colorida de ouvindo, pensando e executando");
        private readonly ToggleSwitch _smoothTransitions = Toggle("Transição suave entre expressões");
        private readonly ToggleSwitch _connectionBadge = Toggle("Mostrar aviso de conexão");
        private readonly ComboBox _avatarSide = Choice(
            new ComboBoxItem { Content = "Direita", Tag = "right" },
            new ComboBoxItem { Content = "Esquerda", Tag = "left" });
        private readonly ComboBox _commandPosition = Choice(
            new ComboBoxItem { Content = "Em cima", Tag = "top" },
            new ComboBoxItem { Content = "Embaixo", Tag = "bottom" });
        private bool _loading;

        public LaylaySettings()
        {
            InitializeComponent();
            BuildInterface();
            LoadPreferences();
            HookEvents();
        }

        private void BuildInterface()
        {
            SettingsPanel.Children.Add(Text("Configurações da Laylay", 25, true, Purple()));
            SettingsPanel.Children.Add(Text(
                "As mudanças aparecem no avatar fixado em poucos instantes.", 14, false, Muted()));
            SettingsPanel.Children.Add(Text(
                "Para voltar aqui, abra Win + G e use a engrenagem do widget Laylay.",
                13, false, Purple(), new Thickness(0, 8, 0, 10)));

            AddSetting("Tamanho do avatar", _avatarSize);
            AddSetting("Opacidade do avatar", _avatarOpacity);
            AddSetting("Intensidade do movimento", _motionIntensity);
            AddControl(_idleMotion);
            AddControl(_speakingMotion);
            AddControl(_reactiveMotion);
            AddControl(_activityIndicator);
            AddControl(_smoothTransitions);
            AddControl(_connectionBadge);
            AddSetting("Lado do avatar", _avatarSide);
            AddSetting("Posição da barra de comando", _commandPosition);

            var reset = new Button { Content = "Restaurar padrão", Margin = new Thickness(0, 12, 0, 8) };
            reset.Click += ResetClicked;
            SettingsPanel.Children.Add(reset);
            SettingsPanel.Children.Add(Text(
                "Para jogar, mantenha o widget fixado e ative o click-through.",
                13, false, Muted()));
        }

        private void HookEvents()
        {
            _avatarSize.ValueChanged += PreferenceChanged;
            _avatarOpacity.ValueChanged += PreferenceChanged;
            _motionIntensity.ValueChanged += PreferenceChanged;
            foreach (var toggle in new[] { _idleMotion, _speakingMotion, _reactiveMotion,
                _activityIndicator, _smoothTransitions, _connectionBadge })
            {
                toggle.Toggled += PreferenceChanged;
            }
            _avatarSide.SelectionChanged += PreferenceChanged;
            _commandPosition.SelectionChanged += PreferenceChanged;
        }

        private void LoadPreferences()
        {
            _loading = true;
            var p = WidgetPreferences.Load();
            _avatarSize.Value = p.AvatarSize;
            _avatarOpacity.Value = p.AvatarOpacity;
            _motionIntensity.Value = p.MotionIntensity;
            _idleMotion.IsOn = p.IdleMotion;
            _speakingMotion.IsOn = p.SpeakingMotion;
            _reactiveMotion.IsOn = p.ReactiveMotion;
            _activityIndicator.IsOn = p.ActivityIndicator;
            _smoothTransitions.IsOn = p.SmoothTransitions;
            _connectionBadge.IsOn = p.ConnectionBadge;
            SelectTag(_avatarSide, p.AvatarSide);
            SelectTag(_commandPosition, p.CommandPosition);
            _loading = false;
        }

        private void PreferenceChanged(object sender, RoutedEventArgs e) => SavePreferences();
        private void PreferenceChanged(object sender, SelectionChangedEventArgs e) => SavePreferences();

        private void SavePreferences()
        {
            if (_loading) return;
            new WidgetPreferences
            {
                AvatarSize = _avatarSize.Value,
                AvatarOpacity = _avatarOpacity.Value,
                MotionIntensity = _motionIntensity.Value,
                IdleMotion = _idleMotion.IsOn,
                SpeakingMotion = _speakingMotion.IsOn,
                ReactiveMotion = _reactiveMotion.IsOn,
                ActivityIndicator = _activityIndicator.IsOn,
                SmoothTransitions = _smoothTransitions.IsOn,
                ConnectionBadge = _connectionBadge.IsOn,
                AvatarSide = SelectedTag(_avatarSide, "right"),
                CommandPosition = SelectedTag(_commandPosition, "top")
            }.Save();
        }

        private void ResetClicked(object sender, RoutedEventArgs e)
        {
            WidgetPreferences.Reset();
            LoadPreferences();
        }

        private void AddSetting(string title, Control control)
        {
            SettingsPanel.Children.Add(Text(title, 14, false, White(), new Thickness(0, 8, 0, 2)));
            AddControl(control);
        }

        private void AddControl(Control control)
        {
            control.Margin = new Thickness(0, 0, 0, 7);
            control.HorizontalAlignment = HorizontalAlignment.Stretch;
            SettingsPanel.Children.Add(control);
        }

        private static TextBlock Text(string value, double size, bool bold, Brush color,
            Thickness? margin = null)
        {
            return new TextBlock
            {
                Text = value,
                FontSize = size,
                FontWeight = bold ? Windows.UI.Text.FontWeights.SemiBold : Windows.UI.Text.FontWeights.Normal,
                Foreground = color,
                TextWrapping = TextWrapping.Wrap,
                Margin = margin ?? new Thickness(0, 0, 0, 5)
            };
        }

        private static Slider Slider(double minimum, double maximum, double step) => new Slider
        {
            Minimum = minimum,
            Maximum = maximum,
            StepFrequency = step
        };

        private static ToggleSwitch Toggle(string header) => new ToggleSwitch
        {
            Header = header,
            Foreground = White()
        };

        private static ComboBox Choice(params ComboBoxItem[] items)
        {
            var combo = new ComboBox();
            foreach (var item in items) combo.Items.Add(item);
            return combo;
        }

        private static string SelectedTag(ComboBox combo, string fallback)
        {
            var item = combo.SelectedItem as ComboBoxItem;
            return item == null ? fallback : item.Tag as string ?? fallback;
        }

        private static void SelectTag(ComboBox combo, string tag)
        {
            foreach (var raw in combo.Items)
            {
                var item = raw as ComboBoxItem;
                if (item != null && (item.Tag as string) == tag)
                {
                    combo.SelectedItem = item;
                    return;
                }
            }
            combo.SelectedIndex = 0;
        }

        private static Brush White() => new SolidColorBrush(Colors.White);
        private static Brush Purple() => new SolidColorBrush(Color.FromArgb(255, 196, 181, 253));
        private static Brush Muted() => new SolidColorBrush(Color.FromArgb(255, 166, 169, 182));
    }
}
