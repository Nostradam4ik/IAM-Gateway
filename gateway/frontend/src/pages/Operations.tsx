import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getOperations, createProvisioningRequest, getPermissionLevels, updateProvisioningRequest, deleteProvisioningRequest } from '../lib/api'
import { format } from 'date-fns'
import {
  Search,
  Filter,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Plus,
  X,
  UserPlus,
  Shield,
  Edit,
  Trash2,
  Save,
  UserCheck,
  Mail,
} from 'lucide-react'

interface Operation {
  operation_id: string
  account_id: string
  status: string
  calculated_attributes: Record<string, any>
  user_data?: Record<string, any>
  target_systems?: string[]
  message: string
  timestamp: string
}

export default function Operations() {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedOperation, setSelectedOperation] = useState<Operation | null>(null)
  const [newUser, setNewUser] = useState({
    account_id: '',
    firstname: '',
    lastname: '',
    email: '',
    department: '',
    permission_level: 2,
    target_systems: ['LDAP', 'SQL'] as string[],
    require_approval: false,
    manager_email: '',
  })
  const [editUser, setEditUser] = useState({
    account_id: '',
    firstname: '',
    lastname: '',
    email: '',
    department: '',
    permission_level: 2,
    target_systems: ['LDAP', 'SQL'] as string[],
  })
  const [confirmDelete, setConfirmDelete] = useState(false)

  const { data: permissionLevels } = useQuery({
    queryKey: ['permissionLevels'],
    queryFn: getPermissionLevels,
  })
  const queryClient = useQueryClient()

  const { data: operations, isLoading } = useQuery({
    queryKey: ['operations', statusFilter],
    queryFn: () => getOperations({ status: statusFilter || undefined }),
    refetchInterval: 10000,
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
        permission_level: 2,
        target_systems: ['LDAP', 'SQL'],
        require_approval: false,
        manager_email: '',
      })
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => updateProvisioningRequest(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['operations'] })
      setShowEditModal(false)
      setSelectedOperation(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: ({ id, targetSystems }: { id: string; targetSystems: string[] }) =>
      deleteProvisioningRequest(id, targetSystems),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['operations'] })
      setShowEditModal(false)
      setSelectedOperation(null)
      setConfirmDelete(false)
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
        permission_level: newUser.permission_level,
        manager_email: newUser.manager_email,
      },
      require_approval: newUser.require_approval,
      priority: 'normal',
    })
  }

  const handleEditClick = (op: Operation) => {
    setSelectedOperation(op)
    const userData = op.user_data || {}
    const calcAttrs = op.calculated_attributes || {}
    const ldapAttrs = calcAttrs.LDAP || {}
    const sqlAttrs = calcAttrs.SQL || {}

    setEditUser({
      account_id: op.account_id,
      firstname: userData.firstname || ldapAttrs.givenName || '',
      lastname: userData.lastname || ldapAttrs.sn || '',
      email: userData.email || ldapAttrs.mail || sqlAttrs.email || '',
      department: userData.department || sqlAttrs.department || '',
      permission_level: userData.permission_level || 2,
      target_systems: op.target_systems || Object.keys(calcAttrs),
    })
    setShowEditModal(true)
    setConfirmDelete(false)
  }

  const handleUpdateUser = () => {
    if (!selectedOperation) return
    updateMutation.mutate({
      id: selectedOperation.operation_id,
      data: {
        operation: 'update',
        account_id: editUser.account_id,
        target_systems: editUser.target_systems,
        attributes: {
          firstname: editUser.firstname,
          lastname: editUser.lastname,
          email: editUser.email,
          department: editUser.department,
          permission_level: editUser.permission_level,
        },
        priority: 'normal',
      },
    })
  }

  const handleDeleteUser = () => {
    if (!selectedOperation) return
    deleteMutation.mutate({
      id: selectedOperation.operation_id,
      targetSystems: editUser.target_systems,
    })
  }

  const getLevelColor = (level: number) => {
    switch (level) {
      case 1: return 'bg-gray-100 text-gray-700 border-gray-300'
      case 2: return 'bg-blue-100 text-blue-700 border-blue-300'
      case 3: return 'bg-green-100 text-green-700 border-green-300'
      case 4: return 'bg-amber-100 text-amber-700 border-amber-300'
      case 5: return 'bg-purple-100 text-purple-700 border-purple-300'
      default: return 'bg-gray-100 text-gray-700 border-gray-300'
    }
  }

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { color: string; icon: any }> = {
      success: { color: 'badge-success', icon: CheckCircle },
      failed: { color: 'badge-danger', icon: XCircle },
      pending: { color: 'badge-warning', icon: Clock },
      in_progress: { color: 'badge-info', icon: Clock },
      awaiting_approval: { color: 'badge-warning', icon: AlertTriangle },
      deleted: { color: 'badge-danger', icon: Trash2 },
      partially_deleted: { color: 'badge-warning', icon: Trash2 },
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
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b bg-gradient-to-r from-blue-600 to-blue-700 sticky top-0 z-10">
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

            <div className="p-6">
              {/* Formulaire de création inline */}
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Prenom
                    </label>
                    <input
                      type="text"
                      value={newUser.firstname}
                      onChange={(e) => setNewUser(prev => ({ ...prev, firstname: e.target.value }))}
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
                      onChange={(e) => setNewUser(prev => ({ ...prev, lastname: e.target.value }))}
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
                    onChange={(e) => setNewUser(prev => ({ ...prev, account_id: e.target.value }))}
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
                    onChange={(e) => setNewUser(prev => ({ ...prev, email: e.target.value }))}
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
                    onChange={(e) => setNewUser(prev => ({ ...prev, department: e.target.value }))}
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
                  <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                    <Shield className="w-4 h-4 text-purple-500" />
                    Niveau de droits
                  </label>
                  <div className="grid grid-cols-5 gap-2">
                    {[1, 2, 3, 4, 5].map((level) => {
                      const levelInfo = permissionLevels?.find((l: any) => l.level === level)
                      return (
                        <button
                          key={level}
                          type="button"
                          onClick={() => setNewUser(prev => ({ ...prev, permission_level: level }))}
                          className={`p-3 rounded-lg border-2 transition-all text-center ${
                            newUser.permission_level === level
                              ? getLevelColor(level) + ' border-current ring-2 ring-offset-1'
                              : 'border-gray-200 bg-white hover:border-gray-300'
                          }`}
                        >
                          <div className="text-xl font-bold">{level}</div>
                          <div className="text-xs truncate">
                            {levelInfo?.name || `Niveau ${level}`}
                          </div>
                        </button>
                      )
                    })}
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    {permissionLevels?.find((l: any) => l.level === newUser.permission_level)?.description || ''}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Systemes cibles
                  </label>
                  <div className="flex gap-3">
                    {['LDAP', 'SQL', 'ODOO'].map((system) => (
                      <button
                        key={system}
                        type="button"
                        onClick={() => setNewUser(prev => ({
                          ...prev,
                          target_systems: prev.target_systems.includes(system)
                            ? prev.target_systems.filter(s => s !== system)
                            : [...prev.target_systems, system]
                        }))}
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

                {/* Section d'approbation */}
                <div className="border-t pt-4 mt-4">
                  <div className="flex items-center gap-3 mb-4">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={newUser.require_approval}
                        onChange={(e) => setNewUser(prev => ({ ...prev, require_approval: e.target.checked }))}
                        className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="flex items-center gap-2 text-sm font-medium text-gray-700">
                        <UserCheck className="w-4 h-4 text-amber-500" />
                        Demander approbation manager
                      </span>
                    </label>
                  </div>

                  {newUser.require_approval && (
                    <div className="pl-7 space-y-3">
                      <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                        <p className="text-sm text-amber-700 flex items-center gap-2">
                          <AlertTriangle className="w-4 h-4" />
                          L'utilisateur sera cree en statut "En attente d'approbation"
                        </p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-2">
                          <Mail className="w-4 h-4 text-gray-500" />
                          Email du manager (approbateur)
                        </label>
                        <input
                          type="email"
                          value={newUser.manager_email}
                          onChange={(e) => setNewUser(prev => ({ ...prev, manager_email: e.target.value }))}
                          className="input"
                          placeholder="manager@entreprise.com"
                        />
                        <p className="text-xs text-gray-500 mt-1">
                          Le manager recevra une notification avec un lien securise pour approuver ou rejeter
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {createMutation.isError && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                  Erreur: {(createMutation.error as any)?.response?.data?.detail || 'Echec du provisionnement'}
                </div>
              )}

              {createMutation.isSuccess && (
                <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
                  Provisionnement reussi !
                </div>
              )}
            </div>

            <div className="flex justify-end gap-3 px-6 py-4 bg-gray-50 border-t sticky bottom-0">
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

      {/* Modal de modification/suppression */}
      {showEditModal && selectedOperation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b bg-gradient-to-r from-amber-500 to-amber-600 sticky top-0 z-10">
              <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                <Edit className="w-6 h-6" />
                Modifier / Supprimer
              </h2>
              <button
                onClick={() => {
                  setShowEditModal(false)
                  setSelectedOperation(null)
                  setConfirmDelete(false)
                }}
                className="text-white/80 hover:text-white"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="p-6">
              <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">
                  <span className="font-medium">Operation ID:</span>{' '}
                  <code className="bg-gray-200 px-1 rounded">{selectedOperation.operation_id.slice(0, 8)}...</code>
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  <span className="font-medium">Statut actuel:</span>{' '}
                  {getStatusBadge(selectedOperation.status)}
                </p>
              </div>

              {!confirmDelete ? (
                <>
                  {/* Formulaire d'édition inline */}
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Prenom
                        </label>
                        <input
                          type="text"
                          value={editUser.firstname}
                          onChange={(e) => setEditUser(prev => ({ ...prev, firstname: e.target.value }))}
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
                          value={editUser.lastname}
                          onChange={(e) => setEditUser(prev => ({ ...prev, lastname: e.target.value }))}
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
                        value={editUser.account_id}
                        className="input bg-gray-100"
                        disabled
                      />
                      <p className="text-xs text-gray-400 mt-1">L'identifiant ne peut pas etre modifie</p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Email
                      </label>
                      <input
                        type="email"
                        value={editUser.email}
                        onChange={(e) => setEditUser(prev => ({ ...prev, email: e.target.value }))}
                        className="input"
                        placeholder="jean.dupont@example.com"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Departement
                      </label>
                      <select
                        value={editUser.department}
                        onChange={(e) => setEditUser(prev => ({ ...prev, department: e.target.value }))}
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
                      <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                        <Shield className="w-4 h-4 text-purple-500" />
                        Niveau de droits
                      </label>
                      <div className="grid grid-cols-5 gap-2">
                        {[1, 2, 3, 4, 5].map((level) => {
                          const levelInfo = permissionLevels?.find((l: any) => l.level === level)
                          return (
                            <button
                              key={level}
                              type="button"
                              onClick={() => setEditUser(prev => ({ ...prev, permission_level: level }))}
                              className={`p-3 rounded-lg border-2 transition-all text-center ${
                                editUser.permission_level === level
                                  ? getLevelColor(level) + ' border-current ring-2 ring-offset-1'
                                  : 'border-gray-200 bg-white hover:border-gray-300'
                              }`}
                            >
                              <div className="text-xl font-bold">{level}</div>
                              <div className="text-xs truncate">
                                {levelInfo?.name || `Niveau ${level}`}
                              </div>
                            </button>
                          )
                        })}
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Systemes cibles
                      </label>
                      <div className="flex gap-3">
                        {['LDAP', 'SQL', 'ODOO'].map((system) => (
                          <button
                            key={system}
                            type="button"
                            onClick={() => setEditUser(prev => ({
                              ...prev,
                              target_systems: prev.target_systems.includes(system)
                                ? prev.target_systems.filter(s => s !== system)
                                : [...prev.target_systems, system]
                            }))}
                            className={`px-4 py-2 rounded-lg border-2 transition-all ${
                              editUser.target_systems.includes(system)
                                ? 'border-blue-500 bg-blue-50 text-blue-700'
                                : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300'
                            }`}
                          >
                            {system}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>

                  {updateMutation.isError && (
                    <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                      Erreur: {(updateMutation.error as any)?.response?.data?.detail || 'Echec de la modification'}
                    </div>
                  )}

                  {updateMutation.isSuccess && (
                    <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
                      Modification reussie !
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-8">
                  <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Trash2 className="w-8 h-8 text-red-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    Confirmer la suppression
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Etes-vous sur de vouloir supprimer l'utilisateur{' '}
                    <span className="font-bold">{editUser.account_id}</span> ?
                  </p>
                  <p className="text-sm text-gray-500">
                    Cette action supprimera le compte des systemes suivants:
                  </p>
                  <div className="flex justify-center gap-2 mt-2">
                    {editUser.target_systems.map((sys) => (
                      <span key={sys} className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm">
                        {sys}
                      </span>
                    ))}
                  </div>

                  {deleteMutation.isError && (
                    <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                      Erreur: {(deleteMutation.error as any)?.response?.data?.detail || 'Echec de la suppression'}
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="flex justify-between gap-3 px-6 py-4 bg-gray-50 border-t sticky bottom-0">
              {!confirmDelete ? (
                <>
                  <button
                    onClick={() => setConfirmDelete(true)}
                    className="btn-danger flex items-center gap-2"
                  >
                    <Trash2 className="w-4 h-4" />
                    Supprimer
                  </button>
                  <div className="flex gap-3">
                    <button
                      onClick={() => {
                        setShowEditModal(false)
                        setSelectedOperation(null)
                      }}
                      className="btn-secondary"
                    >
                      Annuler
                    </button>
                    <button
                      onClick={handleUpdateUser}
                      disabled={updateMutation.isPending}
                      className="btn-primary flex items-center gap-2 disabled:opacity-50"
                    >
                      {updateMutation.isPending ? (
                        <>
                          <Clock className="w-4 h-4 animate-spin" />
                          Modification...
                        </>
                      ) : (
                        <>
                          <Save className="w-4 h-4" />
                          Enregistrer
                        </>
                      )}
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <button
                    onClick={() => setConfirmDelete(false)}
                    className="btn-secondary"
                  >
                    Retour
                  </button>
                  <button
                    onClick={handleDeleteUser}
                    disabled={deleteMutation.isPending}
                    className="btn-danger flex items-center gap-2 disabled:opacity-50"
                  >
                    {deleteMutation.isPending ? (
                      <>
                        <Clock className="w-4 h-4 animate-spin" />
                        Suppression...
                      </>
                    ) : (
                      <>
                        <Trash2 className="w-4 h-4" />
                        Confirmer la suppression
                      </>
                    )}
                  </button>
                </>
              )}
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
              <option value="deleted">Supprime</option>
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
                filteredOperations.map((op: Operation) => (
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
                          onClick={() => handleEditClick(op)}
                          className="text-amber-600 hover:text-amber-700 flex items-center gap-1"
                        >
                          <Edit className="w-4 h-4" />
                          Modifier
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
