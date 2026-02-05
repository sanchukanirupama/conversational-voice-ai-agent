"use client";
import { SiriWaveform } from '@/components/ui/siri-waveform';
import RetroGrid from '@/components/ui/retro-grid';
import { Mic, PhoneOff } from 'lucide-react';
import { useVoiceAgent } from './hooks/useVoiceAgent';

export default function Home() {
  const {
      isCallActive,
      isAgentSpeaking,
      isWaitingForResponse,
      transcript,
      audioLevel,
      startCall,
      endCall
  } = useVoiceAgent();

  // Get the last relevant message for the "subtitle" display
  const lastMessage = transcript.length > 0 ? transcript[transcript.length - 1] : "";
  const displayMessage = lastMessage.replace(/^(You|Agent): /, '');

  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-[#0A0A0A] text-white flex flex-col items-center justify-center">
        <RetroGrid />
        
        {/* Dynamic Waveform Visualization */}
        <div className="w-full max-w-4xl h-96 flex items-center justify-center">
            {isCallActive ? (
                <SiriWaveform audioLevel={audioLevel} />
            ) : (
                <div className="text-center animate-pulse">
                  <div className="text-gray-500 font-light text-2xl">
                    Tap to talk to your AI assistant
                  </div>
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
                <span className="text-white/50 text-xl font-light italic">Processing...</span>
            )}
        </div>

        {/* Control Button */}
        <div className="mt-12 mb-12">
            {!isCallActive ? (
                <button 
                    onClick={startCall}
                    className="group relative flex items-center justify-center w-16 h-16 rounded-full bg-white/10 hover:bg-white/20 backdrop-blur-md border border-white/20 transition-all duration-300 hover:scale-110 cursor-pointer"
                >
                    <Mic className="w-6 h-6 text-white" />
                    <span className="absolute -bottom-8 text-xs text-white/40 font-mono tracking-wider opacity-0 group-hover:opacity-100 transition-opacity">START</span>
                </button>
            ) : (
                <button 
                    onClick={endCall}
                    className="group relative flex items-center justify-center w-16 h-16 rounded-full bg-red-500/20 hover:bg-red-500/40 backdrop-blur-md border border-red-500/50 transition-all duration-300 hover:scale-110 cursor-pointer"
                >
                    <PhoneOff className="w-6 h-6 text-red-500" />
                    <span className="absolute -bottom-8 text-xs text-red-400/80 font-mono tracking-wider opacity-0 group-hover:opacity-100 transition-opacity">END</span>
                </button>
            )}
        </div>
        
        {/* Admin Login Link */}
        <div className="mt-8">
            <a 
                href="/admin/login" 
                className="text-sm text-white/40 hover:text-white/70 transition-colors duration-200 font-light tracking-wide underline decoration-white/20 hover:decoration-white/50"
            >
                Login as an Admin
            </a>
        </div>
        
    </div>
  );
}
