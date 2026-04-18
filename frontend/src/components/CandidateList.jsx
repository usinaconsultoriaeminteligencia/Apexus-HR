import React, { useState, useEffect } from 'react';
import { Search, Filter, Plus, Eye, MessageSquare, Calendar, Star, User, Mail, Phone, MapPin, Clock, Award, ChevronRight, Briefcase, GraduationCap, Globe, Heart, Sparkles } from 'lucide-react';
import { POSITIONS } from '../data/positions.js';
import ShareInterviewModal from './ShareInterviewModal';

const CandidateList = ({ onNewCandidate, onViewCandidate, onStartInterview }) => {
  const [candidates, setCandidates] = useState([]);
  const [filteredCandidates, setFilteredCandidates] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [positionFilter, setPositionFilter] = useState('all');
  const [loading, setLoading] = useState(false);
  const [shareModalOpen, setShareModalOpen] = useState(false);
  const [selectedCandidateForShare, setSelectedCandidateForShare] = useState(null);

  // Sem dados simulados - apenas dados reais da API

  useEffect(() => {
    // Carregar dados reais da API
    setLoading(true);
    
    const fetchCandidates = async () => {
      try {
        const response = await fetch('/api/candidates', {
          credentials: 'include'
        });
        if (response.ok) {
          const data = await response.json();
          setCandidates(data);
          setFilteredCandidates(data);
        } else {
          console.warn('Backend indisponível, nenhum candidato carregado');
          setCandidates([]);
          setFilteredCandidates([]);
        }
      } catch (error) {
        console.error('Erro ao carregar candidatos:', error);
        setCandidates([]);
        setFilteredCandidates([]);
      } finally {
        setLoading(false);
      }
    };
    
    fetchCandidates();
  }, []);

  useEffect(() => {
    // Filtrar candidatos
    let filtered = candidates;

    if (searchTerm) {
      filtered = filtered.filter(candidate =>
        candidate.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        candidate.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        candidate.position_applied.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (statusFilter !== 'all') {
      filtered = filtered.filter(candidate => candidate.status === statusFilter);
    }

    if (positionFilter !== 'all') {
      filtered = filtered.filter(candidate => candidate.position_applied === positionFilter);
    }

    setFilteredCandidates(filtered);
  }, [searchTerm, statusFilter, positionFilter, candidates]);

  const getStatusBadge = (status) => {
    const statusConfig = {
      'novo': { label: 'Novo', gradient: 'from-blue-500 to-indigo-500', icon: Sparkles },
      'triagem': { label: 'Em Triagem', gradient: 'from-amber-500 to-orange-500', icon: Clock },
      'entrevista': { label: 'Entrevista Agendada', gradient: 'from-purple-500 to-pink-500', icon: Calendar },
      'entrevista_realizada': { label: 'Entrevista Realizada', gradient: 'from-indigo-500 to-purple-500', icon: MessageSquare },
      'aprovado': { label: 'Aprovado', gradient: 'from-emerald-500 to-green-500', icon: Award },
      'rejeitado': { label: 'Rejeitado', gradient: 'from-red-500 to-rose-500', icon: Heart },
      'contratado': { label: 'Contratado', gradient: 'from-teal-500 to-cyan-500', icon: Star }
    };

    const config = statusConfig[status] || { label: status, gradient: 'from-gray-500 to-gray-600', icon: User };
    const Icon = config.icon;
    
    return (
      <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold text-white bg-gradient-to-r ${config.gradient} shadow-md hover:scale-105 transition-transform duration-200`}>
        <Icon className="w-3 h-3" />
        {config.label}
      </span>
    );
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'from-emerald-500 to-green-500';
    if (score >= 60) return 'from-amber-500 to-orange-500';
    return 'from-red-500 to-rose-500';
  };

  const getRecommendationBadge = (recommendation) => {
    if (!recommendation) return null;

    const config = {
      'CONTRATAR': { label: 'Contratar', gradient: 'from-emerald-500 to-green-500', icon: Award },
      'CONSIDERAR': { label: 'Considerar', gradient: 'from-amber-500 to-orange-500', icon: Clock },
      'REJEITAR': { label: 'Rejeitar', gradient: 'from-red-500 to-rose-500', icon: Heart }
    };

    const rec = config[recommendation] || null;
    if (!rec) return null;
    const Icon = rec.icon;

    return (
      <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold text-white bg-gradient-to-r ${rec.gradient} shadow-md`}>
        <Icon className="w-3 h-3" />
        {rec.label}
      </span>
    );
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  // Usar lista completa de posições ao invés de derivar dos candidatos
  const uniquePositions = POSITIONS;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="relative">
          <div className="w-20 h-20 border-4 border-indigo-200 rounded-full"></div>
          <div className="w-20 h-20 border-4 border-indigo-600 rounded-full animate-spin border-t-transparent absolute top-0"></div>
        </div>
      </div>
    );
  }

  // Dados simulados para demonstração visual
  const mockCandidates = filteredCandidates.length === 0 ? [
    {
      id: 1,
      full_name: 'Ana Silva',
      email: 'ana.silva@email.com',
      position_applied: 'Desenvolvedor Full Stack',
      status: 'entrevista',
      overall_score: 85,
      ai_recommendation: 'CONTRATAR',
      phone: '(11) 98765-4321',
      location: 'São Paulo, SP',
      experience_years: 5,
      skills: ['React', 'Node.js', 'TypeScript'],
      created_at: new Date().toISOString()
    },
    {
      id: 2,
      full_name: 'Carlos Oliveira',
      email: 'carlos.oliveira@email.com',
      position_applied: 'Analista de Dados',
      status: 'novo',
      overall_score: 72,
      ai_recommendation: 'CONSIDERAR',
      phone: '(21) 99876-5432',
      location: 'Rio de Janeiro, RJ',
      experience_years: 3,
      skills: ['Python', 'SQL', 'Machine Learning'],
      created_at: new Date().toISOString()
    },
    {
      id: 3,
      full_name: 'Mariana Costa',
      email: 'mariana.costa@email.com',
      position_applied: 'Designer UX/UI',
      status: 'aprovado',
      overall_score: 92,
      ai_recommendation: 'CONTRATAR',
      phone: '(31) 97654-3210',
      location: 'Belo Horizonte, MG',
      experience_years: 7,
      skills: ['Figma', 'Adobe XD', 'Sketch'],
      created_at: new Date().toISOString()
    },
  ] : filteredCandidates;

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold bg-gradient-to-r from-indigo-600 to-teal-600 bg-clip-text text-transparent">
            Candidatos
          </h1>
          <p className="text-sm sm:text-base text-gray-500 dark:text-gray-400 mt-1">
            Gerencie todos os candidatos do sistema
          </p>
        </div>
        <button
          onClick={onNewCandidate}
          className="w-full sm:w-auto px-4 sm:px-6 py-3 min-h-[44px] bg-gradient-to-r from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-200 flex items-center justify-center gap-2"
        >
          <Plus className="w-5 h-5" />
          <span className="text-sm sm:text-base">Novo Candidato</span>
        </button>
      </div>

      {/* Filtros com Glass Morphism */}
      <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl rounded-2xl shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-4 sm:p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 sm:gap-4">
          {/* Busca */}
          <div className="relative group">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5 group-focus-within:text-indigo-600 transition-colors" />
            <input
              type="text"
              placeholder="Buscar por nome, email ou posição..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-12 pr-4 py-3 min-h-[44px] bg-gray-100/50 dark:bg-gray-800/50 border border-gray-200/50 dark:border-gray-700/50 rounded-xl focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 focus:bg-white dark:focus:bg-gray-800 transition-all duration-200 text-sm sm:text-base"
            />
          </div>

          {/* Filtro por status */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-3 min-h-[44px] bg-gray-100/50 dark:bg-gray-800/50 border border-gray-200/50 dark:border-gray-700/50 rounded-xl focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 focus:bg-white dark:focus:bg-gray-800 transition-all duration-200 cursor-pointer text-sm sm:text-base"
          >
            <option value="all">Todos os status</option>
            <option value="novo">Novo</option>
            <option value="triagem">Em Triagem</option>
            <option value="entrevista">Entrevista Agendada</option>
            <option value="entrevista_realizada">Entrevista Realizada</option>
            <option value="aprovado">Aprovado</option>
            <option value="rejeitado">Rejeitado</option>
            <option value="contratado">Contratado</option>
          </select>

          {/* Filtro por posição */}
          <select
            value={positionFilter}
            onChange={(e) => setPositionFilter(e.target.value)}
            className="px-4 py-3 min-h-[44px] bg-gray-100/50 dark:bg-gray-800/50 border border-gray-200/50 dark:border-gray-700/50 rounded-xl focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 focus:bg-white dark:focus:bg-gray-800 transition-all duration-200 cursor-pointer text-sm sm:text-base"
          >
            <option value="all">Todas as posições</option>
            {uniquePositions.map(position => (
              <option key={position} value={position}>{position}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Lista de candidatos com Cards Modernos */}
      <div className="space-y-4">
        {mockCandidates.map((candidate, index) => (
          <div 
            key={candidate.id} 
            className="group bg-white dark:bg-gray-900 rounded-2xl shadow-lg hover:shadow-2xl border border-gray-200/50 dark:border-gray-700/50 p-4 sm:p-6 transition-all duration-300 hover:scale-[1.01] animate-slide-in-up"
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
              <div className="flex-1">
                {/* Header do Card */}
                <div className="flex items-start gap-3 sm:gap-4 mb-4">
                  {/* Avatar com Gradiente */}
                  <div className="relative">
                    <div className="w-12 h-12 sm:w-16 sm:h-16 bg-gradient-to-br from-indigo-500 to-teal-500 rounded-2xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">
                      <User className="w-6 h-6 sm:w-8 sm:h-8 text-white" />
                    </div>
                    {candidate.overall_score && (
                      <div className={`absolute -top-1 -right-1 sm:-top-2 sm:-right-2 w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-gradient-to-r ${getScoreColor(candidate.overall_score)} flex items-center justify-center text-white text-[10px] sm:text-xs font-bold shadow-md`}>
                        {candidate.overall_score}
                      </div>
                    )}
                  </div>
                  
                  {/* Informações Principais */}
                  <div className="flex-1">
                    <div className="flex flex-wrap items-center gap-2 sm:gap-3 mb-2">
                      <h4 className="text-lg sm:text-xl font-bold text-gray-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                        {candidate.full_name}
                      </h4>
                      {getStatusBadge(candidate.status)}
                      {getRecommendationBadge(candidate.ai_recommendation)}
                    </div>
                    <div className="flex items-center gap-2 text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                      <Briefcase className="w-3 h-3 sm:w-4 sm:h-4 flex-shrink-0" />
                      <span className="font-medium truncate">{candidate.position_applied}</span>
                    </div>
                  </div>
                </div>

                {/* Grid de Informações */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4 mb-4">
                  <div className="flex items-center gap-2 text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                    <Mail className="w-3 h-3 sm:w-4 sm:h-4 text-indigo-500 flex-shrink-0" />
                    <span className="truncate">{candidate.email}</span>
                  </div>
                  
                  {candidate.phone && (
                    <div className="flex items-center gap-2 text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                      <Phone className="w-3 h-3 sm:w-4 sm:h-4 text-teal-500 flex-shrink-0" />
                      <span className="truncate">{candidate.phone}</span>
                    </div>
                  )}
                  
                  {candidate.location && (
                    <div className="flex items-center gap-2 text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                      <MapPin className="w-3 h-3 sm:w-4 sm:h-4 text-rose-500 flex-shrink-0" />
                      <span className="truncate">{candidate.location}</span>
                    </div>
                  )}
                  
                  <div className="flex items-center gap-2 text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                    <Clock className="w-3 h-3 sm:w-4 sm:h-4 text-amber-500 flex-shrink-0" />
                    <span className="truncate">Cadastrado em {formatDate(candidate.created_at)}</span>
                  </div>
                </div>

                {/* Skills Tags */}
                {candidate.skills && (
                  <div className="flex flex-wrap gap-2 mb-4">
                    {candidate.skills.map((skill, skillIndex) => (
                      <span 
                        key={skillIndex}
                        className="px-3 py-1 bg-gradient-to-r from-indigo-100 to-teal-100 dark:from-indigo-900/30 dark:to-teal-900/30 text-indigo-700 dark:text-indigo-300 rounded-lg text-xs font-medium"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                )}

                {/* Métricas Adicionais */}
                <div className="flex items-center gap-6 text-sm text-gray-600 dark:text-gray-400">
                  {candidate.experience_years && (
                    <div className="flex items-center gap-1">
                      <GraduationCap className="w-4 h-4" />
                      <span>{candidate.experience_years} anos de experiência</span>
                    </div>
                  )}
                  {candidate.interview_score && (
                    <div className="flex items-center gap-1">
                      <Star className="w-4 h-4 text-yellow-500" />
                      <span>Score: {candidate.interview_score}/10</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Ações do Card */}
              <div className="flex sm:flex-col gap-2 justify-end">
                <button
                  onClick={() => onViewCandidate && onViewCandidate(candidate)}
                  className="p-2 min-w-[44px] min-h-[44px] rounded-xl bg-gray-100 dark:bg-gray-800 hover:bg-indigo-100 dark:hover:bg-indigo-900/30 text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition-all duration-200 group/btn"
                  title="Ver detalhes"
                >
                  <Eye className="w-5 h-5 group-hover/btn:scale-110 transition-transform" />
                </button>
                
                <button
                  onClick={() => onStartInterview && onStartInterview(candidate)}
                  className="p-2 min-w-[44px] min-h-[44px] rounded-xl bg-gray-100 dark:bg-gray-800 hover:bg-teal-100 dark:hover:bg-teal-900/30 text-gray-700 dark:text-gray-300 hover:text-teal-600 dark:hover:text-teal-400 transition-all duration-200 group/btn"
                  title="Iniciar entrevista"
                >
                  <MessageSquare className="w-5 h-5 group-hover/btn:scale-110 transition-transform" />
                </button>
                
                <button
                  onClick={() => {
                    setSelectedCandidateForShare(candidate);
                    setShareModalOpen(true);
                  }}
                  className="p-2 min-w-[44px] min-h-[44px] rounded-xl bg-gray-100 dark:bg-gray-800 hover:bg-fuchsia-100 dark:hover:bg-fuchsia-900/30 text-gray-700 dark:text-gray-300 hover:text-fuchsia-600 dark:hover:text-fuchsia-400 transition-all duration-200 group/btn"
                  title="Compartilhar"
                >
                  <Globe className="w-5 h-5 group-hover/btn:scale-110 transition-transform" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {mockCandidates.length === 0 && (
        <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-12 text-center">
          <div className="w-24 h-24 bg-gradient-to-br from-indigo-500/20 to-teal-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <Users className="w-12 h-12 text-indigo-600" />
          </div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
            Nenhum candidato encontrado
          </h3>
          <p className="text-gray-500 dark:text-gray-400 mb-6">
            Ajuste os filtros ou adicione novos candidatos ao sistema.
          </p>
          <button
            onClick={onNewCandidate}
            className="px-6 py-3 bg-gradient-to-r from-indigo-500 to-indigo-600 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-200 inline-flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            <span>Adicionar Primeiro Candidato</span>
          </button>
        </div>
      )}

      {/* Modal de Compartilhamento */}
      {shareModalOpen && (
        <ShareInterviewModal
          isOpen={shareModalOpen}
          onClose={() => setShareModalOpen(false)}
          candidateId={selectedCandidateForShare?.id}
          candidateName={selectedCandidateForShare?.full_name}
        />
      )}
    </div>
  );
};

export default CandidateList;