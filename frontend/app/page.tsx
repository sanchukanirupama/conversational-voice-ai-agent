"use client";
import { useState, useRef } from 'react';
import { VoiceOrb } from './components/VoiceOrb';
import { useAudioRecorder } from './hooks/useAudioRecorder';

export default function Home() {
  const [isCallActive, setIsCallActive] = useState(false);
  const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
  const [transcript, setTranscript] = useState<string[]>([]);
  const ws = useRef<WebSocket | null>(null);
  const audioContext = useRef<AudioContext | null>(null);
  const sourceNodeRef = useRef<AudioBufferSourceNode | null>(null);

  // Play audio from base64
  const playAudio = async (base64Audio: string) => {
    try {
      // Stop any currently playing audio and detach its onended so it cannot
      // race against the new source and reset isAgentSpeaking prematurely.
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
      source.connect(audioContext.current.destination);
      source.start(0);
      sourceNodeRef.current = source;
      setIsAgentSpeaking(true);

      source.onended = () => {
        setIsAgentSpeaking(false);
        sourceNodeRef.current = null;
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
      } catch {}
    }
  };

  const { isRecording, startRecording, stopRecording } = useAudioRecorder({
    isAgentSpeaking,
    isWaitingForResponse,
    onAudioAvailable: (blob) => {
      // Lock immediately – the VAD gate will suppress further recordings
      // until the backend replies.
      setIsWaitingForResponse(true);

      const reader = new FileReader();
      reader.readAsDataURL(blob);
      reader.onloadend = () => {
        const base64data = reader.result as string;
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
          ws.current.send(JSON.stringify({ type: 'audio', data: base64data }));
          setTranscript((prev) => [...prev, 'You: (Audio Sent)']);
        } else {
          // WebSocket is gone – release the lock so the UI does not freeze
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
    ws.current = new WebSocket('ws://localhost:8000/ws');

    ws.current.onopen = () => {
      console.log('WS Connected');
      startRecording();
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      // The backend sends a single {type:"audio"} message per turn that
      // carries both the text transcript and the TTS payload.
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
      setIsCallActive(false);
      setIsWaitingForResponse(false);
      stopRecording();
    };
  };

  const endCall = () => {
    if (ws.current) ws.current.close();
    setIsCallActive(false);
    setIsAgentSpeaking(false);
    setIsWaitingForResponse(false);
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
