import { useState, useRef, useCallback, useEffect } from 'react';

interface UseAudioRecorderProps {
  onAudioAvailable: (blob: Blob) => void;
  onSpeechStart?: () => void;
  isAgentSpeaking: boolean;
}

export function useAudioRecorder({ onAudioAvailable, onSpeechStart, isAgentSpeaking }: UseAudioRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioContext = useRef<AudioContext | null>(null);
  const analyser = useRef<AnalyserNode | null>(null);
  const chunks = useRef<Blob[]>([]);
  const silenceTimer = useRef<NodeJS.Timeout | null>(null);
  const speechStartTime = useRef<number>(0);
  const isSpeaking = useRef(false);
  const animationFrame = useRef<number | null>(null);
  
  // Store isAgentSpeaking in ref for access inside closure/animationFrame
  const isAgentSpeakingRef = useRef(isAgentSpeaking);
  
  useEffect(() => {
      isAgentSpeakingRef.current = isAgentSpeaking;
  }, [isAgentSpeaking]);

  // VAD Parameters
  const THRESHOLD = 30; // Volume threshold (0-255)
  const SILENCE_DURATION = 800; // ms to wait before sending (Reduced for lower latency)
  const MIN_SPEECH_DURATION = 600; // Ignore short clicks/noise

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
          audio: {
              echoCancellation: true,
              noiseSuppression: true,
              autoGainControl: true
          } 
      });
      
      // Setup Audio Analysis
      audioContext.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      analyser.current = audioContext.current.createAnalyser();
      analyser.current.fftSize = 256;
      const source = audioContext.current.createMediaStreamSource(stream);
      source.connect(analyser.current);
      
      const dataArray = new Uint8Array(analyser.current.frequencyBinCount);

      // Setup Recorder
      mediaRecorder.current = new MediaRecorder(stream);
      chunks.current = [];

      mediaRecorder.current.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.current.push(e.data);
      };

      mediaRecorder.current.onstop = () => {
        const duration = Date.now() - speechStartTime.current;
        if (chunks.current.length > 0 && duration > MIN_SPEECH_DURATION) {
            const blob = new Blob(chunks.current, { type: 'audio/webm' });
            onAudioAvailable(blob);
        }
        chunks.current = [];
      };

      // VAD Loop
      const checkVolume = () => {
          if (!analyser.current) return;
          
          // CRITICAL: If Agent is speaking, ignore input (prevent echo loop)
          // We still run the loop to keep it alive, but we don't trigger speech logic
          if (isAgentSpeakingRef.current) {
              animationFrame.current = requestAnimationFrame(checkVolume);
              return;
          }

          analyser.current.getByteFrequencyData(dataArray);
          
          // Calculate average volume
          const volume = dataArray.reduce((a, b) => a + b) / dataArray.length;
          
          if (volume > THRESHOLD) {
              // Speech Detected
              if (!isSpeaking.current) {
                  isSpeaking.current = true;
                  speechStartTime.current = Date.now();
                  
                  // Start Recorder if not running (effective start of phrase)
                  if (mediaRecorder.current && mediaRecorder.current.state === "inactive") {
                      mediaRecorder.current.start();
                      chunks.current = []; 
                  }
                  
                  // Trigger Barge-in
                  if (onSpeechStart) onSpeechStart();
              }
              
              // Reset Silence Timer
              if (silenceTimer.current) {
                  clearTimeout(silenceTimer.current);
                  silenceTimer.current = null;
              }
          } else {
              // Silence
              if (isSpeaking.current) {
                  // If we were speaking, start countdown to stop
                   if (!silenceTimer.current) {
                       silenceTimer.current = setTimeout(() => {
                           // Silence confirmed
                           isSpeaking.current = false;
                           if (mediaRecorder.current && mediaRecorder.current.state === "recording") {
                               mediaRecorder.current.stop();
                           }
                           silenceTimer.current = null;
                       }, SILENCE_DURATION);
                   }
              }
          }
          
          animationFrame.current = requestAnimationFrame(checkVolume);
      };

      checkVolume();
      setIsRecording(true);
      
    } catch (err) {
      console.error("Error accessing microphone:", err);
    }
  }, [onAudioAvailable, onSpeechStart]);

  const stopRecording = useCallback(() => {
    if (animationFrame.current) cancelAnimationFrame(animationFrame.current);
    if (silenceTimer.current) clearTimeout(silenceTimer.current);
    
    if (mediaRecorder.current && mediaRecorder.current.state !== 'inactive') {
      mediaRecorder.current.stop();
      mediaRecorder.current.stream.getTracks().forEach(track => track.stop());
    }
    if (audioContext.current) {
        audioContext.current.close();
    }
    setIsRecording(false);
    isSpeaking.current = false;
  }, []);

  return { isRecording, startRecording, stopRecording };
}
