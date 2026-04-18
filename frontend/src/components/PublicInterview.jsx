import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Mic,
  MicOff,
  Play,
  Pause,
  Send,
  CheckCircle,
  AlertCircle,
  Clock,
  HeadphonesIcon,
  Volume2,
  ArrowRight,
  Info,
  Loader2
} from 'lucide-react';

const PublicInterview = () => {
  const { token } = useParams();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [interview, setInterview] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const [responseText, setResponseText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [completed, setCompleted] = useState(false);
  
  // Carregar dados da entrevista via token
  useEffect(() => {
    loadInterview();
  }, [token]);
  
  const loadInterview = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/interviews/public/${token}`);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Erro ao carregar entrevista');
      }
      
      if (data.is_completed) {
        setCompleted(true);
      } else {
        setInterview(data.interview);
        setCurrentQuestion(data.interview.current_question_index || 0);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Configurar gravação de áudio
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          setAudioChunks(prev => [...prev, event.data]);
        }
      };
      
      recorder.onstop = () => {
        const blob = new Blob(audioChunks, { type: 'audio/wav' });
        setAudioBlob(blob);
      };
      
      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
    } catch (err) {
      alert('Por favor, permita o acesso ao microfone para continuar');
    }
  };
  
  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
      mediaRecorder.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
    }
  };
  
  const submitResponse = async () => {
    if (!responseText && !audioBlob) {
      alert('Por favor, grave sua resposta ou escreva no campo de texto');
      return;
    }
    
    try {
      setSubmitting(true);
      
      const formData = new FormData();
      formData.append('text', responseText);
      if (audioBlob) {
        formData.append('audio', audioBlob, 'response.wav');
      }
      
      const response = await fetch(`/api/interviews/${interview.id}/respond`, {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        throw new Error('Erro ao enviar resposta');
      }
      
      // Próxima pergunta ou finalizar
      if (currentQuestion < interview.total_questions - 1) {
        setCurrentQuestion(currentQuestion + 1);
        setResponseText('');
        setAudioBlob(null);
        setAudioChunks([]);
      } else {
        // Finalizar entrevista
        await finalizeInterview();
      }
    } catch (err) {
      alert('Erro ao enviar resposta. Por favor, tente novamente.');
    } finally {
      setSubmitting(false);
    }
  };
  
  const finalizeInterview = async () => {
    try {
      const response = await fetch(`/api/interviews/${interview.id}/finalize`, {
        method: 'POST'
      });
      
      if (response.ok) {
        setCompleted(true);
      }
    } catch (err) {
      console.error('Erro ao finalizar entrevista:', err);
    }
  };
  
  const startInterview = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/interviews/${interview.id}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        await loadInterview();
      }
    } catch (err) {
      setError('Erro ao iniciar entrevista');
    } finally {
      setLoading(false);
    }
  };
  
  // Renderização de estados
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-purple-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Carregando entrevista...</p>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Oops!</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            Tentar Novamente
          </button>
        </div>
      </div>
    );
  }
  
  if (completed) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
          <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Entrevista Concluída!</h2>
          <p className="text-gray-600 mb-6">
            Obrigado por participar do nosso processo seletivo. 
            Entraremos em contato em breve com o resultado.
          </p>
          <div className="bg-green-50 p-4 rounded-lg">
            <p className="text-sm text-green-800">
              Suas respostas foram enviadas com sucesso e serão analisadas pela nossa equipe.
            </p>
          </div>
        </div>
      </div>
    );
  }
  
  if (!interview) {
    return null;
  }
  
  // Interface principal da entrevista
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-xl font-bold text-gray-900">Entrevista de Áudio</h1>
              <p className="text-sm text-gray-600">{interview.position}</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500">Candidato</p>
              <p className="font-medium">{interview.candidate_name}</p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Progress Bar */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        <div className="bg-white rounded-lg shadow-sm p-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-gray-600">
              Pergunta {currentQuestion + 1} de {interview.total_questions}
            </span>
            <span className="text-sm text-gray-600">
              {Math.round(((currentQuestion + 1) / interview.total_questions) * 100)}% Concluído
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full transition-all"
              style={{ width: `${((currentQuestion + 1) / interview.total_questions) * 100}%` }}
            />
          </div>
        </div>
      </div>
      
      {/* Conteúdo Principal */}
      <div className="max-w-4xl mx-auto px-4 pb-8">
        {interview.status === 'agendada' ? (
          // Tela de Boas-Vindas
          <div className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold mb-4">Bem-vindo(a), {interview.candidate_name}!</h2>
            
            <div className="bg-blue-50 p-6 rounded-lg mb-6">
              <h3 className="font-semibold text-blue-900 mb-3 flex items-center">
                <Info className="w-5 h-5 mr-2" />
                Instruções Importantes
              </h3>
              <ul className="space-y-2 text-sm text-blue-800">
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  Esta entrevista contém {interview.total_questions} perguntas
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  Você pode responder por áudio ou texto
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  Escolha um local calmo e sem ruídos
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  Use fones de ouvido para melhor qualidade
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  Seja natural e objetivo em suas respostas
                </li>
              </ul>
            </div>
            
            <div className="bg-yellow-50 p-4 rounded-lg mb-6">
              <p className="text-sm text-yellow-800">
                <strong>Dica:</strong> Teste seu microfone antes de começar. 
                Após iniciar, você não poderá pausar a entrevista.
              </p>
            </div>
            
            <button
              onClick={startInterview}
              className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:from-purple-700 hover:to-blue-700 transition flex items-center justify-center"
            >
              Iniciar Entrevista
              <ArrowRight className="ml-2 w-5 h-5" />
            </button>
          </div>
        ) : (
          // Interface de Perguntas
          <div className="bg-white rounded-lg shadow-lg p-8">
            {/* Pergunta Atual */}
            <div className="mb-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Pergunta {currentQuestion + 1}
              </h3>
              <div className="bg-gradient-to-r from-purple-50 to-blue-50 p-6 rounded-lg">
                <p className="text-lg text-gray-800">
                  {interview.questions_data?.[currentQuestion]?.question || 'Carregando pergunta...'}
                </p>
              </div>
            </div>
            
            {/* Área de Resposta */}
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Sua Resposta
                </label>
                
                {/* Controles de Áudio */}
                <div className="flex items-center justify-center space-x-4 mb-4">
                  {!isRecording ? (
                    <button
                      onClick={startRecording}
                      disabled={submitting}
                      className="flex items-center px-6 py-3 bg-red-500 text-white rounded-full hover:bg-red-600 transition disabled:opacity-50"
                    >
                      <Mic className="w-5 h-5 mr-2" />
                      Gravar Resposta
                    </button>
                  ) : (
                    <button
                      onClick={stopRecording}
                      className="flex items-center px-6 py-3 bg-gray-600 text-white rounded-full hover:bg-gray-700 transition animate-pulse"
                    >
                      <MicOff className="w-5 h-5 mr-2" />
                      Parar Gravação
                    </button>
                  )}
                  
                  {audioBlob && (
                    <div className="flex items-center text-green-600">
                      <CheckCircle className="w-5 h-5 mr-2" />
                      Áudio gravado
                    </div>
                  )}
                </div>
                
                <div className="relative">
                  <textarea
                    value={responseText}
                    onChange={(e) => setResponseText(e.target.value)}
                    placeholder="Ou digite sua resposta aqui..."
                    className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                    rows="6"
                    disabled={submitting}
                  />
                  <div className="absolute bottom-2 right-2 text-sm text-gray-400">
                    {responseText.length} caracteres
                  </div>
                </div>
              </div>
              
              {/* Botões de Ação */}
              <div className="flex justify-between items-center">
                <div className="text-sm text-gray-600">
                  <HeadphonesIcon className="inline w-4 h-4 mr-1" />
                  Use fones para melhor qualidade
                </div>
                
                <button
                  onClick={submitResponse}
                  disabled={submitting || (!responseText && !audioBlob)}
                  className="flex items-center px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-semibold hover:from-purple-700 hover:to-blue-700 transition disabled:opacity-50"
                >
                  {submitting ? (
                    <>
                      <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                      Enviando...
                    </>
                  ) : currentQuestion < interview.total_questions - 1 ? (
                    <>
                      Próxima Pergunta
                      <ArrowRight className="ml-2 w-5 h-5" />
                    </>
                  ) : (
                    <>
                      Finalizar Entrevista
                      <CheckCircle className="ml-2 w-5 h-5" />
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PublicInterview;