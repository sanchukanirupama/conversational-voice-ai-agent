import { RingingNodes } from "../types";

export const getAudioContext = (): AudioContext => {
    return new (window.AudioContext || (window as any).webkitAudioContext)();
};

export const playRingingTone = (ctx: AudioContext): RingingNodes => {
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
    
    return { osc1, osc2, gain };
};

export const stopRingingTone = (nodes: RingingNodes | null) => {
    if (!nodes) return;
    try {
        const { osc1, osc2, gain } = nodes;
        osc1.stop();
        osc2.stop();
        osc1.disconnect();
        osc2.disconnect();
        gain.disconnect();
    } catch (e) {
        console.error("Error stopping ringing:", e);
    }
};

export const playDisconnectTone = (ctx: AudioContext) => {
    // Create oscillator for "beep"
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    
    osc.connect(gain);
    gain.connect(ctx.destination);
    
    osc.frequency.setValueAtTime(480, ctx.currentTime);
    osc.type = 'sine';
    
    const now = ctx.currentTime;
    
    // Quick Beep-Beep-Beep (Phone cut style)
    gain.gain.setValueAtTime(0, now);
    gain.gain.linearRampToValueAtTime(0.1, now + 0.05);
    gain.gain.linearRampToValueAtTime(0, now + 0.25);
    
    gain.gain.linearRampToValueAtTime(0.1, now + 0.35);
    gain.gain.linearRampToValueAtTime(0, now + 0.55);

    gain.gain.linearRampToValueAtTime(0.1, now + 0.65);
    gain.gain.linearRampToValueAtTime(0, now + 0.85);
    
    osc.start(now);
    osc.stop(now + 1.0);
};

export const decodeBase64Audio = async (ctx: AudioContext, base64: string): Promise<AudioBuffer> => {
    const audioData = atob(base64);
    const arrayBuffer = new ArrayBuffer(audioData.length);
    const view = new Uint8Array(arrayBuffer);
    for (let i = 0; i < audioData.length; i++) {
        view[i] = audioData.charCodeAt(i);
    }
    return await ctx.decodeAudioData(arrayBuffer);
};
