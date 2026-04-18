import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Search, Plus, Filter, ChevronLeft, ChevronRight,
  Loader2, AlertCircle, UserCircle2, SlidersHorizontal,
} from 'lucide-react'
import { candidates as candidatesApi } from '../api/client'

const STATUS_OPTIONS = ['', 'novo', 'em_processo', 'aprovado', 'rejeitado', 'contratado']
const STATUS_LABELS = {
  novo: 'Novo', em_processo: 'Em processo', aprovado: 'Aprovado',
  rejeitado: 'Rejeitado', contratado: 'Contratado',
}
const STATUS_COLORS = {
  novo: 'bg-blue-100 text-blue-700',
  em_processo: 'bg-yellow-100 text-yellow-700',
  aprovado: 'bg-green-100 text-green-700',
  rejeitado: 'bg-red-100 text-red-700',
  contratado: 'bg-purple-100 text-purple-700',
}

export default function CandidatesPage() {
  const navigate = useNavigate()
  const [candidates, setCandidates] = useState([])
  const [pagination, setPagination] = useState({ page: 1, per_page: 20, total: 0, pages: 1 })
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showFilters, setShowFilters] = useState(false)

  const load = useCallback(async (page = 1) => {
    setLoading(true)
    setError('')
    try {
      const params = { page, per_page: 20 }
      if (search.trim()) params.search = search.trim()
      if (status) params.status = status

      const res = await candidatesApi.list(params)
      setCandidates(res.candidates || [])
      setPagination(res.pagination || { page, per_page: 20, total: res.candidates?.length || 0, pages: 1 })
    } catch (e) {
      setError(e.message || 'Erro ao carregar candidatos')
    } finally {
      setLoading(false)
    }
  }, [search, status])

  useEffect(() => {
    const t = setTimeout(() => load(1), search ? 350 : 0)
    return () => clearTimeout(t)
  }, [search, status])

  const ScoreBar = ({ score }) => {
    if (score == null) return <span className="text-xs text-gray-400">—</span>
    const pct = Math.min(100, Math.max(0, score))
    const color = pct >= 70 ? 'bg-green-500' : pct >= 40 ? 'bg-yellow-500' : 'bg-red-400'
    return (
      <div className="flex items-center gap-2">
        <div className="w-16 bg-gray-100 rounded-full h-1.5">
          <div className={`${color} h-1.5 rounded-full`} style={{ width: `${pct}%` }} />
        </div>
        <span className="text-xs text-gray-600 font-medium">{pct.toFixed(0)}</span>
      </div>
    )
  }

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Candidatos</h1>
          <p className="text-sm text-gray-400">
            {loading ? '—' : `${pagination.total} candidatos encontrados`}
          </p>
        </div>
        <button
          onClick={() => navigate('/candidates/new')}
          className="btn-primary"
        >
          <Plus size={16} />
          Novo Candidato
        </button>
      </div>

      {/* Search + Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              className="input-field pl-9"
              placeholder="Buscar por nome, cargo, empresa..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`btn-secondary gap-2 ${showFilters ? 'bg-gray-100 border-gray-300' : ''}`}
          >
            <SlidersHorizontal size={15} />
            <span className="hidden sm:inline">Filtros</span>
          </button>
        </div>

        {showFilters && (
          <div className="mt-3 pt-3 border-t border-gray-100 flex flex-wrap gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Status</label>
              <select
                className="input-field w-44 text-xs py-1.5"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                <option value="">Todos os status</option>
                {STATUS_OPTIONS.filter(Boolean).map((s) => (
                  <option key={s} value={s}>{STATUS_LABELS[s]}</option>
                ))}
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {error && (
          <div className="flex items-center gap-2 p-4 m-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            <AlertCircle size={15} />
            {error}
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide border-b border-gray-100">
                <th className="px-5 py-3 text-left font-medium">Candidato</th>
                <th className="px-4 py-3 text-left font-medium hidden md:table-cell">Cargo Atual</th>
                <th className="px-4 py-3 text-left font-medium hidden lg:table-cell">Score</th>
                <th className="px-4 py-3 text-left font-medium">Status</th>
                <th className="px-4 py-3 text-left font-medium hidden xl:table-cell">Cadastrado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {loading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i}>
                    {[1, 2, 3, 4, 5].map((j) => (
                      <td key={j} className="px-5 py-3.5">
                        <div className="h-4 skeleton rounded w-3/4" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : candidates.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-5 py-12 text-center">
                    <UserCircle2 size={40} className="mx-auto text-gray-300 mb-2" />
                    <p className="text-gray-400 text-sm">Nenhum candidato encontrado</p>
                  </td>
                </tr>
              ) : (
                candidates.map((c) => (
                  <tr
                    key={c.id}
                    className="table-row-hover"
                    onClick={() => navigate(`/candidates/${c.id}`)}
                  >
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-xs font-bold flex-shrink-0">
                          {(c.name || '?')[0].toUpperCase()}
                        </div>
                        <div className="min-w-0">
                          <p className="font-medium text-gray-800 truncate">{c.name}</p>
                          <p className="text-xs text-gray-400 truncate hidden sm:block">
                            {c.email || '—'}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3.5 hidden md:table-cell">
                      <p className="text-gray-700 truncate max-w-[160px]">
                        {c.current_position || c.position || '—'}
                      </p>
                      {c.current_company && (
                        <p className="text-xs text-gray-400 truncate">{c.current_company}</p>
                      )}
                    </td>
                    <td className="px-4 py-3.5 hidden lg:table-cell">
                      <ScoreBar score={c.overall_score} />
                    </td>
                    <td className="px-4 py-3.5">
                      <span className={`badge ${STATUS_COLORS[c.status] || 'bg-gray-100 text-gray-600'}`}>
                        {STATUS_LABELS[c.status] || c.status || '—'}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 hidden xl:table-cell text-gray-400 text-xs">
                      {c.created_at ? new Date(c.created_at).toLocaleDateString('pt-BR') : '—'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {pagination.pages > 1 && (
          <div className="flex items-center justify-between px-5 py-3 border-t border-gray-100 bg-gray-50">
            <p className="text-xs text-gray-400">
              Página {pagination.page} de {pagination.pages} ({pagination.total} total)
            </p>
            <div className="flex gap-1">
              <button
                disabled={pagination.page <= 1 || loading}
                onClick={() => load(pagination.page - 1)}
                className="w-8 h-8 flex items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-600 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed text-sm"
              >
                <ChevronLeft size={15} />
              </button>
              <button
                disabled={pagination.page >= pagination.pages || loading}
                onClick={() => load(pagination.page + 1)}
                className="w-8 h-8 flex items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-600 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed text-sm"
              >
                <ChevronRight size={15} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
