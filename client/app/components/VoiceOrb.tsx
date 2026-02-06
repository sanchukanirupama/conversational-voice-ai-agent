"use client";
import React from 'react';

interface VoiceOrbProps {
  isActive: boolean;
  isSpeaking: boolean;
}

export function VoiceOrb({ isActive, isSpeaking }: VoiceOrbProps) {
  return (
    <div className="relative flex items-center justify-center p-20">
      {/* Core Orb */}
      <div 
        className={`w-32 h-32 rounded-full blur-none transition-all duration-500 ease-in-out z-10 
          ${isActive ? (isSpeaking ? 'bg-blue-400 scale-110' : 'bg-blue-600') : 'bg-gray-500'}
        `}
      ></div>

      {/* Ripple Effects (only when active) */}
      {isActive && (
        <>
            <div className={`absolute w-32 h-32 rounded-full border border-blue-400 opacity-50 ${isSpeaking ? 'animate-ping' : ''}`}></div>
            <div className={`absolute w-40 h-40 rounded-full border border-blue-300 opacity-30 ${isSpeaking ? 'animate-pulse' : ''}`}></div>
        </>
      )}
    </div>
  );
}
