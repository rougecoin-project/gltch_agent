/**
 * GLTCH Talk Mode Runtime
 * Continuous conversation with TTS using AVSpeechSynthesizer
 */

import Foundation
import Speech
import AVFoundation

class TalkModeRuntime: NSObject, ObservableObject {
    static let shared = TalkModeRuntime()
    
    @Published var isActive = false
    @Published var isListening = false
    @Published var isSpeaking = false
    @Published var currentTranscription = ""
    
    private let synthesizer = AVSpeechSynthesizer()
    private var speechRecognizer: SFSpeechRecognizer?
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private let audioEngine = AVAudioEngine()
    
    private var silenceTimer: Timer?
    private var silenceThreshold: TimeInterval = 2.0
    private var lastSpeechTime = Date()
    
    private var onTranscriptionComplete: ((String) -> Void)?
    private var voiceIdentifier = "com.apple.ttsbundle.Samantha-compact"
    private var speechRate: Float = 0.5
    
    private override init() {
        super.init()
        speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
        synthesizer.delegate = self
    }
    
    func onTranscription(_ handler: @escaping (String) -> Void) {
        onTranscriptionComplete = handler
    }
    
    func setVoice(identifier: String) {
        voiceIdentifier = identifier
    }
    
    func setSpeechRate(_ rate: Float) {
        speechRate = rate
    }
    
    func start() {
        guard !isActive else { return }
        
        DispatchQueue.main.async {
            self.isActive = true
        }
        
        startListening()
    }
    
    func stop() {
        stopListening()
        stopSpeaking()
        
        DispatchQueue.main.async {
            self.isActive = false
            self.currentTranscription = ""
        }
    }
    
    func speak(_ text: String, completion: (() -> Void)? = nil) {
        // Stop listening while speaking
        stopListening()
        
        let utterance = AVSpeechUtterance(string: text)
        utterance.voice = AVSpeechSynthesisVoice(identifier: voiceIdentifier)
            ?? AVSpeechSynthesisVoice(language: "en-US")
        utterance.rate = speechRate
        utterance.pitchMultiplier = 1.0
        utterance.volume = 1.0
        
        DispatchQueue.main.async {
            self.isSpeaking = true
        }
        
        synthesizer.speak(utterance)
    }
    
    func stopSpeaking() {
        synthesizer.stopSpeaking(at: .immediate)
        DispatchQueue.main.async {
            self.isSpeaking = false
        }
    }
    
    func interrupt() {
        stopSpeaking()
        startListening()
    }
    
    private func startListening() {
        guard isActive else { return }
        guard !isListening else { return }
        guard let speechRecognizer = speechRecognizer, speechRecognizer.isAvailable else {
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
                    let transcription = result.bestTranscription.formattedString
                    
                    DispatchQueue.main.async {
                        self.currentTranscription = transcription
                        self.lastSpeechTime = Date()
                    }
                    
                    // Reset silence timer
                    self.resetSilenceTimer()
                    
                    if result.isFinal {
                        self.handleFinalTranscription(transcription)
                    }
                }
                
                if error != nil {
                    self.stopListening()
                    // Restart after delay
                    DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                        if self.isActive && !self.isSpeaking {
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
            
            // Start silence detection
            resetSilenceTimer()
            
        } catch {
            print("Talk mode listening error: \(error)")
            stopListening()
        }
    }
    
    private func stopListening() {
        silenceTimer?.invalidate()
        silenceTimer = nil
        
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
    
    private func resetSilenceTimer() {
        silenceTimer?.invalidate()
        silenceTimer = Timer.scheduledTimer(withTimeInterval: silenceThreshold, repeats: false) { [weak self] _ in
            guard let self = self else { return }
            
            // Check if there's accumulated transcription
            let transcription = self.currentTranscription.trimmingCharacters(in: .whitespacesAndNewlines)
            if !transcription.isEmpty {
                self.handleFinalTranscription(transcription)
            }
        }
    }
    
    private func handleFinalTranscription(_ text: String) {
        guard !text.isEmpty else { return }
        
        DispatchQueue.main.async {
            self.currentTranscription = ""
        }
        
        stopListening()
        onTranscriptionComplete?(text)
    }
}

extension TalkModeRuntime: AVSpeechSynthesizerDelegate {
    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        DispatchQueue.main.async {
            self.isSpeaking = false
        }
        
        // Resume listening after speaking
        if isActive {
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                self.startListening()
            }
        }
    }
    
    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didCancel utterance: AVSpeechUtterance) {
        DispatchQueue.main.async {
            self.isSpeaking = false
        }
    }
}
