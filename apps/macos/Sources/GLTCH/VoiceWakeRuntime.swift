/**
 * GLTCH Voice Wake Runtime
 * Wake word detection using SFSpeechRecognizer
 */

import Foundation
import Speech
import AVFoundation

class VoiceWakeRuntime: NSObject, ObservableObject {
    static let shared = VoiceWakeRuntime()
    
    @Published var isListening = false
    @Published var lastWakeWord: String?
    @Published var permissionGranted = false
    
    private var speechRecognizer: SFSpeechRecognizer?
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private let audioEngine = AVAudioEngine()
    
    private var wakeWords: [String] = ["gltch", "hey gltch", "computer"]
    private var onWakeDetected: ((String) -> Void)?
    
    private override init() {
        super.init()
        speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
        speechRecognizer?.delegate = self
    }
    
    func requestPermission(completion: @escaping (Bool) -> Void) {
        SFSpeechRecognizer.requestAuthorization { [weak self] status in
            DispatchQueue.main.async {
                switch status {
                case .authorized:
                    self?.permissionGranted = true
                    completion(true)
                default:
                    self?.permissionGranted = false
                    completion(false)
                }
            }
        }
    }
    
    func setWakeWords(_ words: [String]) {
        wakeWords = words.map { $0.lowercased() }
    }
    
    func onWakeDetected(_ handler: @escaping (String) -> Void) {
        onWakeDetected = handler
    }
    
    func start() {
        guard permissionGranted else {
            requestPermission { [weak self] granted in
                if granted {
                    self?.startListening()
                }
            }
            return
        }
        
        startListening()
    }
    
    func stop() {
        stopListening()
    }
    
    private func startListening() {
        guard !isListening else { return }
        guard let speechRecognizer = speechRecognizer, speechRecognizer.isAvailable else {
            print("Speech recognizer not available")
            return
        }
        
        do {
            // Cancel any existing task
            recognitionTask?.cancel()
            recognitionTask = nil
            
            // Configure audio session
            let audioSession = AVAudioSession.sharedInstance()
            try audioSession.setCategory(.record, mode: .measurement, options: .duckOthers)
            try audioSession.setActive(true, options: .notifyOthersOnDeactivation)
            
            // Create recognition request
            recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
            recognitionRequest?.shouldReportPartialResults = true
            
            // Install audio tap
            let inputNode = audioEngine.inputNode
            let recordingFormat = inputNode.outputFormat(forBus: 0)
            
            inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { [weak self] buffer, _ in
                self?.recognitionRequest?.append(buffer)
            }
            
            // Start recognition
            recognitionTask = speechRecognizer.recognitionTask(with: recognitionRequest!) { [weak self] result, error in
                guard let self = self else { return }
                
                if let result = result {
                    let transcription = result.bestTranscription.formattedString.lowercased()
                    
                    // Check for wake words
                    for wakeWord in self.wakeWords {
                        if transcription.contains(wakeWord) {
                            DispatchQueue.main.async {
                                self.lastWakeWord = wakeWord
                                self.onWakeDetected?(transcription)
                            }
                            break
                        }
                    }
                }
                
                if error != nil || (result?.isFinal ?? false) {
                    // Restart listening
                    self.stopListening()
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                        if self.isListening {
                            self.startListening()
                        }
                    }
                }
            }
            
            // Start audio engine
            audioEngine.prepare()
            try audioEngine.start()
            
            DispatchQueue.main.async {
                self.isListening = true
            }
            
        } catch {
            print("Voice wake error: \(error)")
            stopListening()
        }
    }
    
    private func stopListening() {
        audioEngine.stop()
        audioEngine.inputNode.removeTap(onBus: 0)
        recognitionRequest?.endAudio()
        recognitionRequest = nil
        recognitionTask?.cancel()
        recognitionTask = nil
        
        DispatchQueue.main.async {
            self.isListening = false
        }
    }
}

extension VoiceWakeRuntime: SFSpeechRecognizerDelegate {
    func speechRecognizer(_ speechRecognizer: SFSpeechRecognizer, availabilityDidChange available: Bool) {
        if !available {
            stopListening()
        }
    }
}
