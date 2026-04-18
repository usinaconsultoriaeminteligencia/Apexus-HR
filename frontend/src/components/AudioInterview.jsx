import React, { useState, useRef, useEffect } from 'react';
import { Mic, MicOff, Play, Pause, Volume2, CheckCircle, Clock, User, Briefcase } from 'lucide-react';
import { POSITIONS, POSITION_CATEGORIES } from '../data/positions.js';
import InterviewTimer from './InterviewTimer';

const AudioInterview = () => {
  const [interviewState, setInterviewState] = useState('setup'); // setup, active, recording, processing, completed
  const [sessionId, setSessionId] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [questionNumber, setQuestionNumber] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [isPlayingQuestion, setIsPlayingQuestion] = useState(false);
  const [candidateName, setCandidateName] = useState('');
  const [position, setPosition] = useState('');
  const [responses, setResponses] = useState([]);
  const [finalReport, setFinalReport] = useState(null);
  const [audioPermission, setAudioPermission] = useState(false);
  const [interviewDuration, setInterviewDuration] = useState(0);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const questionAudioRef = useRef(null);
  const streamRef = useRef(null);

  // Solicita permissão de áudio ao carregar
  useEffect(() => {
    requestAudioPermission();
  }, []);

  const requestAudioPermission = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setAudioPermission(true);
      streamRef.current = stream;
    } catch (error) {
      console.error('Erro ao solicitar permissão de áudio:', error);
      alert('É necessário permitir acesso ao microfone para realizar a entrevista.');
    }
  };

  const startInterview = async () => {
    // Validação de entrada
    if (!candidateName || !candidateName.trim()) {
      alert('Por favor, preencha o nome completo');
      return;
    }
    
    if (!position || !position.trim()) {
      alert('Por favor, selecione uma posição');
      return;
    }
    
    // Validação adicional
    if (candidateName.trim().length < 2) {
      alert('O nome deve ter pelo menos 2 caracteres');
      return;
    }

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch('/api/audio-interview/start', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          candidate_name: candidateName.trim(),
          position: position.trim()
        })
      });
      
      if (!response.ok) {
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setSessionId(data.session_id);
      setInterviewState('active');
      
      // Carrega primeira pergunta
      await loadCurrentQuestion(data.session_id);
    } catch (error) {
      console.error('Erro ao iniciar entrevista:', error);
      alert('Erro ao iniciar entrevista. Verifique se o servidor está rodando.');
    }
  };

  const loadCurrentQuestion = async (sessionId) => {
    try {
      // Busca informações da pergunta
      const token = localStorage.getItem('auth_token');
      const infoResponse = await fetch(`/api/audio-interview/${sessionId}/question/info`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!infoResponse.ok) {
        throw new Error(`Erro ao carregar pergunta: ${infoResponse.status}`);
      }
      
      const infoData = await infoResponse.json();
      
      if (infoData.finished) {
        await finalizeInterview();
        return;
      }

      setCurrentQuestion(infoData.question_text);
      setQuestionNumber(infoData.question_number);
      setTotalQuestions(infoData.total_questions);

      // Carrega áudio da pergunta
      const audioResponse = await fetch(`/api/audio-interview/${sessionId}/question`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!audioResponse.ok) {
        throw new Error(`Erro ao carregar áudio: ${audioResponse.status}`);
      }
      
      const audioBlob = await audioResponse.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      
      if (questionAudioRef.current) {
        questionAudioRef.current.src = audioUrl;
      } else {
        console.error('🔊 ERRO: questionAudioRef.current é null ao configurar src');
      }
    } catch (error) {
      console.error('Erro ao carregar pergunta:', error);
      alert('Erro ao carregar pergunta. Tente novamente.');
    }
  };

  const playQuestion = () => {
    
    if (questionAudioRef.current) {
      setIsPlayingQuestion(true);
      questionAudioRef.current.play()
        .then(() => {
        })
        .catch((error) => {
          console.error('🔊 ERRO ao reproduzir áudio:', error);
          setIsPlayingQuestion(false);
          alert('Erro ao reproduzir áudio: ' + error.message);
        });
    } else {
      console.error('🔊 ERRO: questionAudioRef.current é null');
      alert('Erro: Elemento de áudio não encontrado');
    }
  };

  const startRecording = async () => {
    if (!audioPermission || !streamRef.current) {
      await requestAudioPermission();
      return;
    }

    try {
      audioChunksRef.current = [];
      mediaRecorderRef.current = new MediaRecorder(streamRef.current);
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await submitAudioResponse(audioBlob);
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Erro ao iniciar gravação:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setInterviewState('processing');
    }
  };

  const submitAudioResponse = async (audioBlob) => {
    try {
      // Envia dados de áudio diretamente como blob
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/audio-interview/${sessionId}/respond`, {
        method: 'POST',
        headers: {
          'Content-Type': 'audio/wav',
          'Authorization': `Bearer ${token}`
        },
        body: audioBlob
      });

      const data = await response.json();
      
      // Adiciona resposta ao histórico
      setResponses(prev => [...prev, {
        question: currentQuestion,
        transcript: data.transcript,
        analysis: data.analysis
      }]);

      if (data.next_question_available) {
        // Carrega próxima pergunta
        await loadCurrentQuestion(sessionId);
        setInterviewState('active');
      } else {
        // Finaliza entrevista
        await finalizeInterview();
      }
    } catch (error) {
      console.error('Erro ao enviar resposta:', error);
      setInterviewState('active');
    }
  };

  const finalizeInterview = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/audio-interview/${sessionId}/finalize`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      const data = await response.json();
      setFinalReport(data.report);
      setInterviewState('completed');
    } catch (error) {
      console.error('Erro ao finalizar entrevista:', error);
    }
  };

  const resetInterview = () => {
    setInterviewState('setup');
    setSessionId(null);
    setCurrentQuestion(null);
    setQuestionNumber(0);
    setTotalQuestions(0);
    setResponses([]);
    setFinalReport(null);
    setCandidateName('');
    setPosition('');
  };

  // Componente de Setup
  if (interviewState === 'setup') {
    return (
      <div className="max-w-2xl mx-auto p-4 sm:p-6 bg-white rounded-lg shadow-lg">
        <div className="text-center mb-6 sm:mb-8">
          <div className="w-14 h-14 sm:w-16 sm:h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Mic className="w-6 h-6 sm:w-8 sm:h-8 text-blue-600" />
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2">Entrevista por Áudio</h2>
          <p className="text-sm sm:text-base text-gray-600">Sistema de entrevista realista com IA - Perguntas e respostas em áudio</p>
        </div>

        <div className="space-y-4 sm:space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <User className="w-4 h-4 inline mr-2" />
              Nome Completo
            </label>
            <input
              type="text"
              value={candidateName}
              onChange={(e) => setCandidateName(e.target.value)}
              className="w-full px-4 py-3 min-h-[44px] border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm sm:text-base"
              placeholder="Ex: João Silva Santos"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Briefcase className="w-4 h-4 inline mr-2" />
              Posição Desejada
            </label>
            <select
              value={position}
              onChange={(e) => setPosition(e.target.value)}
              className="w-full px-4 py-3 min-h-[44px] border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm sm:text-base"
            >
              <option value="">Selecione uma posição</option>
              
              {/* Tecnologia */}
              <optgroup label="Tecnologia">
                {POSITION_CATEGORIES["Tecnologia"].map(pos => (
                  <option key={pos} value={pos}>{pos}</option>
                ))}
              </optgroup>
              
              {/* Recursos Humanos */}
              <optgroup label="Recursos Humanos">
                {POSITION_CATEGORIES["Recursos Humanos"].map(pos => (
                  <option key={pos} value={pos}>{pos}</option>
                ))}
              </optgroup>
              
              {/* Gestão e Liderança */}
              <optgroup label="Gestão e Liderança">
                {POSITION_CATEGORIES["Gestão e Liderança"].map(pos => (
                  <option key={pos} value={pos}>{pos}</option>
                ))}
              </optgroup>
              
              {/* Marketing e Vendas */}
              <optgroup label="Marketing e Vendas">
                {POSITION_CATEGORIES["Marketing e Vendas"].map(pos => (
                  <option key={pos} value={pos}>{pos}</option>
                ))}
              </optgroup>
              
              {/* Financeiro */}
              <optgroup label="Financeiro">
                {POSITION_CATEGORIES["Financeiro"].map(pos => (
                  <option key={pos} value={pos}>{pos}</option>
                ))}
              </optgroup>
              
              {/* Operações */}
              <optgroup label="Operações">
                {POSITION_CATEGORIES["Operações"].map(pos => (
                  <option key={pos} value={pos}>{pos}</option>
                ))}
              </optgroup>
              
              {/* Atendimento ao Cliente */}
              <optgroup label="Atendimento ao Cliente">
                {POSITION_CATEGORIES["Atendimento ao Cliente"].map(pos => (
                  <option key={pos} value={pos}>{pos}</option>
                ))}
              </optgroup>
              
              {/* Jurídico */}
              <optgroup label="Jurídico">
                {POSITION_CATEGORIES["Jurídico"].map(pos => (
                  <option key={pos} value={pos}>{pos}</option>
                ))}
              </optgroup>
              
              {/* Administrativo */}
              <optgroup label="Administrativo">
                {POSITION_CATEGORIES["Administrativo"].map(pos => (
                  <option key={pos} value={pos}>{pos}</option>
                ))}
              </optgroup>
              
              {/* Logística */}
              <optgroup label="Logística">
                {POSITION_CATEGORIES["Logística"].map(pos => (
                  <option key={pos} value={pos}>{pos}</option>
                ))}
              </optgroup>
            </select>
          </div>

          <div className="bg-blue-50 p-3 sm:p-4 rounded-lg">
            <h3 className="text-sm sm:text-base font-medium text-blue-900 mb-2">Como funciona:</h3>
            <ul className="text-xs sm:text-sm text-blue-800 space-y-1">
              <li>• A IA fará perguntas em áudio</li>
              <li>• Você responde falando no microfone</li>
              <li>• Suas respostas são analisadas automaticamente</li>
              <li>• Relatório final é gerado ao término</li>
            </ul>
          </div>

          <button
            onClick={startInterview}
            disabled={!candidateName || !position || !audioPermission}
            className="w-full bg-blue-600 text-white py-3 px-6 min-h-[44px] rounded-lg text-sm sm:text-base font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {!audioPermission ? 'Aguardando permissão de áudio...' : 'Iniciar Entrevista'}
          </button>
        </div>
      </div>
    );
  }

  // Componente de Entrevista Ativa
  if (interviewState === 'active' || interviewState === 'recording' || interviewState === 'processing') {
    return (
      <div className="max-w-4xl mx-auto p-4 sm:p-6">
        {/* Header da Entrevista */}
        <div className="bg-white rounded-lg shadow-lg p-4 sm:p-6 mb-4 sm:mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-0 mb-4">
            <div>
              <h2 className="text-lg sm:text-xl font-bold text-gray-900">{candidateName}</h2>
              <p className="text-sm sm:text-base text-gray-600">{position}</p>
            </div>
            <InterviewTimer 
              isActive={interviewState === 'active' || interviewState === 'recording'}
              onTimeUpdate={setInterviewDuration}
              className="mr-4"
            />
            <div className="text-right">
              <div className="text-xs sm:text-sm text-gray-500">Pergunta</div>
              <div className="text-xl sm:text-2xl font-bold text-blue-600">
                {questionNumber} / {totalQuestions}
              </div>
            </div>
          </div>

          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(questionNumber / totalQuestions) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Pergunta Atual */}
        <div className="bg-white rounded-lg shadow-lg p-4 sm:p-6 mb-4 sm:mb-6">
          <div className="flex items-start space-x-3 sm:space-x-4">
            <div className="w-10 h-10 sm:w-12 sm:h-12 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
              <Volume2 className="w-5 h-5 sm:w-6 sm:h-6 text-blue-600" />
            </div>
            <div className="flex-1">
              <h3 className="text-sm sm:text-base font-medium text-gray-900 mb-2">Pergunta da IA:</h3>
              <p className="text-gray-700 text-base sm:text-lg leading-relaxed mb-4">{currentQuestion}</p>
              
              <div className="flex items-center space-x-4">
                <button
                  onClick={playQuestion}
                  disabled={isPlayingQuestion}
                  className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 min-h-[44px] rounded-lg text-sm sm:text-base hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
                >
                  {isPlayingQuestion ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  <span>{isPlayingQuestion ? 'Reproduzindo...' : 'Ouvir Pergunta'}</span>
                </button>
                
                <audio
                  ref={questionAudioRef}
                  onEnded={() => setIsPlayingQuestion(false)}
                  onPlay={() => setIsPlayingQuestion(true)}
                  onPause={() => setIsPlayingQuestion(false)}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Área de Resposta */}
        <div className="bg-white rounded-lg shadow-lg p-4 sm:p-6">
          <div className="text-center">
            <div className="w-20 h-20 sm:w-24 sm:h-24 mx-auto mb-4 relative">
              <div className={`w-20 h-20 sm:w-24 sm:h-24 rounded-full flex items-center justify-center transition-all duration-300 ${
                isRecording ? 'bg-red-100 animate-pulse' : 'bg-gray-100'
              }`}>
                {isRecording ? (
                  <MicOff className="w-10 h-10 sm:w-12 sm:h-12 text-red-600" />
                ) : (
                  <Mic className="w-10 h-10 sm:w-12 sm:h-12 text-gray-600" />
                )}
              </div>
              {isRecording && (
                <div className="absolute inset-0 rounded-full border-4 border-red-300 animate-ping"></div>
              )}
            </div>

            {interviewState === 'processing' ? (
              <div>
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Processando sua resposta...</p>
              </div>
            ) : (
              <div>
                <h3 className="text-base sm:text-lg font-medium text-gray-900 mb-2">
                  {isRecording ? 'Gravando sua resposta...' : 'Sua vez de responder'}
                </h3>
                <p className="text-sm sm:text-base text-gray-600 mb-4 sm:mb-6">
                  {isRecording 
                    ? 'Fale naturalmente. Clique em "Parar" quando terminar.'
                    : 'Clique no botão abaixo para começar a gravar sua resposta.'
                  }
                </p>

                <button
                  onClick={isRecording ? stopRecording : startRecording}
                  className={`px-6 sm:px-8 py-3 min-h-[44px] rounded-lg text-sm sm:text-base font-medium transition-colors ${
                    isRecording 
                      ? 'bg-red-600 text-white hover:bg-red-700' 
                      : 'bg-green-600 text-white hover:bg-green-700'
                  }`}
                >
                  {isRecording ? 'Parar Gravação' : 'Iniciar Gravação'}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Histórico de Respostas */}
        {responses.length > 0 && (
          <div className="mt-6 bg-white rounded-lg shadow-lg p-6">
            <h3 className="font-medium text-gray-900 mb-4">Respostas Anteriores:</h3>
            <div className="space-y-4">
              {responses.map((response, index) => (
                <div key={index} className="border-l-4 border-blue-200 pl-4">
                  <p className="text-sm text-gray-600 mb-1">P{index + 1}: {response.question}</p>
                  <p className="text-gray-900 mb-2">{response.transcript}</p>
                  {response.analysis && (
                    <div className="text-sm text-green-600">
                      Score: {response.analysis.score}/100
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // Componente de Relatório Final
  if (interviewState === 'completed' && finalReport) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="text-center mb-8">
            <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Entrevista Finalizada</h2>
            <p className="text-gray-600">Relatório completo da entrevista de {candidateName}</p>
          </div>

          <div className="grid md:grid-cols-2 gap-6 mb-8">
            <div className="bg-blue-50 p-6 rounded-lg">
              <h3 className="font-bold text-blue-900 mb-2">Score Final</h3>
              <div className="text-3xl font-bold text-blue-600">{finalReport.score_final}/100</div>
            </div>
            <div className={`p-6 rounded-lg ${
              finalReport.recomendacao === 'CONTRATAR' ? 'bg-green-50' : 
              finalReport.recomendacao === 'CONSIDERAR' ? 'bg-yellow-50' : 'bg-red-50'
            }`}>
              <h3 className="font-bold mb-2">Recomendação</h3>
              <div className={`text-2xl font-bold ${
                finalReport.recomendacao === 'CONTRATAR' ? 'text-green-600' : 
                finalReport.recomendacao === 'CONSIDERAR' ? 'text-yellow-600' : 'text-red-600'
              }`}>
                {finalReport.recomendacao}
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div>
              <h3 className="font-bold text-gray-900 mb-3">Resumo Executivo</h3>
              <p className="text-gray-700">{finalReport.resumo_executivo}</p>
            </div>

            <div className="grid md:grid-cols-3 gap-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">Competências Técnicas</h4>
                <div className="text-2xl font-bold text-blue-600">{finalReport.competencias_tecnicas}/10</div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">Competências Comportamentais</h4>
                <div className="text-2xl font-bold text-green-600">{finalReport.competencias_comportamentais}/10</div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">Fit Cultural</h4>
                <div className="text-2xl font-bold text-purple-600">{finalReport.fit_cultural}/10</div>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-bold text-gray-900 mb-3">Pontos Fortes</h3>
                <ul className="space-y-2">
                  {(finalReport.pontos_fortes || []).map((ponto, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700">{ponto}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="font-bold text-gray-900 mb-3">Áreas de Desenvolvimento</h3>
                <ul className="space-y-2">
                  {(finalReport.areas_desenvolvimento || []).map((area, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <Clock className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700">{area}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div>
              <h3 className="font-bold text-gray-900 mb-3">Próximos Passos</h3>
              <ul className="space-y-2">
                {(finalReport.proximos_passos || []).map((passo, index) => (
                  <li key={index} className="flex items-start space-x-2">
                    <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center mt-0.5 flex-shrink-0">
                      <span className="text-blue-600 text-sm font-bold">{index + 1}</span>
                    </div>
                    <span className="text-gray-700">{passo}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="mt-8 text-center">
            <button
              onClick={resetInterview}
              className="bg-blue-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              Nova Entrevista
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default AudioInterview;

