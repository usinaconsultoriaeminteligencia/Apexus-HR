import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft, Mail, Phone, MapPin, Briefcase, Star,
  Edit2, Trash2, Loader2, AlertCircle, CheckCircle2, Clock,
  User, Building2, Linkedin, Mic2,
} from 'lucide-react'
import { candidates as candidatesApi, interviews as interviewsApi } from '../api/client'

const STATUS_COLORS = {
  novo: 'bg-blue-100 text-blue-700 border-blue-200',
  em_processo: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  aprovado: 'bg-green-100 text-green-700 border-green-200',
  rejeitado: 'bg-red-100 text-red-700 border-red-200',
  contratado: 'bg-purple-100 text-purple-700 border-purple-200',
}

function InfoRow({ icon: Icon, label, value }) {
  if (!value) return null
  return (
    <div className="flex items-start gap-3 py-2.5 border-b border-gray-50 last:border-0">
      <Icon size={15} className="text-gray-400 mt-0.5 flex-shrink-0" />
      <div>
        <p className="text-xs text-gray-400">{label}</p>
        <p className="text-sm text-gray-800 font-medium">{value}</p>
      </div>
    </div>
  )
}

export default function CandidateDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [candidate, setCandidate] = useState(null)
  const [interviews, setInterviews] = useState([])
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (id === 'new') { setLoading(false); return }
    loadCandidate()
  }, [id])

  const loadCandidate = async () => {
    setLoading(true)
    try {
      const res = await candidatesApi.get(id)
      const c = res.candidate || res
      setCandidate(c)

      // Tentar carregar entrevistas
      try {
        const iRes = await interviewsApi.list()
        const all = Array.isArray(iRes) ? iRes : (iRes.interviews || [])
        setInterviews(all.filter((i) => i.candidate_id === parseInt(id)))
      } catch {}
    } catch (e) {
      setError(e.message || 'Candidato não encontrado')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm(`Excluir ${candidate?.name}? Esta ação não pode ser desfeita.`)) return
    setDeleting(true)
    try {
      await candidatesApi.delete(id)
      navigate('/candidates')
    } catch (e) {
      alert(e.message)
    } finally {
      setDeleting(false)
    }
  }

  const skills = (() => {
    if (!candidate?.skills) return []
    if (Array.isArray(candidate.skills)) return candidate.skills
    try { return JSON.parse(candidate.skills) } catch { return [candidate.skills] }
  })()

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <Loader2 size={24} className="animate-spin text-primary-500" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center gap-3 py-16 text-center">
        <AlertCircle size={36} className="text-red-400" />
        <p className="text-gray-600">{error}</p>
        <button className="btn-secondary" onClick={() => navigate('/candidates')}>
          <ArrowLeft size={15} /> Voltar
        </button>
      </div>
    )
  }

  const score = candidate?.overall_score
  const scoreColor = score >= 70 ? 'text-green-600' : score >= 40 ? 'text-yellow-600' : 'text-red-500'

  return (
    <div className="space-y-5 animate-fade-in max-w-5xl">
      {/* Back + actions */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/candidates')}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 transition-colors"
        >
          <ArrowLeft size={16} /> Candidatos
        </button>
        <div className="flex gap-2">
          <button className="btn-secondary text-xs py-1.5">
            <Edit2 size={13} /> Editar
          </button>
          <button
            className="btn-danger text-xs py-1.5"
            onClick={handleDelete}
            disabled={deleting}
          >
            {deleting ? <Loader2 size={13} className="animate-spin" /> : <Trash2 size={13} />}
            Excluir
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Left: profile */}
        <div className="space-y-4">
          {/* Avatar + name */}
          <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 text-center">
            <div className="w-16 h-16 rounded-full bg-primary-100 text-primary-700 text-2xl font-bold flex items-center justify-center mx-auto mb-3">
              {(candidate?.name || '?')[0].toUpperCase()}
            </div>
            <h2 className="font-bold text-gray-900 text-lg leading-tight">{candidate?.name}</h2>
            <p className="text-sm text-gray-500 mt-0.5">{candidate?.current_position || '—'}</p>

            <div className="mt-3 flex justify-center">
              <span className={`badge border ${STATUS_COLORS[candidate?.status] || 'bg-gray-100 text-gray-600 border-gray-200'}`}>
                {candidate?.status || '—'}
              </span>
            </div>

            {score != null && (
              <div className="mt-4 pt-4 border-t border-gray-100">
                <p className="text-xs text-gray-400 mb-1">Score de IA</p>
                <p className={`text-3xl font-bold ${scoreColor}`}>{score.toFixed(0)}</p>
                <div className="w-full bg-gray-100 rounded-full h-2 mt-2">
                  <div
                    className={`h-2 rounded-full ${score >= 70 ? 'bg-green-500' : score >= 40 ? 'bg-yellow-500' : 'bg-red-400'}`}
                    style={{ width: `${Math.min(100, score)}%` }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Contact info */}
          <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Contato</h3>
            <InfoRow icon={Mail} label="E-mail" value={candidate?.email} />
            <InfoRow icon={Phone} label="Telefone" value={candidate?.phone} />
            <InfoRow icon={MapPin} label="Localização" value={candidate?.location} />
            <InfoRow icon={Building2} label="Empresa Atual" value={candidate?.current_company} />
            {candidate?.linkedin_url && (
              <div className="flex items-center gap-3 py-2.5">
                <Linkedin size={15} className="text-gray-400 flex-shrink-0" />
                <a
                  href={candidate.linkedin_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm text-primary-600 hover:underline truncate"
                >
                  LinkedIn
                </a>
              </div>
            )}
          </div>
        </div>

        {/* Right: details */}
        <div className="lg:col-span-2 space-y-4">
          {/* Skills */}
          {skills.length > 0 && (
            <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Skills</h3>
              <div className="flex flex-wrap gap-2">
                {skills.map((s, i) => (
                  <span key={i} className="px-2.5 py-1 bg-primary-50 text-primary-700 text-xs font-medium rounded-lg">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* AI Analysis */}
          {candidate?.ai_analysis && (
            <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3 flex items-center gap-1.5">
                <Star size={13} className="text-yellow-500" /> Análise de IA
              </h3>
              <p className="text-sm text-gray-700 leading-relaxed">{candidate.ai_analysis}</p>
            </div>
          )}

          {/* Notes */}
          {candidate?.interview_notes && (
            <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
                Notas de Entrevista
              </h3>
              <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                {candidate.interview_notes}
              </p>
            </div>
          )}

          {/* Interviews */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-100">
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide flex items-center gap-1.5">
                <Mic2 size={13} /> Entrevistas ({interviews.length})
              </h3>
            </div>
            {interviews.length === 0 ? (
              <p className="px-5 py-6 text-sm text-gray-400 text-center">
                Nenhuma entrevista registrada
              </p>
            ) : (
              <div className="divide-y divide-gray-50">
                {interviews.map((iv, i) => (
                  <div key={iv.id || i} className="px-5 py-3.5 flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-800">{iv.position || 'Entrevista por áudio'}</p>
                      <p className="text-xs text-gray-400">
                        {iv.created_at ? new Date(iv.created_at).toLocaleDateString('pt-BR') : '—'}
                        {iv.overall_score != null && ` · Score: ${iv.overall_score.toFixed(0)}`}
                      </p>
                    </div>
                    <span className={`badge ${
                      iv.status === 'concluida' || iv.status === 'finalizada'
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-500'
                    }`}>
                      {iv.status || 'agendada'}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
