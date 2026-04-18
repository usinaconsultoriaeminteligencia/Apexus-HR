import React, { useState, useEffect } from 'react';
import {
  FileText,
  Download,
  Filter,
  Calendar,
  Users,
  TrendingUp,
  Clock,
  CheckCircle,
  XCircle,
  BarChart3,
  RefreshCw,
  FileDown,
  Share2
} from 'lucide-react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

const Reports = () => {
  const [reportData, setReportData] = useState(null);
  const [interviewData, setInterviewData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPeriod, setSelectedPeriod] = useState('month');
  const [refreshing, setRefreshing] = useState(false);

  // Cores vibrantes para os gráficos
  const COLORS = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8'];
  const GRADIENT_COLORS = [
    { start: '#667eea', end: '#764ba2' },
    { start: '#f093fb', end: '#f5576c' },
    { start: '#4facfe', end: '#00f2fe' },
    { start: '#43e97b', end: '#38f9d7' },
    { start: '#fa709a', end: '#fee140' }
  ];

  // Buscar dados de relatórios
  const fetchReportsData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('auth_token');
      if (!token) {
        throw new Error('Token não encontrado');
      }

      // Buscar relatório de candidatos
      const candidatesResponse = await fetch(
        `/api/reports/candidates?period=${selectedPeriod}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      // Buscar relatório de entrevistas
      const interviewsResponse = await fetch(
        `/api/reports/interviews?period=${selectedPeriod}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (!candidatesResponse.ok || !interviewsResponse.ok) {
        throw new Error('Erro ao buscar dados');
      }

      const candidatesData = await candidatesResponse.json();
      const interviewsData = await interviewsResponse.json();

      setReportData(candidatesData.data);
      setInterviewData(interviewsData.data);
    } catch (err) {
      console.error('Erro ao buscar relatórios:', err);
      setError(err.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchReportsData();
  }, [selectedPeriod]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchReportsData();
  };

  const handleExport = async (format) => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/reports/export/candidates?format=${format}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `report_${new Date().toISOString()}.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('Erro ao exportar:', err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Carregando relatórios...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Erro ao carregar relatórios: {error}</p>
          <button 
            onClick={handleRefresh}
            className="mt-4 btn-primary"
          >
            Tentar Novamente
          </button>
        </div>
      </div>
    );
  }

  const summary = reportData?.summary || {};
  const statusDistribution = reportData?.status_distribution || [];
  const positionDistribution = reportData?.position_distribution || [];
  const scoreByStatus = reportData?.score_by_status || [];
  const interviewSummary = interviewData?.summary || {};
  const weekdayDistribution = interviewData?.weekday_distribution || [];
  const hourlyDistribution = interviewData?.hourly_distribution || [];

  return (
    <div className="p-4 sm:p-6 space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:justify-between lg:items-center gap-4 mb-6 sm:mb-8">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
            Relatórios do Sistema
          </h1>
          <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400 mt-1 sm:mt-2">
            Análise completa de candidatos e entrevistas
          </p>
        </div>

        <div className="flex items-center gap-2 sm:gap-4">
          {/* Filtro de Período */}
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value)}
            className="px-3 sm:px-4 py-2 min-h-[44px] border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-sm sm:text-base"
          >
            <option value="today">Hoje</option>
            <option value="week">Última Semana</option>
            <option value="month">Último Mês</option>
            <option value="year">Último Ano</option>
            <option value="all">Todos</option>
          </select>

          {/* Botões de Ação */}
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className={`p-2 min-w-[44px] min-h-[44px] rounded-lg ${refreshing ? 'animate-spin' : ''} hover:bg-gray-100 dark:hover:bg-gray-700`}
          >
            <RefreshCw className="h-4 w-4 sm:h-5 sm:w-5" />
          </button>

          <div className="relative group">
            <button className="btn-primary flex items-center gap-2 px-3 sm:px-4 py-2 min-h-[44px] text-sm sm:text-base">
              <Download className="h-4 w-4" />
              <span className="hidden sm:inline">Exportar</span>
            </button>
            <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all">
              <button 
                onClick={() => handleExport('pdf')}
                className="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                Exportar como PDF
              </button>
              <button 
                onClick={() => handleExport('excel')}
                className="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                Exportar como Excel
              </button>
              <button 
                onClick={() => handleExport('json')}
                className="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                Exportar como JSON
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Cards de Resumo */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <div className="card bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900 dark:to-indigo-900 p-4 sm:p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">Total de Candidatos</p>
              <p className="text-2xl sm:text-3xl font-bold text-indigo-600 dark:text-indigo-400">
                {summary.total_candidates || 0}
              </p>
            </div>
            <Users className="h-8 w-8 sm:h-10 sm:w-10 text-indigo-500 opacity-50" />
          </div>
        </div>

        <div className="card bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900 dark:to-emerald-900 p-4 sm:p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">Taxa de Aprovação</p>
              <p className="text-2xl sm:text-3xl font-bold text-green-600 dark:text-green-400">
                {summary.approval_rate || 0}%
              </p>
            </div>
            <CheckCircle className="h-8 w-8 sm:h-10 sm:w-10 text-green-500 opacity-50" />
          </div>
        </div>

        <div className="card bg-gradient-to-br from-red-50 to-pink-50 dark:from-red-900 dark:to-pink-900 p-4 sm:p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">Taxa de Rejeição</p>
              <p className="text-2xl sm:text-3xl font-bold text-red-600 dark:text-red-400">
                {summary.rejection_rate || 0}%
              </p>
            </div>
            <XCircle className="h-8 w-8 sm:h-10 sm:w-10 text-red-500 opacity-50" />
          </div>
        </div>

        <div className="card bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900 dark:to-pink-900 p-4 sm:p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">Tempo Médio (dias)</p>
              <p className="text-2xl sm:text-3xl font-bold text-purple-600 dark:text-purple-400">
                {summary.avg_process_days || 0}
              </p>
            </div>
            <Clock className="h-8 w-8 sm:h-10 sm:w-10 text-purple-500 opacity-50" />
          </div>
        </div>
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        {/* Distribuição por Status */}
        <div className="card p-4 sm:p-6">
          <h3 className="text-base sm:text-lg font-semibold mb-4 flex items-center gap-2">
            <BarChart3 className="h-4 w-4 sm:h-5 sm:w-5 text-indigo-600" />
            Candidatos por Status
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={statusDistribution}>
              <defs>
                <linearGradient id="colorBar" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#8884d8" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis dataKey="status" />
              <YAxis />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: 'none',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
                }}
              />
              <Bar dataKey="count" fill="url(#colorBar)" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Distribuição por Posição */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Users className="h-5 w-5 text-purple-600" />
            Candidatos por Posição
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={positionDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.position}: ${entry.count}`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="count"
              >
                {positionDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Score Médio por Status */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-green-600" />
            Score Médio por Status
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={scoreByStatus}>
              <defs>
                <linearGradient id="colorLine" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#82ca9d" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#82ca9d" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis dataKey="status" />
              <YAxis domain={[0, 10]} />
              <Tooltip />
              <Line 
                type="monotone" 
                dataKey="avg_score" 
                stroke="#82ca9d" 
                strokeWidth={3}
                fill="url(#colorLine)"
                dot={{ fill: '#82ca9d', r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Entrevistas por Dia da Semana */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Calendar className="h-5 w-5 text-blue-600" />
            Entrevistas por Dia da Semana
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={weekdayDistribution}>
              <defs>
                <linearGradient id="colorWeekday" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#667eea" />
                  <stop offset="100%" stopColor="#764ba2" />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="url(#colorWeekday)" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Resumo de Entrevistas */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Resumo de Entrevistas</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400">Total</p>
            <p className="text-2xl font-bold">{interviewSummary.total_interviews || 0}</p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400">Concluídas</p>
            <p className="text-2xl font-bold text-green-600">{interviewSummary.completed || 0}</p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400">Agendadas</p>
            <p className="text-2xl font-bold text-blue-600">{interviewSummary.scheduled || 0}</p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400">Taxa de Conclusão</p>
            <p className="text-2xl font-bold text-indigo-600">{interviewSummary.completion_rate || 0}%</p>
          </div>
        </div>
      </div>

      {/* Tabela de Candidatos Recentes */}
      {reportData?.candidates && reportData.candidates.length > 0 && (
        <div className="card overflow-hidden">
          <h3 className="text-lg font-semibold mb-4">Candidatos Recentes</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Nome
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Posição
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Score
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Recomendação IA
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {reportData.candidates.slice(0, 10).map((candidate) => (
                  <tr key={candidate.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                    <td className="px-4 py-3 text-sm">{candidate.full_name}</td>
                    <td className="px-4 py-3 text-sm">{candidate.position_applied}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        candidate.status === 'aprovado' ? 'bg-green-100 text-green-800' :
                        candidate.status === 'rejeitado' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {candidate.status_display}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">{candidate.overall_score}</td>
                    <td className="px-4 py-3 text-sm">{candidate.ai_recommendation || 'N/A'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default Reports;