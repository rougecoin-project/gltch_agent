/**
 * GLTCH Content View
 * Main chat interface for macOS app
 */

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var appState: AppState
    @State private var inputText = ""
    @FocusState private var isInputFocused: Bool
    
    var body: some View {
        VStack(spacing: 0) {
            // Header
            HeaderView()
            
            Divider()
            
            // Chat messages
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 12) {
                        ForEach(appState.messages) { message in
                            MessageBubble(message: message)
                        }
                        
                        if appState.isTyping {
                            TypingIndicator()
                        }
                    }
                    .padding()
                }
                .onChange(of: appState.messages.count) { _ in
                    if let last = appState.messages.last {
                        withAnimation {
                            proxy.scrollTo(last.id, anchor: .bottom)
                        }
                    }
                }
            }
            
            Divider()
            
            // Input area
            InputArea(text: $inputText, isFocused: $isInputFocused) {
                sendMessage()
            }
        }
        .background(Color("Background"))
        .onAppear {
            isInputFocused = true
        }
    }
    
    private func sendMessage() {
        let text = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        
        appState.sendMessage(text)
        inputText = ""
    }
}

// MARK: - Header View

struct HeaderView: View {
    @EnvironmentObject var appState: AppState
    
    var body: some View {
        HStack {
            // Connection status
            Circle()
                .fill(appState.isConnected ? Color.green : Color.red)
                .frame(width: 8, height: 8)
            
            Text("GLTCH")
                .font(.headline)
                .fontWeight(.bold)
            
            Spacer()
            
            // Mood indicator
            Text(moodEmoji)
                .font(.title2)
            
            // XP display
            Text("\(appState.xp) XP")
                .font(.caption)
                .foregroundColor(.secondary)
            
            // Talk mode toggle
            Button(action: {
                if appState.isTalkModeActive {
                    appState.stopTalkMode()
                } else {
                    appState.startTalkMode()
                }
            }) {
                Image(systemName: appState.isTalkModeActive ? "mic.fill" : "mic")
                    .foregroundColor(appState.isTalkModeActive ? .green : .primary)
            }
            .buttonStyle(.plain)
            .help(appState.isTalkModeActive ? "Stop Talk Mode" : "Start Talk Mode")
        }
        .padding(.horizontal)
        .padding(.vertical, 8)
    }
    
    var moodEmoji: String {
        switch appState.mood {
        case "happy": return "😊"
        case "excited": return "🎉"
        case "curious": return "🤔"
        case "helpful": return "🤝"
        case "mischievous": return "😈"
        case "creative": return "🎨"
        case "focused": return "🎯"
        default: return "🤖"
        }
    }
}

// MARK: - Message Bubble

struct MessageBubble: View {
    let message: ChatMessage
    
    var body: some View {
        HStack {
            if message.role == .user {
                Spacer()
            }
            
            VStack(alignment: message.role == .user ? .trailing : .leading, spacing: 4) {
                Text(message.content)
                    .padding(12)
                    .background(bubbleColor)
                    .foregroundColor(textColor)
                    .cornerRadius(16)
                
                Text(timeString)
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            .frame(maxWidth: 300, alignment: message.role == .user ? .trailing : .leading)
            
            if message.role != .user {
                Spacer()
            }
        }
    }
    
    var bubbleColor: Color {
        switch message.role {
        case .user:
            return Color.accentColor
        case .assistant:
            return Color("BubbleAssistant")
        case .system:
            return Color.gray.opacity(0.3)
        }
    }
    
    var textColor: Color {
        switch message.role {
        case .user:
            return .white
        case .assistant, .system:
            return .primary
        }
    }
    
    var timeString: String {
        let formatter = DateFormatter()
        formatter.timeStyle = .short
        return formatter.string(from: message.timestamp)
    }
}

// MARK: - Typing Indicator

struct TypingIndicator: View {
    @State private var animating = false
    
    var body: some View {
        HStack {
            HStack(spacing: 4) {
                ForEach(0..<3) { index in
                    Circle()
                        .fill(Color.gray)
                        .frame(width: 8, height: 8)
                        .scaleEffect(animating ? 1.0 : 0.5)
                        .animation(
                            Animation.easeInOut(duration: 0.6)
                                .repeatForever()
                                .delay(Double(index) * 0.2),
                            value: animating
                        )
                }
            }
            .padding(12)
            .background(Color("BubbleAssistant"))
            .cornerRadius(16)
            
            Spacer()
        }
        .onAppear {
            animating = true
        }
    }
}

// MARK: - Input Area

struct InputArea: View {
    @Binding var text: String
    var isFocused: FocusState<Bool>.Binding
    let onSend: () -> Void
    
    var body: some View {
        HStack(spacing: 12) {
            TextField("Message GLTCH...", text: $text)
                .textFieldStyle(.plain)
                .padding(10)
                .background(Color("InputBackground"))
                .cornerRadius(20)
                .focused(isFocused)
                .onSubmit(onSend)
            
            Button(action: onSend) {
                Image(systemName: "arrow.up.circle.fill")
                    .font(.title2)
                    .foregroundColor(text.isEmpty ? .gray : .accentColor)
            }
            .buttonStyle(.plain)
            .disabled(text.isEmpty)
        }
        .padding()
    }
}

// MARK: - Menu Bar View

struct MenuBarView: View {
    @EnvironmentObject var appState: AppState
    @State private var quickInput = ""
    
    var body: some View {
        VStack(spacing: 12) {
            // Quick input
            HStack {
                TextField("Quick message...", text: $quickInput)
                    .textFieldStyle(.roundedBorder)
                    .onSubmit {
                        if !quickInput.isEmpty {
                            appState.sendMessage(quickInput)
                            quickInput = ""
                        }
                    }
                
                Button("Send") {
                    if !quickInput.isEmpty {
                        appState.sendMessage(quickInput)
                        quickInput = ""
                    }
                }
                .disabled(quickInput.isEmpty)
            }
            
            Divider()
            
            // Last response
            if let lastMessage = appState.messages.last(where: { $0.role == .assistant }) {
                Text(lastMessage.content)
                    .font(.caption)
                    .lineLimit(3)
                    .foregroundColor(.secondary)
            }
            
            Divider()
            
            // Quick actions
            HStack {
                Button("Open Window") {
                    NSApp.activate(ignoringOtherApps: true)
                }
                
                Spacer()
                
                Button("Quit") {
                    NSApp.terminate(nil)
                }
            }
        }
        .padding()
        .frame(width: 300)
    }
}

// MARK: - Settings View

struct SettingsView: View {
    @EnvironmentObject var appState: AppState
    
    var body: some View {
        TabView {
            GeneralSettingsView()
                .tabItem {
                    Label("General", systemImage: "gear")
                }
            
            VoiceSettingsView()
                .tabItem {
                    Label("Voice", systemImage: "mic")
                }
            
            ConnectionSettingsView()
                .tabItem {
                    Label("Connection", systemImage: "network")
                }
        }
        .frame(width: 450, height: 300)
    }
}

struct GeneralSettingsView: View {
    @EnvironmentObject var appState: AppState
    
    var body: some View {
        Form {
            Toggle("Dark Mode", isOn: $appState.settings.darkMode)
        }
        .padding()
    }
}

struct VoiceSettingsView: View {
    @EnvironmentObject var appState: AppState
    
    var body: some View {
        Form {
            Toggle("Voice Wake", isOn: $appState.settings.voiceWakeEnabled)
            
            TextField("Wake Words", text: Binding(
                get: { appState.settings.wakeWords.joined(separator: ", ") },
                set: { appState.settings.wakeWords = $0.split(separator: ",").map { String($0).trimmingCharacters(in: .whitespaces) } }
            ))
            
            Toggle("Text-to-Speech", isOn: $appState.settings.ttsEnabled)
            
            Picker("TTS Voice", selection: $appState.settings.ttsVoice) {
                Text("Aria").tag("en-US-AriaNeural")
                Text("Guy").tag("en-US-GuyNeural")
                Text("Jenny").tag("en-US-JennyNeural")
            }
            
            Slider(value: $appState.settings.ttsSpeed, in: 0.5...2.0, step: 0.1) {
                Text("Speed: \(appState.settings.ttsSpeed, specifier: "%.1f")x")
            }
        }
        .padding()
    }
}

struct ConnectionSettingsView: View {
    @EnvironmentObject var appState: AppState
    
    var body: some View {
        Form {
            TextField("Gateway URL", text: $appState.settings.gatewayURL)
            
            HStack {
                Text("Status:")
                Text(appState.isConnected ? "Connected" : "Disconnected")
                    .foregroundColor(appState.isConnected ? .green : .red)
            }
            
            Button(appState.isConnected ? "Reconnect" : "Connect") {
                appState.disconnect()
                appState.connectToGateway()
            }
        }
        .padding()
    }
}

#Preview {
    ContentView()
        .environmentObject(AppState.shared)
}
