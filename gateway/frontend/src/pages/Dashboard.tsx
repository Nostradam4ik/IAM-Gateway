import { useQuery } from '@tanstack/react-query'
import { getSystemStatus, getMetrics, getConnectorsStatus } from '../lib/api'
import {
  Activity,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Server,
  Database,
  Users,
  GitBranch,
} from 'lucide-react'

export default function Dashboard() {
  const { data: status } = useQuery({
    queryKey: ['systemStatus'],
    queryFn: getSystemStatus,
    refetchInterval: 30000,
  })

  const { data: metrics } = useQuery({
    queryKey: ['metrics'],
    queryFn: getMetrics,
    refetchInterval: 30000,
  })

  const { data: connectors } = useQuery({
    queryKey: ['connectorsStatus'],
    queryFn: getConnectorsStatus,
    refetchInterval: 60000,
  })

  const stats = [
    {
      name: "Operations aujourd'hui",
      value: metrics?.operations_today || 0,
      icon: GitBranch,
      color: 'blue',
    },
    {
      name: 'Taux de succes',
      value: `${((metrics?.success_rate || 0) * 100).toFixed(1)}%`,
      icon: CheckCircle,
      color: 'green',
    },
    {
      name: 'Approbations en attente',
      value: metrics?.pending_approvals || 0,
      icon: Clock,
      color: 'yellow',
    },
    {
      name: 'Erreurs (24h)',
      value: metrics?.errors_last_24h || 0,
      icon: AlertTriangle,
      color: 'red',
    },
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
      case 'healthy':
        return 'text-green-500'
      case 'error':
      case 'failed':
        return 'text-red-500'
      default:
        return 'text-yellow-500'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected':
      case 'healthy':
        return <CheckCircle className="w-5 h-5" />
      case 'error':
      case 'failed':
        return <XCircle className="w-5 h-5" />
      default:
        return <Clock className="w-5 h-5" />
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Tableau de bord</h1>
          <p className="text-gray-500 mt-1">
            Vue d'ensemble du systeme de provisionnement
          </p>
        </div>
        <div
          className={`flex items-center px-4 py-2 rounded-lg ${
            status?.provisioning_enabled
              ? 'bg-green-100 text-green-700'
              : 'bg-red-100 text-red-700'
          }`}
        >
          <Activity className="w-5 h-5 mr-2" />
          {status?.provisioning_enabled ? 'Systeme actif' : 'Systeme arrete'}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div key={stat.name} className="card">
            <div className="flex items-center">
              <div
                className={`w-12 h-12 rounded-lg flex items-center justify-center bg-${stat.color}-100`}
              >
                <stat.icon className={`w-6 h-6 text-${stat.color}-600`} />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-500">{stat.name}</p>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Connectors Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold mb-4 flex items-center">
            <Server className="w-5 h-5 mr-2" />
            Etat des connecteurs
          </h2>
          <div className="space-y-4">
            {connectors &&
              Object.entries(connectors).map(([name, status]: [string, any]) => (
                <div
                  key={name}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center">
                    <Database className="w-5 h-5 text-gray-400 mr-3" />
                    <span className="font-medium">{name.toUpperCase()}</span>
                  </div>
                  <div className={`flex items-center ${getStatusColor(status.status)}`}>
                    {getStatusIcon(status.status)}
                    <span className="ml-2 capitalize">{status.status}</span>
                  </div>
                </div>
              ))}
            {!connectors && (
              <p className="text-gray-500 text-center py-4">Chargement...</p>
            )}
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold mb-4 flex items-center">
            <Users className="w-5 h-5 mr-2" />
            Services MidPoint
          </h2>
          <div className="space-y-4">
            {status?.services_status &&
              Object.entries(status.services_status).map(
                ([name, serviceStatus]: [string, any]) => (
                  <div
                    key={name}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                  >
                    <span className="font-medium capitalize">{name}</span>
                    <div className={`flex items-center ${getStatusColor(serviceStatus)}`}>
                      {getStatusIcon(serviceStatus)}
                      <span className="ml-2 capitalize">{serviceStatus}</span>
                    </div>
                  </div>
                )
              )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Actions rapides</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button className="p-4 bg-blue-50 rounded-lg text-blue-600 hover:bg-blue-100 transition-colors text-center">
            <GitBranch className="w-6 h-6 mx-auto mb-2" />
            Nouvelle operation
          </button>
          <button className="p-4 bg-green-50 rounded-lg text-green-600 hover:bg-green-100 transition-colors text-center">
            <CheckCircle className="w-6 h-6 mx-auto mb-2" />
            Approuver
          </button>
          <button className="p-4 bg-purple-50 rounded-lg text-purple-600 hover:bg-purple-100 transition-colors text-center">
            <Activity className="w-6 h-6 mx-auto mb-2" />
            Reconciliation
          </button>
          <button className="p-4 bg-gray-50 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors text-center">
            <Database className="w-6 h-6 mx-auto mb-2" />
            Test connecteurs
          </button>
        </div>
      </div>
    </div>
  )
}
