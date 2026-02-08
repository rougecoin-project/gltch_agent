/**
 * GLTCH App State
 * Central state management for the macOS app
 */

import SwiftUI
import Combine

class AppState: ObservableObject {
    static let shared = AppState()
    
    // Connection state
    @Published var isConnected = false
    @Published var isTyping = false
    @Published var connectionError: String?
    
    // Chat state
    @Published var messages: [ChatMessage] = []
    @Published var currentInput = ""
    
    // Agent state
    @Published var mood: String = "neutral"
    @Published var xp: Int = 0
    
    // UI state
    @Published var showSettings = false
    @Published var isTalkModeActive = false
    
    // Settings
    @Published var settings = AppSettings.load()
    
    // Gateway client
    private var gatewayClient: GatewayClient?
    private var cancellables = Set<AnyCancellable>()
    
    private init() {}
    
    func connectToGateway() {
        guard let url = URL(string: settings.gatewayURL) else {
            connectionError = "Invalid gateway URL"
            return
        }
        
        gatewayClient = GatewayClient(gatewayURL: url)
        gatewayClient?.delegate = self
        gatewayClient?.connect()
    }
    
    func disconnect() {
        gatewayClient?.disconnect()
        isConnected = false
    }
    
    func sendMessage(_ text: String) {
        guard !text.isEmpty else { return }
        
        // Add user message to chat
        let userMessage = ChatMessage(role: .user, content: text)
        messages.append(userMessage)
        currentInput = ""
        
        // Send to gateway
        gatewayClient?.sendMessage(text)
    }
    
    func startTalkMode() {
        isTalkModeActive = true
        TalkModeRuntime.shared.start()
    }
    
    func stopTalkMode() {
        isTalkModeActive = false
        TalkModeRuntime.shared.stop()
    }
}

// MARK: - GatewayClientDelegate

extension AppState: GatewayClientDelegate {
    func gatewayDidConnect(clientId: String, sessionId: String) {
        DispatchQueue.main.async {
            self.isConnected = true
            self.connectionError = nil
        }
    }
    
    func gatewayDidDisconnect(error: Error?) {
        DispatchQueue.main.async {
            self.isConnected = false
            self.connectionError = error?.localizedDescription
        }
    }
    
    func gatewayDidReceiveResponse(_ response: String, mood: String?, xpGained: Int?) {
        DispatchQueue.main.async {
            let message = ChatMessage(role: .assistant, content: response, mood: mood)
            self.messages.append(message)
            
            if let mood = mood {
                self.mood = mood
            }
            if let xp = xpGained {
                self.xp += xp
            }
            
            // Speak if in talk mode
            if self.isTalkModeActive {
                TalkModeRuntime.shared.speak(response)
            }
        }
    }
    
    func gatewayDidReceiveError(_ error: String) {
        DispatchQueue.main.async {
            let message = ChatMessage(role: .system, content: "Error: \(error)")
            self.messages.append(message)
        }
    }
    
    func gatewayTypingStateChanged(isTyping: Bool) {
        DispatchQueue.main.async {
            self.isTyping = isTyping
        }
    }
}

// MARK: - Models

struct ChatMessage: Identifiable {
    let id = UUID()
    let role: MessageRole
    let content: String
    let mood: String?
    let timestamp: Date
    
    init(role: MessageRole, content: String, mood: String? = nil) {
        self.role = role
        self.content = content
        self.mood = mood
        self.timestamp = Date()
    }
}

enum MessageRole: String {
    case user
    case assistant
    case system
}

struct AppSettings: Codable {
    var gatewayURL: String = "ws://127.0.0.1:18889"
    var voiceWakeEnabled: Bool = false
    var wakeWords: [String] = ["gltch", "hey gltch"]
    var ttsEnabled: Bool = false
    var ttsVoice: String = "en-US-AriaNeural"
    var ttsSpeed: Double = 1.0
    var darkMode: Bool = true
    
    static func load() -> AppSettings {
        if let data = UserDefaults.standard.data(forKey: "appSettings"),
           let settings = try? JSONDecoder().decode(AppSettings.self, from: data) {
            return settings
        }
        return AppSettings()
    }
    
    func save() {
        if let data = try? JSONEncoder().encode(self) {
            UserDefaults.standard.set(data, forKey: "appSettings")
        }
    }
}
