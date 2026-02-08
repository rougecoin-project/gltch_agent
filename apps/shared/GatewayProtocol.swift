/**
 * GLTCH Gateway Protocol
 * Shared Swift code for gateway communication
 * 
 * Used by macOS and iOS apps to communicate with the GLTCH gateway
 * via WebSocket using JSON-RPC 2.0
 */

import Foundation

// MARK: - JSON-RPC Types

public struct JSONRPCRequest: Codable {
    public let jsonrpc: String
    public let method: String
    public let params: [String: AnyCodable]?
    public let id: Int
    
    public init(method: String, params: [String: AnyCodable]? = nil, id: Int) {
        self.jsonrpc = "2.0"
        self.method = method
        self.params = params
        self.id = id
    }
}

public struct JSONRPCResponse: Codable {
    public let jsonrpc: String
    public let result: AnyCodable?
    public let error: JSONRPCError?
    public let id: Int?
}

public struct JSONRPCError: Codable {
    public let code: Int
    public let message: String
    public let data: AnyCodable?
}

// MARK: - Gateway Messages

public enum GatewayMessageType: String, Codable {
    case connected
    case response
    case error
    case typing
    case pong
    case status
}

public struct GatewayMessage: Codable {
    public let type: GatewayMessageType
    public let clientId: String?
    public let sessionId: String?
    public let response: String?
    public let mood: String?
    public let xpGained: Int?
    public let error: String?
    public let typing: Bool?
    public let timestamp: Int?
    
    enum CodingKeys: String, CodingKey {
        case type, clientId, sessionId, response, mood, error, typing, timestamp
        case xpGained = "xp_gained"
    }
}

public struct ChatRequest: Codable {
    public let type: String
    public let text: String
    public let sessionId: String?
    
    public init(text: String, sessionId: String? = nil) {
        self.type = "chat"
        self.text = text
        self.sessionId = sessionId
    }
}

// MARK: - Gateway Client

public protocol GatewayClientDelegate: AnyObject {
    func gatewayDidConnect(clientId: String, sessionId: String)
    func gatewayDidDisconnect(error: Error?)
    func gatewayDidReceiveResponse(_ response: String, mood: String?, xpGained: Int?)
    func gatewayDidReceiveError(_ error: String)
    func gatewayTypingStateChanged(isTyping: Bool)
}

public class GatewayClient: NSObject {
    public weak var delegate: GatewayClientDelegate?
    
    private var webSocket: URLSessionWebSocketTask?
    private var session: URLSession?
    private var gatewayURL: URL
    private var isConnected = false
    private var clientId: String?
    private var sessionId: String?
    private var reconnectAttempts = 0
    private let maxReconnectAttempts = 5
    
    public init(gatewayURL: URL) {
        self.gatewayURL = gatewayURL
        super.init()
        self.session = URLSession(configuration: .default, delegate: self, delegateQueue: nil)
    }
    
    public func connect() {
        guard !isConnected else { return }
        
        webSocket = session?.webSocketTask(with: gatewayURL)
        webSocket?.resume()
        
        receiveMessage()
    }
    
    public func disconnect() {
        webSocket?.cancel(with: .normalClosure, reason: nil)
        webSocket = nil
        isConnected = false
        clientId = nil
    }
    
    public func sendMessage(_ text: String) {
        let request = ChatRequest(text: text, sessionId: sessionId)
        
        guard let data = try? JSONEncoder().encode(request),
              let jsonString = String(data: data, encoding: .utf8) else {
            return
        }
        
        let message = URLSessionWebSocketTask.Message.string(jsonString)
        webSocket?.send(message) { [weak self] error in
            if let error = error {
                self?.delegate?.gatewayDidReceiveError("Send failed: \(error.localizedDescription)")
            }
        }
    }
    
    public func sendPing() {
        let pingMessage = ["type": "ping"]
        
        guard let data = try? JSONSerialization.data(withJSONObject: pingMessage),
              let jsonString = String(data: data, encoding: .utf8) else {
            return
        }
        
        let message = URLSessionWebSocketTask.Message.string(jsonString)
        webSocket?.send(message) { _ in }
    }
    
    private func receiveMessage() {
        webSocket?.receive { [weak self] result in
            switch result {
            case .success(let message):
                switch message {
                case .string(let text):
                    self?.handleMessage(text)
                case .data(let data):
                    if let text = String(data: data, encoding: .utf8) {
                        self?.handleMessage(text)
                    }
                @unknown default:
                    break
                }
                // Continue receiving
                self?.receiveMessage()
                
            case .failure(let error):
                self?.handleDisconnection(error: error)
            }
        }
    }
    
    private func handleMessage(_ text: String) {
        guard let data = text.data(using: .utf8),
              let message = try? JSONDecoder().decode(GatewayMessage.self, from: data) else {
            return
        }
        
        DispatchQueue.main.async { [weak self] in
            switch message.type {
            case .connected:
                self?.isConnected = true
                self?.clientId = message.clientId
                self?.sessionId = message.sessionId
                self?.reconnectAttempts = 0
                self?.delegate?.gatewayDidConnect(
                    clientId: message.clientId ?? "",
                    sessionId: message.sessionId ?? ""
                )
                
            case .response:
                if let response = message.response {
                    self?.delegate?.gatewayDidReceiveResponse(
                        response,
                        mood: message.mood,
                        xpGained: message.xpGained
                    )
                }
                
            case .error:
                self?.delegate?.gatewayDidReceiveError(message.error ?? "Unknown error")
                
            case .typing:
                self?.delegate?.gatewayTypingStateChanged(isTyping: message.typing ?? false)
                
            case .pong, .status:
                break
            }
        }
    }
    
    private func handleDisconnection(error: Error) {
        isConnected = false
        
        DispatchQueue.main.async { [weak self] in
            self?.delegate?.gatewayDidDisconnect(error: error)
        }
        
        // Attempt reconnection
        if reconnectAttempts < maxReconnectAttempts {
            reconnectAttempts += 1
            let delay = Double(reconnectAttempts) * 2.0
            
            DispatchQueue.main.asyncAfter(deadline: .now() + delay) { [weak self] in
                self?.connect()
            }
        }
    }
}

extension GatewayClient: URLSessionWebSocketDelegate {
    public func urlSession(
        _ session: URLSession,
        webSocketTask: URLSessionWebSocketTask,
        didOpenWithProtocol protocol: String?
    ) {
        // Connection opened, waiting for 'connected' message
    }
    
    public func urlSession(
        _ session: URLSession,
        webSocketTask: URLSessionWebSocketTask,
        didCloseWith closeCode: URLSessionWebSocketTask.CloseCode,
        reason: Data?
    ) {
        handleDisconnection(error: NSError(
            domain: "GatewayClient",
            code: Int(closeCode.rawValue),
            userInfo: nil
        ))
    }
}

// MARK: - AnyCodable Helper

public struct AnyCodable: Codable {
    public let value: Any
    
    public init(_ value: Any) {
        self.value = value
    }
    
    public init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        
        if let bool = try? container.decode(Bool.self) {
            value = bool
        } else if let int = try? container.decode(Int.self) {
            value = int
        } else if let double = try? container.decode(Double.self) {
            value = double
        } else if let string = try? container.decode(String.self) {
            value = string
        } else if let array = try? container.decode([AnyCodable].self) {
            value = array.map { $0.value }
        } else if let dictionary = try? container.decode([String: AnyCodable].self) {
            value = dictionary.mapValues { $0.value }
        } else {
            value = NSNull()
        }
    }
    
    public func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        
        switch value {
        case let bool as Bool:
            try container.encode(bool)
        case let int as Int:
            try container.encode(int)
        case let double as Double:
            try container.encode(double)
        case let string as String:
            try container.encode(string)
        case let array as [Any]:
            try container.encode(array.map { AnyCodable($0) })
        case let dictionary as [String: Any]:
            try container.encode(dictionary.mapValues { AnyCodable($0) })
        default:
            try container.encodeNil()
        }
    }
}
