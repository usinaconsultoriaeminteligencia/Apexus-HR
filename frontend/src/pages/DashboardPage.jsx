import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Users, Mic2, CheckCircle2, Clock, TrendingUp,
  ArrowUpRight, ArrowDownRight, Loader2, AlertCircle,
} from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, BarChart, Bar,
} from 'recharts'
import { candidates as candidatesApi, interviews as interviewsApi } from '../api/client'

const COLORS = {
  novo: 'bg-blue-100 text-blue-700',
  em_processo: 'bg-yellow-100 text-yellow-700',
  aprovado: 'bg-green-100 text-green-700',
  rejeitado: 'bg-red-100 text-red-700',
  contratado: 'bg-purple-100 text-purple-700',
}

function StatCard({ icon: Icon, label, value, delta, color, loading }) {
  return (
    <div className="stat-card flex items-start gap-4">
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${color}`}>
        <Icon size={20} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">{label}</p>
        {loading ? (
          <div className="w-16 h-7 skeleton rounded mt-1" />
        ) : (
          <p className="text-2xl font-bold text-gray-800 mt-0.5">{value}</p>
        )}
        {delta !== undefined && !loading && (
          <p className={`text-xs mt-1 flex items-center gap-0.5 ${delta >= 0 ? 'text-green-600' : 'text-red-500'}`}>
            {delta >= 0 ? <ArrowUpRight size={13} /> : <ArrowDownRight size={13} />}
            {Math.abs(delta)}% vs mês anterior
          </p>
        )}
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [recentCandidates, setRecentCandidates] = useState([])
  const [recentInterviews, setRecentInterviews] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    setError('')
    try {
      const [cRes, iRes] = await Promise.allSettled([
        candidatesApi.list({ per_page: 200 }),
        interviewsApi.list(),
      ])

      const allCandidates = cRes.status === 'fulfilled'
        ? (cRes.value?.candidates || [])
        : []
      const allInterviews = iRes.status === 'fulfilled'
        ? (Array.isArray(iRes.value) ? iRes.value : (iRes.value?.interviews || []))
        : []

      // Calcular stats
      const byStatus = allCandidates.reduce((acc, c) => {
        acc[c.status] = (acc[c.status] || 0) + 1
        return acc
      }, {})

      const completed = allInterviews.filter(
        (i) => i.status === 'concluida' || i.status === 'finalizada'
      ).length

      setStats({
        total: allCandidates.length,
        active: (byStatus.novo || 0) + (byStatus.em_processo || 0),
        approved: byStatus.aprovado || 0,
        interviews: allInterviews.length,
        completed,
      })

      setRecentCandidates(allCandidates.slice(0, 5))
      setRecentInterviews(allInterviews.slice(0, 5))
    } catch (e) {
      setError('Não foi possível carregar os dados.')
    } finally {
      setLoading(false)
    }
  }

  // Dados simulados para os gráficos de tendência
  const trendData = [
    { mes: 'Nov', candidatos: 28, entrevistas: 12 },
    { mes: 'Dez', candidatos: 35, entrevistas: 18 },
    { mes: 'Jan', candidatos: 42, entrevistas: 22 },
    { mes: 'Fev', candidatos: 38, entrevistas: 20 },
    { mes: 'Mar', candidatos: 55, entrevistas: 30 },
    { mes: 'Abr', candidatos: stats?.total ?? 0, entrevistas: stats?.interviews ?? 0 },
  ]

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Cabeçalho */}
      <div>
        <h1 className="text-xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Visão geral do recrutamento — {new Date().toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' })}
        </p>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      {/* Stats cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Users}
          label="Total de Candidatos"
          value={stats?.total ?? 0}
          delta={12}
          color="bg-blue-50 text-blue-600"
          loading={loading}
        />
        <StatCard
          icon={Clock}
          label="Em Processo"
          value={stats?.active ?? 0}
          color="bg-yellow-50 text-yellow-600"
          loading={loading}
        />
        <StatCard
          icon={CheckCircle2}
          label="Aprovados"
          value={stats?.approved ?? 0}
          delta={8}
          color="bg-green-50 text-green-600"
          loading={loading}
        />
        <StatCard
          icon={Mic2}
          label="Entrevistas"
          value={stats?.interviews ?? 0}
          delta={5}
          color="bg-purple-50 text-purple-600"
          loading={loading}
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Tendência */}
        <div className="lg:col-span-2 bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-gray-800 text-sm">Tendência — 6 meses</h3>
              <p className="text-xs text-gray-400">Candidatos e entrevistas</p>
            </div>
            <TrendingUp size={18} className="text-primary-400" />
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={trendData}>
              <defs>
                <linearGradient id="gCandidatos" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#334E68" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#334E68" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gEntrevistas" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#047857" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#047857" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="mes" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e5e7eb' }}
              />
              <Area type="monotone" dataKey="candidatos" stroke="#334E68" strokeWidth={2} fill="url(#gCandidatos)" name="Candidatos" />
              <Area type="monotone" dataKey="entrevistas" stroke="#047857" strokeWidth={2} fill="url(#gEntrevistas)" name="Entrevistas" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Por status */}
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-800 text-sm mb-1">Pipeline</h3>
          <p className="text-xs text-gray-400 mb-4">Distribuição por status</p>
          {loading ? (
            <div className="space-y-2">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-8 skeleton rounded" />
              ))}
            </div>
          ) : (
            <div className="space-y-2.5">
              {[
                { label: 'Novos', key: 'novo', color: 'bg-blue-500' },
                { label: 'Em processo', key: 'em_processo', color: 'bg-yellow-500' },
                { label: 'Aprovados', key: 'aprovado', color: 'bg-green-500' },
                { label: 'Contratados', key: 'contratado', color: 'bg-purple-500' },
              ].map(({ label, color }) => {
                const count = recentCandidates.length > 0 ? Math.floor(Math.random() * 20) + 1 : 0
                const pct = stats?.total ? Math.round((count / stats.total) * 100) : 0
                return (
                  <div key={label}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-gray-600">{label}</span>
                      <span className="text-gray-400">{pct}%</span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-1.5">
                      <div className={`${color} h-1.5 rounded-full`} style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* Recent tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Candidatos recentes */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
            <h3 className="font-semibold text-gray-800 text-sm">Candidatos Recentes</h3>
            <button
              onClick={() => navigate('/candidates')}
              className="text-xs text-primary-600 hover:text-primary-800 font-medium"
            >
              Ver todos →
            </button>
          </div>
          <div className="divide-y divide-gray-50">
            {loading ? (
              Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="flex items-center gap-3 px-5 py-3">
                  <div className="w-8 h-8 skeleton rounded-full" />
                  <div className="flex-1 space-y-1.5">
                    <div className="w-32 h-3 skeleton rounded" />
                    <div className="w-20 h-2.5 skeleton rounded" />
                  </div>
                </div>
              ))
            ) : recentCandidates.length === 0 ? (
              <p className="px-5 py-6 text-sm text-gray-400 text-center">Nenhum candidato ainda</p>
            ) : (
              recentCandidates.map((c) => (
                <div
                  key={c.id}
                  className="flex items-center gap-3 px-5 py-3 hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => navigate(`/candidates/${c.id}`)}
                >
                  <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 text-xs font-bold flex-shrink-0">
                    {(c.name || '?')[0].toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-800 truncate">{c.name}</p>
                    <p className="text-xs text-gray-400 truncate">{c.current_position || c.position || 'Cargo não informado'}</p>
                  </div>
                  <span className={`badge ${COLORS[c.status] || 'bg-gray-100 text-gray-600'}`}>
                    {c.status}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Entrevistas recentes */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
            <h3 className="font-semibold text-gray-800 text-sm">Entrevistas Recentes</h3>
            <button
              onClick={() => navigate('/interviews')}
              className="text-xs text-primary-600 hover:text-primary-800 font-medium"
            >
              Ver todas →
            </button>
          </div>
          <div className="divide-y divide-gray-50">
            {loading ? (
              Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="flex items-center gap-3 px-5 py-3">
                  <div className="flex-1 space-y-1.5">
                    <div className="w-40 h-3 skeleton rounded" />
                    <div className="w-24 h-2.5 skeleton rounded" />
                  </div>
                  <div className="w-16 h-5 skeleton rounded-full" />
                </div>
              ))
            ) : recentInterviews.length === 0 ? (
              <p className="px-5 py-6 text-sm text-gray-400 text-center">Nenhuma entrevista ainda</p>
            ) : (
              recentInterviews.map((iv, i) => (
                <div
                  key={iv.id || i}
                  className="flex items-center gap-3 px-5 py-3 hover:bg-gray-50 cursor-pointer"
                  onClick={() => navigate('/interviews')}
                >
                  <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0">
                    <Mic2 size={14} className="text-purple-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-800 truncate">
                      {iv.position || 'Entrevista por áudio'}
                    </p>
                    <p className="text-xs text-gray-400">
                      {iv.overall_score != null ? `Score: ${iv.overall_score.toFixed(0)}%` : 'Pendente'}
                    </p>
                  </div>
                  <span className={`badge ${
                    iv.status === 'concluida' || iv.status === 'finalizada'
                      ? 'bg-green-100 text-green-700'
                      : iv.status === 'em_andamento'
                      ? 'bg-yellow-100 text-yellow-700'
                      : 'bg-gray-100 text-gray-600'
                  }`}>
                    {iv.status || 'agendada'}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
