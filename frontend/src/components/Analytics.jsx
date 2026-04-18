import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  Activity,
  PieChart as PieChartIcon,
  BarChart3,
  Users,
  Target,
  Award,
  ArrowUp,
  ArrowDown,
  Calendar,
  Clock,
  Filter,
  RefreshCw,
  Zap
} from 'lucide-react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  Scatter
} from 'recharts';

const Analytics = () => {
  const [kpiData, setKpiData] = useState(null);
  const [trendsData, setTrendsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPeriod, setSelectedPeriod] = useState('30');
  const [refreshing, setRefreshing] = useState(false);
  const [compareMode, setCompareMode] = useState(false);

  // Cores vibrantes para os gráficos
  const COLORS = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8'];
  const GRADIENT_COLORS = [
    { id: 'gradient1', start: '#667eea', end: '#764ba2' },
    { id: 'gradient2', start: '#f093fb', end: '#f5576c' },
    { id: 'gradient3', start: '#4facfe', end: '#00f2fe' },
    { id: 'gradient4', start: '#43e97b', end: '#38f9d7' },
    { id: 'gradient5', start: '#fa709a', end: '#fee140' }
  ];

  // Buscar dados de analytics
  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('auth_token');
      if (!token) {
        throw new Error('Token não encontrado');
      }

      // Buscar KPIs
      const kpisResponse = await fetch('/api/analytics/kpis', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      // Buscar tendências
      const trendsResponse = await fetch(`/api/analytics/trends?period=${selectedPeriod}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!kpisResponse.ok || !trendsResponse.ok) {
        throw new Error('Erro ao buscar dados de analytics');
      }

      const kpis = await kpisResponse.json();
      const trends = await trendsResponse.json();

      setKpiData(kpis.data);
      setTrendsData(trends.data);
    } catch (err) {
      console.error('Erro ao buscar analytics:', err);
      setError(err.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAnalyticsData();
  }, [selectedPeriod]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchAnalyticsData();
  };

  // Componente de KPI Card
  const KPICard = ({ title, value, change, icon: Icon, color, description }) => (
    <div className={`card bg-gradient-to-br ${color} p-6`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">{title}</p>
          <p className="text-3xl font-bold mb-2">{value}</p>
          {change !== undefined && (
            <div className="flex items-center gap-1">
              {change > 0 ? (
                <ArrowUp className="h-4 w-4 text-green-500" />
              ) : (
                <ArrowDown className="h-4 w-4 text-red-500" />
              )}
              <span className={`text-sm ${change > 0 ? 'text-green-600' : 'text-red-600'}`}>
                {Math.abs(change)}%
              </span>
            </div>
          )}
          {description && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">{description}</p>
          )}
        </div>
        <Icon className={`h-8 w-8 opacity-50`} />
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Carregando analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">Erro ao carregar analytics: {error}</p>
          <button onClick={handleRefresh} className="btn-primary">
            Tentar Novamente
          </button>
        </div>
      </div>
    );
  }

  const kpis = kpiData || {};
  const trends = trendsData || {};

  // Preparar dados do funil
  const funnelData = trends.conversion_funnel || [];

  // Preparar dados do heatmap
  const heatmapData = trends.interview_heatmap || [];
  
  // Transformar dados do heatmap para o formato necessário
  const weekdays = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];
  const hours = Array.from({ length: 24 }, (_, i) => i);
  
  const heatmapMatrix = hours.map(hour => ({
    hour: `${hour}:00`,
    ...weekdays.reduce((acc, day, index) => {
      const dataPoint = heatmapData.find(d => d.weekday === index && d.hour === hour);
      acc[day] = dataPoint ? dataPoint.count : 0;
      return acc;
    }, {})
  }));

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
            Analytics Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Métricas e insights do sistema de recrutamento
          </p>
        </div>

        <div className="flex items-center gap-4">
          {/* Seletor de Período */}
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
          >
            <option value="7">Últimos 7 dias</option>
            <option value="30">Últimos 30 dias</option>
            <option value="90">Últimos 90 dias</option>
            <option value="365">Último ano</option>
          </select>

          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className={`p-2 rounded-lg ${refreshing ? 'animate-spin' : ''} hover:bg-gray-100 dark:hover:bg-gray-700`}
          >
            <RefreshCw className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Total de Candidatos"
          value={kpis.candidates?.total || 0}
          change={kpis.candidates?.growth_rate}
          icon={Users}
          color="from-blue-50 to-indigo-50 dark:from-blue-900 dark:to-indigo-900"
          description={`${kpis.candidates?.new_this_week || 0} novos esta semana`}
        />
        
        <KPICard
          title="Taxa de Aprovação"
          value={`${kpis.performance?.approval_rate || 0}%`}
          icon={Target}
          color="from-green-50 to-emerald-50 dark:from-green-900 dark:to-emerald-900"
          description="Candidatos aprovados"
        />
        
        <KPICard
          title="Score Médio"
          value={kpis.performance?.avg_score || '0.0'}
          icon={Award}
          color="from-purple-50 to-pink-50 dark:from-purple-900 dark:to-pink-900"
          description="Pontuação geral"
        />
        
        <KPICard
          title="Tempo Médio"
          value={`${kpis.performance?.avg_hiring_days || 0}d`}
          icon={Clock}
          color="from-orange-50 to-red-50 dark:from-orange-900 dark:to-red-900"
          description="Até contratação"
        />
      </div>

      {/* Gráficos de Tendências */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tendência de Candidatos */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-indigo-600" />
            Tendência de Candidatos
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={trends.candidates_trend || []}>
              <defs>
                {GRADIENT_COLORS.map(gradient => (
                  <linearGradient key={gradient.id} id={gradient.id} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={gradient.start} stopOpacity={0.8}/>
                    <stop offset="95%" stopColor={gradient.end} stopOpacity={0.1}/>
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: 'none',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
                }}
              />
              <Area 
                type="monotone" 
                dataKey="count" 
                stroke="#667eea" 
                strokeWidth={2}
                fill="url(#gradient1)" 
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Tendência de Entrevistas */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Activity className="h-5 w-5 text-green-600" />
            Tendência de Entrevistas
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trends.interviews_trend || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line 
                type="monotone" 
                dataKey="count" 
                stroke="#4ECDC4" 
                strokeWidth={3}
                dot={{ fill: '#4ECDC4', r: 4 }}
                activeDot={{ r: 8 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Funil de Conversão */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Filter className="h-5 w-5 text-purple-600" />
          Funil de Conversão de Candidatos
        </h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart 
            data={funnelData}
            layout="horizontal"
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
            <XAxis type="number" />
            <YAxis dataKey="stage" type="category" width={100} />
            <Tooltip 
              formatter={(value, name) => {
                if (name === 'count') return [`${value} candidatos`, 'Total'];
                if (name === 'percentage') return [`${value.toFixed(1)}%`, 'Percentual'];
                return [value, name];
              }}
            />
            <Bar dataKey="count" fill="#667eea" radius={[0, 8, 8, 0]}>
              {funnelData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <div className="mt-4 flex justify-around">
          {funnelData.map((stage, index) => (
            <div key={index} className="text-center">
              <p className="text-sm text-gray-600 dark:text-gray-400">{stage.stage}</p>
              <p className="text-lg font-bold" style={{ color: COLORS[index % COLORS.length] }}>
                {stage.percentage.toFixed(1)}%
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Performance dos Recrutadores e Distribuição de Scores */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Performance dos Recrutadores */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Users className="h-5 w-5 text-blue-600" />
            Performance dos Recrutadores
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={trends.recruiter_performance || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="total_candidates" fill="#8884d8" name="Total" />
              <Bar dataKey="hired" fill="#82ca9d" name="Contratados" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Distribuição de Scores */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <PieChartIcon className="h-5 w-5 text-orange-600" />
            Distribuição de Scores
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={trends.score_distribution || []}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.range}: ${entry.count}`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="count"
              >
                {(trends.score_distribution || []).map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Mapa de Calor de Horários */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Calendar className="h-5 w-5 text-red-600" />
          Mapa de Calor - Horários de Entrevista
        </h3>
        <div className="overflow-x-auto">
          <div className="min-w-[600px]">
            <div className="grid grid-cols-8 gap-1">
              <div className="text-center text-sm font-medium p-2">Hora</div>
              {weekdays.map(day => (
                <div key={day} className="text-center text-sm font-medium p-2">{day}</div>
              ))}
              {heatmapMatrix.map((hourData) => (
                <React.Fragment key={hourData.hour}>
                  <div className="text-sm font-medium p-2">{hourData.hour}</div>
                  {weekdays.map(day => {
                    const value = hourData[day] || 0;
                    const intensity = value > 0 ? Math.min(value / 5, 1) : 0;
                    return (
                      <div
                        key={`${hourData.hour}-${day}`}
                        className="p-2 rounded text-center text-xs"
                        style={{
                          backgroundColor: value > 0 
                            ? `rgba(99, 102, 241, ${intensity})`
                            : 'rgba(229, 231, 235, 0.3)',
                          color: intensity > 0.5 ? 'white' : 'inherit'
                        }}
                        title={`${day} ${hourData.hour}: ${value} entrevistas`}
                      >
                        {value > 0 ? value : ''}
                      </div>
                    );
                  })}
                </React.Fragment>
              ))}
            </div>
          </div>
          <div className="mt-4 flex items-center gap-2 text-sm">
            <span className="text-gray-600 dark:text-gray-400">Menos</span>
            <div className="flex gap-1">
              {[0.2, 0.4, 0.6, 0.8, 1].map(opacity => (
                <div
                  key={opacity}
                  className="w-6 h-6 rounded"
                  style={{ backgroundColor: `rgba(99, 102, 241, ${opacity})` }}
                />
              ))}
            </div>
            <span className="text-gray-600 dark:text-gray-400">Mais</span>
          </div>
        </div>
      </div>

      {/* Distribuição por Fonte e Posição */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Candidatos por Fonte */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Zap className="h-5 w-5 text-yellow-600" />
            Candidatos por Fonte
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={trends.source_distribution || []}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                fill="#8884d8"
                paddingAngle={5}
                dataKey="count"
              >
                {(trends.source_distribution || []).map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 grid grid-cols-2 gap-2">
            {(trends.source_distribution || []).map((source, index) => (
              <div key={index} className="flex items-center gap-2">
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: COLORS[index % COLORS.length] }}
                />
                <span className="text-sm">{source.source}: {source.count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Top Posições */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-cyan-600" />
            Top Posições Mais Procuradas
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart 
              data={trends.position_distribution || []}
              layout="horizontal"
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis type="number" />
              <YAxis dataKey="position" type="category" width={150} />
              <Tooltip />
              <Bar dataKey="count" fill="#45B7D1" radius={[0, 8, 8, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Resumo de Métricas */}
      <div className="card bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900 dark:to-purple-900">
        <h3 className="text-lg font-semibold mb-4">Resumo de Métricas</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Candidatos no Pipeline</p>
            <p className="text-2xl font-bold">{kpis.candidates?.in_pipeline || 0}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Entrevistas Agendadas</p>
            <p className="text-2xl font-bold">{kpis.interviews?.scheduled || 0}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Taxa de Conclusão</p>
            <p className="text-2xl font-bold">{kpis.interviews?.completion_rate || 0}%</p>
          </div>
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Taxa de Desistência</p>
            <p className="text-2xl font-bold">{kpis.performance?.dropout_rate || 0}%</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;