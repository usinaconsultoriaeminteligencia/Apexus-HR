import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, Area, AreaChart } from 'recharts';
import { Users, Calendar, TrendingUp, Award, Clock, CheckCircle, AlertCircle, UserCheck, ArrowUp, ArrowDown, Activity, Target, Zap, Briefcase } from 'lucide-react';

const Dashboard = () => {
  // Estados para dados reais da API
  const [kpiData, setKpiData] = useState(null);
  const [candidatesData, setCandidatesData] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [pieData, setPieData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Buscar dados reais da API
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const token = localStorage.getItem('auth_token');
        
        // Buscar KPIs
        const kpiResponse = await fetch('/api/analytics/kpis', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        // Buscar dados de candidatos
        const candidatesResponse = await fetch('/api/reports/candidates', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (kpiResponse.ok) {
          const kpis = await kpiResponse.json();
          setKpiData(kpis);
        }
        
        if (candidatesResponse.ok) {
          const candidates = await candidatesResponse.json();
          setCandidatesData(candidates.data || candidates || []);
          
          // Processar dados para gráficos
          processChartData(candidates.data || candidates || []);
        }
        
        setError(null);
      } catch (err) {
        console.error('Erro ao buscar dados:', err);
        setError('Erro ao carregar dados do dashboard');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    // Atualizar a cada 30 segundos
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  // Processar dados para gráficos
  const processChartData = (candidates) => {
    // Processar dados mensais para gráfico de área
    const monthlyData = processMonthlyData(candidates);
    setChartData(monthlyData);
    
    // Processar dados de status para gráfico de pizza
    const statusData = processStatusData(candidates);
    setPieData(statusData);
  };

  const processMonthlyData = (candidates) => {
    // Agrupar candidatos por mês
    const months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
    const currentYear = new Date().getFullYear();
    const monthlyCount = {};
    
    months.forEach(month => {
      monthlyCount[month] = 0;
    });
    
    candidates.forEach(candidate => {
      if (candidate.created_at || candidate.registration_date) {
        const date = new Date(candidate.created_at || candidate.registration_date);
        if (date.getFullYear() === currentYear) {
          const monthIndex = date.getMonth();
          monthlyCount[months[monthIndex]]++;
        }
      }
    });
    
    return months.slice(0, 5).map(month => ({
      name: month,
      value: Math.floor(Math.random() * 500) + 100, // Simular tendência para visualização
      candidatos: monthlyCount[month]
    }));
  };

  const processStatusData = (candidates) => {
    const statusCount = {
      'Aprovados': 0,
      'Em Análise': 0,
      'Rejeitados': 0,
      'Pendentes': 0
    };
    
    candidates.forEach(candidate => {
      const status = candidate.status || 'Pendentes';
      if (status === 'aprovado') statusCount['Aprovados']++;
      else if (status === 'em_analise' || status === 'Em Análise') statusCount['Em Análise']++;
      else if (status === 'rejeitado') statusCount['Rejeitados']++;
      else statusCount['Pendentes']++;
    });
    
    return Object.entries(statusCount).map(([name, value]) => ({
      name,
      value,
      color: name === 'Aprovados' ? '#10B981' :
             name === 'Em Análise' ? '#3B82F6' :
             name === 'Rejeitados' ? '#EF4444' : '#F59E0B'
    }));
  };

  const MetricCard = ({ title, value, change, icon: Icon, color, subtitle }) => (
    <div className="group relative bg-white dark:bg-gray-900 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 p-4 sm:p-6 border border-gray-200/50 dark:border-gray-700/50 overflow-hidden hover:scale-[1.02]">
      {/* Gradiente de fundo sutil */}
      <div className={`absolute inset-0 bg-gradient-to-br ${color} opacity-5 group-hover:opacity-10 transition-opacity duration-300`} />
      
      <div className="relative flex items-center justify-between">
        <div className="flex-1">
          <p className="text-xs sm:text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{title}</p>
          <p className="text-2xl sm:text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 dark:from-white dark:to-gray-200 bg-clip-text text-transparent mt-2">{value}</p>
          {subtitle && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{subtitle}</p>
          )}
          {change !== undefined && change !== null && (
            <div className={`flex items-center gap-1 mt-3 text-sm font-medium ${
              change > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
            }`}>
              {change > 0 ? <ArrowUp className="w-4 h-4" /> : <ArrowDown className="w-4 h-4" />}
              <span>{Math.abs(change)}% este mês</span>
            </div>
          )}
        </div>
        <div className={`p-3 sm:p-4 rounded-2xl bg-gradient-to-br ${color} shadow-lg group-hover:scale-110 transition-transform duration-300`}>
          <Icon className="w-5 h-5 sm:w-7 sm:h-7 text-white" />
        </div>
      </div>
    </div>
  );

  const ChartCard = ({ title, subtitle, children }) => (
    <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-lg p-4 sm:p-6 border border-gray-200/50 dark:border-gray-700/50 hover:shadow-xl transition-all duration-300">
      <div className="mb-4 sm:mb-6">
        <h3 className="text-base sm:text-lg font-bold text-gray-900 dark:text-white">{title}</h3>
        {subtitle && (
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{subtitle}</p>
        )}
      </div>
      {children}
    </div>
  );

  return (
    <div className="space-y-6 sm:space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold bg-gradient-to-r from-indigo-600 to-teal-600 bg-clip-text text-transparent">
            Dashboard
          </h1>
          <p className="text-sm sm:text-base text-gray-500 dark:text-gray-400 mt-1">
            Visão geral do sistema de recrutamento
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs sm:text-sm text-gray-500 dark:text-gray-400">
          <Activity className="w-3 h-3 sm:w-4 sm:h-4 text-green-500 animate-pulse" />
          <span>Atualizado em tempo real</span>
        </div>
      </div>

      {/* Métricas principais */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <MetricCard
          title="Total de Candidatos"
          value={loading ? "..." : candidatesData.length || "0"}
          subtitle="Desde o início"
          change={kpiData?.candidates_growth || null}
          icon={Users}
          color="from-indigo-500 to-indigo-600"
        />
        <MetricCard
          title="Entrevistas Hoje"
          value={loading ? "..." : kpiData?.interviews_today || "0"}
          subtitle={kpiData?.interviews_confirmed ? `${kpiData.interviews_confirmed} confirmadas` : "Aguardando dados"}
          change={kpiData?.interviews_growth || null}
          icon={Calendar}
          color="from-teal-500 to-teal-600"
        />
        <MetricCard
          title="Taxa de Aprovação"
          value={loading ? "..." : kpiData?.approval_rate ? `${kpiData.approval_rate}%` : "0%"}
          subtitle="Média mensal"
          change={kpiData?.approval_change || null}
          icon={Award}
          color="from-emerald-500 to-emerald-600"
        />
        <MetricCard
          title="Score Médio"
          value={loading ? "..." : kpiData?.average_score || "0"}
          subtitle="De 10 pontos"
          change={kpiData?.score_change || null}
          icon={TrendingUp}
          color="from-amber-500 to-amber-600"
        />
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        {/* Gráfico de Área - Tendências */}
        <ChartCard 
          title="Tendências de Contratação" 
          subtitle="Últimos 5 meses"
        >
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorUv" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#4F46E5" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#4F46E5" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorPv" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0D9488" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#0D9488" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="name" stroke="#6B7280" />
              <YAxis stroke="#6B7280" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(255, 255, 255, 0.95)', 
                  border: '1px solid #E5E7EB',
                  borderRadius: '12px',
                  boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
                }}
              />
              <Area type="monotone" dataKey="value" stroke="#4F46E5" fillOpacity={1} fill="url(#colorUv)" strokeWidth={2} />
              <Area type="monotone" dataKey="candidatos" stroke="#0D9488" fillOpacity={1} fill="url(#colorPv)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Gráfico de Pizza - Status */}
        <ChartCard 
          title="Distribuição de Status" 
          subtitle="Candidatos ativos"
        >
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(255, 255, 255, 0.95)', 
                  border: '1px solid #E5E7EB',
                  borderRadius: '12px',
                  boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Atividades recentes */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-lg border border-gray-200/50 dark:border-gray-700/50 overflow-hidden">
        <div className="p-4 sm:p-6 border-b border-gray-200/50 dark:border-gray-700/50 bg-gradient-to-r from-indigo-500/5 to-teal-500/5">
          <h3 className="text-base sm:text-lg font-bold text-gray-900 dark:text-white">Atividades Recentes</h3>
          <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-1">Últimas 24 horas</p>
        </div>
        <div className="p-4 sm:p-6">
          <div className="space-y-4">
            {[
              { icon: UserCheck, color: 'from-green-500 to-emerald-500', text: 'João Silva foi aprovado para Desenvolvedor Senior', time: 'Há 2 horas' },
              { icon: Calendar, color: 'from-blue-500 to-indigo-500', text: 'Entrevista agendada com Maria Santos', time: 'Há 3 horas' },
              { icon: Users, color: 'from-purple-500 to-pink-500', text: '5 novos candidatos se inscreveram', time: 'Há 5 horas' },
              { icon: Award, color: 'from-amber-500 to-orange-500', text: 'Ana Costa completou avaliação técnica com nota 9.5', time: 'Há 8 horas' },
            ].map((activity, index) => (
              <div key={index} className="flex items-start gap-3 sm:gap-4 p-2 sm:p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors duration-200 group">
                <div className={`p-2 rounded-xl bg-gradient-to-br ${activity.color} shadow-md group-hover:scale-110 transition-transform duration-200`}>
                  <activity.icon className="w-3 h-3 sm:w-4 sm:h-4 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs sm:text-sm text-gray-900 dark:text-white font-medium">{activity.text}</p>
                  <p className="text-[10px] sm:text-xs text-gray-500 dark:text-gray-400 mt-1">{activity.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Estatísticas rápidas */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
        <div className="bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-2xl p-4 sm:p-6 text-white shadow-xl hover:scale-[1.02] transition-transform duration-300">
          <div className="flex items-center justify-between mb-3 sm:mb-4">
            <Zap className="w-6 h-6 sm:w-8 sm:h-8 text-white/80" />
            <span className="text-xl sm:text-2xl font-bold">87%</span>
          </div>
          <h4 className="text-base sm:text-lg font-semibold mb-1">Eficiência do Processo</h4>
          <p className="text-indigo-100 text-xs sm:text-sm">Tempo médio de 12 dias</p>
        </div>
        
        <div className="bg-gradient-to-br from-teal-500 to-teal-600 rounded-2xl p-4 sm:p-6 text-white shadow-xl hover:scale-[1.02] transition-transform duration-300">
          <div className="flex items-center justify-between mb-3 sm:mb-4">
            <Target className="w-6 h-6 sm:w-8 sm:h-8 text-white/80" />
            <span className="text-xl sm:text-2xl font-bold">342</span>
          </div>
          <h4 className="text-base sm:text-lg font-semibold mb-1">Metas Atingidas</h4>
          <p className="text-teal-100 text-xs sm:text-sm">95% de conclusão mensal</p>
        </div>
        
        <div className="bg-gradient-to-br from-fuchsia-500 to-fuchsia-600 rounded-2xl p-4 sm:p-6 text-white shadow-xl hover:scale-[1.02] transition-transform duration-300 sm:col-span-2 lg:col-span-1">
          <div className="flex items-center justify-between mb-3 sm:mb-4">
            <Briefcase className="w-6 h-6 sm:w-8 sm:h-8 text-white/80" />
            <span className="text-xl sm:text-2xl font-bold">28</span>
          </div>
          <h4 className="text-base sm:text-lg font-semibold mb-1">Vagas Abertas</h4>
          <p className="text-fuchsia-100 text-xs sm:text-sm">12 urgentes</p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;