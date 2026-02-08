"use client";
import { useEffect, useState } from 'react';
import { SiriWaveform } from '@/components/ui/siri-waveform';
import RetroGrid from '@/components/ui/retro-grid';
import { Mic, PhoneOff, Headset, MicOff } from 'lucide-react';
import { useVoiceAgent } from './hooks/useVoiceAgent';

export default function Home() {
  const [micPermission, setMicPermission] = useState<'granted' | 'denied' | 'prompt' | 'checking'>('checking');

  const {
      isCallActive,
      isAgentSpeaking,
      isWaitingForResponse,
      isWakingServer,
      transcript,
      audioLevel,
      startCall,
      endCall
  } = useVoiceAgent();

  // Request microphone access on page load
  useEffect(() => {
    const requestMicrophoneAccess = async () => {
      try {
        console.log('🎤 Requesting microphone access on startup...');
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        // Permission granted - immediately release the stream
        stream.getTracks().forEach(track => track.stop());

        console.log(' Microphone access granted');
        setMicPermission('granted');
      } catch (error) {
        console.error(' Microphone access denied or unavailable:', error);
        setMicPermission('denied');
      }
    };

    requestMicrophoneAccess();
  }, []);

  const lastMessage = transcript.length > 0 ? transcript[transcript.length - 1] : "";
  const displayMessage = lastMessage.replace(/^(You|Agent): /, '');

  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-black text-white flex flex-col">
        <RetroGrid />

        {/* Header */}
        <header className="relative z-10 pt-8 pb-4 px-6">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-400 to-teal-600 flex items-center justify-center">
                <Headset className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-white">ABC Bank</h1>
                <p className="text-xs text-white/50">AI Voice Assistant</p>
              </div>
            </div>

            <a
                href="/admin/login"
                className="text-sm text-white/60 hover:text-emerald-400 transition-colors duration-200 font-medium"
            >
                Admin Portal
            </a>
          </div>
        </header>

        {/* Main Content */}
        <div className="flex-1 flex flex-col items-center justify-start md:justify-center px-6 pt-8 md:pt-0 md:-mt-16">
          <div className="mb-8 flex flex-col items-center gap-3">
            <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full backdrop-blur-xl border transition-all duration-300 ${
              isCallActive
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                : 'bg-white/5 border-white/10 text-white/50'
            }`}>
              <div className={`w-2 h-2 rounded-full ${isCallActive ? 'bg-emerald-400 animate-pulse' : 'bg-white/30'}`} />
              <span className="text-sm font-medium">
                {isCallActive
                  ? (isWakingServer
                      ? 'Connecting...'
                      : (isAgentSpeaking ? 'Speaking' : 'Listening')
                    )
                  : 'Ready to assist'
                }
              </span>
            </div>

            {/* Microphone Status Indicator */}
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-300 ${
              micPermission === 'granted'
                ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400'
                : micPermission === 'denied'
                ? 'bg-red-500/10 border border-red-500/30 text-red-400'
                : 'bg-yellow-500/10 border border-yellow-500/30 text-yellow-400'
            }`}>
              {micPermission === 'granted' ? (
                <>
                  <Mic className="w-3 h-3" />
                  <span>Mic Ready</span>
                </>
              ) : micPermission === 'denied' ? (
                <>
                  <MicOff className="w-3 h-3" />
                  <span>Mic Blocked</span>
                </>
              ) : (
                <span>Checking...</span>
              )}
            </div>
          </div>

          {/* Waveform Visualization */}
          <div className="w-full max-w-4xl h-80 flex items-center justify-center mb-8">
            {isCallActive ? (
              <SiriWaveform audioLevel={audioLevel} />
            ) : (
              <div className="text-center space-y-4">
                <p className="text-white/40 text-lg font-light">
                  Press the button to start a conversation
                </p>
              </div>
            )}
          </div>

          {/* Transcription Display */}
          <div className="w-full max-w-3xl min-h-[80px] flex items-center justify-center px-6 mb-8">
            {isCallActive && isWakingServer && (
              <div className="flex items-center gap-2 text-white/50">
                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                <span className="ml-2 text-sm font-medium">Waking up server...</span>
              </div>
            )}
            {isCallActive && !isWakingServer && displayMessage && (
              <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl px-8 py-6 shadow-2xl">
                <p className="text-xl md:text-2xl text-white/90 leading-relaxed text-center">
                  {displayMessage}
                </p>
              </div>
            )}
            {isCallActive && !isWakingServer && isWaitingForResponse && !displayMessage && (
              <div className="flex items-center gap-2 text-white/50">
                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                <span className="ml-2 text-sm font-medium">Processing</span>
              </div>
            )}
          </div>

          {/* Control Button */}
          <div className="relative">
            {!isCallActive ? (
              <div className="flex flex-col items-center gap-4">
                <button
                  onClick={startCall}
                  disabled={micPermission === 'denied'}
                  className={`group relative flex items-center justify-center w-20 h-20 rounded-full shadow-lg transition-all duration-300 ${
                    micPermission === 'denied'
                      ? 'bg-gray-600 cursor-not-allowed opacity-50'
                      : 'bg-gradient-to-br from-emerald-400 to-teal-600 hover:from-emerald-500 hover:to-teal-700 hover:shadow-emerald-500/50 hover:scale-105'
                  }`}
                >
                  <Mic className="w-8 h-8 text-white" />
                  {micPermission === 'granted' && (
                    <div className="absolute inset-0 rounded-full bg-emerald-400/20 animate-ping" />
                  )}
                </button>

                {micPermission === 'denied' && (
                  <p className="text-sm text-red-400/80 text-center max-w-xs">
                    Microphone access denied. Please enable it in your browser settings.
                  </p>
                )}
              </div>
            ) : (
              <button
                onClick={endCall}
                className="group relative flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 shadow-lg hover:shadow-red-500/50 transition-all duration-300 hover:scale-105"
              >
                <PhoneOff className="w-8 h-8 text-white" />
              </button>
            )}
          </div>
        </div>

        {/* Footer */}
        <footer className="relative z-10 py-6 px-6 text-center">
          <p className="text-xs text-white/30">
            Built by - Sanchuka Nirupama
          </p>
        </footer>
    </div>
  );
}
