/**
 * GLTCH Chat ViewModel
 * State management for chat interface
 */

package com.gltch.agent

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import java.util.*

class ChatViewModel : ViewModel() {
    
    private val _messages = MutableStateFlow<List<ChatMessage>>(emptyList())
    val messages: StateFlow<List<ChatMessage>> = _messages.asStateFlow()
    
    private val _mood = MutableStateFlow("neutral")
    val mood: StateFlow<String> = _mood.asStateFlow()
    
    private val _xp = MutableStateFlow(0)
    val xp: StateFlow<Int> = _xp.asStateFlow()
    
    private val _isTalkMode = MutableStateFlow(false)
    val isTalkMode: StateFlow<Boolean> = _isTalkMode.asStateFlow()
    
    private val speechRecognizer = SpeechRecognizerHelper()
    private val ttsHelper = TTSHelper()
    
    init {
        // Collect gateway messages
        viewModelScope.launch {
            GatewayClient.messages.collect { message ->
                when (message) {
                    is GatewayMessage.Response -> {
                        addMessage(ChatMessage(
                            role = MessageRole.ASSISTANT,
                            content = message.text,
                            mood = message.mood
                        ))
                        
                        message.mood?.let { _mood.value = it }
                        _xp.value += message.xpGained
                        
                        // Speak if in talk mode
                        if (_isTalkMode.value) {
                            ttsHelper.speak(message.text)
                        }
                    }
                    
                    is GatewayMessage.Error -> {
                        addMessage(ChatMessage(
                            role = MessageRole.SYSTEM,
                            content = "Error: ${message.error}"
                        ))
                    }
                }
            }
        }
        
        // Setup speech recognition callback
        speechRecognizer.onResult = { text ->
            if (text.isNotBlank()) {
                sendMessage(text)
            }
        }
        
        // Resume listening after TTS completes
        ttsHelper.onComplete = {
            if (_isTalkMode.value) {
                speechRecognizer.startListening()
            }
        }
    }
    
    fun sendMessage(text: String) {
        if (text.isBlank()) return
        
        // Add user message
        addMessage(ChatMessage(
            role = MessageRole.USER,
            content = text
        ))
        
        // Send to gateway
        GatewayClient.sendMessage(text)
    }
    
    fun toggleTalkMode() {
        _isTalkMode.value = !_isTalkMode.value
        
        if (_isTalkMode.value) {
            speechRecognizer.startListening()
        } else {
            speechRecognizer.stopListening()
            ttsHelper.stop()
        }
    }
    
    private fun addMessage(message: ChatMessage) {
        _messages.value = _messages.value + message
    }
    
    override fun onCleared() {
        super.onCleared()
        speechRecognizer.destroy()
        ttsHelper.shutdown()
    }
}

// Data classes
data class ChatMessage(
    val id: String = UUID.randomUUID().toString(),
    val role: MessageRole,
    val content: String,
    val mood: String? = null,
    val timestamp: Date = Date()
)

enum class MessageRole {
    USER,
    ASSISTANT,
    SYSTEM
}

// Placeholder helpers (would need actual implementation)
class SpeechRecognizerHelper {
    var onResult: ((String) -> Unit)? = null
    
    fun startListening() {
        // TODO: Implement with Android SpeechRecognizer
    }
    
    fun stopListening() {
        // TODO: Stop recognition
    }
    
    fun destroy() {
        // TODO: Clean up
    }
}

class TTSHelper {
    var onComplete: (() -> Unit)? = null
    
    fun speak(text: String) {
        // TODO: Implement with Android TextToSpeech
    }
    
    fun stop() {
        // TODO: Stop TTS
    }
    
    fun shutdown() {
        // TODO: Clean up
    }
}
