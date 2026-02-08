/**
 * GLTCH Gateway Client for Android
 * WebSocket communication with the gateway
 */

package com.gltch.agent

import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import okhttp3.*
import org.json.JSONObject
import java.util.concurrent.TimeUnit

object GatewayClient {
    
    private var webSocket: WebSocket? = null
    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()
    
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    
    // State flows
    private val _connectionState = MutableStateFlow<ConnectionState>(ConnectionState.Disconnected)
    val connectionState: StateFlow<ConnectionState> = _connectionState.asStateFlow()
    
    private val _messages = MutableSharedFlow<GatewayMessage>()
    val messages: SharedFlow<GatewayMessage> = _messages.asSharedFlow()
    
    private val _isTyping = MutableStateFlow(false)
    val isTyping: StateFlow<Boolean> = _isTyping.asStateFlow()
    
    var clientId: String? = null
        private set
    var sessionId: String? = null
        private set
    
    private var gatewayUrl = "ws://10.0.2.2:18889" // Default for Android emulator
    
    fun initialize() {
        // Load settings
        val prefs = GLTCHApplication.context.getSharedPreferences("gltch", 0)
        gatewayUrl = prefs.getString("gateway_url", gatewayUrl) ?: gatewayUrl
    }
    
    fun setGatewayUrl(url: String) {
        gatewayUrl = url
        GLTCHApplication.context.getSharedPreferences("gltch", 0)
            .edit()
            .putString("gateway_url", url)
            .apply()
    }
    
    fun connect() {
        if (_connectionState.value is ConnectionState.Connected) return
        
        _connectionState.value = ConnectionState.Connecting
        
        val request = Request.Builder()
            .url(gatewayUrl)
            .build()
        
        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                // Wait for 'connected' message
            }
            
            override fun onMessage(webSocket: WebSocket, text: String) {
                handleMessage(text)
            }
            
            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                _connectionState.value = ConnectionState.Error(t.message ?: "Connection failed")
                scheduleReconnect()
            }
            
            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                _connectionState.value = ConnectionState.Disconnected
            }
        })
    }
    
    fun disconnect() {
        webSocket?.close(1000, "User disconnect")
        webSocket = null
        _connectionState.value = ConnectionState.Disconnected
    }
    
    fun sendMessage(text: String) {
        val json = JSONObject().apply {
            put("type", "chat")
            put("text", text)
            sessionId?.let { put("sessionId", it) }
        }
        webSocket?.send(json.toString())
    }
    
    fun sendPing() {
        val json = JSONObject().apply {
            put("type", "ping")
        }
        webSocket?.send(json.toString())
    }
    
    private fun handleMessage(text: String) {
        try {
            val json = JSONObject(text)
            val type = json.optString("type")
            
            when (type) {
                "connected" -> {
                    clientId = json.optString("clientId")
                    sessionId = json.optString("sessionId")
                    _connectionState.value = ConnectionState.Connected(clientId!!, sessionId!!)
                }
                
                "response" -> {
                    val message = GatewayMessage.Response(
                        text = json.optString("response"),
                        mood = json.optString("mood", null),
                        xpGained = json.optInt("xp_gained", 0)
                    )
                    scope.launch {
                        _messages.emit(message)
                    }
                    _isTyping.value = false
                }
                
                "error" -> {
                    val message = GatewayMessage.Error(
                        error = json.optString("error")
                    )
                    scope.launch {
                        _messages.emit(message)
                    }
                    _isTyping.value = false
                }
                
                "typing" -> {
                    _isTyping.value = json.optBoolean("typing", false)
                }
                
                "pong" -> {
                    // Ping response received
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
    
    private var reconnectAttempts = 0
    private val maxReconnectAttempts = 5
    
    private fun scheduleReconnect() {
        if (reconnectAttempts >= maxReconnectAttempts) {
            return
        }
        
        reconnectAttempts++
        val delay = reconnectAttempts * 2000L
        
        scope.launch {
            delay(delay)
            connect()
        }
    }
}

// State classes
sealed class ConnectionState {
    object Disconnected : ConnectionState()
    object Connecting : ConnectionState()
    data class Connected(val clientId: String, val sessionId: String) : ConnectionState()
    data class Error(val message: String) : ConnectionState()
}

sealed class GatewayMessage {
    data class Response(
        val text: String,
        val mood: String?,
        val xpGained: Int
    ) : GatewayMessage()
    
    data class Error(
        val error: String
    ) : GatewayMessage()
}
