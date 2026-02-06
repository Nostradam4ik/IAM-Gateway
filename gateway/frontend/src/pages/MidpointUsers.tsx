import { useState, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getMidpointUsers,
  getMidpointUser,
  getMidpointRoles,
  getMidpointUserRoles,
  createMidpointUser,
  deleteMidpointUser,
  disableMidpointUser,
  enableMidpointUser,
  assignMidpointRole,
  removeMidpointRole,
  getMidpointHealth,
} from '../lib/api'
import {
  Users,
  Plus,
  Trash2,
  Shield,
  UserCheck,
  UserX,
  RefreshCw,
  XCircle,
  ChevronDown,
  ChevronUp,
  Server,
  Building2,
  Database,
  FolderTree,
  Filter,
} from 'lucide-react'

interface User {
  oid: string
  name: string
  fullName?: string
  firstname?: string
  lastname?: string
  email?: string
  active?: boolean
  administrativeStatus?: string
}

interface Role {
  oid: string
  name: string
  displayName?: string
  description?: string
}

// Catégories de rôles
type RoleCategory = 'all' | 'departments' | 'ldap' | 'odoo'

const ROLE_CATEGORIES: { key: RoleCategory; i18nKey: string; icon: typeof Shield; color: string }[] = [
  { key: 'all', i18nKey: 'roles.categories.all', icon: Filter, color: 'gray' },
  { key: 'departments', i18nKey: 'roles.categories.departments', icon: Building2, color: 'blue' },
  { key: 'ldap', i18nKey: 'roles.categories.ldap', icon: FolderTree, color: 'green' },
  { key: 'odoo', i18nKey: 'roles.categories.odoo', icon: Database, color: 'orange' },
]

// Fonction pour catégoriser les rôles
const categorizeRole = (role: Role): RoleCategory[] => {
  const name = role.name?.toLowerCase() || ''
  const categories: RoleCategory[] = []

  if (name.includes('department') || name.includes('management') || name.includes('hr') ||
      name.includes('finance') || name.includes('it') || name.includes('sales') ||
      name.includes('marketing')) {
    categories.push('departments')
  }
  if (name.includes('ldap') || name.includes('employee') || name.includes('printer') ||
      name.includes('internet') || name.includes('vpn') || name.includes('public_share')) {
    categories.push('ldap')
  }
  if (name.includes('odoo') || name.includes('crm')) {
    categories.push('odoo')
  }

  // Les rôles non catégorisés sont accessibles via "Tous"
  return categories
}

export default function MidpointUsers() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showRoleModal, setShowRoleModal] = useState(false)
  const [expandedUser, setExpandedUser] = useState<string | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<RoleCategory>('all')
  const [formData, setFormData] = useState({
    username: '',
    firstname: '',
    lastname: '',
    email: '',
    department: '',
    title: '',
    password: '',
  })

  // Queries
  const { data: healthData } = useQuery({
    queryKey: ['midpointHealth'],
    queryFn: getMidpointHealth,
    refetchInterval: 30000,
  })

  const { data: usersData, isLoading: usersLoading, refetch: refetchUsers } = useQuery({
    queryKey: ['midpointUsers'],
    queryFn: getMidpointUsers,
  })

  const { data: rolesData } = useQuery({
    queryKey: ['midpointRoles'],
    queryFn: getMidpointRoles,
  })

  const { data: userDetails } = useQuery({
    queryKey: ['midpointUser', expandedUser],
    queryFn: () => getMidpointUser(expandedUser!),
    enabled: !!expandedUser,
  })

  const { data: userRoles } = useQuery({
    queryKey: ['midpointUserRoles', expandedUser],
    queryFn: () => getMidpointUserRoles(expandedUser!),
    enabled: !!expandedUser,
  })

  // Mutations
  const createUserMutation = useMutation({
    mutationFn: createMidpointUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['midpointUsers'] })
      setShowCreateModal(false)
      resetForm()
    },
  })

  const deleteUserMutation = useMutation({
    mutationFn: deleteMidpointUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['midpointUsers'] })
    },
  })

  const disableUserMutation = useMutation({
    mutationFn: disableMidpointUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['midpointUsers'] })
      queryClient.invalidateQueries({ queryKey: ['midpointUser', expandedUser] })
    },
  })

  const enableUserMutation = useMutation({
    mutationFn: enableMidpointUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['midpointUsers'] })
      queryClient.invalidateQueries({ queryKey: ['midpointUser', expandedUser] })
    },
  })

  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const assignRoleMutation = useMutation({
    mutationFn: ({ userId, roleId }: { userId: string; roleId: string }) =>
      assignMidpointRole(userId, roleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['midpointUserRoles', expandedUser] })
      setErrorMessage(null)
    },
    onError: (error: any) => {
      const msg = error?.response?.data?.detail || error?.message || "Erreur lors de l'assignation du rôle"
      setErrorMessage(msg)
    },
  })

  const removeRoleMutation = useMutation({
    mutationFn: ({ userId, roleId }: { userId: string; roleId: string }) =>
      removeMidpointRole(userId, roleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['midpointUserRoles', expandedUser] })
      setErrorMessage(null)
    },
    onError: (error: any) => {
      const msg = error?.response?.data?.detail || error?.message || "Erreur lors de la suppression du rôle"
      setErrorMessage(msg)
    },
  })

  const resetForm = () => {
    setFormData({
      username: '',
      firstname: '',
      lastname: '',
      email: '',
      department: '',
      title: '',
      password: '',
    })
  }

  const handleCreateUser = (e: React.FormEvent) => {
    e.preventDefault()
    createUserMutation.mutate({
      username: formData.username,
      firstname: formData.firstname,
      lastname: formData.lastname,
      email: formData.email || undefined,
      department: formData.department || undefined,
      title: formData.title || undefined,
      password: formData.password || undefined,
    })
  }

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'enabled':
        return 'text-green-600 bg-green-100'
      case 'disabled':
        return 'text-red-600 bg-red-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const users: User[] = usersData?.users || []
  const roles: Role[] = rolesData?.roles || []

  // Filtrer les rôles par catégorie
  const filteredRoles = useMemo(() => {
    if (selectedCategory === 'all') return roles
    return roles.filter(role => categorizeRole(role).includes(selectedCategory))
  }, [roles, selectedCategory])

  // Compter les rôles par catégorie
  const roleCounts = useMemo(() => {
    const counts: Record<RoleCategory, number> = {
      all: roles.length,
      departments: 0,
      ldap: 0,
      odoo: 0,
    }
    roles.forEach(role => {
      const cats = categorizeRole(role)
      cats.forEach(cat => {
        if (cat !== 'all') counts[cat]++
      })
    })
    return counts
  }, [roles])

  // Obtenir la couleur du badge selon la catégorie
  const getCategoryBadgeColor = (role: Role) => {
    const cats = categorizeRole(role)
    if (cats.includes('departments')) return 'bg-blue-100 text-blue-800'
    if (cats.includes('odoo')) return 'bg-orange-100 text-orange-800'
    if (cats.includes('ldap')) return 'bg-green-100 text-green-800'
    return 'bg-gray-100 text-gray-800'
  }

  // Obtenir le label de catégorie
  const getCategoryLabel = (role: Role) => {
    const cats = categorizeRole(role)
    if (cats.includes('departments')) return t('roles.categoryLabels.department')
    if (cats.includes('odoo')) return t('roles.categoryLabels.odoo')
    if (cats.includes('ldap')) return t('roles.categoryLabels.ldap')
    return t('roles.categoryLabels.other')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('users.title')}</h1>
          <p className="text-gray-500 mt-1">
            {t('users.subtitle')}
          </p>
        </div>
        <div className="flex items-center gap-4">
          {/* MidPoint Status */}
          <div
            className={`flex items-center px-3 py-1.5 rounded-lg ${
              healthData?.status === 'connected'
                ? 'bg-green-100 text-green-700'
                : 'bg-red-100 text-red-700'
            }`}
          >
            <Server className="w-4 h-4 mr-2" />
            MidPoint: {healthData?.status || t('common.loading')}
          </div>
          <button
            onClick={() => refetchUsers()}
            className="btn-secondary flex items-center"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            {t('common.refresh')}
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary flex items-center"
          >
            <Plus className="w-4 h-4 mr-2" />
            {t('users.newUser')}
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center">
            <Users className="w-8 h-8 text-blue-500" />
            <div className="ml-4">
              <p className="text-sm text-gray-500">{t('users.totalUsers')}</p>
              <p className="text-2xl font-bold">{usersData?.total || 0}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <Shield className="w-8 h-8 text-purple-500" />
            <div className="ml-4">
              <p className="text-sm text-gray-500">{t('users.availableRoles')}</p>
              <p className="text-2xl font-bold">{rolesData?.total || 0}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <UserCheck className="w-8 h-8 text-green-500" />
            <div className="ml-4">
              <p className="text-sm text-gray-500">{t('users.activeUsers')}</p>
              <p className="text-2xl font-bold">
                {users.filter(u => u.administrativeStatus === 'enabled').length}
              </p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <UserX className="w-8 h-8 text-red-500" />
            <div className="ml-4">
              <p className="text-sm text-gray-500">{t('users.disabledUsers')}</p>
              <p className="text-2xl font-bold">
                {users.filter(u => u.administrativeStatus === 'disabled').length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Users Table */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">{t('users.userList')}</h2>
        {usersLoading ? (
          <div className="text-center py-8">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto text-gray-400" />
            <p className="text-gray-500 mt-2">{t('common.loading')}</p>
          </div>
        ) : users.length === 0 ? (
          <div className="text-center py-8">
            <Users className="w-12 h-12 mx-auto text-gray-400" />
            <p className="text-gray-500 mt-2">{t('users.noUsersFound')}</p>
            <p className="text-sm text-gray-400">
              {t('users.createUserToStart')}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {t('users.username')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {t('users.fullName')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {t('common.email')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {t('common.status')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {t('common.actions')}
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {users.map((user) => (
                  <>
                    <tr
                      key={user.oid}
                      className={`hover:bg-gray-50 cursor-pointer ${
                        expandedUser === user.oid ? 'bg-blue-50' : ''
                      }`}
                      onClick={() =>
                        setExpandedUser(expandedUser === user.oid ? null : user.oid)
                      }
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          {expandedUser === user.oid ? (
                            <ChevronUp className="w-4 h-4 mr-2 text-gray-400" />
                          ) : (
                            <ChevronDown className="w-4 h-4 mr-2 text-gray-400" />
                          )}
                          <span className="font-medium text-gray-900">
                            {user.name}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                        {user.fullName || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                        {user.email || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs rounded-full ${getStatusColor(
                            user.administrativeStatus
                          )}`}
                        >
                          {user.administrativeStatus || 'unknown'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          {user.administrativeStatus === 'enabled' ? (
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                disableUserMutation.mutate(user.oid)
                              }}
                              className="text-yellow-600 hover:text-yellow-800"
                              title={t('users.disable')}
                            >
                              <UserX className="w-4 h-4" />
                            </button>
                          ) : (
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                enableUserMutation.mutate(user.oid)
                              }}
                              className="text-green-600 hover:text-green-800"
                              title={t('users.enable')}
                            >
                              <UserCheck className="w-4 h-4" />
                            </button>
                          )}
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              setExpandedUser(user.oid)
                              setShowRoleModal(true)
                            }}
                            className="text-purple-600 hover:text-purple-800"
                            title={t('roles.title')}
                          >
                            <Shield className="w-4 h-4" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              if (
                                confirm(t('users.deleteConfirm', { name: user.name }))
                              ) {
                                deleteUserMutation.mutate(user.oid)
                              }
                            }}
                            className="text-red-600 hover:text-red-800"
                            title="Supprimer"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                    {/* Expanded row with user details */}
                    {expandedUser === user.oid && userDetails && (
                      <tr>
                        <td colSpan={5} className="px-6 py-4 bg-gray-50">
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <h4 className="font-medium text-gray-900 mb-2">
                                Details
                              </h4>
                              <dl className="space-y-1 text-sm">
                                <div className="flex">
                                  <dt className="w-32 text-gray-500">OID:</dt>
                                  <dd className="text-gray-900 font-mono text-xs">
                                    {userDetails.oid}
                                  </dd>
                                </div>
                                <div className="flex">
                                  <dt className="w-32 text-gray-500">Prenom:</dt>
                                  <dd className="text-gray-900">
                                    {userDetails.givenName || '-'}
                                  </dd>
                                </div>
                                <div className="flex">
                                  <dt className="w-32 text-gray-500">Nom:</dt>
                                  <dd className="text-gray-900">
                                    {userDetails.familyName || '-'}
                                  </dd>
                                </div>
                              </dl>
                            </div>
                            <div>
                              <h4 className="font-medium text-gray-900 mb-2">
                                Roles assignes
                              </h4>
                              {userRoles?.roles?.length > 0 ? (
                                <div className="flex flex-wrap gap-2">
                                  {userRoles.roles.map((role: any) => (
                                    <span
                                      key={role.oid}
                                      className="inline-flex items-center px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded"
                                    >
                                      {role.name}
                                      <button
                                        onClick={() =>
                                          removeRoleMutation.mutate({
                                            userId: user.oid,
                                            roleId: role.oid,
                                          })
                                        }
                                        className="ml-1 text-purple-600 hover:text-purple-800"
                                      >
                                        <XCircle className="w-3 h-3" />
                                      </button>
                                    </span>
                                  ))}
                                </div>
                              ) : (
                                <p className="text-sm text-gray-500">
                                  Aucun role assigne
                                </p>
                              )}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create User Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Nouvel utilisateur</h3>
            <form onSubmit={handleCreateUser} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Nom d'utilisateur *
                </label>
                <input
                  type="text"
                  required
                  value={formData.username}
                  onChange={(e) =>
                    setFormData({ ...formData, username: e.target.value })
                  }
                  className="input mt-1"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Prenom *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.firstname}
                    onChange={(e) =>
                      setFormData({ ...formData, firstname: e.target.value })
                    }
                    className="input mt-1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Nom *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.lastname}
                    onChange={(e) =>
                      setFormData({ ...formData, lastname: e.target.value })
                    }
                    className="input mt-1"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Email
                </label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) =>
                    setFormData({ ...formData, email: e.target.value })
                  }
                  className="input mt-1"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Departement
                  </label>
                  <input
                    type="text"
                    value={formData.department}
                    onChange={(e) =>
                      setFormData({ ...formData, department: e.target.value })
                    }
                    className="input mt-1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Titre
                  </label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) =>
                      setFormData({ ...formData, title: e.target.value })
                    }
                    className="input mt-1"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Mot de passe
                </label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) =>
                    setFormData({ ...formData, password: e.target.value })
                  }
                  className="input mt-1"
                  placeholder="Laissez vide pour generer"
                />
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false)
                    resetForm()
                  }}
                  className="btn-secondary"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  disabled={createUserMutation.isPending}
                  className="btn-primary"
                >
                  {createUserMutation.isPending ? 'Creation...' : 'Creer'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Assign Role Modal - Enhanced */}
      {showRoleModal && expandedUser && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center"
          onClick={() => setShowRoleModal(false)}
        >
          <div
            className="bg-white rounded-lg w-full max-w-2xl mx-4 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="p-4 border-b">
              <h3 className="text-lg font-semibold flex items-center">
                <Shield className="w-5 h-5 mr-2 text-purple-600" />
                {t('roles.title')}
              </h3>
              <p className="text-sm text-gray-500 mt-1">
                {t('users.username')}: {users.find(u => u.oid === expandedUser)?.name || expandedUser}
              </p>
            </div>

            {/* Error Message */}
            {errorMessage && (
              <div className="p-4 bg-red-50 border-b border-red-200">
                <div className="flex items-start">
                  <XCircle className="w-5 h-5 text-red-500 mr-2 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-red-800">{t('common.error')}</p>
                    <p className="text-sm text-red-700 mt-1">{errorMessage}</p>
                  </div>
                  <button
                    onClick={() => setErrorMessage(null)}
                    className="text-red-500 hover:text-red-700"
                  >
                    <XCircle className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {/* Current Roles Section */}
            <div className="p-4 border-b bg-gray-50">
              <h4 className="text-sm font-medium text-gray-700 mb-2">{t('roles.currentRoles')}</h4>
              {userRoles?.roles?.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {userRoles.roles.map((role: Role) => (
                    <span
                      key={role.oid}
                      className={`inline-flex items-center px-3 py-1.5 rounded-lg text-sm ${getCategoryBadgeColor(role)}`}
                    >
                      {role.name}
                      <button
                        onClick={() => {
                          if (confirm(t('roles.removeRoleConfirm', { name: role.name }))) {
                            removeRoleMutation.mutate({
                              userId: expandedUser,
                              roleId: role.oid,
                            })
                          }
                        }}
                        disabled={removeRoleMutation.isPending}
                        className="ml-2 hover:text-red-600 transition-colors"
                        title={t('roles.removeRole')}
                      >
                        <XCircle className="w-4 h-4" />
                      </button>
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500 italic">{t('roles.noRolesAssigned')}</p>
              )}
            </div>

            {/* Category Filter Tabs */}
            <div className="p-4 border-b">
              <div className="flex flex-wrap gap-2">
                {ROLE_CATEGORIES.map((cat) => {
                  const Icon = cat.icon
                  const isActive = selectedCategory === cat.key
                  return (
                    <button
                      key={cat.key}
                      onClick={() => setSelectedCategory(cat.key)}
                      className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                        isActive
                          ? `bg-${cat.color}-100 text-${cat.color}-800 ring-2 ring-${cat.color}-500`
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                      style={isActive ? {
                        backgroundColor: cat.color === 'gray' ? '#f3f4f6' :
                          cat.color === 'blue' ? '#dbeafe' :
                          cat.color === 'green' ? '#dcfce7' :
                          cat.color === 'orange' ? '#ffedd5' : '#f3e8ff',
                        color: cat.color === 'gray' ? '#374151' :
                          cat.color === 'blue' ? '#1e40af' :
                          cat.color === 'green' ? '#166534' :
                          cat.color === 'orange' ? '#c2410c' : '#7c3aed'
                      } : {}}
                    >
                      <Icon className="w-4 h-4 mr-1.5" />
                      {t(cat.i18nKey)}
                      <span className="ml-1.5 px-1.5 py-0.5 rounded-full text-xs bg-white bg-opacity-50">
                        {roleCounts[cat.key]}
                      </span>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Roles List */}
            <div className="p-4 overflow-y-auto" style={{ maxHeight: '300px' }}>
              <div className="space-y-2">
                {filteredRoles.length === 0 ? (
                  <p className="text-center text-gray-500 py-4">
                    {t('roles.noRolesInCategory')}
                  </p>
                ) : (
                  filteredRoles.map((role) => {
                    const isAssigned = userRoles?.roles?.some((r: Role) => r.oid === role.oid)
                    return (
                      <div
                        key={role.oid}
                        className={`p-3 border rounded-lg transition-colors ${
                          isAssigned
                            ? 'bg-green-50 border-green-200'
                            : 'hover:bg-gray-50 border-gray-200'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{role.displayName || role.name}</span>
                              <span className={`text-xs px-2 py-0.5 rounded ${getCategoryBadgeColor(role)}`}>
                                {getCategoryLabel(role)}
                              </span>
                              {isAssigned && (
                                <span className="text-xs px-2 py-0.5 rounded bg-green-100 text-green-800">
                                  {t('roles.assigned')}
                                </span>
                              )}
                            </div>
                            {role.description && (
                              <p className="text-sm text-gray-500 mt-1">{role.description}</p>
                            )}
                          </div>
                          <div className="ml-4">
                            {isAssigned ? (
                              <button
                                onClick={() => {
                                  if (confirm(t('roles.removeRoleConfirm', { name: role.name }))) {
                                    removeRoleMutation.mutate({
                                      userId: expandedUser,
                                      roleId: role.oid,
                                    })
                                  }
                                }}
                                disabled={removeRoleMutation.isPending}
                                className="px-3 py-1.5 text-sm bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            ) : (
                              <button
                                onClick={() =>
                                  assignRoleMutation.mutate({
                                    userId: expandedUser,
                                    roleId: role.oid,
                                  })
                                }
                                disabled={assignRoleMutation.isPending}
                                className="px-3 py-1.5 text-sm bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
                              >
                                <Plus className="w-4 h-4" />
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  })
                )}
              </div>
            </div>

            {/* Footer */}
            <div className="p-4 border-t bg-gray-50">
              <button
                onClick={() => {
                  setShowRoleModal(false)
                  setSelectedCategory('all')
                  setErrorMessage(null)
                }}
                className="btn-secondary w-full"
              >
                {t('common.close')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
