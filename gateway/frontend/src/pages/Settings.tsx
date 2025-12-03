import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getSystemStatus,
  emergencyStop,
  resumeProvisioning,
  getConnectorsStatus,
} from '../lib/api'
import {
  Settings as SettingsIcon,
  AlertTriangle,
  Play,
  Power,
  Database,
  CheckCircle,
  XCircle,
  RefreshCw,
} from 'lucide-react'

export default function Settings() {
  const [confirmStop, setConfirmStop] = useState(false)
  const queryClient = useQueryClient()

  const { data: status } = useQuery({
    queryKey: ['systemStatus'],
    queryFn: getSystemStatus,
    refetchInterval: 5000,
  })

  const { data: connectors, refetch: refetchConnectors } = useQuery({
    queryKey: ['connectorsStatus'],
    queryFn: getConnectorsStatus,
  })

  const stopMutation = useMutation({
    mutationFn: emergencyStop,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['systemStatus'] })
      setConfirmStop(false)
    },
  })

  const resumeMutation = useMutation({
    mutationFn: resumeProvisioning,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['systemStatus'] })
    },
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <SettingsIcon className="w-8 h-8 text-gray-400" />
          Parametres
        </h1>
        <p className="text-gray-500 mt-1">
          Configuration et controle du systeme
        </p>
      </div>

      {/* System Status */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Power className="w-5 h-5" />
          Etat du systeme
        </h2>

        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg mb-4">
          <div>
            <p className="font-medium">Provisionnement</p>
            <p className="text-sm text-gray-500">
              {status?.provisioning_enabled
                ? 'Le systeme traite les operations normalement'
                : 'Le systeme est en pause - aucune operation traitee'}
            </p>
          </div>
          <div
            className={`px-4 py-2 rounded-lg font-medium ${
              status?.provisioning_enabled
                ? 'bg-green-100 text-green-700'
                : 'bg-red-100 text-red-700'
            }`}
          >
            {status?.provisioning_enabled ? 'Actif' : 'Arrete'}
          </div>
        </div>

        <div className="flex gap-4">
          {status?.provisioning_enabled ? (
            <button
              onClick={() => setConfirmStop(true)}
              className="btn-danger flex items-center gap-2"
            >
              <AlertTriangle className="w-5 h-5" />
              Arret d'urgence
            </button>
          ) : (
            <button
              onClick={() => resumeMutation.mutate()}
              disabled={resumeMutation.isPending}
              className="btn-primary flex items-center gap-2"
            >
              <Play className="w-5 h-5" />
              Reprendre le provisionnement
            </button>
          )}
        </div>

        {/* Emergency stop confirmation */}
        {confirmStop && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700 font-medium mb-3">
              Etes-vous sur de vouloir arreter le systeme?
            </p>
            <p className="text-red-600 text-sm mb-4">
              Toutes les operations en cours seront suspendues. Les nouvelles
              requetes seront rejetees.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => stopMutation.mutate()}
                disabled={stopMutation.isPending}
                className="btn-danger"
              >
                {stopMutation.isPending ? 'Arret en cours...' : 'Confirmer l\'arret'}
              </button>
              <button
                onClick={() => setConfirmStop(false)}
                className="btn-secondary"
              >
                Annuler
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Connectors */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Database className="w-5 h-5" />
            Connecteurs
          </h2>
          <button
            onClick={() => refetchConnectors()}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Tester
          </button>
        </div>

        <div className="space-y-3">
          {connectors &&
            Object.entries(connectors).map(([name, status]: [string, any]) => (
              <div
                key={name}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <Database className="w-5 h-5 text-gray-400" />
                  <div>
                    <p className="font-medium">{name.toUpperCase()}</p>
                    {status.error && (
                      <p className="text-sm text-red-500">{status.error}</p>
                    )}
                  </div>
                </div>
                <div
                  className={`flex items-center gap-2 ${
                    status.status === 'connected'
                      ? 'text-green-600'
                      : 'text-red-600'
                  }`}
                >
                  {status.status === 'connected' ? (
                    <CheckCircle className="w-5 h-5" />
                  ) : (
                    <XCircle className="w-5 h-5" />
                  )}
                  <span className="capitalize">{status.status}</span>
                </div>
              </div>
            ))}
        </div>
      </div>

      {/* Configuration */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Configuration</h2>

        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">Timeout workflow par defaut</p>
            <p className="font-medium">72 heures</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">Niveaux max workflow</p>
            <p className="font-medium">5 niveaux</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">URL MidPoint</p>
            <p className="font-medium text-sm">http://localhost:8080/midpoint</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">Base LDAP</p>
            <p className="font-medium text-sm">dc=example,dc=com</p>
          </div>
        </div>
      </div>
    </div>
  )
}
