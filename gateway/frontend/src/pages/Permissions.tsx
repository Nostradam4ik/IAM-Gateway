import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  getPermissionLevels,
  getUsersPermissions,
  getPermissionsStats,
} from '../lib/api'
import {
  Shield,
  Users,
  User,
  Building2,
  Eye,
  Edit,
  FileText,
  CheckCircle,
  Lock,
} from 'lucide-react'

export default function Permissions() {
  const [selectedLevel, setSelectedLevel] = useState<number | null>(null)
  const [selectedDepartment, setSelectedDepartment] = useState<string | null>(null)

  // Fetch permission levels
  const { data: levels, isLoading: levelsLoading } = useQuery({
    queryKey: ['permissionLevels'],
    queryFn: getPermissionLevels,
  })

  // Fetch users with permissions
  const { data: users, isLoading: usersLoading } = useQuery({
    queryKey: ['usersPermissions', selectedLevel, selectedDepartment],
    queryFn: () => getUsersPermissions(selectedLevel || undefined, selectedDepartment || undefined),
  })

  // Fetch stats
  const { data: stats } = useQuery({
    queryKey: ['permissionsStats'],
    queryFn: getPermissionsStats,
  })

  const getLevelIcon = (level: number) => {
    switch (level) {
      case 1:
        return <Eye className="w-5 h-5" />
      case 2:
        return <User className="w-5 h-5" />
      case 3:
        return <Edit className="w-5 h-5" />
      case 4:
        return <FileText className="w-5 h-5" />
      case 5:
        return <Shield className="w-5 h-5" />
      default:
        return <Lock className="w-5 h-5" />
    }
  }

  const getLevelColor = (level: number) => {
    switch (level) {
      case 1:
        return 'bg-gray-100 text-gray-700 border-gray-300'
      case 2:
        return 'bg-blue-100 text-blue-700 border-blue-300'
      case 3:
        return 'bg-green-100 text-green-700 border-green-300'
      case 4:
        return 'bg-amber-100 text-amber-700 border-amber-300'
      case 5:
        return 'bg-purple-100 text-purple-700 border-purple-300'
      default:
        return 'bg-gray-100 text-gray-700 border-gray-300'
    }
  }

  const getLevelBgGradient = (level: number) => {
    switch (level) {
      case 1:
        return 'from-gray-500 to-gray-600'
      case 2:
        return 'from-blue-500 to-blue-600'
      case 3:
        return 'from-green-500 to-green-600'
      case 4:
        return 'from-amber-500 to-amber-600'
      case 5:
        return 'from-purple-500 to-purple-600'
      default:
        return 'from-gray-500 to-gray-600'
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Shield className="w-7 h-7 text-purple-500" />
          Niveaux de Droits
        </h1>
        <p className="text-gray-500 mt-1">
          Gestion des permissions utilisateurs par niveau hierarchique (1-5)
        </p>
      </div>

      {/* Stats Overview */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {stats.by_level?.map((levelStat: any) => (
            <div
              key={levelStat.level}
              onClick={() => setSelectedLevel(selectedLevel === levelStat.level ? null : levelStat.level)}
              className={`card cursor-pointer transition-all hover:shadow-lg ${
                selectedLevel === levelStat.level ? 'ring-2 ring-purple-500' : ''
              }`}
            >
              <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${getLevelBgGradient(levelStat.level)} flex items-center justify-center text-white mb-3`}>
                <span className="text-xl font-bold">{levelStat.level}</span>
              </div>
              <h3 className="font-semibold text-gray-900">{levelStat.name}</h3>
              <div className="flex items-baseline gap-2 mt-2">
                <span className="text-2xl font-bold">{levelStat.count}</span>
                <span className="text-sm text-gray-500">utilisateurs</span>
              </div>
              <div className="text-xs text-gray-400 mt-1">{levelStat.percentage}%</div>
            </div>
          ))}
        </div>
      )}

      {/* Levels Description */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Lock className="w-5 h-5 text-gray-500" />
          Description des Niveaux
        </h2>

        {levelsLoading ? (
          <p className="text-gray-500">Chargement...</p>
        ) : (
          <div className="space-y-4">
            {levels?.map((level: any) => (
              <div
                key={level.level}
                className={`p-4 rounded-lg border-2 transition-all ${
                  selectedLevel === level.level
                    ? 'border-purple-400 bg-purple-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-start gap-4">
                  <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${getLevelBgGradient(level.level)} flex items-center justify-center text-white flex-shrink-0`}>
                    <span className="text-2xl font-bold">{level.level}</span>
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-1">
                      <h3 className="text-lg font-semibold">{level.name}</h3>
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${getLevelColor(level.level)}`}>
                        Niveau {level.level}
                      </span>
                      <span className="text-sm text-gray-500">
                        ({level.user_count} utilisateurs)
                      </span>
                    </div>
                    <p className="text-gray-600 mb-3">{level.description}</p>

                    <div className="flex flex-wrap gap-2 mb-3">
                      <span className="text-xs text-gray-500 font-medium">Exemples:</span>
                      {level.examples?.map((ex: string, i: number) => (
                        <span key={i} className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                          {ex}
                        </span>
                      ))}
                    </div>

                    <details className="text-sm">
                      <summary className="cursor-pointer text-purple-600 hover:text-purple-700 font-medium">
                        Voir les {level.permissions?.length} permissions
                      </summary>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {level.permissions?.map((perm: string, i: number) => (
                          <span
                            key={i}
                            className={`px-2 py-1 rounded text-xs flex items-center gap-1 ${getLevelColor(level.level)}`}
                          >
                            <CheckCircle className="w-3 h-3" />
                            {perm.replace(/_/g, ' ')}
                          </span>
                        ))}
                      </div>
                    </details>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Filter by Department */}
      {stats?.by_department && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Building2 className="w-5 h-5 text-gray-500" />
            Filtrer par Departement
          </h2>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedDepartment(null)}
              className={`px-4 py-2 rounded-lg border transition-colors ${
                selectedDepartment === null
                  ? 'bg-purple-100 border-purple-300 text-purple-700'
                  : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              Tous ({stats.total_users})
            </button>
            {stats.by_department?.map((dept: any) => (
              <button
                key={dept.department}
                onClick={() => setSelectedDepartment(selectedDepartment === dept.department ? null : dept.department)}
                className={`px-4 py-2 rounded-lg border transition-colors ${
                  selectedDepartment === dept.department
                    ? 'bg-purple-100 border-purple-300 text-purple-700'
                    : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                {dept.department} ({dept.total})
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Users List */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Users className="w-5 h-5 text-gray-500" />
          Utilisateurs
          {selectedLevel && <span className="text-purple-600">(Niveau {selectedLevel})</span>}
          {selectedDepartment && <span className="text-purple-600">- {selectedDepartment}</span>}
        </h2>

        {usersLoading ? (
          <p className="text-gray-500">Chargement...</p>
        ) : users?.length === 0 ? (
          <p className="text-gray-500 text-center py-8">Aucun utilisateur trouve</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Utilisateur</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Departement</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-500">Niveau</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Role</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-500">Permissions</th>
                </tr>
              </thead>
              <tbody>
                {users?.map((user: any) => (
                  <tr key={user.user_id} className="border-t hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-full bg-gradient-to-br ${getLevelBgGradient(user.level)} flex items-center justify-center text-white font-semibold`}>
                          {user.full_name?.split(' ').map((n: string) => n[0]).join('').slice(0, 2)}
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{user.full_name}</p>
                          <p className="text-sm text-gray-500">@{user.username}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-1 bg-gray-100 text-gray-700 text-sm rounded">
                        {user.department}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full ${getLevelColor(user.level)}`}>
                        <span className="font-bold">{user.level}</span>
                        {getLevelIcon(user.level)}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="font-medium">{user.level_name}</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="text-sm text-gray-500">
                        {user.permissions?.length} droits
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="card bg-gradient-to-r from-purple-50 to-blue-50">
        <h3 className="font-semibold mb-3">Legende des Niveaux</h3>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-500 to-gray-600 flex items-center justify-center text-white font-bold">1</div>
            <span>Visiteur - Acces minimal</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white font-bold">2</div>
            <span>Utilisateur - Standard</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center text-white font-bold">3</div>
            <span>Operateur - Etendu</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-amber-500 to-amber-600 flex items-center justify-center text-white font-bold">4</div>
            <span>Manager - Avance</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center text-white font-bold">5</div>
            <span>Chef Dept - Maximum</span>
          </div>
        </div>
      </div>
    </div>
  )
}
