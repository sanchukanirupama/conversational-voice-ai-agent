import { useState, useRef, useEffect, useCallback } from 'react';
import { useAudioRecorder } from './useAudioRecorder';
import { getAudioContext, playRingingTone, stopRingingTone, playDisconnectTone, decodeBase64Audio } from '../utils/audio';
import { RingingNodes, WSMessage } from '../types';

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
const HTTP_BASE_URL = WS_BASE_URL.replace('ws://', 'http://').replace('wss://', 'https://');

export function useVoiceAgent() {
    const [isCallActive, setIsCallActive] = useState(false);
    const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);
    const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
    const [transcript, setTranscript] = useState<string[]>([]);
    const [audioLevel, setAudioLevel] = useState(0);
    const [isWakingServer, setIsWakingServer] = useState(false);

    const ws = useRef<WebSocket | null>(null);
    const audioContext = useRef<AudioContext | null>(null);
    const sourceNodeRef = useRef<AudioBufferSourceNode | null>(null);
    const analyserRef = useRef<AnalyserNode | null>(null);
    const animationFrameRef = useRef<number | null>(null);
    const shouldDisconnectRef = useRef(false);
    const idleTimerRef = useRef<NodeJS.Timeout | null>(null);
    const ringingNodesRef = useRef<RingingNodes | null>(null);
    const hasGreetingPlayedRef = useRef(false);
    const isRecordingRef = useRef(false); // Track recording state for callbacks


    const startIdleTimer = useCallback(() => {
        if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
        idleTimerRef.current = setTimeout(() => {
            console.log('Idle timeout triggered');
            // Safety check: don't send timeout if user is actively recording
            if (isRecordingRef.current) {
                console.log('Timeout cancelled - user is recording');
                return;
            }
            if (ws.current && ws.current.readyState === WebSocket.OPEN) {
                ws.current.send(JSON.stringify({ type: 'timeout' }));
            }
        }, 8000);
    }, []);

    const stopIdleTimer = useCallback(() => {
        if (idleTimerRef.current) {
            clearTimeout(idleTimerRef.current);
            idleTimerRef.current = null;
        }
    }, []);

    const handleCallEnded = useCallback(() => {
        if (audioContext.current) playDisconnectTone(audioContext.current);
        
        setIsCallActive(false);
        setTranscript([]);
        hasGreetingPlayedRef.current = false;
        shouldDisconnectRef.current = false;
        setIsAgentSpeaking(false);
        setIsWaitingForResponse(false);
        setAudioLevel(0);
    }, []);

    const stopAudioPlayback = useCallback(() => {
        if (sourceNodeRef.current) {
            sourceNodeRef.current.onended = null;
            try {
                sourceNodeRef.current.stop();
                sourceNodeRef.current = null;
                setIsAgentSpeaking(false);
                stopIdleTimer();
                if (animationFrameRef.current) {
                    cancelAnimationFrame(animationFrameRef.current);
                    setAudioLevel(0);
                }
            } catch (e) { console.error(e) }
        }
    }, [stopIdleTimer]);

    // -- Audio & Recorder Hooks --

    const { isRecording, startRecording, stopRecording } = useAudioRecorder({
        isAgentSpeaking,
        isWaitingForResponse,
        onAudioAvailable: (blob) => {
            setIsWaitingForResponse(true);
            stopIdleTimer();

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
            stopIdleTimer();
        },
    });

    // Update ref and stop idle timer when recording state changes
    useEffect(() => {
        isRecordingRef.current = isRecording;
        if (isRecording) {
            console.log('Recording started - stopping idle timer');
            stopIdleTimer();
        }
    }, [isRecording, stopIdleTimer]);

    const playAudio = async (base64Audio: string) => {
        try {
            stopAudioPlayback(); // Stop any previous
            stopIdleTimer();

            if (!audioContext.current) audioContext.current = getAudioContext();
            
            const audioBuffer = await decodeBase64Audio(audioContext.current, base64Audio);
            const source = audioContext.current.createBufferSource();
            source.buffer = audioBuffer;

            // Analyser setup
            if (!analyserRef.current) {
                analyserRef.current = audioContext.current.createAnalyser();
                analyserRef.current.fftSize = 256;
            }
            
            source.connect(analyserRef.current);
            analyserRef.current.connect(audioContext.current.destination);
            
            source.start(0);
            sourceNodeRef.current = source;
            setIsAgentSpeaking(true);

            // Visualizer loop
            const updateAudioLevel = () => {
                if (analyserRef.current) {
                    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
                    analyserRef.current.getByteFrequencyData(dataArray);
                    const avg = dataArray.reduce((a,b) => a+b) / dataArray.length;
                    setAudioLevel(avg / 128);
                    animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
                }
            };
            updateAudioLevel();

            source.onended = () => {
                setIsAgentSpeaking(false);
                sourceNodeRef.current = null;
                if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
                setAudioLevel(0);
                
                // Finished speaking -> Start Listening/Idle
                startIdleTimer();
                
                if (!isRecording) {
                    startRecording();
                    hasGreetingPlayedRef.current = true;
                }
                
                if (shouldDisconnectRef.current) {
                    handleCallEnded();
                }
            };

        } catch (e) {
            console.error('Audio playback error:', e);
            stopRingingTone(ringingNodesRef.current);
            setIsAgentSpeaking(false);
            startIdleTimer();
        }
    };

    // -- Main Actions --

    const wakeUpServer = async (): Promise<boolean> => {
        try {
            const response = await fetch(`${HTTP_BASE_URL}/health`, {
                method: 'GET',
                signal: AbortSignal.timeout(10000) // 10s timeout
            });
            return response.ok;
        } catch (error) {
            console.error('Failed to wake up server:', error);
            return false;
        }
    };

    const connectWebSocket = useCallback((retryCount = 0) => {
        const wsUrl = `${WS_BASE_URL}/ws`;
        const maxRetries = 3;

        ws.current = new WebSocket(wsUrl);

        ws.current.onopen = () => {
            console.log('WS Connected');
            setIsWakingServer(false);
        };

        ws.current.onerror = (error) => {
            console.error('WebSocket error:', error);
            if (retryCount < maxRetries) {
                console.log(`Retrying WebSocket connection (${retryCount + 1}/${maxRetries})...`);
                setTimeout(() => connectWebSocket(retryCount + 1), 1000 * (retryCount + 1)); // Exponential backoff
            } else {
                console.error('Max WebSocket retries reached');
                setIsWakingServer(false);
                handleCallEnded();
            }
        };

        ws.current.onmessage = (event) => {
            const data: WSMessage = JSON.parse(event.data);
            if (data.type === 'audio') {
                stopRingingTone(ringingNodesRef.current);
                ringingNodesRef.current = null;
                setIsWaitingForResponse(false);

                if (data.content) {
                    setTranscript((prev) => [...prev, `Agent: ${data.content}`]);
                }
                if (data.audio) {
                    playAudio(data.audio);
                } else {
                    startIdleTimer();
                }
            }
        };

        ws.current.onclose = () => {
            console.log('WS Disconnected');
            stopRingingTone(ringingNodesRef.current);
            ringingNodesRef.current = null;
            setIsWaitingForResponse(false);
            stopRecording();
            stopIdleTimer();

            if (sourceNodeRef.current) {
                console.log('Audio still playing, waiting to disconnect UI...');
                shouldDisconnectRef.current = true;
            } else {
                handleCallEnded();
            }
        };
    }, [startIdleTimer, handleCallEnded, stopRecording]);

    const startCall = useCallback(async () => {
        setIsCallActive(true);
        setIsWakingServer(true);
        shouldDisconnectRef.current = false;
        hasGreetingPlayedRef.current = false;

        if (!audioContext.current) audioContext.current = getAudioContext();

        // Start Ringing
        stopRingingTone(ringingNodesRef.current);
        ringingNodesRef.current = playRingingTone(audioContext.current);

        // Wake up server first (handles cold start)
        console.log('Waking up server...');
        const serverAwake = await wakeUpServer();

        if (!serverAwake) {
            console.warn('Server health check failed, attempting connection anyway...');
        }

        // Small delay to ensure server is fully ready
        await new Promise(resolve => setTimeout(resolve, 500));

        // Now connect to WebSocket
        connectWebSocket();
    }, [connectWebSocket]);

    const endCall = useCallback(() => {
        if (ws.current) ws.current.close();
        stopAudioPlayback();
        stopRecording();
        // UI reset happens in ws.onclose -> handleCallEnded
    }, [stopAudioPlayback, stopRecording]);


    return {
        isCallActive,
        isAgentSpeaking,
        isWaitingForResponse,
        isWakingServer,
        transcript,
        audioLevel,
        startCall,
        endCall
    };
}
