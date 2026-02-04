"use client";
import { useState, useRef } from 'react';
import { useAudioRecorder } from './hooks/useAudioRecorder';
import { SiriWaveform } from '@/components/ui/siri-waveform';
import { Mic, PhoneOff } from 'lucide-react';

export default function Home() {
  const [isCallActive, setIsCallActive] = useState(false);
  const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
  const [transcript, setTranscript] = useState<string[]>([]);
  const [audioLevel, setAudioLevel] = useState(0);
  
  const ws = useRef<WebSocket | null>(null);
  const audioContext = useRef<AudioContext | null>(null);
  const sourceNodeRef = useRef<AudioBufferSourceNode | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const shouldDisconnectRef = useRef(false);
  const idleTimerRef = useRef<NodeJS.Timeout | null>(null);
  const ringingNodesRef = useRef<{ osc1: OscillatorNode; osc2: OscillatorNode; gain: GainNode } | null>(null);

  const stopRinging = () => {
    if (ringingNodesRef.current) {
        try {
            const { osc1, osc2, gain } = ringingNodesRef.current;
            osc1.stop();
            osc2.stop();
            osc1.disconnect();
            osc2.disconnect();
            gain.disconnect();
        } catch (e) {
            console.error("Error stopping ringing:", e);
        }
        ringingNodesRef.current = null;
    }
  };

  const startRinging = () => {
    stopRinging(); // Ensure clear before start
    
    if (!audioContext.current) {
        audioContext.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    }
    const ctx = audioContext.current;
    
    // Standard US Ringtone: 440Hz + 480Hz
    const osc1 = ctx.createOscillator();
    const osc2 = ctx.createOscillator();
    const gain = ctx.createGain();
    
    osc1.frequency.setValueAtTime(440, ctx.currentTime);
    osc2.frequency.setValueAtTime(480, ctx.currentTime);
    
    osc1.type = 'sine';
    osc2.type = 'sine';
    
    // Pulse pattern: 2s ON, 4s OFF
    const now = ctx.currentTime;
    gain.gain.setValueAtTime(0, now);
    
    // Create a loop of rings for 30 seconds
    for (let i = 0; i < 5; i++) {
        const start = now + (i * 6);
        const end = start + 2;
        // Fade in/out slightly to avoid clicks
        gain.gain.setTargetAtTime(0.1, start, 0.05); 
        gain.gain.setTargetAtTime(0, end, 0.05);
    }

    osc1.connect(gain);
    osc2.connect(gain);
    gain.connect(ctx.destination);
    
    osc1.start();
    osc2.start();
    
    ringingNodesRef.current = { osc1, osc2, gain };
  };

  const startIdleTimer = () => {
    if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
    idleTimerRef.current = setTimeout(() => {
        console.log('Idle timeout triggered');
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ type: 'timeout' }));
        }
    }, 8000); // 8 seconds
  };

  const stopIdleTimer = () => {
      if (idleTimerRef.current) {
          clearTimeout(idleTimerRef.current);
          idleTimerRef.current = null;
      }
  };

  // Play audio from base64
  const playAudio = async (base64Audio: string) => {
    try {
      if (sourceNodeRef.current) {
        sourceNodeRef.current.onended = null;
        try { sourceNodeRef.current.stop(); } catch {}
      }

      if (!audioContext.current) {
        audioContext.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      }

      const audioData = atob(base64Audio);
      const arrayBuffer = new ArrayBuffer(audioData.length);
      const view = new Uint8Array(arrayBuffer);
      for (let i = 0; i < audioData.length; i++) {
        view[i] = audioData.charCodeAt(i);
      }

      const audioBuffer = await audioContext.current.decodeAudioData(arrayBuffer);
      const source = audioContext.current.createBufferSource();
      source.buffer = audioBuffer;

      // Create and connect analyser if needed
      if (!analyserRef.current) {
        analyserRef.current = audioContext.current.createAnalyser();
        analyserRef.current.fftSize = 256;
      }
      
      source.connect(analyserRef.current);
      analyserRef.current.connect(audioContext.current.destination);
      
      source.start(0);
      sourceNodeRef.current = source;
      setIsAgentSpeaking(true);

      // Start visualizing
      const updateAudioLevel = () => {
        if (analyserRef.current) {
          const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
          analyserRef.current.getByteFrequencyData(dataArray);
          
          let sum = 0;
          for (let i = 0; i < dataArray.length; i++) {
            sum += dataArray[i];
          }
          const average = sum / dataArray.length;
          setAudioLevel(average / 128); 
          
          animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
        }
      };
      updateAudioLevel();

      source.onended = () => {
        setIsAgentSpeaking(false);
        sourceNodeRef.current = null;
        if (animationFrameRef.current) {
            cancelAnimationFrame(animationFrameRef.current);
            setAudioLevel(0);
        }
        
        // Agent finished speaking, start idle timer
        startIdleTimer();
        
        if (shouldDisconnectRef.current) {
            setIsCallActive(false);
            shouldDisconnectRef.current = false;
        }
      };
    } catch (e) {
      console.error('Error playing audio', e);
      stopRinging(); // safety
      setIsAgentSpeaking(false);
      startIdleTimer(); // Fallback: start timer if audio fails
    }
  };

  const stopAudioPlayback = () => {
    if (sourceNodeRef.current) {
      sourceNodeRef.current.onended = null;
      try {
        sourceNodeRef.current.stop();
        sourceNodeRef.current = null;
        setIsAgentSpeaking(false);
        stopIdleTimer(); // Stop timer if we interrupt playback
        if (animationFrameRef.current) {
            cancelAnimationFrame(animationFrameRef.current);
            setAudioLevel(0);
        }
      } catch {}
    }
  };

  const { isRecording, startRecording, stopRecording } = useAudioRecorder({
    isAgentSpeaking,
    isWaitingForResponse,
    onAudioAvailable: (blob) => {
      setIsWaitingForResponse(true);
      stopIdleTimer(); // Stop timer when user speaks

      const reader = new FileReader();
      reader.readAsDataURL(blob);
      reader.onloadend = () => {
        const base64data = reader.result as string;
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
          ws.current.send(JSON.stringify({ type: 'audio', data: base64data }));
          setTranscript((prev) => [...prev, 'You: ...']); 
        } else {
          setIsWaitingForResponse(false);
        }
      };
    },
    onSpeechStart: () => {
      console.log('Speech detected - Interrupting Agent');
      stopAudioPlayback();
      stopIdleTimer(); // Reset timer on speech start
    },
  });

  const startCall = () => {
    setIsCallActive(true);
    shouldDisconnectRef.current = false; 
    startRinging(); // Start ringing sound
    const wsUrl = `ws://${window.location.hostname}:8000/ws`;
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log('WS Connected');
      startRecording();
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'audio') {
        stopRinging(); // Stop ringing when agent responds
        setIsWaitingForResponse(false);
        if (data.content) {
             setTranscript((prev) => [...prev, `Agent: ${data.content}`]);
        }
        if (data.audio) {
          playAudio(data.audio);
        } else {
            // No audio provided, start timer immediately
            startIdleTimer();
        }
      }
    };

    ws.current.onclose = () => {
      console.log('WS Disconnected');
      stopRinging(); // Safety stop
      setIsWaitingForResponse(false);
      stopRecording();
      stopIdleTimer();

      if (sourceNodeRef.current) {
          console.log('Audio still playing, waiting to disconnect UI...');
          shouldDisconnectRef.current = true;
      } else {
          setIsCallActive(false);
      }
    };
  };

  const endCall = () => {
    if (ws.current) ws.current.close();
    shouldDisconnectRef.current = false;
    setIsCallActive(false);
    setIsAgentSpeaking(false);
    setIsWaitingForResponse(false);
    stopAudioPlayback();
    stopRecording();
  };

  // Get the last relevant message for the "subtitle" display
  const lastMessage = transcript.length > 0 ? transcript[transcript.length - 1] : "";
  const displayMessage = lastMessage.replace(/^(You|Agent): /, '');

  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-[#0A0A0A] text-white flex flex-col items-center justify-center">
        
        {/* Dynamic Waveform Visualization */}
        <div className="w-full max-w-4xl h-96 flex items-center justify-center">
            {isCallActive ? (
                <SiriWaveform audioLevel={audioLevel} />
            ) : (
                <div className="text-gray-500 font-light text-2xl animate-pulse">
                    Tap to start assistant
                </div>
            )}
        </div>

        {/* Transcription Subtitle */}
        <div className="w-full max-w-2xl text-center min-h-[100px] flex items-center justify-center px-4">
            {isCallActive && displayMessage && (
                <h2 className="text-2xl md:text-3xl font-medium text-white/90 leading-relaxed transition-all duration-500">
                    "{displayMessage}"
                </h2>
            )}
            {isCallActive && isWaitingForResponse && !displayMessage && (
                <span className="text-white/50 text-xl font-light italic">Listening...</span>
            )}
        </div>

        {/* Control Button */}
        <div className="mt-12 mb-12">
            {!isCallActive ? (
                <button 
                    onClick={startCall}
                    className="group relative flex items-center justify-center w-16 h-16 rounded-full bg-white/10 hover:bg-white/20 backdrop-blur-md border border-white/20 transition-all duration-300 hover:scale-110"
                >
                    <Mic className="w-6 h-6 text-white" />
                    <span className="absolute -bottom-8 text-xs text-white/40 font-mono tracking-wider opacity-0 group-hover:opacity-100 transition-opacity">START</span>
                </button>
            ) : (
                <button 
                    onClick={endCall}
                    className="group relative flex items-center justify-center w-16 h-16 rounded-full bg-red-500/20 hover:bg-red-500/40 backdrop-blur-md border border-red-500/50 transition-all duration-300 hover:scale-110"
                >
                    <PhoneOff className="w-6 h-6 text-red-500" />
                    <span className="absolute -bottom-8 text-xs text-red-400/80 font-mono tracking-wider opacity-0 group-hover:opacity-100 transition-opacity">END</span>
                </button>
            )}
        </div>
        
    </div>
  );
}
