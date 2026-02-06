import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listGatewayUsers,
  createGatewayUser,
  updateUserRoles,
  deleteGatewayUser,
  getAvailableRoles,
  getApprovalChain,
  GatewayUser,
} from '../lib/api'
import {
  Users,
  UserPlus,
  Shield,
  Mail,
  CheckCircle,
  XCircle,
  Edit2,
  Trash2,
  Save,
  X,
  RefreshCw,
  ChevronRight,
} from 'lucide-react'

export default function UsersPage() {
  const queryClient = useQueryClient()
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingUser, setEditingUser] = useState<string | null>(null)
  const [editRoles, setEditRoles] = useState<string[]>([])
  const [selectedWorkflowType, setSelectedWorkflowType] = useState<'full' | 'manager_only' | 'rh_it'>('full')
  const [newUser, setNewUser] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
    roles: [] as string[],
  })

  // Queries
  const { data: users, isLoading: usersLoading, refetch: refetchUsers } = useQuery({
    queryKey: ['gatewayUsers'],
    queryFn: listGatewayUsers,
  })

  const { data: roles } = useQuery({
    queryKey: ['approvalRoles'],
    queryFn: getAvailableRoles,
  })

  const { data: approvalChain, refetch: refetchChain } = useQuery({
    queryKey: ['approvalChain', selectedWorkflowType],
    queryFn: () => getApprovalChain(selectedWorkflowType),
  })

  // Mutations
  const createMutation = useMutation({
    mutationFn: createGatewayUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gatewayUsers'] })
      queryClient.invalidateQueries({ queryKey: ['approvalChain'] })
      setShowCreateModal(false)
      setNewUser({ username: '', email: '', password: '', full_name: '', roles: [] })
    },
  })

  const updateRolesMutation = useMutation({
    mutationFn: ({ username, roles }: { username: string; roles: string[] }) =>
      updateUserRoles(username, roles),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gatewayUsers'] })
      queryClient.invalidateQueries({ queryKey: ['approvalChain'] })
      setEditingUser(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteGatewayUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gatewayUsers'] })
      queryClient.invalidateQueries({ queryKey: ['approvalChain'] })
    },
  })

  const handleToggleRole = (role: string) => {
    if (editRoles.includes(role)) {
      setEditRoles(editRoles.filter((r) => r !== role))
    } else {
      setEditRoles([...editRoles, role])
    }
  }

  const handleToggleNewUserRole = (role: string) => {
    if (newUser.roles.includes(role)) {
      setNewUser({ ...newUser, roles: newUser.roles.filter((r) => r !== role) })
    } else {
      setNewUser({ ...newUser, roles: [...newUser.roles, role] })
    }
  }

  const startEditRoles = (user: GatewayUser) => {
    setEditingUser(user.username)
    setEditRoles(user.roles || [])
  }

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'bg-red-100 text-red-700'
      case 'it_admin':
        return 'bg-purple-100 text-purple-700'
      case 'rh_manager':
        return 'bg-blue-100 text-blue-700'
      case 'manager':
        return 'bg-green-100 text-green-700'
      case 'iam_engineer':
        return 'bg-yellow-100 text-yellow-700'
      default:
        return 'bg-gray-100 text-gray-700'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Users className="w-7 h-7 text-blue-500" />
            Gestion des Utilisateurs
          </h1>
          <p className="text-gray-500 mt-1">
            Gerez les utilisateurs Gateway et leurs roles d'approbation
          </p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => refetchUsers()}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${usersLoading ? 'animate-spin' : ''}`} />
            Actualiser
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary flex items-center gap-2"
          >
            <UserPlus className="w-4 h-4" />
            Nouvel Utilisateur
          </button>
        </div>
      </div>

      {/* Chaine d'approbation */}
      <div className="card border-2 border-blue-200 bg-blue-50/30">
        <h3 className="font-semibold mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-blue-600" />
          Chaine d'Approbation Actuelle
        </h3>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Type de workflow
          </label>
          <div className="flex gap-2">
            {(['full', 'manager_only', 'rh_it'] as const).map((type) => (
              <button
                key={type}
                onClick={() => {
                  setSelectedWorkflowType(type)
                  refetchChain()
                }}
                className={`px-4 py-2 rounded-lg text-sm transition-colors ${
                  selectedWorkflowType === type
                    ? 'bg-blue-500 text-white'
                    : 'bg-white text-gray-700 border border-gray-300 hover:border-blue-300'
                }`}
              >
                {type === 'full' && 'Complet (Manager → RH → IT)'}
                {type === 'manager_only' && 'Manager seul'}
                {type === 'rh_it' && 'RH + IT'}
              </button>
            ))}
          </div>
        </div>

        {approvalChain && (
          <div className="flex items-center gap-2 flex-wrap">
            {approvalChain.levels?.map((level: any, index: number) => (
              <div key={level.level} className="flex items-center gap-2">
                <div className="bg-white rounded-lg p-3 border border-blue-200">
                  <div className="text-sm font-medium text-gray-700">
                    Niveau {level.level}: {level.role_name}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {level.approvers_count} approbateur(s)
                  </div>
                  {level.emails.length > 0 && (
                    <div className="text-xs text-blue-600 mt-1">
                      {level.emails.slice(0, 2).join(', ')}
                      {level.emails.length > 2 && ` +${level.emails.length - 2}`}
                    </div>
                  )}
                  {level.emails.length === 0 && (
                    <div className="text-xs text-orange-600 mt-1">
                      Aucun approbateur configure!
                    </div>
                  )}
                </div>
                {index < approvalChain.levels.length - 1 && (
                  <ChevronRight className="w-5 h-5 text-gray-400" />
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Liste des utilisateurs */}
      <div className="card">
        <h3 className="font-semibold mb-4 flex items-center gap-2">
          <Users className="w-5 h-5 text-gray-600" />
          Utilisateurs Gateway ({users?.length || 0})
        </h3>

        {usersLoading ? (
          <div className="text-center py-8 text-gray-500">Chargement...</div>
        ) : users && users.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Utilisateur</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Email</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Roles</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-500">Statut</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id} className="border-t hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div className="font-medium">{user.username}</div>
                      <div className="text-xs text-gray-500">{user.full_name || '-'}</div>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <div className="flex items-center gap-1">
                        <Mail className="w-4 h-4 text-gray-400" />
                        {user.email}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {editingUser === user.username ? (
                        <div className="space-y-2">
                          <div className="flex flex-wrap gap-1">
                            <span className="text-xs text-gray-400 w-full">Acces:</span>
                            {roles?.filter(r => r.category === 'access').map((role) => (
                              <button
                                key={role.name}
                                onClick={() => handleToggleRole(role.name)}
                                className={`px-2 py-1 rounded text-xs transition-colors ${
                                  editRoles.includes(role.name)
                                    ? getRoleBadgeColor(role.name)
                                    : 'bg-gray-100 text-gray-400 border border-dashed border-gray-300'
                                }`}
                              >
                                {role.display_name}
                              </button>
                            ))}
                          </div>
                          <div className="flex flex-wrap gap-1">
                            <span className="text-xs text-gray-400 w-full">Approbation:</span>
                            {roles?.filter(r => r.category === 'approval').map((role) => (
                              <button
                                key={role.name}
                                onClick={() => handleToggleRole(role.name)}
                                className={`px-2 py-1 rounded text-xs transition-colors ${
                                  editRoles.includes(role.name)
                                    ? getRoleBadgeColor(role.name)
                                    : 'bg-gray-100 text-gray-400 border border-dashed border-gray-300'
                                }`}
                              >
                                {role.display_name}
                              </button>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <div className="flex flex-wrap gap-1">
                          {(user.roles?.length > 0 ? user.roles : [user.role]).map((role) => (
                            <span
                              key={role}
                              className={`px-2 py-1 rounded text-xs ${getRoleBadgeColor(role)}`}
                            >
                              {role}
                            </span>
                          ))}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {user.is_active ? (
                        <CheckCircle className="w-5 h-5 text-green-500 mx-auto" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-500 mx-auto" />
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {editingUser === user.username ? (
                          <>
                            <button
                              onClick={() =>
                                updateRolesMutation.mutate({
                                  username: user.username,
                                  roles: editRoles,
                                })
                              }
                              disabled={updateRolesMutation.isPending}
                              className="p-1 rounded text-green-600 hover:bg-green-50"
                              title="Sauvegarder"
                            >
                              <Save className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => setEditingUser(null)}
                              className="p-1 rounded text-gray-600 hover:bg-gray-100"
                              title="Annuler"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              onClick={() => startEditRoles(user)}
                              className="p-1 rounded text-blue-600 hover:bg-blue-50"
                              title="Modifier les roles"
                            >
                              <Edit2 className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => {
                                if (confirm(`Supprimer l'utilisateur ${user.username} ?`)) {
                                  deleteMutation.mutate(user.username)
                                }
                              }}
                              disabled={user.username === 'admin'}
                              className="p-1 rounded text-red-600 hover:bg-red-50 disabled:opacity-50"
                              title="Supprimer"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <Users className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p>Aucun utilisateur trouve</p>
          </div>
        )}
      </div>

      {/* Roles disponibles - groupes par categorie */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Roles d'acces */}
        <div className="card">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Users className="w-5 h-5 text-blue-600" />
            Roles d'Acces
          </h3>
          <p className="text-sm text-gray-500 mb-4">
            Ces roles definissent les permissions d'acces a l'application Gateway.
          </p>
          <div className="space-y-3">
            {roles?.filter(r => r.category === 'access').map((role) => (
              <div
                key={role.name}
                className="p-3 border rounded-lg hover:border-blue-300 transition-colors bg-blue-50/30"
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className={`px-2 py-1 rounded text-xs ${getRoleBadgeColor(role.name)}`}>
                    {role.name}
                  </span>
                  <span className="font-medium">{role.display_name}</span>
                </div>
                <p className="text-sm text-gray-500">{role.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Roles d'approbation */}
        <div className="card">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Shield className="w-5 h-5 text-purple-600" />
            Roles d'Approbation
          </h3>
          <p className="text-sm text-gray-500 mb-4">
            Ces roles permettent d'approuver les demandes dans la chaine d'approbation.
          </p>
          <div className="space-y-3">
            {roles?.filter(r => r.category === 'approval').map((role) => (
              <div
                key={role.name}
                className="p-3 border rounded-lg hover:border-purple-300 transition-colors bg-purple-50/30"
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className={`px-2 py-1 rounded text-xs ${getRoleBadgeColor(role.name)}`}>
                    Niveau {role.level}
                  </span>
                  <span className="font-medium">{role.display_name}</span>
                </div>
                <p className="text-sm text-gray-500">{role.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Modal creation utilisateur */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-lg">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <UserPlus className="w-5 h-5 text-blue-500" />
              Nouvel Utilisateur Gateway
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nom d'utilisateur *
                </label>
                <input
                  type="text"
                  value={newUser.username}
                  onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                  placeholder="john.doe"
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email *
                </label>
                <input
                  type="email"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  placeholder="john.doe@entreprise.com"
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Mot de passe *
                </label>
                <input
                  type="password"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  placeholder="********"
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nom complet
                </label>
                <input
                  type="text"
                  value={newUser.full_name}
                  onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })}
                  placeholder="John Doe"
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Roles (cliquez pour selectionner)
                </label>

                {/* Roles d'acces */}
                <div className="mb-3">
                  <span className="text-xs text-gray-500 uppercase tracking-wide">Roles d'acces</span>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {roles?.filter(r => r.category === 'access').map((role) => (
                      <button
                        key={role.name}
                        type="button"
                        onClick={() => handleToggleNewUserRole(role.name)}
                        className={`px-3 py-2 rounded-lg text-sm transition-colors ${
                          newUser.roles.includes(role.name)
                            ? getRoleBadgeColor(role.name) + ' ring-2 ring-offset-1 ring-blue-500'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                      >
                        {role.display_name}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Roles d'approbation */}
                <div className="mb-3">
                  <span className="text-xs text-gray-500 uppercase tracking-wide">Roles d'approbation</span>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {roles?.filter(r => r.category === 'approval').map((role) => (
                      <button
                        key={role.name}
                        type="button"
                        onClick={() => handleToggleNewUserRole(role.name)}
                        className={`px-3 py-2 rounded-lg text-sm transition-colors ${
                          newUser.roles.includes(role.name)
                            ? getRoleBadgeColor(role.name) + ' ring-2 ring-offset-1 ring-blue-500'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                      >
                        {role.display_name} (N{role.level})
                      </button>
                    ))}
                  </div>
                </div>

                {newUser.roles.length > 0 && (
                  <p className="text-xs text-gray-500 mt-2">
                    Roles selectionnes: {newUser.roles.join(', ')}
                  </p>
                )}
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => {
                  setShowCreateModal(false)
                  setNewUser({ username: '', email: '', password: '', full_name: '', roles: [] })
                }}
                className="btn-secondary"
              >
                Annuler
              </button>
              <button
                onClick={() => createMutation.mutate(newUser)}
                disabled={
                  !newUser.username.trim() ||
                  !newUser.email.trim() ||
                  !newUser.password.trim() ||
                  createMutation.isPending
                }
                className="btn-primary"
              >
                {createMutation.isPending ? (
                  <RefreshCw className="w-4 h-4 animate-spin inline mr-2" />
                ) : null}
                Creer
              </button>
            </div>

            {createMutation.isError && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
                Erreur: {(createMutation.error as any)?.response?.data?.detail || 'Erreur inconnue'}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
