import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, Brain, CheckCircle2, AlertTriangle, 
  Activity, ArrowRight, Save, Database, Sparkles, RefreshCw 
} from 'lucide-react';
import { fetchHealth, createIncident, analyzeIncident, resolveIncident } from './services/api';

export default function App() {
  const [health, setHealth] = useState(null);
  const [currentIncident, setCurrentIncident] = useState(null);
  const [assessment, setAssessment] = useState(null);
  const [loading, setLoading] = useState(false);
  const [retaining, setRetaining] = useState(false);
  const [resolvedStatus, setResolvedStatus] = useState(null);

  // Form states for resolution confirmation
  const [rootCause, setRootCause] = useState("");
  const [fix, setFix] = useState("");
  const [failedAttempts, setFailedAttempts] = useState("Restarted GPU inference pods");

  useEffect(() => {
    fetchHealth().then(setHealth).catch(console.error);
  }, []);

  // Demo Incident Preset Loaders
  const loadDemoIncident = async (type) => {
    setLoading(true);
    setAssessment(null);
    setResolvedStatus(null);

    let payload;
    if (type === 'INC-2001') {
      payload = {
        service: "recommendation-engine",
        summary: "Inference requests timing out with CUDA memory exhaustion",
        symptoms: ["CUDA out of memory", "P99 latency > 5000ms"],
        logs: ["RuntimeError: CUDA out of memory. Tried to allocate 2.00 GiB on GPU 0"],
        metrics: { gpu_memory: "100%", batch_size: 64 },
        recent_changes: ["Batch size increased from 16 to 64 two hours ago"]
      };
      setRootCause("Batch size increased to 64 exceeded GPU VRAM limit");
      setFix("Reduced batch size back to 16 in config");
    } else {
      payload = {
        service: "recommendation-engine",
        summary: "Recommendation engine timing out under high load",
        symptoms: ["CUDA memory allocation failure", "P99 latency spike"],
        logs: ["RuntimeError: CUDA out of memory on GPU 0"],
        metrics: { gpu_memory: "99%" },
        recent_changes: ["Increased batch size"]
      };
      setRootCause("GPU VRAM saturation due to large batch size");
      setFix("Lowered batch size to 16 and enabled FP16");
    }

    try {
      const inc = await createIncident(payload);
      setCurrentIncident(inc);
      const res = await analyzeIncident(inc.incident_id);
      setAssessment(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleResolve = async (e) => {
    e.preventDefault();
    if (!currentIncident) return;
    setRetaining(true);
    try {
      const res = await resolveIncident(currentIncident.incident_id, {
        confirmed_root_cause: rootCause,
        actual_resolution: fix,
        failed_attempts: failedAttempts.split(',').map(s => s.strip ? s.strip() : s.trim()).filter(Boolean),
        was_agent_helpful: true
      });
      setResolvedStatus(res);
    } catch (err) {
      console.error(err);
    } finally {
      setRetaining(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-6">
      {/* Header */}
      <header className="max-w-7xl mx-auto flex items-center justify-between border-b border-slate-800 pb-4 mb-6">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-indigo-600 rounded-lg">
            <Brain className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-wide">Incident Response Agent</h1>
            <p className="text-xs text-slate-400">AI Operations Copilot with Persistent Hindsight Memory</p>
          </div>
        </div>

        {/* Health Status Badges */}
        <div className="flex items-center space-x-4 text-xs font-mono">
          <div className="flex items-center space-x-2 bg-slate-800 px-3 py-1.5 rounded-full border border-slate-700">
            <Database className="w-3.5 h-3.5 text-emerald-400" />
            <span>Hindsight Bank:</span>
            <span className={health?.hindsight_configured ? "text-emerald-400 font-bold" : "text-amber-400"}>
              {health?.hindsight_configured ? "CONNECTED" : "MOCK"}
            </span>
          </div>
          <div className="flex items-center space-x-2 bg-slate-800 px-3 py-1.5 rounded-full border border-slate-700">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>LLM Reasoning:</span>
            <span className={health?.groq_configured ? "text-indigo-400 font-bold" : "text-amber-400"}>
              {health?.groq_configured ? "Groq (gpt-oss-120b)" : "Fallback"}
            </span>
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <main className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Intake Controls & Current Incident */}
        <div className="lg:col-span-5 space-y-6">
          {/* Preset Buttons */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">Simulate Incident Scenarios</h2>
            <div className="grid grid-cols-2 gap-3">
              <button 
                onClick={() => loadDemoIncident('INC-2001')}
                disabled={loading}
                className="flex items-center justify-center space-x-2 bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/40 text-indigo-300 py-2.5 px-3 rounded-lg text-xs font-medium transition"
              >
                <ShieldAlert className="w-4 h-4" />
                <span>Demo 1: Novel (INC-2001)</span>
              </button>
              <button 
                onClick={() => loadDemoIncident('INC-2002')}
                disabled={loading}
                className="flex items-center justify-center space-x-2 bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/40 text-emerald-300 py-2.5 px-3 rounded-lg text-xs font-medium transition"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Demo 2: Similar (INC-2002)</span>
              </button>
            </div>
          </div>

          {/* Current Incident Evidence Card */}
          {currentIncident && (
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-700 pb-3">
                <span className="text-xs font-mono bg-indigo-950 text-indigo-400 border border-indigo-800 px-2.5 py-1 rounded">
                  {currentIncident.incident_id}
                </span>
                <span className="text-xs font-bold text-rose-400 bg-rose-950/60 border border-rose-900 px-2 py-0.5 rounded uppercase">
                  {currentIncident.severity} severity
                </span>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-slate-200">{currentIncident.service}</h3>
                <p className="text-xs text-slate-400 mt-1">{currentIncident.summary}</p>
              </div>

              <div className="space-y-2 text-xs">
                <div className="font-semibold text-slate-300">Symptoms & Metrics:</div>
                <div className="flex flex-wrap gap-1.5">
                  {currentIncident.symptoms.map((s, idx) => (
                    <span key={idx} className="bg-slate-900 text-slate-300 px-2 py-1 rounded border border-slate-700">
                      {s}
                    </span>
                  ))}
                  {Object.entries(currentIncident.metrics || {}).map(([k, v]) => (
                    <span key={k} className="bg-slate-900 text-cyan-400 px-2 py-1 rounded border border-slate-700">
                      {k}: {v}
                    </span>
                  ))}
                </div>
              </div>

              {currentIncident.logs && currentIncident.logs.length > 0 && (
                <div className="space-y-1 text-xs">
                  <div className="font-semibold text-slate-300">Log Error Trace:</div>
                  <pre className="bg-slate-950 text-rose-300 p-2.5 rounded font-mono text-[11px] whitespace-pre-wrap overflow-x-auto border border-slate-900">
                    {currentIncident.logs[0]}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Hindsight Memory & Agent Diagnosis */}
        <div className="lg:col-span-7 space-y-6">
          {loading && (
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-12 text-center text-slate-400">
              <RefreshCw className="w-8 h-8 animate-spin mx-auto text-indigo-400 mb-3" />
              <p className="text-sm">Querying Hindsight Memory Bank & Running Agent Reasoning...</p>
            </div>
          )}

          {!loading && assessment && (
            <>
              {/* Warnings Alert Box */}
              {assessment.warnings && assessment.warnings.length > 0 && (
                <div className="bg-amber-950/40 border border-amber-500/30 rounded-xl p-4 space-y-2">
                  <div className="flex items-center space-x-2 text-amber-400 font-semibold text-xs">
                    <AlertTriangle className="w-4 h-4" />
                    <span>AGENT WARNING & FAILED APPROACH ALERT</span>
                  </div>
                  <ul className="text-xs text-amber-200/90 space-y-1 pl-6 list-disc">
                    {assessment.warnings.map((w, idx) => (
                      <li key={idx}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Hindsight Memory Recall Panel */}
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-700 pb-3">
                  <div className="flex items-center space-x-2">
                    <Database className="w-4 h-4 text-emerald-400" />
                    <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                      Hindsight Historical Memory Recall
                    </h2>
                  </div>
                  <span className={`text-xs px-2.5 py-0.5 rounded-full font-semibold border ${
                    assessment.historical_evidence.status === 'found' 
                      ? 'bg-emerald-950 text-emerald-400 border-emerald-800' 
                      : 'bg-slate-900 text-slate-400 border-slate-700'
                  }`}>
                    Status: {assessment.historical_evidence.status.toUpperCase()}
                  </span>
                </div>

                <div className="space-y-3">
                  {assessment.historical_evidence.matches.length === 0 ? (
                    <p className="text-xs text-slate-400 italic">No historical memory matches found. Investigating as a novel incident.</p>
                  ) : (
                    assessment.historical_evidence.matches.map((match, idx) => (
                      <div key={idx} className="bg-slate-900 border border-slate-700 rounded-lg p-3 text-xs space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-indigo-300">Memory Match #{idx + 1}</span>
                          <span className="font-mono bg-indigo-950 text-indigo-400 border border-indigo-800 px-2 py-0.5 rounded text-[11px]">
                            Similarity: {(match.score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <p className="text-slate-300 leading-relaxed">{match.content}</p>
                        {match.failed_attempts && match.failed_attempts.length > 0 && (
                          <div className="text-rose-400 font-mono text-[11px] bg-rose-950/40 border border-rose-900/40 p-1.5 rounded">
                            ⚠️ Failed Fix Attempt Recorded: {match.failed_attempts.join(", ")}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Agent Hypotheses & Recommended Actions */}
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 space-y-4">
                <div className="flex items-center space-x-2 border-b border-slate-700 pb-3">
                  <Brain className="w-4 h-4 text-indigo-400" />
                  <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                    Agent Assessment & Investigation Plan
                  </h2>
                </div>

                {/* Hypotheses */}
                <div className="space-y-2">
                  <div className="text-xs font-semibold text-slate-300">Formulated Hypotheses:</div>
                  {assessment.hypotheses.map((h, idx) => (
                    <div key={idx} className="bg-slate-900/80 border border-indigo-900/50 rounded-lg p-3 text-xs space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-indigo-200">{h.statement}</span>
                        <span className="bg-amber-950 text-amber-400 border border-amber-800 px-2 py-0.5 rounded text-[10px] uppercase font-bold">
                          {h.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Recommended Actions */}
                <div className="space-y-2">
                  <div className="text-xs font-semibold text-slate-300">Recommended Investigation Steps:</div>
                  <ol className="space-y-2 text-xs">
                    {assessment.recommended_actions.map((act, idx) => (
                      <li key={idx} className="flex items-start space-x-2.5 bg-slate-900 p-2.5 rounded border border-slate-700">
                        <span className="font-mono text-indigo-400 font-bold">{idx + 1}.</span>
                        <span className="text-slate-200 leading-relaxed">{act}</span>
                      </li>
                    ))}
                  </ol>
                </div>
              </div>

              {/* Engineer Resolution Form */}
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 space-y-4">
                <div className="flex items-center space-x-2 border-b border-slate-700 pb-3">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                    Engineer Resolution & Hindsight Learning Capture
                  </h2>
                </div>

                <form onSubmit={handleResolve} className="space-y-3 text-xs">
                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Confirmed Root Cause:</label>
                    <input 
                      type="text" 
                      value={rootCause} 
                      onChange={(e) => setRootCause(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-100 focus:outline-none focus:border-indigo-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Confirmed Resolution / Fix:</label>
                    <input 
                      type="text" 
                      value={fix} 
                      onChange={(e) => setFix(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-100 focus:outline-none focus:border-indigo-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Failed Fix Attempts (Comma separated):</label>
                    <input 
                      type="text" 
                      value={failedAttempts} 
                      onChange={(e) => setFailedAttempts(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-100 focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  <button 
                    type="submit" 
                    disabled={retaining}
                    className="w-full flex items-center justify-center space-x-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-2.5 rounded-lg transition"
                  >
                    <Save className="w-4 h-4" />
                    <span>{retaining ? "Retaining into Hindsight Memory..." : "Confirm & Retain Experience in Hindsight"}</span>
                  </button>
                </form>

                {resolvedStatus && (
                  <div className="bg-emerald-950/60 border border-emerald-500/40 p-3 rounded-lg text-xs text-emerald-300 flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span>{resolvedStatus.message}</span>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}