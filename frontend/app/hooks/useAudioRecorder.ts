import { useState, useRef, useCallback, useEffect } from 'react';

interface UseAudioRecorderProps {
  onAudioAvailable: (blob: Blob) => void;
  onSpeechStart?: () => void;
  isAgentSpeaking: boolean;
  isWaitingForResponse: boolean;
}

export function useAudioRecorder({
  onAudioAvailable,
  onSpeechStart,
  isAgentSpeaking,
  isWaitingForResponse,
}: UseAudioRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioContext = useRef<AudioContext | null>(null);
  const analyser = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunks = useRef<Blob[]>([]);
  const silenceTimer = useRef<NodeJS.Timeout | null>(null);
  const speechStartTime = useRef<number>(0);
  const isSpeaking = useRef(false);
  const isAborting = useRef(false);
  const animationFrame = useRef<number | null>(null);

  // Refs that keep callbacks and gate flags visible to the long-lived VAD closure
  // without requiring it to be torn down and recreated on every render.
  const isAgentSpeakingRef = useRef(isAgentSpeaking);
  const isWaitingForResponseRef = useRef(isWaitingForResponse);
  const onAudioAvailableRef = useRef(onAudioAvailable);
  const onSpeechStartRef = useRef(onSpeechStart);

  useEffect(() => { isAgentSpeakingRef.current = isAgentSpeaking; }, [isAgentSpeaking]);
  useEffect(() => { isWaitingForResponseRef.current = isWaitingForResponse; }, [isWaitingForResponse]);
  useEffect(() => { onAudioAvailableRef.current = onAudioAvailable; }, [onAudioAvailable]);
  useEffect(() => { onSpeechStartRef.current = onSpeechStart; }, [onSpeechStart]);

  // VAD Parameters
  const THRESHOLD = 30;           // Volume threshold (0-255)
  const SILENCE_DURATION = 800;   // ms of silence before finalising an utterance
  const MIN_SPEECH_DURATION = 600; // Ignore bursts shorter than this
  const MIN_BLOB_SIZE = 2000;     // Discard blobs below this byte count (dead-air)

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      streamRef.current = stream;

      // Audio-analysis pipeline
      audioContext.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      analyser.current = audioContext.current.createAnalyser();
      analyser.current.fftSize = 256;
      const source = audioContext.current.createMediaStreamSource(stream);
      source.connect(analyser.current);
      const dataArray = new Uint8Array(analyser.current.frequencyBinCount);

      // MediaRecorder – created once; start/stop is called by the VAD loop
      mediaRecorder.current = new MediaRecorder(stream);
      chunks.current = [];

      mediaRecorder.current.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.current.push(e.data);
      };

      mediaRecorder.current.onstop = () => {
        // Recordings aborted because the gate was engaged must never be sent.
        if (isAborting.current) {
          isAborting.current = false;
          chunks.current = [];
          return;
        }

        const duration = Date.now() - speechStartTime.current;
        if (chunks.current.length > 0 && duration > MIN_SPEECH_DURATION) {
          const blob = new Blob(chunks.current, { type: 'audio/webm' });
          if (blob.size >= MIN_BLOB_SIZE) {
            onAudioAvailableRef.current(blob);
          }
        }
        chunks.current = [];
      };

      // VAD loop – one iteration per animation frame
      const checkVolume = () => {
        if (!analyser.current) return;

        // ── Gate: suppress input while the agent is speaking or a response is pending ──
        // If a recording was already in progress when the gate engaged, abort it so that
        // the stale audio is never dispatched to the backend.
        if (isAgentSpeakingRef.current || isWaitingForResponseRef.current) {
          if (isSpeaking.current) {
            if (silenceTimer.current) {
              clearTimeout(silenceTimer.current);
              silenceTimer.current = null;
            }
            isSpeaking.current = false;
            if (mediaRecorder.current && mediaRecorder.current.state === 'recording') {
              isAborting.current = true;
              mediaRecorder.current.stop();
            }
          }
          animationFrame.current = requestAnimationFrame(checkVolume);
          return;
        }

        analyser.current.getByteFrequencyData(dataArray);
        const volume = dataArray.reduce((a, b) => a + b) / dataArray.length;

        if (volume > THRESHOLD) {
          // ── Speech detected ──
          if (!isSpeaking.current) {
            isSpeaking.current = true;
            speechStartTime.current = Date.now();
            chunks.current = [];

            if (mediaRecorder.current && mediaRecorder.current.state === 'inactive') {
              mediaRecorder.current.start();
            }

            // Barge-in: let the page stop agent playback immediately
            if (onSpeechStartRef.current) onSpeechStartRef.current();
          }

          // Reset silence countdown every frame that has speech
          if (silenceTimer.current) {
            clearTimeout(silenceTimer.current);
            silenceTimer.current = null;
          }
        } else {
          // ── Silence ──
          if (isSpeaking.current && !silenceTimer.current) {
            silenceTimer.current = setTimeout(() => {
              isSpeaking.current = false;
              if (mediaRecorder.current && mediaRecorder.current.state === 'recording') {
                mediaRecorder.current.stop(); // triggers onstop → sends the blob
              }
              silenceTimer.current = null;
            }, SILENCE_DURATION);
          }
        }

        animationFrame.current = requestAnimationFrame(checkVolume);
      };

      checkVolume();
      setIsRecording(true);
    } catch (err) {
      console.error('Error accessing microphone:', err);
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (animationFrame.current) cancelAnimationFrame(animationFrame.current);
    if (silenceTimer.current) clearTimeout(silenceTimer.current);

    if (mediaRecorder.current && mediaRecorder.current.state !== 'inactive') {
      isAborting.current = true;
      mediaRecorder.current.stop();
    }

    // Always release the mic track regardless of recorder state
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (audioContext.current) {
      audioContext.current.close();
      audioContext.current = null;
    }

    setIsRecording(false);
    isSpeaking.current = false;
  }, []);

  return { isRecording, startRecording, stopRecording };
}
