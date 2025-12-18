import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getConnectors,
  getConnectorTypes,
  createConnector,
  updateConnector,
  deleteConnector,
  testConnector,
  testConnectorPreview,
} from '../lib/api'
import { format } from 'date-fns'
import {
  Database,
  Users,
  Globe,
  Box,
  Plus,
  X,
  CheckCircle,
  XCircle,
  AlertCircle,
  Clock,
  Settings,
  Trash2,
  Play,
  Power,
  PowerOff,
  Search,
  Filter,
  Shield,
  Server,
  Flame,
  Building,
  Edit,
  Save,
  RefreshCw,
  Eye,
  EyeOff,
} from 'lucide-react'

interface Connector {
  id: string
  name: string
  connector_type: string
  connector_subtype: string
  display_name: string
  description?: string
  is_active: boolean
  configuration: Record<string, any>
  last_health_status: string
  last_health_check?: string
  last_health_error?: string
  created_at: string
  updated_at: string
  created_by?: string
}

interface ConnectorType {
  type: string
  subtype: string
  name: string
  icon: string
  description: string
  config_schema: Record<string, any>
}

const ICON_MAP: Record<string, any> = {
  database: Database,
  users: Users,
  globe: Globe,
  box: Box,
  shield: Shield,
  server: Server,
  flame: Flame,
  building: Building,
}

const TYPE_COLORS: Record<string, string> = {
  sql: 'bg-blue-100 text-blue-700 border-blue-300',
  ldap: 'bg-purple-100 text-purple-700 border-purple-300',
  rest: 'bg-green-100 text-green-700 border-green-300',
  erp: 'bg-amber-100 text-amber-700 border-amber-300',
}

export default function Connectors() {
  const [searchTerm, setSearchTerm] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedConnector, setSelectedConnector] = useState<Connector | null>(null)
  const [createStep, setCreateStep] = useState(1)
  const [selectedType, setSelectedType] = useState<ConnectorType | null>(null)
  const [formData, setFormData] = useState<Record<string, any>>({})
  const [connectorName, setConnectorName] = useState('')
  const [connectorDisplayName, setConnectorDisplayName] = useState('')
  const [connectorDescription, setConnectorDescription] = useState('')
  const [showPasswords, setShowPasswords] = useState<Record<string, boolean>>({})
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)

  const queryClient = useQueryClient()

  const { data: connectors, isLoading } = useQuery({
    queryKey: ['connectors', typeFilter],
    queryFn: () => getConnectors({ connector_type: typeFilter || undefined }),
    refetchInterval: 30000,
  })

  const { data: connectorTypes } = useQuery({
    queryKey: ['connectorTypes'],
    queryFn: getConnectorTypes,
  })

  const createMutation = useMutation({
    mutationFn: createConnector,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['connectors'] })
      handleCloseCreate()
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => updateConnector(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['connectors'] })
      setShowEditModal(false)
      setSelectedConnector(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteConnector,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['connectors'] })
      setShowEditModal(false)
      setSelectedConnector(null)
    },
  })

  const testMutation = useMutation({
    mutationFn: testConnector,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['connectors'] })
      setTestResult(data)
    },
  })

  const testPreviewMutation = useMutation({
    mutationFn: testConnectorPreview,
    onSuccess: (data) => {
      setTestResult(data)
    },
  })

  const handleCloseCreate = () => {
    setShowCreateModal(false)
    setCreateStep(1)
    setSelectedType(null)
    setFormData({})
    setConnectorName('')
    setConnectorDisplayName('')
    setConnectorDescription('')
    setTestResult(null)
    setShowPasswords({})
  }

  const handleSelectType = (type: ConnectorType) => {
    setSelectedType(type)
    setCreateStep(2)
    // Initialize form with defaults from schema
    const defaults: Record<string, any> = {}
    const props = type.config_schema.properties || {}
    Object.entries(props).forEach(([key, value]: [string, any]) => {
      if (value.default !== undefined) {
        defaults[key] = value.default
      }
    })
    setFormData(defaults)
  }

  const handleTestPreview = () => {
    if (!selectedType) return
    testPreviewMutation.mutate({
      connector_type: selectedType.type,
      connector_subtype: selectedType.subtype,
      configuration: formData,
    })
  }

  const handleCreateConnector = () => {
    if (!selectedType) return
    createMutation.mutate({
      name: connectorName,
      connector_type: selectedType.type,
      connector_subtype: selectedType.subtype,
      display_name: connectorDisplayName || connectorName,
      description: connectorDescription,
      configuration: formData,
      is_active: true,
    })
  }

  const handleEditClick = (connector: Connector) => {
    setSelectedConnector(connector)
    setConnectorDisplayName(connector.display_name)
    setConnectorDescription(connector.description || '')
    setFormData(connector.configuration)
    setShowEditModal(true)
    setTestResult(null)
  }

  const handleUpdateConnector = () => {
    if (!selectedConnector) return
    updateMutation.mutate({
      id: selectedConnector.id,
      data: {
        display_name: connectorDisplayName,
        description: connectorDescription,
        configuration: formData,
      },
    })
  }

  const getHealthBadge = (status: string) => {
    const config: Record<string, { color: string; icon: any; text: string }> = {
      healthy: { color: 'badge-success', icon: CheckCircle, text: 'Connecte' },
      unhealthy: { color: 'badge-danger', icon: XCircle, text: 'Erreur' },
      unknown: { color: 'badge-warning', icon: AlertCircle, text: 'Inconnu' },
      testing: { color: 'badge-info', icon: Clock, text: 'Test...' },
    }
    const cfg = config[status] || config.unknown
    const Icon = cfg.icon
    return (
      <span className={`badge ${cfg.color} flex items-center gap-1`}>
        <Icon className="w-3 h-3" />
        {cfg.text}
      </span>
    )
  }

  const getTypeIcon = (iconName: string) => {
    const Icon = ICON_MAP[iconName] || Database
    return Icon
  }

  const renderConfigField = (key: string, schema: any, value: any, onChange: (val: any) => void) => {
    const isPassword = schema.format === 'password'
    const isTextarea = schema.format === 'textarea'
    const isSelect = schema.enum !== undefined
    const isBoolean = schema.type === 'boolean'
    const isNumber = schema.type === 'integer' || schema.type === 'number'

    if (isBoolean) {
      return (
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={value || false}
            onChange={(e) => onChange(e.target.checked)}
            className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-700">{schema.title || key}</span>
        </label>
      )
    }

    if (isSelect) {
      return (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {schema.title || key}
          </label>
          <select
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            className="input"
          >
            <option value="">Selectionner...</option>
            {schema.enum.map((opt: string) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        </div>
      )
    }

    if (isTextarea) {
      return (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {schema.title || key}
          </label>
          <textarea
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            className="input min-h-[100px]"
            placeholder={schema.placeholder}
          />
        </div>
      )
    }

    return (
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {schema.title || key}
        </label>
        <div className="relative">
          <input
            type={isPassword && !showPasswords[key] ? 'password' : isNumber ? 'number' : 'text'}
            value={value || ''}
            onChange={(e) => onChange(isNumber ? parseInt(e.target.value) || 0 : e.target.value)}
            className={`input ${isPassword ? 'pr-10' : ''}`}
            placeholder={schema.placeholder || schema.default?.toString()}
          />
          {isPassword && (
            <button
              type="button"
              onClick={() => setShowPasswords((prev) => ({ ...prev, [key]: !prev[key] }))}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              {showPasswords[key] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          )}
        </div>
      </div>
    )
  }

  const filteredConnectors =
    connectors?.filter(
      (c: Connector) =>
        (c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          c.display_name.toLowerCase().includes(searchTerm.toLowerCase())) &&
        (!typeFilter || c.connector_type === typeFilter)
    ) || []

  // Group connector types by category
  const groupedTypes = connectorTypes?.reduce((acc: Record<string, ConnectorType[]>, type: ConnectorType) => {
    if (!acc[type.type]) acc[type.type] = []
    acc[type.type].push(type)
    return acc
  }, {})

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Connecteurs</h1>
          <p className="text-gray-500 mt-1">
            Gerez les connexions aux bases de donnees et systemes externes
          </p>
        </div>
        <button onClick={() => setShowCreateModal(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-5 h-5" />
          Ajouter un connecteur
        </button>
      </div>

      {/* Modal de création */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl mx-4 overflow-hidden max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b bg-gradient-to-r from-blue-600 to-blue-700 sticky top-0 z-10">
              <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                <Database className="w-6 h-6" />
                {createStep === 1 ? 'Choisir un type de connecteur' : `Configurer ${selectedType?.name}`}
              </h2>
              <button onClick={handleCloseCreate} className="text-white/80 hover:text-white">
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="p-6">
              {createStep === 1 ? (
                /* Step 1: Select connector type */
                <div className="space-y-6">
                  {groupedTypes &&
                    Object.entries(groupedTypes).map(([category, types]) => (
                      <div key={category}>
                        <h3 className="text-sm font-semibold text-gray-500 uppercase mb-3 flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded ${TYPE_COLORS[category]}`}>
                            {category.toUpperCase()}
                          </span>
                        </h3>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                          {(types as ConnectorType[]).map((type) => {
                            const Icon = getTypeIcon(type.icon)
                            return (
                              <button
                                key={type.subtype}
                                onClick={() => handleSelectType(type)}
                                className="p-4 border-2 border-gray-200 rounded-xl hover:border-blue-400 hover:bg-blue-50 transition-all text-left group"
                              >
                                <div className="flex items-center gap-3 mb-2">
                                  <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center group-hover:bg-blue-100">
                                    <Icon className="w-5 h-5 text-gray-600 group-hover:text-blue-600" />
                                  </div>
                                  <div>
                                    <div className="font-semibold text-gray-900">{type.name}</div>
                                  </div>
                                </div>
                                <p className="text-sm text-gray-500">{type.description}</p>
                              </button>
                            )
                          })}
                        </div>
                      </div>
                    ))}
                </div>
              ) : (
                /* Step 2: Configure connector */
                <div className="space-y-6">
                  {/* Basic info */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Nom technique (unique)
                      </label>
                      <input
                        type="text"
                        value={connectorName}
                        onChange={(e) => setConnectorName(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, '_'))}
                        className="input"
                        placeholder="ex: postgres_prod"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Nom d'affichage
                      </label>
                      <input
                        type="text"
                        value={connectorDisplayName}
                        onChange={(e) => setConnectorDisplayName(e.target.value)}
                        className="input"
                        placeholder="ex: PostgreSQL Production"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Description (optionnel)
                    </label>
                    <input
                      type="text"
                      value={connectorDescription}
                      onChange={(e) => setConnectorDescription(e.target.value)}
                      className="input"
                      placeholder="Description du connecteur..."
                    />
                  </div>

                  {/* Configuration fields */}
                  <div className="border-t pt-4">
                    <h3 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
                      <Settings className="w-4 h-4" />
                      Configuration {selectedType?.name}
                    </h3>
                    <div className="space-y-4">
                      {selectedType?.config_schema.properties &&
                        Object.entries(selectedType.config_schema.properties).map(
                          ([key, schema]: [string, any]) =>
                            renderConfigField(key, schema, formData[key], (val) =>
                              setFormData((prev) => ({ ...prev, [key]: val }))
                            )
                        )}
                    </div>
                  </div>

                  {/* Test result */}
                  {testResult && (
                    <div
                      className={`p-4 rounded-lg border ${
                        testResult.success
                          ? 'bg-green-50 border-green-200 text-green-700'
                          : 'bg-red-50 border-red-200 text-red-700'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        {testResult.success ? (
                          <CheckCircle className="w-5 h-5" />
                        ) : (
                          <XCircle className="w-5 h-5" />
                        )}
                        <span className="font-medium">
                          {testResult.success ? 'Connexion reussie !' : 'Echec de connexion'}
                        </span>
                      </div>
                      <p className="mt-1 text-sm">{testResult.message}</p>
                    </div>
                  )}

                  {createMutation.isError && (
                    <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                      Erreur: {(createMutation.error as any)?.response?.data?.detail || 'Echec de la creation'}
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="flex justify-between gap-3 px-6 py-4 bg-gray-50 border-t sticky bottom-0">
              {createStep === 1 ? (
                <button onClick={handleCloseCreate} className="btn-secondary">
                  Annuler
                </button>
              ) : (
                <>
                  <button
                    onClick={() => {
                      setCreateStep(1)
                      setTestResult(null)
                    }}
                    className="btn-secondary"
                  >
                    Retour
                  </button>
                  <div className="flex gap-3">
                    <button
                      onClick={handleTestPreview}
                      disabled={testPreviewMutation.isPending}
                      className="btn-secondary flex items-center gap-2"
                    >
                      {testPreviewMutation.isPending ? (
                        <RefreshCw className="w-4 h-4 animate-spin" />
                      ) : (
                        <Play className="w-4 h-4" />
                      )}
                      Tester
                    </button>
                    <button
                      onClick={handleCreateConnector}
                      disabled={createMutation.isPending || !connectorName}
                      className="btn-primary flex items-center gap-2 disabled:opacity-50"
                    >
                      {createMutation.isPending ? (
                        <Clock className="w-4 h-4 animate-spin" />
                      ) : (
                        <Plus className="w-4 h-4" />
                      )}
                      Creer le connecteur
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal d'édition */}
      {showEditModal && selectedConnector && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl mx-4 overflow-hidden max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b bg-gradient-to-r from-amber-500 to-amber-600 sticky top-0 z-10">
              <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                <Edit className="w-6 h-6" />
                Modifier {selectedConnector.display_name}
              </h2>
              <button
                onClick={() => {
                  setShowEditModal(false)
                  setSelectedConnector(null)
                }}
                className="text-white/80 hover:text-white"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Info */}
              <div className="p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <span className={`px-2 py-0.5 rounded ${TYPE_COLORS[selectedConnector.connector_type]}`}>
                    {selectedConnector.connector_type.toUpperCase()}
                  </span>
                  <span className="text-gray-400">/</span>
                  <span>{selectedConnector.connector_subtype}</span>
                  <span className="text-gray-400">|</span>
                  <code className="bg-gray-200 px-1 rounded">{selectedConnector.name}</code>
                </div>
              </div>

              {/* Edit fields */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nom d'affichage
                  </label>
                  <input
                    type="text"
                    value={connectorDisplayName}
                    onChange={(e) => setConnectorDisplayName(e.target.value)}
                    className="input"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <input
                    type="text"
                    value={connectorDescription}
                    onChange={(e) => setConnectorDescription(e.target.value)}
                    className="input"
                  />
                </div>
              </div>

              {/* Configuration */}
              <div className="border-t pt-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
                  <Settings className="w-4 h-4" />
                  Configuration
                </h3>
                <div className="space-y-4">
                  {Object.entries(formData).map(([key, value]) => (
                    <div key={key}>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {key}
                      </label>
                      <div className="relative">
                        <input
                          type={
                            typeof value === 'string' && value.includes('*')
                              ? 'text'
                              : key.toLowerCase().includes('password') ||
                                key.toLowerCase().includes('secret') ||
                                key.toLowerCase().includes('token')
                              ? showPasswords[key]
                                ? 'text'
                                : 'password'
                              : 'text'
                          }
                          value={value?.toString() || ''}
                          onChange={(e) =>
                            setFormData((prev) => ({
                              ...prev,
                              [key]:
                                typeof value === 'number' ? parseInt(e.target.value) || 0 : e.target.value,
                            }))
                          }
                          className="input pr-10"
                        />
                        {(key.toLowerCase().includes('password') ||
                          key.toLowerCase().includes('secret') ||
                          key.toLowerCase().includes('token')) && (
                          <button
                            type="button"
                            onClick={() => setShowPasswords((prev) => ({ ...prev, [key]: !prev[key] }))}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                          >
                            {showPasswords[key] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Test result */}
              {testResult && (
                <div
                  className={`p-4 rounded-lg border ${
                    testResult.success
                      ? 'bg-green-50 border-green-200 text-green-700'
                      : 'bg-red-50 border-red-200 text-red-700'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {testResult.success ? <CheckCircle className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
                    <span className="font-medium">
                      {testResult.success ? 'Connexion reussie !' : 'Echec de connexion'}
                    </span>
                  </div>
                  <p className="mt-1 text-sm">{testResult.message}</p>
                </div>
              )}

              {updateMutation.isError && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                  Erreur: {(updateMutation.error as any)?.response?.data?.detail || 'Echec de la modification'}
                </div>
              )}
            </div>

            <div className="flex justify-between gap-3 px-6 py-4 bg-gray-50 border-t sticky bottom-0">
              <button
                onClick={() => {
                  if (confirm('Etes-vous sur de vouloir supprimer ce connecteur ?')) {
                    deleteMutation.mutate(selectedConnector.id)
                  }
                }}
                disabled={deleteMutation.isPending}
                className="btn-danger flex items-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                Supprimer
              </button>
              <div className="flex gap-3">
                <button
                  onClick={() => testMutation.mutate(selectedConnector.id)}
                  disabled={testMutation.isPending}
                  className="btn-secondary flex items-center gap-2"
                >
                  {testMutation.isPending ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <Play className="w-4 h-4" />
                  )}
                  Tester
                </button>
                <button
                  onClick={handleUpdateConnector}
                  disabled={updateMutation.isPending}
                  className="btn-primary flex items-center gap-2 disabled:opacity-50"
                >
                  {updateMutation.isPending ? (
                    <Clock className="w-4 h-4 animate-spin" />
                  ) : (
                    <Save className="w-4 h-4" />
                  )}
                  Enregistrer
                </button>
              </div>
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
              placeholder="Rechercher un connecteur..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input pl-10"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-400" />
            <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} className="input w-48">
              <option value="">Tous les types</option>
              <option value="sql">SQL</option>
              <option value="ldap">LDAP</option>
              <option value="rest">REST API</option>
              <option value="erp">ERP</option>
            </select>
          </div>
        </div>
      </div>

      {/* Connectors grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {isLoading ? (
          <div className="col-span-full text-center py-12 text-gray-500">Chargement...</div>
        ) : filteredConnectors.length === 0 ? (
          <div className="col-span-full text-center py-12">
            <Database className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">Aucun connecteur configure</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-4 text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1 mx-auto"
            >
              <Plus className="w-4 h-4" />
              Ajouter votre premier connecteur
            </button>
          </div>
        ) : (
          filteredConnectors.map((connector: Connector) => {
            const typeInfo = connectorTypes?.find(
              (t: ConnectorType) => t.subtype === connector.connector_subtype
            )
            const Icon = getTypeIcon(typeInfo?.icon || 'database')
            return (
              <div
                key={connector.id}
                className="card hover:shadow-lg transition-shadow cursor-pointer group"
                onClick={() => handleEditClick(connector)}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                        connector.is_active ? 'bg-blue-100' : 'bg-gray-100'
                      }`}
                    >
                      <Icon
                        className={`w-6 h-6 ${connector.is_active ? 'text-blue-600' : 'text-gray-400'}`}
                      />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                        {connector.display_name}
                      </h3>
                      <p className="text-sm text-gray-500">{connector.name}</p>
                    </div>
                  </div>
                  {getHealthBadge(connector.last_health_status)}
                </div>

                <div className="flex items-center gap-2 mb-3">
                  <span className={`px-2 py-0.5 text-xs rounded ${TYPE_COLORS[connector.connector_type]}`}>
                    {connector.connector_type.toUpperCase()}
                  </span>
                  <span className="text-xs text-gray-400">{typeInfo?.name || connector.connector_subtype}</span>
                </div>

                {connector.description && (
                  <p className="text-sm text-gray-500 mb-3 line-clamp-2">{connector.description}</p>
                )}

                <div className="flex items-center justify-between text-xs text-gray-400 pt-3 border-t">
                  <div className="flex items-center gap-1">
                    {connector.is_active ? (
                      <>
                        <Power className="w-3 h-3 text-green-500" />
                        <span className="text-green-600">Actif</span>
                      </>
                    ) : (
                      <>
                        <PowerOff className="w-3 h-3 text-gray-400" />
                        <span>Inactif</span>
                      </>
                    )}
                  </div>
                  {connector.last_health_check && (
                    <span>Verifie {format(new Date(connector.last_health_check), 'dd/MM HH:mm')}</span>
                  )}
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
