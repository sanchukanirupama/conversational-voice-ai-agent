"use client";
import { useState, useEffect, useRef } from 'react';
import { VoiceOrb } from './components/VoiceOrb';
import { useAudioRecorder } from './hooks/useAudioRecorder';

export default function Home() {
  const [isCallActive, setIsCallActive] = useState(false);
  const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);
  const [transcript, setTranscript] = useState<string[]>([]);
  const ws = useRef<WebSocket | null>(null);
  const audioContext = useRef<AudioContext | null>(null);

  const [sourceNode, setSourceNode] = useState<AudioBufferSourceNode | null>(null);

  // Play audio from base64
  const playAudio = async (base64Audio: string) => {
      try {
        if (sourceNode) {
            try { sourceNode.stop(); } catch {} // Barge-in
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
        source.connect(audioContext.current.destination);
        source.start(0);
        setSourceNode(source);
        setIsAgentSpeaking(true);
        
        source.onended = () => {
             setIsAgentSpeaking(false);
             setSourceNode(null);
        };
      } catch (e) {
          console.error("Error playing audio", e);
      }
  };
  
  const stopAudioPlayback = () => {
      if (sourceNode) {
          try {
             sourceNode.stop();
             setSourceNode(null);
             setIsAgentSpeaking(false);
          } catch(e) {
              // ignore
          }
      }
      window.speechSynthesis.cancel();
  };

  const { isRecording, startRecording, stopRecording } = useAudioRecorder({
      isAgentSpeaking: isAgentSpeaking, // Pass the state
      onAudioAvailable: (blob) => {
          // Convert blob to base64 and send
          const reader = new FileReader();
          reader.readAsDataURL(blob);
          reader.onloadend = () => {
              const base64data = reader.result as string;
              if (ws.current && ws.current.readyState === WebSocket.OPEN) {
                  ws.current.send(JSON.stringify({ type: 'audio', data: base64data }));
                  setTranscript(prev => [...prev, `You: (Audio Sent)`]);
              }
          };
      },
      onSpeechStart: () => {
          console.log("Speech detected - Interrupting Agent");
          stopAudioPlayback();
      }
  });

  const startCall = () => {
    setIsCallActive(true);
    // Connect WS
    ws.current = new WebSocket('ws://localhost:8000/ws');
    
    ws.current.onopen = () => {
      console.log('WS Connected');
      startRecording(); // Auto-start recording
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'audio') {
        setTranscript(prev => [...prev, `Agent: ${data.content}`]);
        if (data.audio) {
            playAudio(data.audio);
        } else {
             setIsAgentSpeaking(true);
             setTimeout(() => setIsAgentSpeaking(false), 2000);
        }
      } else if (data.type === 'text') {
           setTranscript(prev => [...prev, `Agent: ${data.content}`]);
      }
    };

    ws.current.onclose = () => {
      console.log('WS Disconnected');
      setIsCallActive(false);
      stopRecording();
    };
  };

  const endCall = () => {
    if (ws.current) ws.current.close();
    setIsCallActive(false);
    setIsAgentSpeaking(false);
    stopAudioPlayback();
    stopRecording();
  };

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center text-white">
      <main className="flex flex-col items-center gap-8 w-full max-w-2xl px-4">
        <h1 className="text-4xl font-bold tracking-tighter bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
          Bank ABC AI Agent
        </h1>

        <div className="w-full flex justify-center py-10 relative">
            <VoiceOrb isActive={isCallActive} isSpeaking={isAgentSpeaking} />
            
            {/* Recording Indicator */}
            {isRecording && (
                <div className="absolute bottom-0 text-green-400 font-mono text-xs opacity-50">
                     Listening (Hands-free)
                </div>
            )}
        </div>

        <div className="flex gap-4">
            {!isCallActive ? (
                <button 
                    onClick={startCall}
                    className="px-8 py-3 bg-green-600 hover:bg-green-700 rounded-full font-bold text-lg transition-colors shadow-lg shadow-green-900/50"
                >
                    Start Call
                </button>
            ) : (
                <button 
                    onClick={endCall}
                    className="px-8 py-3 bg-red-600 hover:bg-red-700 rounded-full font-bold text-lg transition-colors shadow-lg shadow-red-900/50"
                >
                    End Call
                </button>
            )}
        </div>

        {isCallActive && (
            <div className="w-full bg-gray-800 rounded-xl p-4 mt-8 flex flex-col gap-2 h-64 overflow-y-auto">
                <div className="text-sm text-gray-400 mb-2 font-mono uppercase">Live Transcript</div>
                {transcript.map((line, i) => (
                    <div key={i} className={`p-2 rounded ${line.includes('You') ? 'bg-gray-700 self-end' : 'bg-gray-700/50 self-start'}`}>
                        {line}
                    </div>
                ))}
            </div>
        )}
      </main>
    </div>
  );
}
