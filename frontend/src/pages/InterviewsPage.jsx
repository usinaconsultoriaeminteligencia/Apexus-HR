import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Mic2, Clock, CheckCircle2, AlertCircle, Loader2, Star } from 'lucide-react'
import { interviews as interviewsApi } from '../api/client'

const STATUS_COLORS = {
  agendada: 'bg-blue-100 text-blue-700',
  em_andamento: 'bg-yellow-100 text-yellow-700',
  concluida: 'bg-green-100 text-green-700',
  finalizada: 'bg-green-100 text-green-700',
  cancelada: 'bg-red-100 text-red-700',
}

const RECOMMENDATION_COLORS = {
  CONTRATAR: 'text-green-600 bg-green-50',
  CONSIDERAR: 'text-yellow-600 bg-yellow-50',
  REJEITAR: 'text-red-600 bg-red-50',
}

export default function InterviewsPage() {
  const navigate = useNavigate()
  const [interviews, setInterviews] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState(null)
  const [assessments, setAssessments] = useState([])
  const [loadingAssessments, setLoadingAssessments] = useState(false)

  useEffect(() => {
    loadInterviews()
  }, [])

  const loadInterviews = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await interviewsApi.list()
      const list = Array.isArray(res) ? res : (res.interviews || [])
      setInterviews(list)
    } catch (e) {
      setError(e.message || 'Erro ao carregar entrevistas')
    } finally {
      setLoading(false)
    }
  }

  const loadAssessments = async (id) => {
    setLoadingAssessments(true)
    setAssessments([])
    try {
      const res = await interviewsApi.assessments(id)
      setAssessments(res.assessments || [])
    } catch {}
    finally { setLoadingAssessments(false) }
  }

  const handleSelect = (iv) => {
    if (selected?.id === iv.id) {
      setSelected(null)
      return
    }
    setSelected(iv)
    loadAssessments(iv.id)
  }

  const ScoreRing = ({ score }) => {
    if (score == null) return <span className="text-xs text-gray-400">—</span>
    const s = Math.min(100, Math.max(0, score))
    const color = s >= 70 ? '#22c55e' : s >= 40 ? '#eab308' : '#ef4444'
    const r = 18; const circ = 2 * Math.PI * r
    const dash = (s / 100) * circ
    return (
      <div className="relative w-12 h-12 flex items-center justify-center">
        <svg width="48" height="48" className="-rotate-90">
          <circle cx="24" cy="24" r={r} fill="none" stroke="#f3f4f6" strokeWidth="4" />
          <circle cx="24" cy="24" r={r} fill="none" stroke={color} strokeWidth="4"
            strokeDasharray={`${dash} ${circ}`} strokeLinecap="round" />
        </svg>
        <span className="absolute text-xs font-bold text-gray-700">{s.toFixed(0)}</span>
      </div>
    )
  }

  return (
    <div className="space-y-5 animate-fade-in">
      <div>
        <h1 className="text-xl font-bold text-gray-900">Entrevistas</h1>
        <p className="text-sm text-gray-400">
          {loading ? '—' : `${interviews.length} entrevistas no sistema`}
        </p>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">
          <AlertCircle size={15} /> {error}
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-5">
        {/* List */}
        <div className="xl:col-span-2 bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100">
            <h3 className="font-semibold text-sm text-gray-800">Todas as Entrevistas</h3>
          </div>
          <div className="divide-y divide-gray-50 max-h-[600px] overflow-y-auto">
            {loading ? (
              Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="p-4 flex gap-3">
                  <div className="w-12 h-12 skeleton rounded-full flex-shrink-0" />
                  <div className="flex-1 space-y-2">
                    <div className="h-3.5 skeleton rounded w-2/3" />
                    <div className="h-3 skeleton rounded w-1/2" />
                  </div>
                </div>
              ))
            ) : interviews.length === 0 ? (
              <div className="py-12 text-center">
                <Mic2 size={36} className="mx-auto text-gray-300 mb-2" />
                <p className="text-sm text-gray-400">Nenhuma entrevista registrada</p>
              </div>
            ) : (
              interviews.map((iv, i) => (
                <div
                  key={iv.id || i}
                  className={`p-4 flex items-center gap-3 cursor-pointer transition-colors ${
                    selected?.id === iv.id ? 'bg-primary-50 border-l-2 border-primary-600' : 'hover:bg-gray-50'
                  }`}
                  onClick={() => handleSelect(iv)}
                >
                  <ScoreRing score={iv.overall_score} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-800 truncate">
                      {iv.position || 'Entrevista por áudio'}
                    </p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      {iv.created_at ? new Date(iv.created_at).toLocaleDateString('pt-BR') : '—'}
                    </p>
                    <span className={`badge mt-1 ${STATUS_COLORS[iv.status] || 'bg-gray-100 text-gray-500'}`}>
                      {iv.status || '—'}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Detail */}
        <div className="xl:col-span-3">
          {!selected ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col items-center justify-center py-20 text-center">
              <Mic2 size={40} className="text-gray-200 mb-3" />
              <p className="text-gray-400 text-sm">Selecione uma entrevista para ver os detalhes</p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Header card */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="font-bold text-gray-900 text-base">
                      {selected.position || 'Entrevista por áudio'}
                    </h2>
                    <p className="text-sm text-gray-400 mt-0.5">
                      ID #{selected.id} · {selected.created_at
                        ? new Date(selected.created_at).toLocaleString('pt-BR')
                        : '—'}
                    </p>
                  </div>
                  <ScoreRing score={selected.overall_score} />
                </div>

                <div className="mt-4 flex flex-wrap gap-3">
                  <span className={`badge ${STATUS_COLORS[selected.status] || 'bg-gray-100 text-gray-500'}`}>
                    {selected.status || '—'}
                  </span>
                  {selected.recommendation && (
                    <span className={`badge ${RECOMMENDATION_COLORS[selected.recommendation] || 'bg-gray-100 text-gray-600'}`}>
                      <Star size={11} className="mr-0.5" />
                      {selected.recommendation}
                    </span>
                  )}
                </div>

                {selected.insights?.summary && (
                  <div className="mt-4 pt-4 border-t border-gray-100">
                    <p className="text-xs text-gray-400 mb-1">Resumo da análise</p>
                    <p className="text-sm text-gray-700">{selected.insights.summary}</p>
                  </div>
                )}
              </div>

              {/* Assessments */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="px-5 py-4 border-b border-gray-100">
                  <h3 className="font-semibold text-sm text-gray-800">
                    Assessments por Pergunta
                  </h3>
                </div>
                {loadingAssessments ? (
                  <div className="p-5 space-y-3">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="h-14 skeleton rounded-lg" />
                    ))}
                  </div>
                ) : assessments.length === 0 ? (
                  <p className="p-5 text-sm text-gray-400 text-center">
                    Nenhum assessment disponível para esta entrevista
                  </p>
                ) : (
                  <div className="divide-y divide-gray-50">
                    {assessments.map((a, i) => (
                      <div key={a.id || i} className="px-5 py-3.5">
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1">
                            <p className="text-xs text-gray-400 mb-0.5">
                              Pergunta {a.question_index + 1} · {a.dimension || a.rubric_id || '—'}
                            </p>
                            {a.question_text && (
                              <p className="text-sm text-gray-700 font-medium">{a.question_text}</p>
                            )}
                            {a.answer_excerpt && (
                              <p className="text-xs text-gray-500 mt-1 italic">"{a.answer_excerpt}"</p>
                            )}
                          </div>
                          <div className="text-right flex-shrink-0">
                            <p className={`text-lg font-bold ${
                              (a.score || 0) >= 3.5 ? 'text-green-600' :
                              (a.score || 0) >= 2.5 ? 'text-yellow-600' : 'text-red-500'
                            }`}>
                              {a.score != null ? `${a.score}/5` : '—'}
                            </p>
                            <p className="text-xs text-gray-400">
                              {a.confidence != null ? `${(a.confidence * 100).toFixed(0)}% conf.` : ''}
                            </p>
                          </div>
                        </div>
                        <div className="flex gap-2 mt-2">
                          {a.model_name && (
                            <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">
                              {a.model_name}
                            </span>
                          )}
                          {a.human_review_status && a.human_review_status !== 'approved' && (
                            <span className="text-xs text-yellow-600 bg-yellow-50 px-2 py-0.5 rounded">
                              {a.human_review_status}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
