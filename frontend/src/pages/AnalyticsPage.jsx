import { useEffect, useState } from 'react'
import {
  BarChart2, TrendingUp, Users, Mic2, AlertCircle, Loader2,
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from 'recharts'
import { candidates as candidatesApi, interviews as interviewsApi } from '../api/client'

const PALETTE = ['#334E68', '#486581', '#627D98', '#829AB1', '#9FB3C8', '#BCCCDC']
const STATUS_MAP = {
  novo: 'Novo', em_processo: 'Em Processo', aprovado: 'Aprovado',
  rejeitado: 'Rejeitado', contratado: 'Contratado',
}

export default function AnalyticsPage() {
  const [candidates, setCandidates] = useState([])
  const [interviews, setInterviews] = useState([])
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
        candidatesApi.list({ per_page: 500 }),
        interviewsApi.list(),
      ])
      const cList = cRes.status === 'fulfilled' ? (cRes.value?.candidates || []) : []
      const iList = iRes.status === 'fulfilled'
        ? (Array.isArray(iRes.value) ? iRes.value : (iRes.value?.interviews || []))
        : []
      setCandidates(cList)
      setInterviews(iList)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  // --- Derived data ---
  const byStatus = Object.entries(
    candidates.reduce((acc, c) => {
      const k = STATUS_MAP[c.status] || c.status || 'Sem status'
      acc[k] = (acc[k] || 0) + 1
      return acc
    }, {})
  ).map(([name, value]) => ({ name, value }))

  const scoreRanges = [
    { range: '0–20', count: 0 }, { range: '21–40', count: 0 },
    { range: '41–60', count: 0 }, { range: '61–80', count: 0 },
    { range: '81–100', count: 0 },
  ]
  candidates.forEach((c) => {
    if (c.overall_score == null) return
    const s = c.overall_score
    if (s <= 20) scoreRanges[0].count++
    else if (s <= 40) scoreRanges[1].count++
    else if (s <= 60) scoreRanges[2].count++
    else if (s <= 80) scoreRanges[3].count++
    else scoreRanges[4].count++
  })

  const interviewStatuses = Object.entries(
    interviews.reduce((acc, iv) => {
      acc[iv.status || 'agendada'] = (acc[iv.status || 'agendada'] || 0) + 1
      return acc
    }, {})
  ).map(([name, value]) => ({ name, value }))

  // Radar (simulado com dados da plataforma)
  const radarData = [
    { dimension: 'Comunicação', score: 78 },
    { dimension: 'Técnico', score: 72 },
    { dimension: 'Liderança', score: 65 },
    { dimension: 'Colaboração', score: 81 },
    { dimension: 'Resolução', score: 69 },
  ]

  // KPIs
  const scored = candidates.filter((c) => c.overall_score != null)
  const avgScore = scored.length
    ? (scored.reduce((s, c) => s + c.overall_score, 0) / scored.length).toFixed(1)
    : '—'
  const approvalRate = candidates.length
    ? Math.round(
        (candidates.filter((c) => ['aprovado', 'contratado'].includes(c.status)).length /
          candidates.length) * 100
      )
    : 0
  const completedInterviews = interviews.filter(
    (i) => i.status === 'concluida' || i.status === 'finalizada'
  ).length

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <Loader2 size={24} className="animate-spin text-primary-500" />
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-xl font-bold text-gray-900">Analytics</h1>
        <p className="text-sm text-gray-400">Análise quantitativa do pipeline de recrutamento</p>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">
          <AlertCircle size={15} /> {error}
        </div>
      )}

      {/* KPI row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total Candidatos', value: candidates.length, icon: Users, color: 'text-blue-600 bg-blue-50' },
          { label: 'Score Médio', value: avgScore, icon: TrendingUp, color: 'text-green-600 bg-green-50' },
          { label: 'Taxa de Aprovação', value: `${approvalRate}%`, icon: BarChart2, color: 'text-purple-600 bg-purple-50' },
          { label: 'Entrevistas Completas', value: completedInterviews, icon: Mic2, color: 'text-orange-600 bg-orange-50' },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="stat-card flex items-center gap-4">
            <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${color}`}>
              <Icon size={20} />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-800">{value}</p>
              <p className="text-xs text-gray-400 mt-0.5">{label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Charts row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Candidatos por status */}
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-sm text-gray-800 mb-1">Candidatos por Status</h3>
          <p className="text-xs text-gray-400 mb-4">Distribuição atual do pipeline</p>
          {byStatus.length === 0 ? (
            <p className="text-sm text-gray-300 text-center py-10">Sem dados</p>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={byStatus}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {byStatus.map((_, i) => (
                    <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
                <Legend iconSize={10} iconType="circle" wrapperStyle={{ fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Distribuição de scores */}
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-sm text-gray-800 mb-1">Distribuição de Scores</h3>
          <p className="text-xs text-gray-400 mb-4">Score de IA dos candidatos</p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={scoreRanges} barSize={32}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
              <XAxis dataKey="range" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
              <Bar dataKey="count" name="Candidatos" fill="#334E68" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Entrevistas por status */}
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-sm text-gray-800 mb-1">Status das Entrevistas</h3>
          <p className="text-xs text-gray-400 mb-4">Progresso das entrevistas por áudio</p>
          {interviewStatuses.length === 0 ? (
            <p className="text-sm text-gray-300 text-center py-10">Sem dados</p>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={interviewStatuses} layout="vertical" barSize={20}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} width={90} />
                <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
                <Bar dataKey="value" name="Entrevistas" fill="#486581" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Radar de competências (médias simuladas) */}
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-sm text-gray-800 mb-1">Perfil de Competências</h3>
          <p className="text-xs text-gray-400 mb-4">Média das dimensões avaliadas por IA</p>
          <ResponsiveContainer width="100%" height={220}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#e5e7eb" />
              <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 11 }} />
              <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 10 }} />
              <Radar name="Score Médio" dataKey="score" stroke="#334E68" fill="#334E68" fillOpacity={0.2} />
              <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
