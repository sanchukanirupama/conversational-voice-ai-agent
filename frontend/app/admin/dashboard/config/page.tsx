"use client";
import { useState, useEffect } from 'react';
import { Save, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ConfigData {
  metadata?: any;
  system_persona?: string;
  greeting?: string;
  verification_prompts?: any;
  routing_flows?: any;
  escalation_strategies?: any;
  stt_prompt?: string;
}

export default function ConfigEditorPage() {
  const [config, setConfig] = useState<ConfigData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [expandedFlows, setExpandedFlows] = useState<Record<string, boolean>>({});
  const [activeTab, setActiveTab] = useState<'forms' | 'json'>('forms');

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('admin_token');
      const response = await fetch(`${API_BASE_URL}/admin/config`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setConfig(data);
      } else {
        setMessage({ type: 'error', text: 'Failed to load configuration' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error loading configuration' });
    } finally {
      setIsLoading(false);
    }
  };

  const saveConfig = async () => {
    if (!config) return;

    setIsSaving(true);
    setMessage(null);

    try {
      const token = localStorage.getItem('admin_token');
      const response = await fetch(`${API_BASE_URL}/admin/config`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ config }),
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Configuration saved successfully!' });
        setTimeout(() => setMessage(null), 3000);
      } else {
        setMessage({ type: 'error', text: 'Failed to save configuration' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error saving configuration' });
    } finally {
      setIsSaving(false);
    }
  };

  const updateConfig = (path: string, value: any) => {
    if (!config) return;
    
    const newConfig = { ...config };
    const keys = path.split('.');
    let current: any = newConfig;
    
    for (let i = 0; i < keys.length - 1; i++) {
      current = current[keys[i]];
    }
    
    current[keys[keys.length - 1]] = value;
    setConfig(newConfig);
  };

  const updateFlowField = (flowKey: string, field: string, value: any) => {
    if (!config?.routing_flows) return;
    
    const newConfig = { ...config };
    newConfig.routing_flows[flowKey][field] = value;
    setConfig(newConfig);
  };

  const updateFlowInstructionList = (flowKey: string, instructionType: string, index: number, value: string) => {
    if (!config?.routing_flows) return;
    
    const newConfig = { ...config };
    const instructions = [...(newConfig.routing_flows[flowKey].flow_instructions[instructionType] || [])];
    instructions[index] = value;
    newConfig.routing_flows[flowKey].flow_instructions[instructionType] = instructions;
    setConfig(newConfig);
  };

  const addFlowInstruction = (flowKey: string, instructionType: string) => {
    if (!config?.routing_flows) return;
    
    const newConfig = { ...config };
    const instructions = [...(newConfig.routing_flows[flowKey].flow_instructions[instructionType] || [])];
    instructions.push('');
    newConfig.routing_flows[flowKey].flow_instructions[instructionType] = instructions;
    setConfig(newConfig);
  };

  const removeFlowInstruction = (flowKey: string, instructionType: string, index: number) => {
    if (!config?.routing_flows) return;
    
    const newConfig = { ...config };
    const instructions = [...(newConfig.routing_flows[flowKey].flow_instructions[instructionType] || [])];
    instructions.splice(index, 1);
    newConfig.routing_flows[flowKey].flow_instructions[instructionType] = instructions;
    setConfig(newConfig);
  };

  const toggleFlow = (flowKey: string) => {
    setExpandedFlows(prev => ({ ...prev, [flowKey]: !prev[flowKey] }));
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-white/60">Loading configuration...</div>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-red-400">Failed to load configuration</div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">Configuration Editor</h1>
          <p className="text-white/50 mt-1">Manage AI agent behavior and flow settings</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={fetchConfig}
            disabled={isLoading}
            className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 text-white rounded-xl transition-all disabled:opacity-50"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button
            onClick={saveConfig}
            disabled={isSaving}
            className="flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white rounded-xl transition-all disabled:opacity-50 shadow-lg shadow-emerald-500/20"
          >
            <Save className="w-4 h-4" />
            {isSaving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      {/* Message */}
      {message && (
        <div className={`mb-6 p-4 rounded-xl ${
          message.type === 'success'
            ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400'
            : 'bg-red-500/10 border border-red-500/30 text-red-400'
        }`}>
          {message.text}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-white/10">
        <button
          onClick={() => setActiveTab('forms')}
          className={`px-6 py-3 font-medium transition-all ${
            activeTab === 'forms'
              ? 'text-white border-b-2 border-emerald-500'
              : 'text-white/50 hover:text-white/80'
          }`}
        >
          Detailed Forms
        </button>
        <button
          onClick={() => setActiveTab('json')}
          className={`px-6 py-3 font-medium transition-all ${
            activeTab === 'json'
              ? 'text-white border-b-2 border-emerald-500'
              : 'text-white/50 hover:text-white/80'
          }`}
        >
          Advanced JSON Editor
        </button>
      </div>

      {/* Configuration Sections */}
      {activeTab === 'forms' ? (
        <div className="space-y-6">
          {/* System Persona */}
          <section className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-6">
            <h2 className="text-xl font-semibold text-white mb-4">System Persona</h2>
            <p className="text-white/60 text-sm mb-4">Core AI agent behavior and rules</p>
            <textarea
              value={config.system_persona || ''}
              onChange={(e) => updateConfig('system_persona', e.target.value)}
              className="w-full h-40 px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white text-sm placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-none font-mono"
              placeholder="System persona..."
            />
          </section>

          {/* Greeting */}
          <section className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-6">
            <h2 className="text-xl font-semibold text-white mb-4">Greeting Message</h2>
            <p className="text-white/60 text-sm mb-4">Initial message when call starts</p>
            <input
              type="text"
              value={config.greeting || ''}
              onChange={(e) => updateConfig('greeting', e.target.value)}
              className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              placeholder="Greeting message..."
            />
          </section>

          {/* Routing Flows */}
          <section className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-6">
            <h2 className="text-2xl font-semibold text-white mb-2">Routing Flows</h2>
            <p className="text-white/60 text-sm mb-6">Configure each flow's behavior, tools, and instructions</p>
            
            <div className="space-y-4">
              {config.routing_flows && Object.entries(config.routing_flows).map(([flowKey, flowData]: [string, any]) => (
                <div key={flowKey} className="border border-white/20 rounded-lg overflow-hidden">
                  {/* Flow Header */}
                  <button
                    onClick={() => toggleFlow(flowKey)}
                    className="w-full flex items-center justify-between p-4 bg-white/5 hover:bg-white/10 transition-all"
                  >
                    <div className="flex items-center gap-3">
                      {expandedFlows[flowKey] ? (
                        <ChevronUp className="w-5 h-5 text-white/60" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-white/60" />
                      )}
                      <div className="text-left">
                        <h3 className="text-lg font-semibold text-white">{flowKey.replace(/_/g, ' ').toUpperCase()}</h3>
                        <p className="text-sm text-white/60">{flowData.description}</p>
                      </div>
                    </div>
                    <span className="text-xs text-white/40">ID: {flowData.id}</span>
                  </button>

                  {/* Flow Content (Expandable) */}
                  {expandedFlows[flowKey] && (
                    <div className="p-6 space-y-6 bg-black/20">
                      {/* Basic Settings */}
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-white/80 mb-2">Description</label>
                          <textarea
                            value={flowData.description || ''}
                            onChange={(e) => updateFlowField(flowKey, 'description', e.target.value)}
                            className="w-full h-20 px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-none"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-white/80 mb-2">Settings</label>
                          <div className="space-y-2">
                            <label className="flex items-center gap-2 text-white/80 text-sm">
                              <input
                                type="checkbox"
                                checked={flowData.requires_verification || false}
                                onChange={(e) => updateFlowField(flowKey, 'requires_verification', e.target.checked)}
                                className="w-4 h-4"
                              />
                              Requires Identity Verification
                            </label>
                            <div>
                              <label className="block text-xs text-white/60 mb-1">Max Questions Before Escalation (null = unlimited)</label>
                              <input
                                type="number"
                                value={flowData.max_questions_before_escalation ?? ''}
                                onChange={(e) => updateFlowField(flowKey, 'max_questions_before_escalation', e.target.value === '' ? null : parseInt(e.target.value))}
                                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                                placeholder="null"
                              />
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Keywords */}
                      <div>
                        <label className="block text-sm font-medium text-white/80 mb-2">Strict Keywords (comma-separated)</label>
                        <textarea
                          value={(flowData.strict_keywords || []).join(', ')}
                          onChange={(e) => updateFlowField(flowKey, 'strict_keywords', e.target.value.split(',').map(k => k.trim()).filter(k => k))}
                          className="w-full h-20 px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-none"
                          placeholder="block card, freeze card, lost card..."
                        />
                      </div>

                      {/* Tools */}
                      <div>
                        <label className="block text-sm font-medium text-white/80 mb-2">Available Tools (comma-separated)</label>
                        <input
                          type="text"
                          value={(flowData.tools || []).join(', ')}
                          onChange={(e) => updateFlowField(flowKey, 'tools', e.target.value.split(',').map(t => t.trim()).filter(t => t))}
                          className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                          placeholder="t_verify_identity, t_block_card..."
                        />
                      </div>

                      {/* Pre-Verification Instructions */}
                      {flowData.flow_instructions?.pre_verification && (
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <label className="text-sm font-medium text-white/80">Pre-Verification Instructions</label>
                            <button
                              onClick={() => addFlowInstruction(flowKey, 'pre_verification')}
                              className="text-xs px-3 py-1 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded"
                            >
                              + Add
                            </button>
                          </div>
                          <div className="space-y-2">
                            {flowData.flow_instructions.pre_verification.map((instruction: string, idx: number) => (
                              <div key={idx} className="flex gap-2">
                                <input
                                  type="text"
                                  value={instruction}
                                  onChange={(e) => updateFlowInstructionList(flowKey, 'pre_verification', idx, e.target.value)}
                                  className="flex-1 px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                                  placeholder={`Instruction ${idx + 1}...`}
                                />
                                <button
                                  onClick={() => removeFlowInstruction(flowKey, 'pre_verification', idx)}
                                  className="px-3 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded"
                                >
                                  ×
                                </button>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Post-Verification Instructions */}
                      {flowData.flow_instructions?.post_verification && (
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <label className="text-sm font-medium text-white/80">Post-Verification Instructions</label>
                            <button
                              onClick={() => addFlowInstruction(flowKey, 'post_verification')}
                              className="text-xs px-3 py-1 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded"
                            >
                              + Add
                            </button>
                          </div>
                          <div className="space-y-2">
                            {flowData.flow_instructions.post_verification.map((instruction: string, idx: number) => (
                              <div key={idx} className="flex gap-2">
                                <input
                                  type="text"
                                  value={instruction}
                                  onChange={(e) => updateFlowInstructionList(flowKey, 'post_verification', idx, e.target.value)}
                                  className="flex-1 px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                                  placeholder={`Instruction ${idx + 1}...`}
                                />
                                <button
                                  onClick={() => removeFlowInstruction(flowKey, 'post_verification', idx)}
                                  className="px-3 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded"
                                >
                                  ×
                                </button>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Edge Cases */}
                      {flowData.flow_instructions?.edge_cases && (
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <label className="text-sm font-medium text-white/80">Edge Cases</label>
                            <button
                              onClick={() => addFlowInstruction(flowKey, 'edge_cases')}
                              className="text-xs px-3 py-1 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded"
                            >
                              + Add
                            </button>
                          </div>
                          <div className="space-y-2">
                            {flowData.flow_instructions.edge_cases.map((edgeCase: string, idx: number) => (
                              <div key={idx} className="flex gap-2">
                                <input
                                  type="text"
                                  value={edgeCase}
                                  onChange={(e) => updateFlowInstructionList(flowKey, 'edge_cases', idx, e.target.value)}
                                  className="flex-1 px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                                  placeholder={`Edge case ${idx + 1}...`}
                                />
                                <button
                                  onClick={() => removeFlowInstruction(flowKey, 'edge_cases', idx)}
                                  className="px-3 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded"
                                >
                                  ×
                                </button>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>

          {/* Escalation Strategies */}
          {config.escalation_strategies && (
            <section className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-6">
              <h2 className="text-xl font-semibold text-white mb-4">Escalation Messages</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">
                    Deep Flows Default Message
                  </label>
                  <textarea
                    value={config.escalation_strategies.deep_flows_default_message || ''}
                    onChange={(e) => updateConfig('escalation_strategies.deep_flows_default_message', e.target.value)}
                    className="w-full h-20 px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white text-sm placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-none"
                  />
                </div>
                {config.escalation_strategies.escalation_message_templates && 
                  Object.entries(config.escalation_strategies.escalation_message_templates).map(([key, value]) => (
                    <div key={key}>
                      <label className="block text-sm font-medium text-white/80 mb-2 capitalize">
                        {key.replace(/_/g, ' ')}
                      </label>
                      <textarea
                        value={value as string || ''}
                        onChange={(e) => updateConfig(`escalation_strategies.escalation_message_templates.${key}`, e.target.value)}
                        className="w-full h-20 px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white text-sm placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-none"
                      />
                    </div>
                  ))
                }
              </div>
            </section>
          )}
        </div>
      ) : (
        /* JSON Editor Tab */
        <section className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Advanced: Full JSON Editor</h2>
          <p className="text-white/60 text-sm mb-4">Direct JSON editing for advanced configuration</p>
          <textarea
            value={JSON.stringify(config, null, 2)}
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value);
                setConfig(parsed);
              } catch (err) {
                // Invalid JSON, don't update
              }
            }}
            className="w-full h-[600px] px-4 py-3 bg-black/40 border border-white/20 rounded-lg text-white text-sm font-mono placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-none"
          />
        </section>
      )}
    </div>
  );
}
