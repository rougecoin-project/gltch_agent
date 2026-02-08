/**
 * GLTCH Main Activity
 * Jetpack Compose chat interface
 */

package com.gltch.agent

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.MicOff
import androidx.compose.material.icons.filled.Send
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.gltch.agent.ui.theme.GLTCHTheme
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.*

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Connect to gateway
        GatewayClient.connect()
        
        setContent {
            GLTCHTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    ChatScreen()
                }
            }
        }
    }
    
    override fun onDestroy() {
        super.onDestroy()
        GatewayClient.disconnect()
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatScreen(viewModel: ChatViewModel = viewModel()) {
    val messages by viewModel.messages.collectAsState()
    val connectionState by GatewayClient.connectionState.collectAsState()
    val isTyping by GatewayClient.isTyping.collectAsState()
    val isTalkMode by viewModel.isTalkMode.collectAsState()
    
    var inputText by remember { mutableStateOf("") }
    val listState = rememberLazyListState()
    val scope = rememberCoroutineScope()
    
    // Scroll to bottom when new message arrives
    LaunchedEffect(messages.size) {
        if (messages.isNotEmpty()) {
            listState.animateScrollToItem(messages.size - 1)
        }
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        // Connection indicator
                        Box(
                            modifier = Modifier
                                .size(8.dp)
                                .padding(end = 8.dp)
                        ) {
                            val color = when (connectionState) {
                                is ConnectionState.Connected -> Color.Green
                                is ConnectionState.Connecting -> Color.Yellow
                                else -> Color.Red
                            }
                            Surface(
                                shape = RoundedCornerShape(4.dp),
                                color = color,
                                modifier = Modifier.fillMaxSize()
                            ) {}
                        }
                        
                        Spacer(modifier = Modifier.width(8.dp))
                        
                        Text(
                            text = "GLTCH",
                            fontWeight = FontWeight.Bold
                        )
                    }
                },
                actions = {
                    // Talk mode toggle
                    IconButton(onClick = { viewModel.toggleTalkMode() }) {
                        Icon(
                            imageVector = if (isTalkMode) Icons.Default.Mic else Icons.Default.MicOff,
                            contentDescription = "Talk Mode",
                            tint = if (isTalkMode) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface
                        )
                    }
                    
                    // Settings
                    IconButton(onClick = { /* TODO: Open settings */ }) {
                        Icon(Icons.Default.Settings, contentDescription = "Settings")
                    }
                }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            // Messages list
            LazyColumn(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp),
                state = listState
            ) {
                items(messages) { message ->
                    MessageBubble(message = message)
                    Spacer(modifier = Modifier.height(8.dp))
                }
                
                if (isTyping) {
                    item {
                        TypingIndicator()
                    }
                }
            }
            
            // Input area
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                OutlinedTextField(
                    value = inputText,
                    onValueChange = { inputText = it },
                    modifier = Modifier.weight(1f),
                    placeholder = { Text("Message GLTCH...") },
                    shape = RoundedCornerShape(24.dp),
                    singleLine = true
                )
                
                Spacer(modifier = Modifier.width(8.dp))
                
                FilledIconButton(
                    onClick = {
                        if (inputText.isNotBlank()) {
                            viewModel.sendMessage(inputText)
                            inputText = ""
                        }
                    },
                    enabled = inputText.isNotBlank()
                ) {
                    Icon(Icons.Default.Send, contentDescription = "Send")
                }
            }
        }
    }
}

@Composable
fun MessageBubble(message: ChatMessage) {
    val isUser = message.role == MessageRole.USER
    
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = if (isUser) Arrangement.End else Arrangement.Start
    ) {
        Column(
            horizontalAlignment = if (isUser) Alignment.End else Alignment.Start,
            modifier = Modifier.widthIn(max = 280.dp)
        ) {
            Surface(
                shape = RoundedCornerShape(
                    topStart = 16.dp,
                    topEnd = 16.dp,
                    bottomStart = if (isUser) 16.dp else 4.dp,
                    bottomEnd = if (isUser) 4.dp else 16.dp
                ),
                color = if (isUser) 
                    MaterialTheme.colorScheme.primary 
                else 
                    MaterialTheme.colorScheme.surfaceVariant
            ) {
                Text(
                    text = message.content,
                    modifier = Modifier.padding(12.dp),
                    color = if (isUser) 
                        MaterialTheme.colorScheme.onPrimary 
                    else 
                        MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            
            Text(
                text = formatTime(message.timestamp),
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f),
                modifier = Modifier.padding(top = 4.dp, start = 4.dp, end = 4.dp)
            )
        }
    }
}

@Composable
fun TypingIndicator() {
    Row(
        modifier = Modifier.padding(8.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        repeat(3) { index ->
            val alpha = remember { androidx.compose.animation.core.Animatable(0.3f) }
            
            LaunchedEffect(Unit) {
                while (true) {
                    alpha.animateTo(
                        targetValue = 1f,
                        animationSpec = androidx.compose.animation.core.tween(
                            durationMillis = 300,
                            delayMillis = index * 100
                        )
                    )
                    alpha.animateTo(
                        targetValue = 0.3f,
                        animationSpec = androidx.compose.animation.core.tween(
                            durationMillis = 300
                        )
                    )
                }
            }
            
            Surface(
                shape = RoundedCornerShape(4.dp),
                color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = alpha.value),
                modifier = Modifier
                    .size(8.dp)
                    .padding(horizontal = 2.dp)
            ) {}
        }
    }
}

private fun formatTime(date: Date): String {
    val format = SimpleDateFormat("HH:mm", Locale.getDefault())
    return format.format(date)
}
