import React, { useState, useEffect } from 'react';
import { 
  Calendar, 
  Clock, 
  Users, 
  CheckCircle, 
  XCircle, 
  Eye,
  Filter,
  Search,
  Award,
  TrendingUp,
  Download,
  Play
} from 'lucide-react';

const InterviewsList = () => {
  const [interviews, setInterviews] = useState([]);
  const [filteredInterviews, setFilteredInterviews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [positionFilter, setPositionFilter] = useState('all');
  const [selectedInterview, setSelectedInterview] = useState(null);

  // Função para baixar relatório individual de entrevista
  const handleDownloadReport = async (interviewId) => {
    try {
      // Buscar dados da entrevista específica
      let interviewData = null;
      
      // Tentar buscar do backend primeiro
      try {
        const interviewRes = await fetch('/interviews', { credentials: 'include' });
        if (interviewRes.ok) {
          const interviewsData = await interviewRes.json();
          interviewData = interviewsData.find(i => i.id === interviewId);
        }
      } catch (e) {
        console.warn('Erro ao buscar entrevistas do backend, usando dados locais');
      }
      
      // Fallback para dados locais se não encontrou no backend
      if (!interviewData) {
        interviewData = interviews.find(i => i.id === interviewId) || {};
      }
      
      // Gerar CSV com dados da entrevista
      const csvContent = generateInterviewReportCSV(interviewData);
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `interview_report_${interviewId}_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      alert('✅ Relatório de entrevista baixado com sucesso!');
    } catch (error) {
      console.error('Erro ao baixar relatório:', error);
      alert('❌ Erro ao baixar relatório: ' + error.message);
    }
  };

  // Função para exportar todas as entrevistas
  const handleExportInterviews = async () => {
    try {
      const response = await fetch('/interviews', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }

      const interviewsData = await response.json();
      
      // Gerar CSV com todas as entrevistas - ajustar para formato esperado
      const csvContent = generateInterviewsExportCSV({ interviews: interviewsData });
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `interviews_export_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      alert('✅ Relatório de entrevistas exportado com sucesso!');
    } catch (error) {
      console.error('Erro ao exportar entrevistas:', error);
      alert('❌ Erro ao exportar entrevistas: ' + error.message);
    }
  };

  // Função para gerar CSV de uma entrevista específica
  const generateInterviewReportCSV = (interview) => {
    const headers = 'Campo,Valor\n';
    const rows = [
      `"Candidato","${interview.candidate_name || ''}"`,
      `"Posição","${interview.position || ''}"`,
      `"Data","${interview.date || ''}"`,
      `"Duração","${interview.duration || 0} minutos"`,
      `"Score Geral","${interview.overall_score || 0}"`,
      `"Status","${interview.status || ''}"`,
      `"Qualidade do Áudio","${interview.audio_quality_score || 0}%"`,
      `"Taxa de Fala","${interview.speech_rate || 0} palavras/min"`,
      `"Estabilidade da Voz","${interview.voice_stability || 0}%"`,
      `"Transcrição Disponível","${interview.transcription_available ? 'Sim' : 'Não'}"`,
      `"Observações","${interview.notes || ''}"`
    ];
    return headers + rows.join('\n');
  };

  // Função para gerar CSV de exportação geral
  const generateInterviewsExportCSV = (data) => {
    const headers = 'ID,Candidato,Posição,Data,Duração (min),Score,Status,Qualidade Áudio (%),Taxa Fala (pal/min),Estabilidade Voz (%)\n';
    const rows = data.interviews?.map(interview => 
      `"${interview.id || ''}","${interview.candidate_name || ''}","${interview.position || ''}","${interview.date || ''}","${interview.duration || 0}","${interview.overall_score || 0}","${interview.status || ''}","${interview.audio_quality_score || 0}","${interview.speech_rate || 0}","${interview.voice_stability || 0}"`
    ).join('\n') || '';
    return headers + rows;
  };

  // Sem dados simulados - apenas dados reais da API

  useEffect(() => {
    // Buscar dados reais da API
    const fetchInterviews = async () => {
      setLoading(true);
      try {
        const response = await fetch('/interviews', {
          method: 'GET',
          credentials: 'include'
        });
        
        if (response.ok) {
          const data = await response.json();
          setInterviews(data);
        } else {
          console.warn('Backend indisponível, nenhum dado carregado');
          setInterviews([]);
        }
      } catch (error) {
        console.error('Erro na requisição:', error);
        // Sem dados se API falhar
        setInterviews([]);
      } finally {
        setLoading(false);
      }
    };

    fetchInterviews();
  }, []);

  // Filtrar entrevistas
  useEffect(() => {
    let filtered = interviews;

    // Filtro por busca
    if (searchTerm) {
      filtered = filtered.filter(interview => 
        interview.candidate_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        interview.candidate_email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        interview.position.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filtro por status
    if (statusFilter !== 'all') {
      filtered = filtered.filter(interview => interview.status === statusFilter);
    }

    // Filtro por posição
    if (positionFilter !== 'all') {
      filtered = filtered.filter(interview => interview.position === positionFilter);
    }

    setFilteredInterviews(filtered);
  }, [searchTerm, statusFilter, positionFilter, interviews]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'concluida': return 'bg-green-100 text-green-800';
      case 'em_andamento': return 'bg-blue-100 text-blue-800';
      case 'agendada': return 'bg-yellow-100 text-yellow-800';
      case 'cancelada': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'concluida': return <CheckCircle className="w-4 h-4" />;
      case 'em_andamento': return <Clock className="w-4 h-4" />;
      case 'agendada': return <Calendar className="w-4 h-4" />;
      case 'cancelada': return <XCircle className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  const getRecommendationColor = (recommendation) => {
    switch (recommendation) {
      case 'CONTRATAR': return 'text-green-600 bg-green-50 border-green-200';
      case 'CONSIDERAR': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'REJEITAR': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatDuration = (minutes) => {
    if (!minutes) return '-';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}min` : `${mins}min`;
  };

  const uniquePositions = [...new Set(interviews.map(interview => interview.position))];

  const showInterviewDetails = (interview) => {
    setSelectedInterview(interview);
  };

  const InterviewModal = ({ interview, onClose }) => {
    if (!interview) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6 border-b border-gray-200">
            <div className="flex justify-between items-start">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">{interview.candidate_name}</h2>
                <p className="text-gray-600">{interview.position}</p>
                <div className="flex items-center space-x-4 mt-2">
                  <span className={`px-3 py-1 rounded-full text-sm font-medium flex items-center space-x-1 ${getStatusColor(interview.status)}`}>
                    {getStatusIcon(interview.status)}
                    <span className="capitalize">{interview.status}</span>
                  </span>
                  {interview.recommendation && (
                    <span className={`px-3 py-1 rounded-lg text-sm font-medium border ${getRecommendationColor(interview.recommendation)}`}>
                      {interview.recommendation}
                    </span>
                  )}
                </div>
              </div>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 p-2"
              >
                ✕
              </button>
            </div>
          </div>

          <div className="p-6 space-y-6">
            {/* Informações Gerais */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900">Informações Gerais</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Email:</span>
                    <span className="font-medium">{interview.candidate_email}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Entrevistador:</span>
                    <span className="font-medium">{interview.interviewer_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Data/Hora:</span>
                    <span className="font-medium">{formatDate(interview.scheduled_at)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Duração:</span>
                    <span className="font-medium">{formatDuration(interview.duration_minutes)}</span>
                  </div>
                </div>
              </div>

              {/* Score Geral */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900">Score Geral</h3>
                <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-lg">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-600">{interview.overall_score.toFixed(1)}</div>
                    <div className="text-sm text-gray-600">Score Geral</div>
                    <div className="text-xs text-gray-500 mt-1">Confiança: {interview.confidence_level.toFixed(1)}%</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Scores Detalhados */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Análise Detalhada</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="text-center">
                    <div className="text-xl font-bold text-gray-700">{interview.technical_score.toFixed(1)}</div>
                    <div className="text-sm text-gray-600">Técnico</div>
                  </div>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="text-center">
                    <div className="text-xl font-bold text-gray-700">{interview.behavioral_score.toFixed(1)}</div>
                    <div className="text-sm text-gray-600">Comportamental</div>
                  </div>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="text-center">
                    <div className="text-xl font-bold text-gray-700">{interview.communication_score.toFixed(1)}</div>
                    <div className="text-sm text-gray-600">Comunicação</div>
                  </div>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="text-center">
                    <div className="text-xl font-bold text-gray-700">{interview.confidence_score.toFixed(1)}</div>
                    <div className="text-sm text-gray-600">Confiança</div>
                  </div>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="text-center">
                    <div className="text-xl font-bold text-gray-700">{interview.enthusiasm_score.toFixed(1)}</div>
                    <div className="text-sm text-gray-600">Entusiasmo</div>
                  </div>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="text-center">
                    <div className="text-xl font-bold text-gray-700">{interview.clarity_score.toFixed(1)}</div>
                    <div className="text-sm text-gray-600">Clareza</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Análise de Áudio */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Análise de Áudio</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-green-50 p-4 rounded-lg">
                  <div className="text-center">
                    <div className="text-xl font-bold text-green-600">{interview.audio_quality_score.toFixed(1)}%</div>
                    <div className="text-sm text-gray-600">Qualidade do Áudio</div>
                  </div>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="text-center">
                    <div className="text-xl font-bold text-blue-600">{interview.speech_rate.toFixed(0)}</div>
                    <div className="text-sm text-gray-600">Palavras/min</div>
                  </div>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg">
                  <div className="text-center">
                    <div className="text-xl font-bold text-purple-600">{interview.voice_stability.toFixed(1)}%</div>
                    <div className="text-sm text-gray-600">Estabilidade da Voz</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Ações */}
            <div className="flex space-x-3 pt-4 border-t border-gray-200">
              {interview.transcription_available && (
                <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 text-sm transition-colors">
                  <Eye className="w-4 h-4" />
                  <span>Ver Transcrição</span>
                </button>
              )}
              <button 
                onClick={() => handleDownloadReport(interview.id)}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 text-sm transition-colors"
              >
                <Download className="w-4 h-4" />
                <span>Baixar Relatório</span>
              </button>
              {interview.status === 'concluida' && (
                <button className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 text-sm transition-colors">
                  <Play className="w-4 h-4" />
                  <span>Reproduzir Áudio</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="space-y-6 fade-in">
        <h1 className="text-3xl font-bold text-foreground">Entrevistas</h1>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 fade-in">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Entrevistas</h1>
          <p className="text-muted-foreground">Visualize e analise todas as entrevistas realizadas</p>
        </div>
        <div className="flex items-center space-x-3">
          <button 
            onClick={handleExportInterviews}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
          >
            <Download className="w-4 h-4" />
            <span>Exportar Relatório</span>
          </button>
        </div>
      </div>

      {/* Estatísticas Rápidas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total de Entrevistas</p>
              <p className="text-2xl font-bold text-foreground">{interviews.length}</p>
            </div>
            <Users className="h-8 w-8 text-blue-600" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Concluídas</p>
              <p className="text-2xl font-bold text-foreground">{interviews.filter(i => i.status === 'concluida').length}</p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Score Médio</p>
              <p className="text-2xl font-bold text-foreground">
                {interviews.filter(i => i.overall_score > 0).length > 0 
                  ? (interviews.filter(i => i.overall_score > 0).reduce((acc, i) => acc + i.overall_score, 0) / interviews.filter(i => i.overall_score > 0).length).toFixed(1)
                  : '0.0'
                }
              </p>
            </div>
            <Award className="h-8 w-8 text-purple-600" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Recomendações Positivas</p>
              <p className="text-2xl font-bold text-foreground">{interviews.filter(i => i.recommendation === 'CONTRATAR').length}</p>
            </div>
            <TrendingUp className="h-8 w-8 text-green-600" />
          </div>
        </div>
      </div>

      {/* Filtros */}
      <div className="bg-white rounded-lg shadow-sm border border-border p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Buscar por candidato, email ou posição..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">Todos os status</option>
            <option value="concluida">Concluída</option>
            <option value="em_andamento">Em Andamento</option>
            <option value="agendada">Agendada</option>
            <option value="cancelada">Cancelada</option>
          </select>

          <select
            value={positionFilter}
            onChange={(e) => setPositionFilter(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">Todas as posições</option>
            {uniquePositions.map(position => (
              <option key={position} value={position}>{position}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Lista de Entrevistas */}
      <div className="bg-white rounded-lg shadow-sm border border-border">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left py-3 px-6 text-xs font-medium text-gray-500 uppercase tracking-wider">Candidato</th>
                <th className="text-left py-3 px-6 text-xs font-medium text-gray-500 uppercase tracking-wider">Posição</th>
                <th className="text-left py-3 px-6 text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="text-left py-3 px-6 text-xs font-medium text-gray-500 uppercase tracking-wider">Data</th>
                <th className="text-left py-3 px-6 text-xs font-medium text-gray-500 uppercase tracking-wider">Duração</th>
                <th className="text-left py-3 px-6 text-xs font-medium text-gray-500 uppercase tracking-wider">Score</th>
                <th className="text-left py-3 px-6 text-xs font-medium text-gray-500 uppercase tracking-wider">Recomendação</th>
                <th className="text-left py-3 px-6 text-xs font-medium text-gray-500 uppercase tracking-wider">Ações</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredInterviews.map((interview) => (
                <tr key={interview.id} className="hover:bg-gray-50 transition-colors">
                  <td className="py-4 px-6">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{interview.candidate_name}</div>
                      <div className="text-sm text-gray-500">{interview.candidate_email}</div>
                    </div>
                  </td>
                  <td className="py-4 px-6">
                    <div className="text-sm text-gray-900">{interview.position}</div>
                  </td>
                  <td className="py-4 px-6">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(interview.status)}`}>
                      {getStatusIcon(interview.status)}
                      <span className="ml-1 capitalize">{interview.status}</span>
                    </span>
                  </td>
                  <td className="py-4 px-6">
                    <div className="text-sm text-gray-900">{formatDate(interview.scheduled_at)}</div>
                  </td>
                  <td className="py-4 px-6">
                    <div className="text-sm text-gray-900">{formatDuration(interview.duration_minutes)}</div>
                  </td>
                  <td className="py-4 px-6">
                    <div className="text-sm font-medium text-gray-900">
                      {interview.overall_score > 0 ? interview.overall_score.toFixed(1) : '-'}
                    </div>
                  </td>
                  <td className="py-4 px-6">
                    {interview.recommendation && (
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium border ${getRecommendationColor(interview.recommendation)}`}>
                        {interview.recommendation}
                      </span>
                    )}
                  </td>
                  <td className="py-4 px-6">
                    <button
                      onClick={() => showInterviewDetails(interview)}
                      className="text-blue-600 hover:text-blue-900 text-sm font-medium flex items-center space-x-1"
                    >
                      <Eye className="w-4 h-4" />
                      <span>Ver Detalhes</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredInterviews.length === 0 && (
          <div className="text-center py-12">
            <Users className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">Nenhuma entrevista encontrada</h3>
            <p className="mt-1 text-sm text-gray-500">
              {searchTerm || statusFilter !== 'all' || positionFilter !== 'all'
                ? 'Tente ajustar os filtros de busca.'
                : 'Não há entrevistas cadastradas no sistema.'
              }
            </p>
          </div>
        )}
      </div>

      {/* Modal de detalhes */}
      {selectedInterview && (
        <InterviewModal 
          interview={selectedInterview} 
          onClose={() => setSelectedInterview(null)} 
        />
      )}
    </div>
  );
};

export default InterviewsList;