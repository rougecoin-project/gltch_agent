/**
 * GLTCH macOS App
 * Native macOS application for GLTCH agent
 */

import SwiftUI

@main
struct GLTCHApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    @StateObject private var appState = AppState.shared
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(appState)
                .frame(minWidth: 400, minHeight: 500)
        }
        .windowStyle(.hiddenTitleBar)
        .commands {
            CommandGroup(after: .appSettings) {
                Button("Preferences...") {
                    appState.showSettings = true
                }
                .keyboardShortcut(",", modifiers: .command)
            }
        }
        
        // Menu bar extra
        MenuBarExtra("GLTCH", systemImage: "message.circle.fill") {
            MenuBarView()
                .environmentObject(appState)
        }
        .menuBarExtraStyle(.window)
        
        // Settings window
        Settings {
            SettingsView()
                .environmentObject(appState)
        }
    }
}

class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        // Initialize voice wake if enabled
        if AppState.shared.settings.voiceWakeEnabled {
            VoiceWakeRuntime.shared.start()
        }
        
        // Connect to gateway
        AppState.shared.connectToGateway()
    }
    
    func applicationWillTerminate(_ notification: Notification) {
        VoiceWakeRuntime.shared.stop()
        AppState.shared.disconnect()
    }
}
