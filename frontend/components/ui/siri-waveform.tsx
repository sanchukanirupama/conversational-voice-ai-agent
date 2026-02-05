"use client";

import { useEffect, useRef } from "react";

interface SiriWaveformProps {
    audioLevel: number; // 0 to 1
}

export function SiriWaveform({ audioLevel }: SiriWaveformProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        let animationFrameId: number;
        let phase = 0;
        
        // Configuration for the waves - Emerald/Teal theme
        const waves = [
            { color: "rgba(16, 185, 129, 0.7)", speed: 0.01, amplitude: 0.5 },   // Emerald
            { color: "rgba(20, 184, 166, 0.6)", speed: 0.02, amplitude: 0.8 },   // Teal
            { color: "rgba(52, 211, 153, 0.5)", speed: 0.015, amplitude: 0.6 },  // Light emerald
            { color: "rgba(94, 234, 212, 0.4)", speed: 0.03, amplitude: 0.4 },   // Light teal
        ];

        const render = () => {
            if (!canvas || !ctx) return;
            
            // Resize canvas to match display size
            const width = canvas.clientWidth;
            const height = canvas.clientHeight;
            if (canvas.width !== width || canvas.height !== height) {
                canvas.width = width;
                canvas.height = height;
            }

            ctx.clearRect(0, 0, width, height);
            ctx.globalCompositeOperation = "lighter"; // Additive blending for glowing effect

            const centerY = height / 2;
            const baseAmplitude = height * 0.15; // Base height of idle wave
            // Dynamic amplitude based on audio level (smoothed)
            const activeAmplitude = height * 0.3 * (Math.max(0.1, audioLevel * 3)); 

            waves.forEach((wave, index) => {
                ctx.beginPath();
                ctx.strokeStyle = wave.color;
                ctx.lineWidth = 2;

                for (let x = 0; x < width; x++) {
                    // Combine multiple sine waves for organic look
                    // x * frequency + phase
                    const scaling = (x / width) * Math.PI * 2; 
                    
                    // Envelope to taper ends (0 at edges, 1 in center)
                    const envelope = Math.sin((x / width) * Math.PI);
                    
                    const y = centerY + 
                        Math.sin(x * 0.01 + phase * (index + 1) + index) * 
                        (baseAmplitude + activeAmplitude * wave.amplitude) * 
                        envelope;

                    if (x === 0) ctx.moveTo(x, y);
                    else ctx.lineTo(x, y);
                }
                ctx.stroke();
            });

            // Auto-animate phase even if silent
            phase += 0.05 + (audioLevel * 0.1); 
            animationFrameId = requestAnimationFrame(render);
        };

        render();

        return () => {
            cancelAnimationFrame(animationFrameId);
        };
    }, [audioLevel]);

    return (
        <canvas 
            ref={canvasRef} 
            className="w-full h-64 md:h-96 pointer-events-none"
        />
    );
}
