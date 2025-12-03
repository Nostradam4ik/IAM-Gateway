import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getOperations, rollbackOperation } from '../lib/api'
import { format } from 'date-fns'
import {
  Search,
  Filter,
  RotateCcw,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
} from 'lucide-react'

export default function Operations() {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const queryClient = useQueryClient()

  const { data: operations, isLoading } = useQuery({
    queryKey: ['operations', statusFilter],
    queryFn: () => getOperations({ status: statusFilter || undefined }),
    refetchInterval: 10000,
  })

  const rollbackMutation = useMutation({
    mutationFn: rollbackOperation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['operations'] })
    },
  })

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { color: string; icon: any }> = {
      success: { color: 'badge-success', icon: CheckCircle },
      failed: { color: 'badge-danger', icon: XCircle },
      pending: { color: 'badge-warning', icon: Clock },
      in_progress: { color: 'badge-info', icon: Clock },
      awaiting_approval: { color: 'badge-warning', icon: AlertTriangle },
      rolled_back: { color: 'badge-danger', icon: RotateCcw },
    }

    const config = statusConfig[status] || { color: 'badge-info', icon: Clock }
    const Icon = config.icon

    return (
      <span className={`badge ${config.color} flex items-center gap-1`}>
        <Icon className="w-3 h-3" />
        {status.replace('_', ' ')}
      </span>
    )
  }

  const filteredOperations = operations?.filter((op: any) =>
    op.operation_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    op.account_id?.toLowerCase().includes(searchTerm.toLowerCase())
  ) || []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Operations</h1>
          <p className="text-gray-500 mt-1">
            Historique des operations de provisionnement
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Rechercher par ID ou compte..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input pl-10"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input w-48"
            >
              <option value="">Tous les statuts</option>
              <option value="success">Succes</option>
              <option value="failed">Echec</option>
              <option value="pending">En attente</option>
              <option value="in_progress">En cours</option>
              <option value="awaiting_approval">Approbation</option>
            </select>
          </div>
        </div>
      </div>

      {/* Operations table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-4 px-4 font-medium text-gray-500">
                  ID Operation
                </th>
                <th className="text-left py-4 px-4 font-medium text-gray-500">
                  Compte
                </th>
                <th className="text-left py-4 px-4 font-medium text-gray-500">
                  Statut
                </th>
                <th className="text-left py-4 px-4 font-medium text-gray-500">
                  Cibles
                </th>
                <th className="text-left py-4 px-4 font-medium text-gray-500">
                  Date
                </th>
                <th className="text-left py-4 px-4 font-medium text-gray-500">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-gray-500">
                    Chargement...
                  </td>
                </tr>
              ) : filteredOperations.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-gray-500">
                    Aucune operation trouvee
                  </td>
                </tr>
              ) : (
                filteredOperations.map((op: any) => (
                  <tr
                    key={op.operation_id}
                    className="border-b border-gray-100 hover:bg-gray-50"
                  >
                    <td className="py-4 px-4">
                      <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                        {op.operation_id?.slice(0, 8)}...
                      </code>
                    </td>
                    <td className="py-4 px-4 font-medium">{op.account_id}</td>
                    <td className="py-4 px-4">{getStatusBadge(op.status)}</td>
                    <td className="py-4 px-4">
                      <div className="flex gap-1">
                        {Object.keys(op.calculated_attributes || {}).map(
                          (target) => (
                            <span
                              key={target}
                              className="text-xs bg-gray-100 px-2 py-1 rounded"
                            >
                              {target}
                            </span>
                          )
                        )}
                      </div>
                    </td>
                    <td className="py-4 px-4 text-gray-500">
                      {op.timestamp
                        ? format(new Date(op.timestamp), 'dd/MM/yyyy HH:mm')
                        : '-'}
                    </td>
                    <td className="py-4 px-4">
                      {(op.status === 'success' || op.status === 'failed') && (
                        <button
                          onClick={() => rollbackMutation.mutate(op.operation_id)}
                          disabled={rollbackMutation.isPending}
                          className="text-red-600 hover:text-red-700 flex items-center gap-1"
                        >
                          <RotateCcw className="w-4 h-4" />
                          Rollback
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
