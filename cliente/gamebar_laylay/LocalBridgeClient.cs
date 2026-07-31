using System;
using System.IO;
using System.Runtime.InteropServices.WindowsRuntime;
using System.Threading;
using System.Threading.Tasks;
using Windows.Data.Json;
using Windows.Networking;
using Windows.Networking.Sockets;

namespace LaylayGameBar
{
    public sealed class CommandBarState
    {
        public bool Visible { get; set; }
        public string Text { get; set; } = "";
    }

    public sealed class WidgetState
    {
        public string Emotion { get; set; } = "calma";
        public bool Speaking { get; set; }
        public string Activity { get; set; } = "idle";
        public double Intensity { get; set; } = 0.33;
        public string ReactionId { get; set; } = "";
        public CommandBarState CommandBar { get; set; } = new CommandBarState();
    }

    public sealed class LocalBridgeClient : IDisposable
    {
        private readonly int _port;
        private readonly Action<WidgetState> _onState;
        private readonly Action<bool> _onConnection;
        private readonly CancellationTokenSource _cancellation = new CancellationTokenSource();
        private Task _worker;
        private volatile bool _pinned;

        public LocalBridgeClient(int port, Action<WidgetState> onState, Action<bool> onConnection)
        {
            _port = port;
            _onState = onState;
            _onConnection = onConnection;
        }

        public void Start()
        {
            if (_worker == null)
            {
                _worker = RunAsync(_cancellation.Token);
            }
        }

        public void SetPinned(bool pinned)
        {
            _pinned = pinned;
        }

        private string StatusMessage(string type)
        {
            return "{\"type\":\"" + type + "\",\"version\":1,\"pinned\":"
                + (_pinned ? "true" : "false") + "}";
        }

        private async Task RunAsync(CancellationToken token)
        {
            while (!token.IsCancellationRequested)
            {
                try
                {
                    using (var socket = new StreamSocket())
                    {
                        await socket.ConnectAsync(
                            new HostName("127.0.0.1"),
                            _port.ToString(),
                            SocketProtectionLevel.PlainSocket);
                        _onConnection(true);
                        using (var reader = new StreamReader(socket.InputStream.AsStreamForRead()))
                        using (var writer = new StreamWriter(socket.OutputStream.AsStreamForWrite()) { AutoFlush = true })
                        {
                            await writer.WriteLineAsync(StatusMessage("ready"));
                            var heartbeat = SendHeartbeatsAsync(writer, token);
                            while (!token.IsCancellationRequested)
                            {
                                var line = await reader.ReadLineAsync();
                                if (line == null)
                                {
                                    break;
                                }
                                WidgetState state;
                                if (TryParseState(line, out state))
                                {
                                    _onState(state);
                                }
                            }
                            await heartbeat;
                        }
                    }
                }
                catch (Exception) when (!token.IsCancellationRequested)
                {
                    _onConnection(false);
                }
                if (!token.IsCancellationRequested)
                {
                    await Task.Delay(1200);
                }
            }
        }

        private async Task SendHeartbeatsAsync(StreamWriter writer, CancellationToken token)
        {
            try
            {
                while (!token.IsCancellationRequested)
                {
                    await Task.Delay(2000, token);
                    await writer.WriteLineAsync(StatusMessage("heartbeat"));
                }
            }
            catch (OperationCanceledException) { }
            catch (IOException) { }
            catch (ObjectDisposedException) { }
        }

        private static bool TryParseState(string line, out WidgetState state)
        {
            state = null;
            JsonObject root;
            if (!JsonObject.TryParse(line, out root) || root.GetNamedString("type", "") != "state")
            {
                return false;
            }
            var command = root.GetNamedObject("command_bar", new JsonObject());
            state = new WidgetState
            {
                Emotion = root.GetNamedString("emotion", "calma"),
                Speaking = root.GetNamedBoolean("speaking", false),
                Activity = root.GetNamedString("activity", "idle"),
                Intensity = root.GetNamedNumber("intensity", 0.33),
                ReactionId = root.GetNamedString("reaction_id", ""),
                CommandBar = new CommandBarState
                {
                    Visible = command.GetNamedBoolean("visible", false),
                    Text = command.GetNamedString("text", "")
                }
            };
            return true;
        }

        public void Dispose()
        {
            _cancellation.Cancel();
            _onConnection(false);
        }
    }
}
