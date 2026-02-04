"use client";
import { useState, useRef, useEffect } from 'react';
import { useAudioRecorder } from './hooks/useAudioRecorder';
import { BackgroundCircles } from '@/components/ui/background-circles';
import { AIVoiceInput } from '@/components/ui/ai-voice-input';

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
          
          // Calculate average level
          let sum = 0;
          for (let i = 0; i < dataArray.length; i++) {
            sum += dataArray[i];
          }
          const average = sum / dataArray.length;
          // Normalize to 0-1
          setAudioLevel(average / 128); // Division by 128 to make it more sensitive/visible
          
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
        
        if (shouldDisconnectRef.current) {
            setIsCallActive(false);
            shouldDisconnectRef.current = false;
        }
      };
    } catch (e) {
      console.error('Error playing audio', e);
    }
  };

  const stopAudioPlayback = () => {
    if (sourceNodeRef.current) {
      sourceNodeRef.current.onended = null;
      try {
        sourceNodeRef.current.stop();
        sourceNodeRef.current = null;
        setIsAgentSpeaking(false);
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

      const reader = new FileReader();
      reader.readAsDataURL(blob);
      reader.onloadend = () => {
        const base64data = reader.result as string;
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
          ws.current.send(JSON.stringify({ type: 'audio', data: base64data }));
          setTranscript((prev) => [...prev, 'You: (Audio Sent)']);
        } else {
          setIsWaitingForResponse(false);
        }
      };
    },
    onSpeechStart: () => {
      console.log('Speech detected - Interrupting Agent');
      stopAudioPlayback();
    },
  });

  const startCall = () => {
    setIsCallActive(true);
    shouldDisconnectRef.current = false; // Reset disconnect flag
    // Use window.location.hostname to connect to the backend running on the same host but port 8000
    // If you are developing locally, it will likely be localhost
    const wsUrl = `ws://${window.location.hostname}:8000/ws`;
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log('WS Connected');
      startRecording();
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'audio') {
        setIsWaitingForResponse(false);
        setTranscript((prev) => [...prev, `Agent: ${data.content}`]);
        if (data.audio) {
          playAudio(data.audio);
        }
      }
    };

    ws.current.onclose = () => {
      console.log('WS Disconnected');
      setIsWaitingForResponse(false);
      stopRecording();

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
    // ws.onclose will handle the state updates, but we force it here 
    // in case onclose doesn't fire immediately or we want instant feedback logic?
    // Actually, if we call close(), onclose will fire.
    // But if we want to stop audio immediately when USER clicks end:
    shouldDisconnectRef.current = false; // Don't delay if user explicitly ends
    setIsCallActive(false);
    setIsAgentSpeaking(false);
    setIsWaitingForResponse(false);
    stopAudioPlayback();
    stopRecording();
  };

  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-white dark:bg-black/90">
        
        {/* Background Animation */}
        <div className="absolute inset-0 z-0">
             <BackgroundCircles 
                variant="octonary" 
                audioLevel={audioLevel} 
                isActive={isCallActive}
            />
        </div>

        {/* Content */}
        <div className="relative z-10 flex flex-col items-center justify-between min-h-screen p-4">
            
            {/* Header */}
            <header className="w-full max-w-4xl flex justify-between items-center pt-8">
                 <h1 className="text-2xl font-bold tracking-tighter bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-400 bg-clip-text text-transparent">
                  Bank ABC AI Agent
                </h1>
            </header>

            {/* Main Interaction Area */}
            <main className="flex-1 flex flex-col items-center justify-center w-full max-w-lg gap-12">
                
                <div className="w-full flex justify-center">
                    <AIVoiceInput 
                        onStart={startCall}
                        onStop={endCall}
                        isConnected={isCallActive}
                    />
                </div>

                {isRecording && !isAgentSpeaking && (
                    <div className="text-emerald-500 font-mono text-sm animate-pulse">
                         Listening...
                    </div>
                )}
                 
                 {isWaitingForResponse && (
                     <div className="text-gray-400 font-mono text-sm">
                         Thinking...
                     </div>
                 )}

            </main>

            {/* Transcript / Footer */}
            <footer className="w-full max-w-2xl h-48 mb-8 transition-all duration-500 ease-in-out">
                {isCallActive && (
                    <div className="w-full bg-white/50 dark:bg-black/40 backdrop-blur-md border border-gray-200 dark:border-white/10 rounded-2xl p-4 h-full overflow-y-auto shadow-sm">
                        <div className="text-xs text-gray-500 dark:text-gray-400 mb-3 font-mono uppercase tracking-widest sticky top-0 bg-transparent">Live Transcript</div>
                        <div className="space-y-3">
                            {transcript.map((line, i) => (
                                <div key={i} className={`flex ${line.includes('You') ? 'justify-end' : 'justify-start'}`}>
                                    <div className={`
                                        max-w-[80%] p-3 rounded-2xl text-sm
                                        ${line.includes('You') 
                                            ? 'bg-blue-500 text-white rounded-br-none' 
                                            : 'bg-gray-100 dark:bg-white/10 text-gray-800 dark:text-gray-200 rounded-bl-none'}
                                    `}>
                                        {line.replace(/^(You|Agent): /, '')}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </footer>
        </div>
    </div>
  );
}
