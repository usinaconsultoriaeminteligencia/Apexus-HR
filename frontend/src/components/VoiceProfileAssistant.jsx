import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Mic, MicOff, Play, CheckCircle, AlertCircle, Save, TestTube } from 'lucide-react';
import { POSITIONS, POSITION_CATEGORIES } from '../data/positions.js';

/**
 * VoiceProfileAssistant - Componente de entrevista por áudio com análise de perfil
 * 
 * Integrado com:
 * - Backend Flask (rotas /api/audio-interview e /api/assessments)
 * - Autenticação JWT
 * - Sistema de posições (75+ cargos)
 * - OpenAI API (TTS, Whisper, GPT-4o-mini)
 * 
 * @param {Object} props
 * @param {string} props.candidateName - Nome do candidato
 * @param {string} props.position - Cargo pretendido
 * @param {string} props.seniority - Nível de senioridade
 * @param {boolean} props.autoStart - Iniciar automaticamente
 * @param {Function} props.onComplete - Callback ao completar avaliação
 */
export default function VoiceProfileAssistant({
  candidateName = "",
  position = "",
  seniority = "Pleno",
  autoStart = false,
  onComplete,
}) {
  const [sessionId, setSessionId] = useState(null);
  const [running, setRunning] = useState(false);
  const [log, setLog] = useState([]);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [questionNumber, setQuestionNumber] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(0);
  
  const audioRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);
  const [recording, setRecording] = useState(false);

  const apiBase = "/api";
  const token = localStorage.getItem('auth_token');

  /**
   * Helper para requisições autenticadas
   */
  const fetchWithAuth = useCallback(async (path, options = {}) => {
    if (!token) {
      throw new Error('Você precisa estar autenticado para usar esta funcionalidade. Por favor, faça login.');
    }
    
    const headers = {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    };
    
    const response = await fetch(`${apiBase}${path}`, {
      ...options,
      headers
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }
    
    return response;
  }, [token]);

  /**
   * Inicia sessão de entrevista
   */
  const startSession = useCallback(async () => {
    const resp = await fetchWithAuth("/audio-interview/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        candidate_name: candidateName,
        position,
      }),
    });
    
    const data = await resp.json();
    if (!data?.success) throw new Error(data?.error || "Falha ao iniciar sessão");
    
    setSessionId(data.session_id);
    return data.session_id;
  }, [candidateName, position, fetchWithAuth]);

  /**
   * Carrega informações da pergunta atual
   */
  const loadQuestionInfo = useCallback(async (sid) => {
    const id = sid || sessionId;
    if (!id) throw new Error("Sessão não iniciada");

    try {
      const resp = await fetchWithAuth(`/audio-interview/${id}/question/info`);
      const info = await resp.json();
      
      if (info?.finished) {
        return { finished: true };
      }
      
      setCurrentQuestion(info.question_text);
      setQuestionNumber(info.question_number);
      setTotalQuestions(info.total_questions);
      setLog((p) => [...p, { 
        role: "assistant", 
        content: `Pergunta ${info.question_number}/${info.total_questions}: ${info.question_text}` 
      }]);
      
      return info;
    } catch (err) {
      // Endpoint opcional, tolera ausência
      return { finished: false };
    }
  }, [sessionId, fetchWithAuth]);

  /**
   * Reproduz áudio da pergunta
   */
  const playQuestion = useCallback(async (sid) => {
    const id = sid || sessionId;
    if (!id) throw new Error("Sessão não iniciada");

    const resp = await fetchWithAuth(`/audio-interview/${id}/question`);
    const blob = await resp.blob();
    const contentType = resp.headers.get('Content-Type') || 'audio/mpeg';
    
    const url = URL.createObjectURL(new Blob([blob], { type: contentType }));

    if (!audioRef.current) {
      audioRef.current = new Audio();
    }
    audioRef.current.src = url;
    await audioRef.current.play();
  }, [sessionId, fetchWithAuth]);

  /**
   * Inicia gravação de áudio
   */
  const startRecording = useCallback(async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error("Navegador não suporta gravação de áudio");
    }

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    streamRef.current = stream;

    const recorder = new MediaRecorder(stream, { 
      mimeType: 'audio/webm' 
    });
    audioChunksRef.current = [];

    recorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) {
        audioChunksRef.current.push(e.data);
      }
    };

    recorder.onstart = () => setRecording(true);
    recorder.onstop = () => setRecording(false);

    mediaRecorderRef.current = recorder;
    recorder.start();
  }, []);

  /**
   * Para gravação e retorna blob de áudio
   */
  const stopRecording = useCallback(async () => {
    if (!mediaRecorderRef.current) return null;
    
    const recorder = mediaRecorderRef.current;
    
    return new Promise((resolve) => {
      recorder.onstop = () => {
        setRecording(false);
        const blob = new Blob(audioChunksRef.current, { 
          type: recorder.mimeType 
        });
        
        // Encerra stream
        streamRef.current?.getTracks?.().forEach((t) => t.stop());
        
        resolve(blob);
      };
      recorder.stop();
    });
  }, []);

  /**
   * Envia resposta em áudio
   */
  const sendResponse = useCallback(async (sid, blob) => {
    const id = sid || sessionId;
    if (!id) throw new Error("Sessão não iniciada");

    const resp = await fetchWithAuth(`/audio-interview/${id}/respond`, {
      method: "POST",
      headers: { 
        "Content-Type": blob?.type || "application/octet-stream" 
      },
      body: blob,
    });

    const json = await resp.json();

    // Adiciona transcrição ao log
    if (json?.transcription) {
      setLog((p) => [...p, { 
        role: "user", 
        content: `Você: ${json.transcription}` 
      }]);
    }
    
    if (json?.message) {
      setLog((p) => [...p, { 
        role: "system", 
        content: json.message 
      }]);
    }

    // Carrega próxima pergunta se houver
    if (json?.next === "question") {
      const info = await loadQuestionInfo(id);
      if (!info.finished) {
        await playQuestion(id);
      }
    }
    
    return json;
  }, [sessionId, loadQuestionInfo, playQuestion, fetchWithAuth]);

  /**
   * Finaliza entrevista e obtém relatório
   */
  const finalize = useCallback(async (sid) => {
    const id = sid || sessionId;
    if (!id) throw new Error("Sessão não iniciada");
    
    const resp = await fetchWithAuth(`/audio-interview/${id}/finalize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    
    const json = await resp.json();
    
    if (json?.success && json?.report) {
      setSummary(json.report);
      setLog((p) => [...p, { 
        role: "system", 
        content: "✅ Entrevista finalizada com sucesso!" 
      }]);
    }
    
    return json;
  }, [sessionId, fetchWithAuth]);

  /**
   * Handlers de UI
   */
  const handleStart = useCallback(async () => {
    try {
      setError(null);
      setSummary(null);
      setLog([]);
      
      setLog([{ 
        role: "system", 
        content: `🎙️ Iniciando entrevista de perfil para ${position} (${seniority})...` 
      }]);
      
      const sid = await startSession();
      setRunning(true);
      
      await loadQuestionInfo(sid);
      await playQuestion(sid);
    } catch (e) {
      setError(e.message);
      setRunning(false);
      setLog((p) => [...p, { 
        role: "error", 
        content: `❌ Erro: ${e.message}` 
      }]);
    }
  }, [position, seniority, startSession, loadQuestionInfo, playQuestion]);

  const handleRecordToggle = useCallback(async () => {
    try {
      if (!recording) {
        await startRecording();
        setLog((p) => [...p, { 
          role: "system", 
          content: "🔴 Gravando..." 
        }]);
      } else {
        const blob = await stopRecording();
        setLog((p) => [...p, { 
          role: "system", 
          content: "⏹️ Processando resposta..." 
        }]);
        await sendResponse(null, blob);
      }
    } catch (e) {
      setError(e.message);
      setLog((p) => [...p, { 
        role: "error", 
        content: `❌ Erro: ${e.message}` 
      }]);
    }
  }, [recording, startRecording, stopRecording, sendResponse]);

  const handleFinalize = useCallback(async () => {
    try {
      setLog((p) => [...p, { 
        role: "system", 
        content: "📊 Gerando relatório final..." 
      }]);
      
      await finalize();
      setRunning(false);
    } catch (e) {
      setError(e.message);
      setLog((p) => [...p, { 
        role: "error", 
        content: `❌ Erro: ${e.message}` 
      }]);
    }
  }, [finalize]);

  const handleSaveBackend = useCallback(async () => {
    if (!summary) return;
    
    setSaving(true);
    try {
      const payload = {
        candidateName,
        position,
        seniority,
        result: summary,
        transcript: log
          .filter(m => m.role === "user" || m.role === "assistant")
          .map((m) => m?.content ?? "")
          .filter(Boolean),
        sessionId,
      };
      
      const resp = await fetchWithAuth("/assessments/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      
      const json = await resp.json();
      
      setLog((p) => [...p, { 
        role: "system", 
        content: `✅ Avaliação salva com sucesso! ID: ${json.interview_id}` 
      }]);
      
      onComplete?.(summary);
    } catch (e) {
      setError(`Falha ao salvar: ${e.message}`);
      setLog((p) => [...p, { 
        role: "error", 
        content: `❌ Erro ao salvar: ${e.message}` 
      }]);
    } finally {
      setSaving(false);
    }
  }, [candidateName, log, onComplete, position, seniority, sessionId, summary, fetchWithAuth]);

  // Auto-start opcional
  useEffect(() => {
    if (autoStart && !running && !sessionId) {
      handleStart();
    }
  }, [autoStart, handleStart, running, sessionId]);

  /**
   * Auto-testes
   */
  const [tests, setTests] = useState([]);
  const runSelfTests = useCallback(() => {
    const results = [];
    
    results.push({ 
      name: "Backend configurado", 
      ok: !!apiBase && apiBase.length > 0 
    });
    results.push({ 
      name: "Token JWT presente", 
      ok: !!token 
    });
    results.push({ 
      name: "Nome do candidato fornecido", 
      ok: !!candidateName && candidateName.length > 0 
    });
    results.push({ 
      name: "Posição selecionada", 
      ok: !!position && POSITIONS.includes(position) 
    });
    results.push({ 
      name: "Permissão de microfone", 
      ok: !!navigator.mediaDevices?.getUserMedia 
    });
    
    setTests(results);
  }, [candidateName, position, token]);

  return (
    <div className="w-full max-w-4xl mx-auto p-6 bg-white rounded-xl shadow-lg border border-gray-200">
      {/* Header */}
      <header className="flex items-center justify-between pb-4 border-b border-gray-200">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Assistente de Voz — Análise de Perfil</h2>
          <p className="text-sm text-gray-600 mt-1">
            <strong className="text-gray-900">{candidateName}</strong> · {position} · {seniority}
          </p>
          {questionNumber > 0 && (
            <p className="text-xs text-gray-500 mt-1">
              Pergunta {questionNumber} de {totalQuestions}
            </p>
          )}
        </div>
        
        <div className="flex gap-2">
          {!running ? (
            <button 
              onClick={handleStart} 
              className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors flex items-center gap-2"
            >
              <Play className="w-4 h-4" />
              Iniciar
            </button>
          ) : (
            <button 
              onClick={handleFinalize} 
              className="px-4 py-2 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 transition-colors flex items-center gap-2"
            >
              <CheckCircle className="w-4 h-4" />
              Finalizar
            </button>
          )}
          
          <button 
            onClick={handleRecordToggle} 
            disabled={!running} 
            className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
              recording 
                ? 'bg-red-600 text-white hover:bg-red-700' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {recording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
            {recording ? "Parar & Enviar" : "Gravar Resposta"}
          </button>
        </div>
      </header>

      {/* Erro */}
      {error && (
        <div className="mt-4 p-3 rounded-lg bg-red-50 border border-red-200 flex items-start gap-2">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-red-800">Erro</p>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Log de transcrição */}
      <section className="mt-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Transcrição / Log</h3>
        <div className="h-64 overflow-auto p-4 rounded-lg border border-gray-200 bg-gray-50 text-sm space-y-2">
          {log.length === 0 && (
            <p className="text-gray-500 italic">Aguardando início da entrevista...</p>
          )}
          {log.map((m, i) => (
            <div 
              key={i} 
              className={`${
                m.role === "user" ? "text-blue-900 font-medium" : 
                m.role === "error" ? "text-red-600" :
                m.role === "assistant" ? "text-purple-700" :
                "text-gray-700"
              }`}
            >
              <span className="inline-block min-w-20 mr-2 text-xs uppercase tracking-wide opacity-60">
                {m.role || "system"}
              </span>
              <span>{m.content}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Resultado estruturado */}
      <section className="mt-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Resultado da Avaliação</h3>
        <div className="p-4 rounded-lg border border-gray-200 bg-gray-50 text-sm max-h-96 overflow-auto">
          {!summary ? (
            <p className="text-gray-500 italic">Finalize a entrevista para gerar o relatório.</p>
          ) : (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-gray-600 uppercase">Score Final</p>
                  <p className="text-2xl font-bold text-blue-600">{summary.score_final || 0}/100</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600 uppercase">Recomendação</p>
                  <p className="text-2xl font-bold text-emerald-600">{summary.recomendacao || "—"}</p>
                </div>
              </div>
              
              {summary.perfil_disc && (
                <div>
                  <p className="text-xs text-gray-600 uppercase">Perfil DISC</p>
                  <p className="text-lg font-semibold text-gray-900">{summary.perfil_disc}</p>
                </div>
              )}
              
              <details className="cursor-pointer">
                <summary className="text-xs text-gray-600 uppercase font-medium">
                  Ver JSON Completo
                </summary>
                <pre className="mt-2 whitespace-pre-wrap break-words text-xs bg-white p-3 rounded border">
                  {JSON.stringify(summary, null, 2)}
                </pre>
              </details>
            </div>
          )}
        </div>
      </section>

      {/* Footer com ações */}
      <footer className="mt-6 flex items-center gap-3 pt-4 border-t border-gray-200">
        <button 
          onClick={handleSaveBackend} 
          disabled={!summary || saving} 
          className="px-4 py-2 rounded-lg bg-indigo-600 text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-indigo-700 transition-colors flex items-center gap-2"
        >
          <Save className="w-4 h-4" />
          {saving ? "Salvando..." : "Salvar no Backend"}
        </button>
        
        <button 
          onClick={runSelfTests} 
          className="px-4 py-2 rounded-lg bg-gray-100 border border-gray-300 hover:bg-gray-200 transition-colors flex items-center gap-2"
        >
          <TestTube className="w-4 h-4" />
          Auto-testes
        </button>
      </footer>

      {/* Resultados dos auto-testes */}
      {tests.length > 0 && (
        <section className="mt-4 p-4 rounded-lg border border-gray-200 bg-white text-sm">
          <h4 className="font-semibold mb-2 text-gray-900">Resultados dos Auto-testes</h4>
          <ul className="space-y-1">
            {tests.map((t, i) => (
              <li 
                key={i} 
                className={`flex items-center gap-2 ${
                  t.ok ? "text-emerald-700" : "text-red-600"
                }`}
              >
                <span className="text-lg">{t.ok ? "✔" : "✖"}</span>
                <span>{t.name}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
