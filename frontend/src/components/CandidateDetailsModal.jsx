import React, { useState, useEffect } from 'react';
import { 
  X, 
  User, 
  Mail, 
  Phone, 
  MapPin, 
  Clock, 
  Briefcase, 
  GraduationCap, 
  Star, 
  Calendar,
  Award,
  Globe,
  MessageSquare,
  Download,
  ExternalLink,
  Heart,
  Target,
  Sparkles
} from 'lucide-react';

const CandidateDetailsModal = ({ candidate, isOpen, onClose, onStartInterview }) => {
  const [candidateDetails, setCandidateDetails] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && candidate) {
      setCandidateDetails(null); // Reset previous data
      const candidateId = typeof candidate === 'object' ? candidate.id : candidate;
      if (candidateId) {
        fetchCandidateDetails(candidateId);
      }
    } else if (!isOpen) {
      setCandidateDetails(null); // Clear data when modal closes
    }
  }, [isOpen, candidate]);

  const fetchCandidateDetails = async (candidateId) => {
    setLoading(true);
    try {
      const id = candidateId || (typeof candidate === 'object' ? candidate.id : candidate);
      const response = await fetch(`/api/candidates/${id}`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setCandidateDetails(data);
      }
    } catch (error) {
      console.error('Erro ao carregar detalhes do candidato:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      'novo': { label: 'Novo', gradient: 'from-blue-500 to-indigo-500', icon: Sparkles },
      'triagem': { label: 'Em Triagem', gradient: 'from-amber-500 to-orange-500', icon: Clock },
      'entrevista': { label: 'Entrevista Agendada', gradient: 'from-purple-500 to-pink-500', icon: Calendar },
      'aprovado': { label: 'Aprovado', gradient: 'from-emerald-500 to-teal-500', icon: Award },
      'reprovado': { label: 'Reprovado', gradient: 'from-red-500 to-rose-500', icon: X },
      'rejeitado': { label: 'Rejeitado', gradient: 'from-red-500 to-rose-500', icon: X },
      'contratado': { label: 'Contratado', gradient: 'from-green-500 to-emerald-500', icon: Heart }
    };

    const config = statusConfig[status] || statusConfig['novo'];
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold text-white bg-gradient-to-r ${config.gradient} shadow-sm`}>
        <Icon className="w-3 h-3" />
        {config.label}
      </span>
    );
  };

  const getRecommendationBadge = (recommendation) => {
    const config = {
      'strongly_recommended': { 
        label: 'Fortemente Recomendado', 
        gradient: 'from-emerald-500 to-teal-500',
        icon: Award 
      },
      'recommended': { 
        label: 'Recomendado', 
        gradient: 'from-blue-500 to-indigo-500',
        icon: Star 
      },
      'neutral': { 
        label: 'Neutro', 
        gradient: 'from-gray-500 to-slate-500',
        icon: Target 
      },
      'not_recommended': { 
        label: 'Não Recomendado', 
        gradient: 'from-red-500 to-rose-500',
        icon: X 
      }
    };

    if (!recommendation || !config[recommendation]) return null;
    
    const recConfig = config[recommendation];
    const Icon = recConfig.icon;

    return (
      <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold text-white bg-gradient-to-r ${recConfig.gradient} shadow-sm`}>
        <Icon className="w-3 h-3" />
        {recConfig.label}
      </span>
    );
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Data não informada';
    return new Intl.DateTimeFormat('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    }).format(new Date(dateString));
  };

  if (!isOpen) return null;

  const details = candidateDetails || candidate;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="relative w-full max-w-4xl max-h-[90vh] overflow-y-auto bg-white dark:bg-gray-900 rounded-3xl shadow-2xl">
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 p-6 rounded-t-3xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-gradient-to-br from-indigo-500 to-teal-500 rounded-2xl flex items-center justify-center shadow-lg">
                <User className="w-8 h-8 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                  {details?.full_name || 'Carregando...'}
                </h2>
                <p className="text-gray-600 dark:text-gray-400 flex items-center gap-2">
                  <Briefcase className="w-4 h-4" />
                  {details?.position_applied || 'Posição não informada'}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              <X className="w-6 h-6 text-gray-500" />
            </button>
          </div>
          
          {/* Status e Recomendações */}
          <div className="flex gap-3 mt-4">
            {details?.status && getStatusBadge(details.status)}
            {details?.ai_recommendation && getRecommendationBadge(details.ai_recommendation)}
          </div>
        </div>

        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">Carregando detalhes...</p>
          </div>
        ) : (
          <div className="p-6">
            {/* Informações de Contato */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                  <Mail className="w-5 h-5 text-indigo-500" />
                  Informações de Contato
                </h3>
                <div className="space-y-3">
                  <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-xl">
                    <Mail className="w-4 h-4 text-indigo-500" />
                    <span className="text-gray-900 dark:text-white">{details?.email || 'Email não informado'}</span>
                  </div>
                  {details?.phone && (
                    <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-xl">
                      <Phone className="w-4 h-4 text-teal-500" />
                      <span className="text-gray-900 dark:text-white">{details.phone}</span>
                    </div>
                  )}
                  {details?.location && (
                    <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-xl">
                      <MapPin className="w-4 h-4 text-rose-500" />
                      <span className="text-gray-900 dark:text-white">{details.location}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                  <Clock className="w-5 h-5 text-amber-500" />
                  Informações do Processo
                </h3>
                <div className="space-y-3">
                  <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-xl">
                    <Calendar className="w-4 h-4 text-purple-500" />
                    <span className="text-gray-900 dark:text-white">
                      Cadastrado em {formatDate(details?.created_at)}
                    </span>
                  </div>
                  {details?.experience_years && (
                    <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-xl">
                      <GraduationCap className="w-4 h-4 text-green-500" />
                      <span className="text-gray-900 dark:text-white">
                        {details.experience_years} anos de experiência
                      </span>
                    </div>
                  )}
                  {details?.interview_score && (
                    <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-xl">
                      <Star className="w-4 h-4 text-yellow-500" />
                      <span className="text-gray-900 dark:text-white">
                        Score da entrevista: {details.interview_score}/10
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Skills */}
            {details?.skills && Array.isArray(details.skills) && details.skills.length > 0 && (
              <div className="mb-8">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <Award className="w-5 h-5 text-purple-500" />
                  Habilidades
                </h3>
                <div className="flex flex-wrap gap-2">
                  {details.skills.map((skill, index) => (
                    <span 
                      key={index}
                      className="px-3 py-1 bg-gradient-to-r from-indigo-100 to-teal-100 dark:from-indigo-900/30 dark:to-teal-900/30 text-indigo-700 dark:text-indigo-300 rounded-lg text-sm font-medium"
                    >
                      {typeof skill === 'string' ? skill : String(skill)}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Resumo/Observações */}
            {details?.summary && typeof details.summary === 'string' && details.summary.trim() && (
              <div className="mb-8">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <MessageSquare className="w-5 h-5 text-blue-500" />
                  Resumo
                </h3>
                <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl">
                  <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                    {details.summary}
                  </p>
                </div>
              </div>
            )}

            {/* Análise de IA */}
            {details?.ai_analysis && typeof details.ai_analysis === 'string' && details.ai_analysis.trim() && (
              <div className="mb-8">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-purple-500" />
                  Análise de IA
                </h3>
                <div className="p-4 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-xl border border-purple-200 dark:border-purple-700">
                  <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                    {details.ai_analysis}
                  </p>
                </div>
              </div>
            )}

            {/* Ações */}
            <div className="flex gap-3 pt-6 border-t border-gray-200 dark:border-gray-700">
              <button 
                onClick={() => {
                  onClose();
                  onStartInterview && onStartInterview(details);
                }}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 text-white rounded-xl font-medium transition-all duration-200 shadow-lg hover:shadow-xl"
              >
                <MessageSquare className="w-4 h-4" />
                Iniciar Entrevista
              </button>
              <button className="flex items-center justify-center gap-2 px-4 py-3 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-xl font-medium transition-all duration-200">
                <Download className="w-4 h-4" />
                Baixar CV
              </button>
              <button className="flex items-center justify-center gap-2 px-4 py-3 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-xl font-medium transition-all duration-200">
                <ExternalLink className="w-4 h-4" />
                Ver Mais
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CandidateDetailsModal;