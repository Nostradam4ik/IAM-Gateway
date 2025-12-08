import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getOperations, rollbackOperation, createProvisioningRequest } from '../lib/api'
import { format } from 'date-fns'
import {
  Search,
  Filter,
  RotateCcw,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Plus,
  X,
  UserPlus,
} from 'lucide-react'

export default function Operations() {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newUser, setNewUser] = useState({
    account_id: '',
    firstname: '',
    lastname: '',
    email: '',
    department: '',
    target_systems: ['LDAP', 'SQL'] as string[],
  })
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

  const createMutation = useMutation({
    mutationFn: createProvisioningRequest,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['operations'] })
      setShowCreateModal(false)
      setNewUser({
        account_id: '',
        firstname: '',
        lastname: '',
        email: '',
        department: '',
        target_systems: ['LDAP', 'SQL'],
      })
    },
  })

  const handleCreateUser = () => {
    createMutation.mutate({
      operation: 'create',
      account_id: newUser.account_id,
      target_systems: newUser.target_systems,
      attributes: {
        firstname: newUser.firstname,
        lastname: newUser.lastname,
        email: newUser.email,
        department: newUser.department,
      },
      priority: 'normal',
    })
  }

  const toggleTargetSystem = (system: string) => {
    setNewUser(prev => ({
      ...prev,
      target_systems: prev.target_systems.includes(system)
        ? prev.target_systems.filter(s => s !== system)
        : [...prev.target_systems, system]
    }))
  }

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
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn-primary flex items-center gap-2"
        >
          <UserPlus className="w-5 h-5" />
          Nouveau provisionnement
        </button>
      </div>

      {/* Modal de création */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b bg-gradient-to-r from-blue-600 to-blue-700">
              <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                <UserPlus className="w-6 h-6" />
                Nouveau provisionnement
              </h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-white/80 hover:text-white"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Prenom
                  </label>
                  <input
                    type="text"
                    value={newUser.firstname}
                    onChange={(e) => setNewUser({ ...newUser, firstname: e.target.value })}
                    className="input"
                    placeholder="Jean"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nom
                  </label>
                  <input
                    type="text"
                    value={newUser.lastname}
                    onChange={(e) => setNewUser({ ...newUser, lastname: e.target.value })}
                    className="input"
                    placeholder="Dupont"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Identifiant compte
                </label>
                <input
                  type="text"
                  value={newUser.account_id}
                  onChange={(e) => setNewUser({ ...newUser, account_id: e.target.value })}
                  className="input"
                  placeholder="jdupont"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  className="input"
                  placeholder="jean.dupont@example.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Departement
                </label>
                <select
                  value={newUser.department}
                  onChange={(e) => setNewUser({ ...newUser, department: e.target.value })}
                  className="input"
                >
                  <option value="">Selectionner...</option>
                  <option value="IT">IT</option>
                  <option value="Finance">Finance</option>
                  <option value="RH">Ressources Humaines</option>
                  <option value="Marketing">Marketing</option>
                  <option value="Direction">Direction</option>
                  <option value="Commercial">Commercial</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Systemes cibles
                </label>
                <div className="flex gap-3">
                  {['LDAP', 'SQL', 'ODOO'].map((system) => (
                    <button
                      key={system}
                      onClick={() => toggleTargetSystem(system)}
                      className={`px-4 py-2 rounded-lg border-2 transition-all ${
                        newUser.target_systems.includes(system)
                          ? 'border-blue-500 bg-blue-50 text-blue-700'
                          : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300'
                      }`}
                    >
                      {system}
                    </button>
                  ))}
                </div>
              </div>

              {createMutation.isError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                  Erreur: {(createMutation.error as any)?.response?.data?.detail || 'Echec du provisionnement'}
                </div>
              )}

              {createMutation.isSuccess && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
                  Provisionnement reussi !
                </div>
              )}
            </div>

            <div className="flex justify-end gap-3 px-6 py-4 bg-gray-50 border-t">
              <button
                onClick={() => setShowCreateModal(false)}
                className="btn-secondary"
              >
                Annuler
              </button>
              <button
                onClick={handleCreateUser}
                disabled={createMutation.isPending || !newUser.account_id || !newUser.firstname || !newUser.lastname}
                className="btn-primary flex items-center gap-2 disabled:opacity-50"
              >
                {createMutation.isPending ? (
                  <>
                    <Clock className="w-4 h-4 animate-spin" />
                    Provisionnement...
                  </>
                ) : (
                  <>
                    <Plus className="w-4 h-4" />
                    Creer le compte
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

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
