/**
 * Dashboard.tsx - Tableau de bord principal de la Gateway IAM.
 *
 * Affiche :
 *   1. Etat du systeme (actif/arrete) en haut a droite
 *   2. Grille des connecteurs configures avec leur statut de sante :
 *      - Vert (healthy) = connecte | Rouge (unhealthy) = erreur | Jaune = inconnu
 *      - Couleur par type : bleu=LDAP, orange=ERP, violet=SQL, indigo=IGA/MidPoint
 *      - Bouton "Tester tout" lance un health check sur tous les connecteurs
 *      - Clic sur un connecteur navigue vers /dashboard/connectors
 *   3. Services MidPoint : statut en temps reel de DB, Redis, LDAP, MidPoint
 *
 * Rafraichissement automatique :
 *   - Statut systeme : toutes les 30 secondes
 *   - Liste des connecteurs : toutes les 60 secondes
 */
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { getSystemStatus, getConnectors, runHealthChecks } from '../lib/api'
import {
  Activity,
  CheckCircle,
  XCircle,
  Clock,
  Server,
  Database,
  RefreshCw,
  Plug,
  Globe,
} from 'lucide-react'
import { useState } from 'react'

// Mapping type de connecteur -> icone Lucide (pour la grille du dashboard)
const connectorTypeIcons: Record<string, any> = {
  ldap: Globe,
  erp: Database,
  sql: Database,
  iga: Server,
  midpoint: Server,
}

// Mapping type de connecteur -> couleur Tailwind (pour les cartes du dashboard)
const connectorTypeColors: Record<string, string> = {
  ldap: 'blue',
  erp: 'orange',
  sql: 'purple',
  iga: 'indigo',
  midpoint: 'indigo',
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [testingConnectors, setTestingConnectors] = useState(false)
  const { data: status } = useQuery({
    queryKey: ['systemStatus'],
    queryFn: getSystemStatus,
    refetchInterval: 30000,
  })

  const { data: connectorsList, refetch: refetchConnectors } = useQuery({
    queryKey: ['connectors'],
    queryFn: () => getConnectors(),
    refetchInterval: 60000,
  })

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'healthy':
        return 'text-green-500'
      case 'unhealthy':
      case 'error':
        return 'text-red-500'
      default:
        return 'text-yellow-500'
    }
  }

  const getHealthBg = (health: string) => {
    switch (health) {
      case 'healthy':
        return 'bg-green-50 border-green-200'
      case 'unhealthy':
      case 'error':
        return 'bg-red-50 border-red-200'
      default:
        return 'bg-yellow-50 border-yellow-200'
    }
  }

  const getHealthIcon = (health: string) => {
    switch (health) {
      case 'healthy':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'unhealthy':
      case 'error':
        return <XCircle className="w-5 h-5 text-red-500" />
      default:
        return <Clock className="w-5 h-5 text-yellow-500" />
    }
  }

  const getHealthLabel = (health: string) => {
    switch (health) {
      case 'healthy':
        return 'Connecte'
      case 'unhealthy':
      case 'error':
        return 'Erreur'
      default:
        return 'Inconnu'
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

      {/* Connectors Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center">
            <Plug className="w-5 h-5 mr-2" />
            Connecteurs configures
          </h2>
          <button
            onClick={async () => {
              setTestingConnectors(true)
              try {
                await runHealthChecks()
                await refetchConnectors()
              } catch (error) {
                console.error('Health check failed:', error)
              } finally {
                setTestingConnectors(false)
              }
            }}
            disabled={testingConnectors}
            className="flex items-center px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 mr-1.5 ${testingConnectors ? 'animate-spin' : ''}`} />
            {testingConnectors ? 'Test en cours...' : 'Tester tout'}
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {connectorsList && connectorsList.map((conn: any) => {
            const Icon = connectorTypeIcons[conn.connector_subtype] || connectorTypeIcons[conn.connector_type] || Database
            const color = connectorTypeColors[conn.connector_subtype] || connectorTypeColors[conn.connector_type] || 'gray'
            return (
              <div
                key={conn.id}
                onClick={() => navigate('/dashboard/connectors')}
                className={`border rounded-lg p-4 cursor-pointer hover:shadow-md transition-shadow ${getHealthBg(conn.last_health_status)}`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center bg-${color}-100`}>
                    <Icon className={`w-5 h-5 text-${color}-600`} />
                  </div>
                  {getHealthIcon(conn.last_health_status)}
                </div>
                <h3 className="font-semibold text-gray-900 text-sm">{conn.display_name}</h3>
                <p className="text-xs text-gray-500 mt-0.5">{conn.connector_subtype?.toUpperCase()}</p>
                <div className="mt-2 flex items-center">
                  <span className={`text-xs font-medium ${getHealthColor(conn.last_health_status)}`}>
                    {getHealthLabel(conn.last_health_status)}
                  </span>
                  {conn.last_health_check && (
                    <span className="text-xs text-gray-400 ml-auto">
                      {new Date(conn.last_health_check).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  )}
                </div>
              </div>
            )
          })}
          {(!connectorsList || connectorsList.length === 0) && (
            <div className="col-span-full text-center py-8 text-gray-500">
              <Plug className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>Aucun connecteur configure</p>
              <button
                onClick={() => navigate('/dashboard/connectors')}
                className="mt-2 text-blue-600 hover:text-blue-700 text-sm"
              >
                Ajouter un connecteur
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Services MidPoint */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4 flex items-center">
          <Server className="w-5 h-5 mr-2" />
          Services MidPoint
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {status?.services_status &&
            Object.entries(status.services_status).map(
              ([name, serviceStatus]: [string, any]) => (
                <div
                  key={name}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <span className="font-medium capitalize text-sm">{name}</span>
                  <div className={`flex items-center ${getHealthColor(serviceStatus)}`}>
                    {getHealthIcon(serviceStatus)}
                    <span className="ml-1.5 capitalize text-sm">{serviceStatus}</span>
                  </div>
                </div>
              )
            )}
        </div>
      </div>

    </div>
  )
}
