using Windows.Storage;
using Windows.Foundation.Collections;

namespace LaylayGameBar
{
    public sealed class WidgetPreferences
    {
        private const string AvatarSizeKey = "avatar_size";
        private const string MotionIntensityKey = "motion_intensity";
        private const string IdleMotionKey = "idle_motion";
        private const string SpeakingMotionKey = "speaking_motion";
        private const string ConnectionBadgeKey = "connection_badge";
        private const string AvatarOpacityKey = "avatar_opacity";
        private const string ActivityIndicatorKey = "activity_indicator";
        private const string ReactiveMotionKey = "reactive_motion";
        private const string SmoothTransitionsKey = "smooth_transitions";
        private const string CommandPositionKey = "command_position";
        private const string AvatarSideKey = "avatar_side";

        public double AvatarSize { get; set; } = 250;
        public double MotionIntensity { get; set; } = 1.0;
        public bool IdleMotion { get; set; } = true;
        public bool SpeakingMotion { get; set; } = true;
        public bool ConnectionBadge { get; set; } = true;
        public double AvatarOpacity { get; set; } = 1.0;
        public bool ActivityIndicator { get; set; } = true;
        public bool ReactiveMotion { get; set; } = true;
        public bool SmoothTransitions { get; set; } = true;
        public string CommandPosition { get; set; } = "top";
        public string AvatarSide { get; set; } = "right";

        public static WidgetPreferences Load()
        {
            var values = ApplicationData.Current.LocalSettings.Values;
            return new WidgetPreferences
            {
                AvatarSize = GetDouble(values, AvatarSizeKey, 250, 140, 380),
                MotionIntensity = GetDouble(values, MotionIntensityKey, 1.0, 0, 2),
                IdleMotion = GetBool(values, IdleMotionKey, true),
                SpeakingMotion = GetBool(values, SpeakingMotionKey, true),
                ConnectionBadge = GetBool(values, ConnectionBadgeKey, true),
                AvatarOpacity = GetDouble(values, AvatarOpacityKey, 1.0, 0.4, 1.0),
                ActivityIndicator = GetBool(values, ActivityIndicatorKey, true),
                ReactiveMotion = GetBool(values, ReactiveMotionKey, true),
                SmoothTransitions = GetBool(values, SmoothTransitionsKey, true),
                CommandPosition = GetString(values, CommandPositionKey, "top"),
                AvatarSide = GetString(values, AvatarSideKey, "right")
            };
        }

        public void Save()
        {
            var values = ApplicationData.Current.LocalSettings.Values;
            values[AvatarSizeKey] = AvatarSize;
            values[MotionIntensityKey] = MotionIntensity;
            values[IdleMotionKey] = IdleMotion;
            values[SpeakingMotionKey] = SpeakingMotion;
            values[ConnectionBadgeKey] = ConnectionBadge;
            values[AvatarOpacityKey] = AvatarOpacity;
            values[ActivityIndicatorKey] = ActivityIndicator;
            values[ReactiveMotionKey] = ReactiveMotion;
            values[SmoothTransitionsKey] = SmoothTransitions;
            values[CommandPositionKey] = CommandPosition;
            values[AvatarSideKey] = AvatarSide;
        }

        public static void Reset()
        {
            var values = ApplicationData.Current.LocalSettings.Values;
            foreach (var key in new[] { AvatarSizeKey, MotionIntensityKey, IdleMotionKey,
                SpeakingMotionKey, ConnectionBadgeKey, AvatarOpacityKey, ActivityIndicatorKey,
                ReactiveMotionKey, SmoothTransitionsKey, CommandPositionKey, AvatarSideKey })
            {
                values.Remove(key);
            }
        }

        private static double GetDouble(IPropertySet values, string key, double fallback, double min, double max)
        {
            object raw;
            if (!values.TryGetValue(key, out raw) || !(raw is double)) return fallback;
            var value = (double)raw;
            return value < min ? min : value > max ? max : value;
        }

        private static bool GetBool(IPropertySet values, string key, bool fallback)
        {
            object raw;
            return values.TryGetValue(key, out raw) && raw is bool ? (bool)raw : fallback;
        }

        private static string GetString(IPropertySet values, string key, string fallback)
        {
            object raw;
            return values.TryGetValue(key, out raw) && raw is string ? (string)raw : fallback;
        }
    }
}
