/**
 * GLTCH Android Application
 */

package com.gltch.agent

import android.app.Application
import android.content.Context

class GLTCHApplication : Application() {
    
    companion object {
        lateinit var instance: GLTCHApplication
            private set
        
        val context: Context
            get() = instance.applicationContext
    }
    
    override fun onCreate() {
        super.onCreate()
        instance = this
        
        // Initialize gateway client
        GatewayClient.initialize()
    }
}
