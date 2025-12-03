import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { searchAuditLogs, getRecentAuditLogs } from '../lib/api'
import { format } from 'date-fns'
import { Search, FileText, Filter, AlertTriangle, Info, CheckCircle } from 'lucide-react'

export default function AuditLogs() {
  const [searchQuery, setSearchQuery] = useState('')
  const [eventTypeFilter, setEventTypeFilter] = useState('')
  const [limit, setLimit] = useState(100)

  const { data: logs, isLoading, refetch } = useQuery({
    queryKey: ['auditLogs', limit],
    queryFn: () => getRecentAuditLogs(limit),
    refetchInterval: 30000,
  })

  const { data: searchResults, isLoading: isSearching } = useQuery({
    queryKey: ['auditSearch', searchQuery, eventTypeFilter],
    queryFn: () =>
      searchAuditLogs({
        query: searchQuery || undefined,
        event_types: eventTypeFilter ? [eventTypeFilter] : undefined,
        limit: 50,
      }),
    enabled: !!(searchQuery || eventTypeFilter),
  })

  const displayLogs = searchQuery || eventTypeFilter ? searchResults?.results : logs

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'error':
      case 'critical':
        return <AlertTriangle className="w-4 h-4 text-red-500" />
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />
      case 'info':
      default:
        return <Info className="w-4 h-4 text-blue-500" />
    }
  }

  const getEventTypeColor = (eventType: string) => {
    if (eventType.includes('success')) return 'bg-green-100 text-green-700'
    if (eventType.includes('failure') || eventType.includes('error'))
      return 'bg-red-100 text-red-700'
    if (eventType.includes('approval')) return 'bg-blue-100 text-blue-700'
    if (eventType.includes('workflow')) return 'bg-purple-100 text-purple-700'
    return 'bg-gray-100 text-gray-700'
  }

  const eventTypes = [
    'provision_request',
    'provision_success',
    'provision_failure',
    'provision_rollback',
    'rule_update',
    'workflow_approval',
    'workflow_rejection',
    'reconciliation_start',
    'config_change',
    'ai_query',
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <FileText className="w-8 h-8 text-gray-400" />
            Logs d'audit
          </h1>
          <p className="text-gray-500 mt-1">
            Tracabilite complete des operations du systeme
          </p>
        </div>
        <button onClick={() => refetch()} className="btn-secondary">
          Rafraichir
        </button>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Recherche semantique..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input pl-10"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-400" />
            <select
              value={eventTypeFilter}
              onChange={(e) => setEventTypeFilter(e.target.value)}
              className="input w-48"
            >
              <option value="">Tous les types</option>
              {eventTypes.map((type) => (
                <option key={type} value={type}>
                  {type.replace(/_/g, ' ')}
                </option>
              ))}
            </select>
          </div>
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="input w-32"
          >
            <option value={50}>50 logs</option>
            <option value={100}>100 logs</option>
            <option value={200}>200 logs</option>
            <option value={500}>500 logs</option>
          </select>
        </div>
      </div>

      {/* Logs table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
          <table className="w-full">
            <thead className="sticky top-0 bg-white">
              <tr className="border-b border-gray-200">
                <th className="text-left py-4 px-4 font-medium text-gray-500">
                  Date
                </th>
                <th className="text-left py-4 px-4 font-medium text-gray-500">
                  Type
                </th>
                <th className="text-left py-4 px-4 font-medium text-gray-500">
                  Action
                </th>
                <th className="text-left py-4 px-4 font-medium text-gray-500">
                  Compte
                </th>
                <th className="text-left py-4 px-4 font-medium text-gray-500">
                  Acteur
                </th>
                <th className="text-left py-4 px-4 font-medium text-gray-500">
                  Cible
                </th>
              </tr>
            </thead>
            <tbody>
              {isLoading || isSearching ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-gray-500">
                    Chargement...
                  </td>
                </tr>
              ) : displayLogs?.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-gray-500">
                    Aucun log trouve
                  </td>
                </tr>
              ) : (
                displayLogs?.map((log: any, index: number) => (
                  <tr
                    key={log.id || index}
                    className="border-b border-gray-100 hover:bg-gray-50"
                  >
                    <td className="py-3 px-4 text-sm text-gray-500">
                      <div className="flex items-center gap-2">
                        {getSeverityIcon(log.severity)}
                        {log.created_at
                          ? format(new Date(log.created_at), 'dd/MM HH:mm:ss')
                          : '-'}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`text-xs px-2 py-1 rounded-full ${getEventTypeColor(
                          log.event_type
                        )}`}
                      >
                        {log.event_type?.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-sm max-w-xs truncate">
                      {log.action}
                    </td>
                    <td className="py-3 px-4 text-sm">
                      {log.account_id && (
                        <code className="bg-gray-100 px-2 py-0.5 rounded text-xs">
                          {log.account_id}
                        </code>
                      )}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-500">
                      {log.actor || '-'}
                    </td>
                    <td className="py-3 px-4 text-sm">
                      {log.target_system && (
                        <span className="text-xs bg-gray-100 px-2 py-0.5 rounded">
                          {log.target_system}
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Semantic search results */}
      {searchQuery && searchResults?.semantic_matches && (
        <div className="card">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-500" />
            Resultats de recherche semantique
          </h3>
          <div className="space-y-2">
            {searchResults.semantic_matches.map((match: any, index: number) => (
              <div
                key={index}
                className="p-3 bg-green-50 rounded-lg text-sm"
              >
                <p>{match.summary}</p>
                <p className="text-xs text-gray-500 mt-1">
                  Score: {(match.score * 100).toFixed(1)}%
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
