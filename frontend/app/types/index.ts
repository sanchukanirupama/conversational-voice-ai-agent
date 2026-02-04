export interface AgentState {
    isCallActive: boolean;
    isAgentSpeaking: boolean;
    isWaitingForResponse: boolean;
    transcript: string[];
    audioLevel: number;
}

export interface RingingNodes {
    osc1: OscillatorNode;
    osc2: OscillatorNode;
    gain: GainNode;
}

export interface WSMessage {
    type: 'audio' | 'text' | 'timeout';
    content?: string;
    audio?: string;
    data?: string;
}
