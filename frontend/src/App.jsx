import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, Brain, CheckCircle2, AlertTriangle, 
  Activity, Save, Database, Sparkles, RefreshCw, FileText, 
  Search, ListPlus, Sliders, Layers, Terminal, Trash2, X, ChevronRight, Zap, Check, Info, ArrowUpRight
} from 'lucide-react';
import { 
  fetchHealth, parseRawLog, createIncident, listIncidents, 
  analyzeIncident, resolveIncident, searchMemories, resetSystem 
} from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('intake');
  const [health, setHealth] = useState(null);
  
  // Incidents & Assessment State
  const [incidentsList, setIncidentsList] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [assessment, setAssessment] = useState(null);
  const [loading, setLoading] = useState(false);

  // Intake Form State
  const [service, setService] = useState('recommendation-engine');
  const [environment, setEnvironment] = useState('production');
  const [severity, setSeverity] = useState('high');
  const [summary, setSummary] = useState('');
  const [symptoms, setSymptoms] = useState('');
  const [rawLogs, setRawLogs] = useState('');
  const [recentChanges, setRecentChanges] = useState('');
  const [parsing, setParsing] = useState(false);

  // Resolution Form State
  const [rootCause, setRootCause] = useState('');
  const [actualFix, setActualFix] = useState('');
  const [failedAttempts, setFailedAttempts] = useState('');
  const [retaining, setRetaining] = useState(false);
  const [resolutionStatus, setResolutionStatus] = useState(null);

  // Memory Detail Modal State
  const [activeMemoryModal, setActiveMemoryModal] = useState(null);

  // Memory Explorer State
  const [searchQuery, setSearchQuery] = useState('');
  const [explorerResults, setExplorerResults] = useState([]);
  const [searching, setSearching] = useState(false);

  // Similarity Filter Threshold
  const [threshold, setThreshold] = useState(0.4);

  useEffect(() => {
    fetchHealth().then(setHealth).catch(console.error);
    loadIncidents();
  }, []);

  const loadIncidents = async () => {
    try {
      const list = await listIncidents();
      setIncidentsList(list);
    } catch (err) {
      console.error(err);
    }
  };

  // System Reset Handler
  const handleResetSystem = async () => {
    if (!window.confirm("Are you sure you want to clear all SQLite incidents and reset Hindsight Cloud memory bank?")) return;
    setLoading(true);
    try {
      await resetSystem();
      setSelectedIncident(null);
      setAssessment(null);
      setExplorerResults([]);
      await loadIncidents();
      alert("System reset completed! Database and Hindsight memory bank are clean.");
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Auto-parse raw logs using Universal AI Parser
  const handleAutoParseLog = async () => {
    if (!rawLogs.trim()) return;
    setParsing(true);
    try {
      const parsed = await parseRawLog(rawLogs);
      setService(parsed.service || service);
      setSeverity(parsed.severity || severity);
      setSummary(parsed.summary || summary);
      setSymptoms((parsed.symptoms || []).join(', '));
      if (parsed.recent_changes) {
        setRecentChanges((parsed.recent_changes || []).join(', '));
      }
    } catch (err) {
      console.error(err);
    } finally {
      setParsing(false);
    }
  };

  // Submit custom incident
  const handleCreateAndAnalyze = async (e) => {
    e.preventDefault();
    setLoading(true);
    setAssessment(null);
    
    // Clear Tab 3 inputs for fresh manual entry
    setRootCause('');
    setActualFix('');
    setFailedAttempts('');
    setResolutionStatus(null);

    try {
      const payload = {
        service,
        environment,
        severity,
        summary: summary || "Custom Production Incident",
        symptoms: symptoms.split(',').map(s => s.trim()).filter(Boolean),
        logs: rawLogs ? [rawLogs] : ["No log trace attached"],
        metrics: { source: "Dynamic Intake" },
        recent_changes: recentChanges ? recentChanges.split(',').map(s => s.trim()).filter(Boolean) : []
      };
      
      const created = await createIncident(payload);
      setSelectedIncident(created);
      await loadIncidents();
      
      const result = await analyzeIncident(created.incident_id);
      setAssessment(result);
      setActiveTab('investigation');
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Select existing incident
  const handleSelectIncident = async (inc) => {
    setSelectedIncident(inc);
    setLoading(true);

    // Clear Tab 3 inputs
    setRootCause('');
    setActualFix('');
    setFailedAttempts('');
    setResolutionStatus(null);

    try {
      const res = await analyzeIncident(inc.incident_id);
      setAssessment(res);
      setActiveTab('investigation');
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Auto-fill Tab 3 fix from Agent Diagnosis
  const handleAutoFillResolution = () => {
    if (!assessment) return;
    if (assessment.hypotheses && assessment.hypotheses.length > 0) {
      setRootCause(assessment.hypotheses[0].statement);
    }
    if (assessment.recommended_actions && assessment.recommended_actions.length > 0) {
      setActualFix(assessment.recommended_actions[0]);
    }
  };

  // Apply resolution template from memory card to Tab 3
  const handleApplyResolutionTemplate = (mem) => {
    if (mem.root_cause) setRootCause(mem.root_cause);
    if (mem.resolution) setActualFix(mem.resolution);
    if (mem.failed_attempts) setFailedAttempts(Array.isArray(mem.failed_attempts) ? mem.failed_attempts.join(", ") : mem.failed_attempts);
    setActiveMemoryModal(null);
    setActiveTab('resolution');
  };

  // Retain resolution
  const handleResolveSubmit = async (e) => {
    e.preventDefault();
    if (!selectedIncident) return;
    setRetaining(true);
    try {
      const res = await resolveIncident(selectedIncident.incident_id, {
        confirmed_root_cause: rootCause,
        actual_resolution: actualFix,
        failed_attempts: failedAttempts.split(',').map(s => s.trim()).filter(Boolean)
      });
      setResolutionStatus(res);
      await loadIncidents();
      
      const updatedAssessment = await analyzeIncident(selectedIncident.incident_id);
      setAssessment(updatedAssessment);
    } catch (err) {
      console.error(err);
    } finally {
      setRetaining(false);
    }
  };

  // Search Hindsight Memory Explorer
  const handleExplorerSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const data = await searchMemories(searchQuery, 10);
      setExplorerResults(data.memories || []);
    } catch (err) {
      console.error(err);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 selection:bg-indigo-500 selection:text-white">
      {/* SaaS Navbar / Header */}
      <header className="border-b border-slate-800/80 bg-[#0c121e]/90 backdrop-blur-md sticky top-0 z-40 px-6 py-3.5">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gradient-to-br from-indigo-500 to-indigo-700 rounded-xl shadow-lg shadow-indigo-500/20">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-base font-bold tracking-tight text-white">Incident Response Agent</h1>
                <span className="text-[10px] font-mono font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded-full">
                  PRO
                </span>
              </div>
              <p className="text-[11px] text-slate-400">Autonomous Operations Copilot & Hindsight Memory System</p>
            </div>
          </div>

          {/* Controls & Telemetry */}
          <div className="flex items-center space-x-3 text-xs font-mono">
            <button
              onClick={handleResetSystem}
              disabled={loading}
              className="flex items-center space-x-1.5 bg-rose-500/10 text-rose-400 border border-rose-500/20 hover:bg-rose-500/20 px-3 py-1.5 rounded-lg font-semibold transition"
            >
              <Trash2 className="w-3.5 h-3.5 text-rose-400" />
              <span>Reset System</span>
            </button>

            <div className="flex items-center space-x-2 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
              <Database className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-slate-400">Hindsight:</span>
              <span className={health?.hindsight_configured ? "text-emerald-400 font-bold" : "text-amber-400"}>
                {health?.hindsight_configured ? "CONNECTED" : "MOCK"}
              </span>
            </div>

            <div className="flex items-center space-x-2 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
              <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
              <span className="text-slate-400">LLM:</span>
              <span className={health?.groq_configured ? "text-indigo-400 font-bold" : "text-amber-400"}>
                {health?.groq_configured ? "Groq (gpt-oss-120b)" : "Fallback"}
              </span>
            </div>
          </div>
        </div>

        {/* Global Active Incident Context Sync Banner */}
        {selectedIncident && (
          <div className="max-w-7xl mx-auto mt-3 bg-gradient-to-r from-indigo-950/60 to-slate-900 border border-indigo-500/30 rounded-xl px-4 py-2 flex items-center justify-between text-xs">
            <div className="flex items-center space-x-3">
              <span className="font-mono font-bold text-indigo-300 bg-indigo-900/50 px-2.5 py-0.5 rounded border border-indigo-700/50">
                ACTIVE INCIDENT: {selectedIncident.incident_id}
              </span>
              <span className="font-semibold text-white">{selectedIncident.service}</span>
              <span className="text-slate-400 truncate max-w-md">{selectedIncident.summary}</span>
            </div>
            <span className={`text-[10px] font-mono font-bold px-2.5 py-0.5 rounded uppercase border ${
              selectedIncident.status === 'resolved' 
                ? 'bg-emerald-950/80 text-emerald-400 border-emerald-800' 
                : 'bg-amber-950/80 text-amber-400 border-amber-800'
            }`}>
              STATUS: {selectedIncident.status}
            </span>
          </div>
        )}

        {/* Navigation Tabs Bar */}
        <div className="max-w-7xl mx-auto flex space-x-1 mt-3 pt-2 border-t border-slate-800/60">
          <button
            onClick={() => setActiveTab('intake')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-semibold transition ${
              activeTab === 'intake' 
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30' 
                : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
            }`}
          >
            <ListPlus className="w-4 h-4" />
            <span>1. Dynamic Intake & AI Log Parser</span>
          </button>
          
          <button
            onClick={() => setActiveTab('investigation')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-semibold transition ${
              activeTab === 'investigation' 
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30' 
                : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
            }`}
          >
            <Brain className="w-4 h-4" />
            <span>2. Active Investigation ({selectedIncident?.incident_id || 'None'})</span>
          </button>

          <button
            onClick={() => setActiveTab('resolution')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-semibold transition ${
              activeTab === 'resolution' 
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30' 
                : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
            }`}
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>3. Resolution Lab ({selectedIncident?.incident_id || 'None'})</span>
          </button>

          <button
            onClick={() => setActiveTab('explorer')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-semibold transition ${
              activeTab === 'explorer' 
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30' 
                : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
            }`}
          >
            <Search className="w-4 h-4" />
            <span>4. Hindsight Memory Explorer</span>
          </button>
        </div>
      </header>

      {/* Main Content Workspace */}
      <main className="max-w-7xl mx-auto p-6">
        
        {/* ================= TAB 1: DYNAMIC INTAKE & AI LOG PARSER ================= */}
        {activeTab === 'intake' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Box: Intake & Log Parser */}
            <div className="lg:col-span-7 bg-[#0d1322] border border-slate-800/80 rounded-2xl p-6 space-y-5 shadow-2xl">
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-3.5">
                <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-indigo-400" />
                  Universal AI Log Parser & Intake Studio
                </h2>
              </div>

              <form onSubmit={handleCreateAndAnalyze} className="space-y-4 text-xs">
                {/* Code-Editor Log Trace Terminal */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-slate-300 font-semibold flex items-center gap-2">
                      <span>Raw Server Log Trace / Stack Trace Dump:</span>
                      <span className="text-[10px] text-slate-400 font-mono font-normal">(Python, Java, Go, Rust, K8s, SQL)</span>
                    </label>
                    <button
                      type="button"
                      onClick={handleAutoParseLog}
                      disabled={parsing || !rawLogs.trim()}
                      className="flex items-center space-x-1.5 bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-500/20 px-3 py-1 rounded-lg text-xs font-semibold transition"
                    >
                      <Zap className="w-3.5 h-3.5 text-indigo-400" />
                      <span>{parsing ? "AI Normalizing..." : "Universal AI Log Extract"}</span>
                    </button>
                  </div>

                  <div className="relative rounded-xl overflow-hidden border border-slate-800 bg-[#060911]">
                    <div className="bg-slate-900/90 px-3 py-1.5 border-b border-slate-800 flex items-center justify-between text-[11px] font-mono text-slate-400">
                      <span>console_output.log</span>
                      <span>UTF-8</span>
                    </div>
                    <textarea
                      rows={5}
                      value={rawLogs}
                      onChange={(e) => setRawLogs(e.target.value)}
                      placeholder="Paste raw error log stack trace here..."
                      className="w-full bg-transparent p-3.5 text-rose-300 font-mono text-xs focus:outline-none resize-y"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="block text-slate-300 font-semibold mb-1">Target Service:</label>
                    <input
                      type="text"
                      value={service}
                      onChange={(e) => setService(e.target.value)}
                      className="w-full bg-[#060911] border border-slate-800 rounded-lg p-2.5 text-slate-100 focus:border-indigo-500 font-mono"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-slate-300 font-semibold mb-1">Environment:</label>
                    <select
                      value={environment}
                      onChange={(e) => setEnvironment(e.target.value)}
                      className="w-full bg-[#060911] border border-slate-800 rounded-lg p-2.5 text-slate-100"
                    >
                      <option value="production">production</option>
                      <option value="staging">staging</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-slate-300 font-semibold mb-1">Severity:</label>
                    <select
                      value={severity}
                      onChange={(e) => setSeverity(e.target.value)}
                      className="w-full bg-[#060911] border border-slate-800 rounded-lg p-2.5 text-slate-100 font-semibold"
                    >
                      <option value="high">high</option>
                      <option value="critical">critical</option>
                      <option value="medium">medium</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Incident Summary:</label>
                  <input
                    type="text"
                    value={summary}
                    onChange={(e) => setSummary(e.target.value)}
                    placeholder="e.g. Inference requests timing out with CUDA memory exhaustion"
                    className="w-full bg-[#060911] border border-slate-800 rounded-lg p-2.5 text-slate-100 focus:border-indigo-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Symptoms (Comma separated):</label>
                  <input
                    type="text"
                    value={symptoms}
                    onChange={(e) => setSymptoms(e.target.value)}
                    placeholder="e.g. CUDA out of memory, P99 latency > 5000ms"
                    className="w-full bg-[#060911] border border-slate-800 rounded-lg p-2.5 text-slate-100"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Recent Changes / Deployments:</label>
                  <input
                    type="text"
                    value={recentChanges}
                    onChange={(e) => setRecentChanges(e.target.value)}
                    placeholder="e.g. Batch size increased from 16 to 64 two hours ago"
                    className="w-full bg-[#060911] border border-slate-800 rounded-lg p-2.5 text-slate-100"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex items-center justify-center space-x-2 bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white font-semibold py-3 rounded-xl transition shadow-lg shadow-indigo-600/25"
                >
                  <Brain className="w-4 h-4" />
                  <span>{loading ? "Analyzing with Hindsight Memory..." : "Submit Incident & Trigger AI Agent Diagnosis"}</span>
                </button>
              </form>
            </div>

            {/* Right Box: SQLite Incidents Queue */}
            <div className="lg:col-span-5 bg-[#0d1322] border border-slate-800/80 rounded-2xl p-6 space-y-4 shadow-2xl">
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-3.5">
                <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                  <Database className="w-4 h-4 text-emerald-400" />
                  Persisted Incidents Queue (SQLite DB)
                </h2>
                <button onClick={loadIncidents} className="text-xs text-slate-400 hover:text-white p-1">
                  <RefreshCw className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="space-y-2.5 max-h-[520px] overflow-y-auto pr-1">
                {incidentsList.length === 0 ? (
                  <p className="text-xs text-slate-500 italic p-6 text-center">No persistent incidents recorded in database yet.</p>
                ) : (
                  incidentsList.map((inc) => (
                    <div 
                      key={inc.incident_id}
                      onClick={() => handleSelectIncident(inc)}
                      className={`p-4 rounded-xl border text-xs cursor-pointer transition ${
                        selectedIncident?.incident_id === inc.incident_id
                          ? 'bg-indigo-950/60 border-indigo-500 text-slate-100 shadow-md'
                          : 'bg-[#060911] border-slate-800/80 hover:border-slate-700 text-slate-300'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-mono font-bold text-indigo-400 bg-indigo-950/80 px-2 py-0.5 rounded border border-indigo-900/50">
                          {inc.incident_id}
                        </span>
                        <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-mono font-bold ${
                          inc.status === 'resolved' 
                            ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800' 
                            : 'bg-amber-950/80 text-amber-400 border border-amber-800'
                        }`}>
                          {inc.status}
                        </span>
                      </div>
                      <div className="font-semibold text-white">{inc.service}</div>
                      <p className="text-slate-400 mt-1 line-clamp-1">{inc.summary}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* ================= TAB 2: ACTIVE INVESTIGATION COMMAND CENTER ================= */}
        {activeTab === 'investigation' && (
          <div className="space-y-6">
            {!selectedIncident ? (
              <div className="bg-[#0d1322] border border-slate-800 rounded-2xl p-12 text-center text-slate-400">
                <ShieldAlert className="w-8 h-8 text-amber-400 mx-auto mb-3" />
                <p className="text-sm">No active incident selected. Select or parse an incident in Tab 1.</p>
              </div>
            ) : (
              <>
                {/* Failed Approach Warning Banner */}
                {assessment?.warnings && assessment.warnings.length > 0 && (
                  <div className="bg-rose-950/30 border border-rose-500/40 rounded-2xl p-5 space-y-2 shadow-xl">
                    <div className="flex items-center space-x-2 text-rose-400 font-bold text-xs">
                      <AlertTriangle className="w-4 h-4" />
                      <span>HINDSIGHT FAILED APPROACH WARNINGS</span>
                    </div>
                    <ul className="text-xs text-rose-200/90 space-y-1.5 pl-6 list-disc font-medium">
                      {assessment.warnings.map((w, idx) => (
                        <li key={idx}>{w}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Hindsight Memory Recall Visualizer */}
                <div className="bg-[#0d1322] border border-slate-800/80 rounded-2xl p-6 space-y-5 shadow-2xl">
                  <div className="flex items-center justify-between border-b border-slate-800/80 pb-3.5">
                    <div className="flex items-center space-x-2">
                      <Database className="w-4 h-4 text-emerald-400" />
                      <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                        Recalled Organizational Experience for [{selectedIncident.incident_id}]
                      </h2>
                    </div>

                    <div className="flex items-center space-x-3 text-xs font-mono">
                      <span className="text-slate-400">Similarity Filter:</span>
                      <input
                        type="range"
                        min="0.4"
                        max="1.0"
                        step="0.05"
                        value={threshold}
                        onChange={(e) => setThreshold(parseFloat(e.target.value))}
                        className="accent-indigo-500 cursor-pointer"
                      />
                      <span className="text-indigo-400 font-bold">{(threshold * 100).toFixed(0)}%</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {assessment?.historical_evidence?.matches?.filter(m => m.score >= threshold).length === 0 ? (
                      <p className="text-xs text-slate-500 italic col-span-2 p-6 text-center">
                        No historical memories meet similarity threshold ({(threshold * 100).toFixed(0)}%). Investigating from current evidence.
                      </p>
                    ) : (
                      assessment?.historical_evidence?.matches?.filter(m => m.score >= threshold).map((match, idx) => (
                        <div 
                          key={idx} 
                          onClick={() => setActiveMemoryModal(match)}
                          className="bg-[#060911] border border-slate-800/80 hover:border-indigo-500/60 rounded-xl p-4 text-xs space-y-3 cursor-pointer transition shadow-lg group"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-indigo-300 group-hover:text-indigo-200 flex items-center gap-1">
                              Memory Match #{idx + 1}
                              <ChevronRight className="w-3.5 h-3.5 text-indigo-400" />
                            </span>
                            <span className="font-mono bg-indigo-950 text-indigo-300 border border-indigo-800 px-2.5 py-0.5 rounded-full text-[11px] font-bold">
                              {(match.score * 100).toFixed(0)}% Similarity
                            </span>
                          </div>
                          <p className="text-slate-300 leading-relaxed line-clamp-3">{match.content}</p>
                          {match.failed_attempts && match.failed_attempts.length > 0 && (
                            <div className="text-rose-400 font-mono text-[11px] bg-rose-950/40 border border-rose-900/40 p-2 rounded-lg">
                              ⚠️ Failed Action Recorded: {match.failed_attempts.join(", ")}
                            </div>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Hypotheses & Action Plan */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-[#0d1322] border border-slate-800/80 rounded-2xl p-5 space-y-4 shadow-2xl">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-2">
                      <Brain className="w-4 h-4" />
                      Formulated Hypotheses
                    </h3>
                    <div className="space-y-2.5">
                      {assessment?.hypotheses?.map((h, idx) => (
                        <div key={idx} className="bg-[#060911] border border-indigo-950/60 rounded-xl p-3.5 text-xs space-y-1.5">
                          <div className="font-semibold text-slate-100">{h.statement}</div>
                          <div className="text-slate-400 text-[11px]">Evidence: {h.evidence.join("; ")}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="bg-[#0d1322] border border-slate-800/80 rounded-2xl p-5 space-y-4 shadow-2xl">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4" />
                      Recommended Investigation Action Plan
                    </h3>
                    <ol className="space-y-2 text-xs">
                      {assessment?.recommended_actions?.map((act, idx) => (
                        <li key={idx} className="flex items-start space-x-2.5 bg-[#060911] p-3 rounded-xl border border-slate-800">
                          <span className="font-mono text-indigo-400 font-bold">{idx + 1}.</span>
                          <span className="text-slate-200 leading-relaxed">{act}</span>
                        </li>
                      ))}
                    </ol>
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {/* TAB 3: RESOLUTION & RETAIN LAB */}
        {activeTab === 'resolution' && (
          <div className="max-w-3xl mx-auto bg-[#0d1322] border border-slate-800/80 rounded-2xl p-6 space-y-6 shadow-2xl">
            {!selectedIncident ? (
              <div className="p-8 text-center text-slate-400">
                <ShieldAlert className="w-8 h-8 text-amber-400 mx-auto mb-3" />
                <p className="text-sm">No active incident selected. Please select an incident in Tab 1.</p>
              </div>
            ) : (
              <>
                <div className="border-b border-slate-800/80 pb-4">
                  <div className="flex items-center justify-between">
                    <h2 className="text-sm font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-2">
                      <Save className="w-4 h-4" />
                      Resolution Lab for [{selectedIncident.incident_id}]
                    </h2>
                    <button
                      type="button"
                      onClick={handleAutoFillResolution}
                      className="flex items-center space-x-1.5 bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-500/20 px-3 py-1 rounded-lg text-xs font-semibold transition"
                    >
                      <Zap className="w-3.5 h-3.5 text-indigo-400" />
                      <span>Auto-Fill Fix from AI Diagnosis</span>
                    </button>
                  </div>
                  <div className="text-xs text-slate-300 mt-2 bg-[#060911] p-3 rounded-xl border border-slate-800">
                    <div className="font-semibold text-white">{selectedIncident.service}: {selectedIncident.summary}</div>
                  </div>
                </div>

                <form onSubmit={handleResolveSubmit} className="space-y-4 text-xs">
                  <div>
                    <label className="block text-slate-300 font-semibold mb-1">Confirmed Root Cause:</label>
                    <input
                      type="text"
                      value={rootCause}
                      onChange={(e) => setRootCause(e.target.value)}
                      placeholder="e.g. Batch size increased to 64 exceeded GPU VRAM during concurrent inference"
                      className="w-full bg-[#060911] border border-slate-800 rounded-lg p-3 text-slate-100 focus:border-indigo-500"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-slate-300 font-semibold mb-1">Confirmed Resolution / Fix:</label>
                    <input
                      type="text"
                      value={actualFix}
                      onChange={(e) => setActualFix(e.target.value)}
                      placeholder="e.g. Reduced batch size from 64 back to 16 in config"
                      className="w-full bg-[#060911] border border-slate-800 rounded-lg p-3 text-slate-100 focus:border-indigo-500"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-slate-300 font-semibold mb-1">Failed Fix Attempts (Comma separated):</label>
                    <input
                      type="text"
                      value={failedAttempts}
                      onChange={(e) => setFailedAttempts(e.target.value)}
                      placeholder="e.g. Restarted GPU inference pods, Cleared token cache"
                      className="w-full bg-[#060911] border border-slate-800 rounded-lg p-3 text-slate-100 focus:border-indigo-500"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={retaining}
                    className="w-full flex items-center justify-center space-x-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-3.5 rounded-xl transition shadow-lg shadow-emerald-600/25"
                  >
                    <Save className="w-4 h-4" />
                    <span>{retaining ? "Retaining into Hindsight Cloud Bank..." : `Confirm & Retain Fix for ${selectedIncident.incident_id}`}</span>
                  </button>
                </form>

                {resolutionStatus && (
                  <div className="bg-emerald-950/60 border border-emerald-500/40 p-4 rounded-xl text-xs text-emerald-300 flex items-start space-x-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                    <div>
                      <div className="font-bold">Retain Successful!</div>
                      <p className="mt-0.5">{resolutionStatus.message}</p>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* TAB 4: HINDSIGHT MEMORY EXPLORER */}
        {activeTab === 'explorer' && (
          <div className="space-y-6">
            <div className="bg-[#0d1322] border border-slate-800/80 rounded-2xl p-6 space-y-4 shadow-2xl">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
                <Search className="w-4 h-4 text-indigo-400" />
                Direct Hindsight Memory Bank Explorer
              </h2>

              <form onSubmit={handleExplorerSearch} className="flex space-x-3 text-xs">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Enter search query (e.g. CUDA memory, Redis pool, Auth 500, Batch size)..."
                  className="flex-1 bg-[#060911] border border-slate-800 rounded-xl p-3.5 text-slate-100 focus:outline-none focus:border-indigo-500"
                />
                <button
                  type="submit"
                  disabled={searching}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-6 py-3.5 rounded-xl transition flex items-center space-x-2"
                >
                  <Search className="w-4 h-4" />
                  <span>{searching ? "Searching..." : "Search Bank"}</span>
                </button>
              </form>

              <div className="space-y-3 pt-2">
                {explorerResults.length === 0 ? (
                  <p className="text-xs text-slate-500 italic p-6 text-center">Enter a search query to inspect stored memories in Hindsight Cloud.</p>
                ) : (
                  explorerResults.map((mem, idx) => (
                    <div 
                      key={idx} 
                      onClick={() => setActiveMemoryModal(mem)}
                      className="bg-[#060911] border border-slate-800/80 hover:border-indigo-500/60 rounded-xl p-4 text-xs space-y-2 cursor-pointer transition group shadow-md"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-indigo-400 font-bold group-hover:text-indigo-300">Memory #{idx + 1} ({mem.memory_id || 'Cloud ID'})</span>
                        <span className="font-mono bg-indigo-950 text-indigo-300 border border-indigo-800 px-2.5 py-0.5 rounded-full text-[11px] font-bold">
                          Score: {((mem.score || 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-slate-200 leading-relaxed">{mem.content}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* EXPANDABLE MEMORY DETAIL MODAL */}
        {activeMemoryModal && (
          <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-6 z-50">
            <div className="bg-[#0d1322] border border-slate-700/80 rounded-2xl max-w-2xl w-full p-6 space-y-5 shadow-2xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3.5">
                <div className="flex items-center space-x-2">
                  <Database className="w-5 h-5 text-indigo-400" />
                  <h3 className="text-sm font-bold text-white">Detailed Hindsight Memory Inspection</h3>
                </div>
                <button onClick={() => setActiveMemoryModal(null)} className="text-slate-400 hover:text-white p-1">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-3.5 text-xs">
                <div>
                  <div className="text-slate-400 font-semibold mb-1">Full Memory Text:</div>
                  <p className="bg-[#060911] p-3.5 rounded-xl border border-slate-800 text-slate-200 leading-relaxed font-sans">
                    {activeMemoryModal.content}
                  </p>
                </div>

                {activeMemoryModal.root_cause && (
                  <div>
                    <div className="text-slate-400 font-semibold mb-1">Recorded Root Cause:</div>
                    <div className="bg-[#060911] p-3 rounded-xl border border-slate-800 text-indigo-300">
                      {activeMemoryModal.root_cause}
                    </div>
                  </div>
                )}

                {activeMemoryModal.resolution && (
                  <div>
                    <div className="text-slate-400 font-semibold mb-1">Verified Resolution:</div>
                    <div className="bg-[#060911] p-3 rounded-xl border border-slate-800 text-emerald-300 font-medium">
                      {activeMemoryModal.resolution}
                    </div>
                  </div>
                )}

                {activeMemoryModal.failed_attempts && activeMemoryModal.failed_attempts.length > 0 && (
                  <div>
                    <div className="text-rose-400 font-semibold mb-1">Recorded Failed Fix Attempts:</div>
                    <div className="bg-rose-950/40 p-3 rounded-xl border border-rose-900/50 text-rose-300 font-mono">
                      ⚠️ {Array.isArray(activeMemoryModal.failed_attempts) ? activeMemoryModal.failed_attempts.join(", ") : activeMemoryModal.failed_attempts}
                    </div>
                  </div>
                )}
              </div>

              <div className="flex items-center justify-between border-t border-slate-800 pt-4">
                <button
                  type="button"
                  onClick={() => handleApplyResolutionTemplate(activeMemoryModal)}
                  className="flex items-center space-x-2 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2.5 rounded-xl font-semibold text-xs transition shadow-lg shadow-emerald-600/20"
                >
                  <Save className="w-4 h-4" />
                  <span>🚀 Apply Resolution as Fix Template in Tab 3</span>
                </button>
                <button
                  onClick={() => setActiveMemoryModal(null)}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-300 px-4 py-2.5 rounded-xl text-xs font-semibold"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

      </main>
    </div>
  );
}