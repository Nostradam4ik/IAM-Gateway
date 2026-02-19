/**
 * LiveComparison.tsx - Page de comparaison temps reel entre systemes.
 *
 * 4 onglets :
 *   1. Odoo : affiche les contacts, entreprises et utilisateurs Odoo en direct
 *   2. Recherche : recherche cross-reference d'un utilisateur dans LDAP/SQL/Odoo
 *   3. Sync MidPoint : synchronisation Odoo -> MidPoint
 *      - Mode direct : creation immediate des comptes MidPoint
 *      - Mode approbation : workflow multi-niveaux (Manager -> RH -> IT)
 *      - Selection individuelle ou en masse des employes a synchroniser
 *   4. Planification : configuration des synchronisations automatiques
 *      - Presets rapides : Jours ouvrables (8h/12h/18h), Nocturne (2h), Horaire
 *      - Jobs personnalises : heure fixe, intervalle, ou multi-heures (grille 24h)
 *      - Gestion des jobs : activer/desactiver, executer maintenant, supprimer
 *      - Historique des synchronisations avec statistiques
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getUserCrossReference,
  getOdooContacts,
  checkSystemsHealth,
  compareOdooMidpoint,
  syncOdooToMidpoint,
  syncOdooToMidpointWithApproval,
  getScheduledJobs,
  createDailySync,
  createIntervalSync,
  toggleScheduledJob,
  runJobNow,
  deleteScheduledJob,
  getSyncHistory,
  createWorkdaySync,
  createNightlySync,
  createHourlySync,
} from '../lib/api'
import {
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Search,
  Users,
  Building2,
  Zap,
  Eye,
  Upload,
  Server,
  Clock,
  Calendar,
  Play,
  Pause,
  Trash2,
  Plus,
  History,
  Shield,
  Mail,
  Database,
} from 'lucide-react'

export default function LiveComparison() {
  const queryClient = useQueryClient()
  const [searchQuery, setSearchQuery] = useState('')
  const [activeTab, setActiveTab] = useState<'odoo' | 'search' | 'sync' | 'schedule'>('odoo')
  const [selectedEmployees, setSelectedEmployees] = useState<number[]>([])
  const [syncWithApproval, setSyncWithApproval] = useState(false)
  const [managerEmail, setManagerEmail] = useState('')
  const [workflowType, setWorkflowType] = useState<'full' | 'manager_only' | 'rh_it'>('full')
  const [showAddJobModal, setShowAddJobModal] = useState(false)
  const [newJobType, setNewJobType] = useState<'daily' | 'interval' | 'multi'>('daily')
  const [newJobConfig, setNewJobConfig] = useState({
    job_id: '',
    hour: 8,
    minute: 0,
    hours: 1,
    minutes: 0,
  })
  const [selectedHours, setSelectedHours] = useState<number[]>([8, 12, 18])

  // Health check query
  const { data: health } = useQuery({
    queryKey: ['systemsHealth'],
    queryFn: checkSystemsHealth,
    refetchInterval: 60000,
  })

  // Odoo contacts
  const { data: odooData, isLoading: odooLoading } = useQuery({
    queryKey: ['odooContacts'],
    queryFn: () => getOdooContacts(50),
    enabled: activeTab === 'odoo',
  })

  // User search
  const searchMutation = useMutation({
    mutationFn: (identifier: string) => getUserCrossReference(identifier),
  })

  // Odoo-MidPoint comparison
  const { data: odooMidpointComparison, isLoading: odooMidpointLoading, refetch: refetchOdooMidpoint } = useQuery({
    queryKey: ['odooMidpointCompare'],
    queryFn: compareOdooMidpoint,
    enabled: activeTab === 'sync',
  })

  // Sync mutation (direct)
  const syncMutation = useMutation({
    mutationFn: (employeeIds?: number[]) => syncOdooToMidpoint(employeeIds),
    onSuccess: () => {
      refetchOdooMidpoint()
      setSelectedEmployees([])
    },
  })

  // Sync mutation with approval workflow
  const syncWithApprovalMutation = useMutation({
    mutationFn: (data: { employee_ids?: number[], manager_email: string, workflow_type: 'full' | 'manager_only' | 'rh_it' }) =>
      syncOdooToMidpointWithApproval(data),
    onSuccess: () => {
      refetchOdooMidpoint()
      setSelectedEmployees([])
      setManagerEmail('')
      setSyncWithApproval(false)
    },
  })

  // Scheduled jobs
  const { data: scheduledJobs, isLoading: jobsLoading, refetch: refetchJobs } = useQuery({
    queryKey: ['scheduledJobs'],
    queryFn: getScheduledJobs,
    enabled: activeTab === 'schedule',
    refetchInterval: 10000,
  })

  // Sync history
  const { data: syncHistory } = useQuery({
    queryKey: ['syncHistory'],
    queryFn: () => getSyncHistory(20),
    enabled: activeTab === 'schedule',
  })

  // Create daily job
  const createDailyMutation = useMutation({
    mutationFn: createDailySync,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduledJobs'] })
      setShowAddJobModal(false)
      setNewJobConfig({ job_id: '', hour: 8, minute: 0, hours: 1, minutes: 0 })
    },
  })

  // Create interval job
  const createIntervalMutation = useMutation({
    mutationFn: createIntervalSync,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduledJobs'] })
      setShowAddJobModal(false)
      setNewJobConfig({ job_id: '', hour: 8, minute: 0, hours: 1, minutes: 0 })
    },
  })

  // Toggle job
  const toggleJobMutation = useMutation({
    mutationFn: ({ jobId, enabled }: { jobId: string; enabled: boolean }) => toggleScheduledJob(jobId, enabled),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['scheduledJobs'] }),
  })

  // Run job now
  const runNowMutation = useMutation({
    mutationFn: runJobNow,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduledJobs'] })
      queryClient.invalidateQueries({ queryKey: ['syncHistory'] })
    },
  })

  // Delete job
  const deleteJobMutation = useMutation({
    mutationFn: deleteScheduledJob,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['scheduledJobs'] }),
  })

  // Preset mutations
  const workdayPresetMutation = useMutation({
    mutationFn: createWorkdaySync,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['scheduledJobs'] }),
  })

  const nightlyPresetMutation = useMutation({
    mutationFn: () => createNightlySync(2),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['scheduledJobs'] }),
  })

  const hourlyPresetMutation = useMutation({
    mutationFn: createHourlySync,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['scheduledJobs'] }),
  })

  const handleCreateJob = () => {
    if (newJobType === 'multi') {
      // Create multiple daily jobs for each selected hour
      selectedHours.forEach((hour) => {
        const jobId = `sync-${hour}h`
        createDailyMutation.mutate({
          job_id: jobId,
          hour: hour,
          minute: 0,
        })
      })
      setShowAddJobModal(false)
      return
    }

    if (!newJobConfig.job_id.trim()) return

    if (newJobType === 'daily') {
      createDailyMutation.mutate({
        job_id: newJobConfig.job_id,
        hour: newJobConfig.hour,
        minute: newJobConfig.minute,
      })
    } else {
      createIntervalMutation.mutate({
        job_id: newJobConfig.job_id,
        hours: newJobConfig.hours,
        minutes: newJobConfig.minutes,
      })
    }
  }

  const toggleHourSelection = (hour: number) => {
    if (selectedHours.includes(hour)) {
      setSelectedHours(selectedHours.filter(h => h !== hour))
    } else {
      setSelectedHours([...selectedHours, hour].sort((a, b) => a - b))
    }
  }

  const handleSearch = () => {
    if (searchQuery.trim()) {
      searchMutation.mutate(searchQuery.trim())
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
      case 'healthy':
        return 'text-green-600 bg-green-100'
      case 'error':
      case 'unhealthy':
      case 'critical':
        return 'text-red-600 bg-red-100'
      case 'degraded':
        return 'text-yellow-600 bg-yellow-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const getSyncStatusBadge = (status: string) => {
    switch (status) {
      case 'fully_synced':
      case 'synced':
        return (
          <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700 flex items-center gap-1">
            <CheckCircle className="w-3 h-3" />
            Synchronise
          </span>
        )
      case 'partially_synced':
      case 'partial':
        return (
          <span className="px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-700 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" />
            Partiel
          </span>
        )
      case 'isolated':
        return (
          <span className="px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-700 flex items-center gap-1">
            <XCircle className="w-3 h-3" />
            Isole
          </span>
        )
      case 'not_found':
        return (
          <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700 flex items-center gap-1">
            <XCircle className="w-3 h-3" />
            Non trouve
          </span>
        )
      default:
        return <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700">{status}</span>
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Zap className="w-7 h-7 text-yellow-500" />
            Comparaison Temps Reel
          </h1>
          <p className="text-gray-500 mt-1">
            Visualisez et comparez les donnees entre tous les systemes instantanement
          </p>
        </div>

        {/* Health Status */}
        {health && (
          <div className={`px-4 py-2 rounded-lg ${getStatusColor(health.overall_status)}`}>
            <span className="text-sm font-medium">
              Etat: {health.overall_status === 'healthy' ? 'Tous systemes OK' :
                    health.overall_status === 'degraded' ? 'Certains problemes' : 'Critique'}
            </span>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-4">
          {[
            { id: 'odoo', label: 'Odoo', icon: Building2 },
            { id: 'search', label: 'Recherche', icon: Search },
            { id: 'sync', label: 'Sync MidPoint', icon: Upload },
            { id: 'schedule', label: 'Planification', icon: Calendar },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Odoo Tab */}
      {activeTab === 'odoo' && (
        <div className="space-y-6">
          <div className="flex items-center gap-4">
            <Building2 className="w-8 h-8 text-purple-500" />
            <div>
              <h2 className="text-lg font-semibold">Donnees Odoo en direct</h2>
              <p className="text-gray-500 text-sm">Contacts, entreprises et utilisateurs Odoo</p>
            </div>
          </div>

          {odooLoading ? (
            <div className="text-center py-8 text-gray-500">Chargement des donnees Odoo...</div>
          ) : odooData ? (
            <>
              {/* Odoo Summary */}
              <div className="grid grid-cols-3 gap-4">
                <div className="card text-center">
                  <Users className="w-8 h-8 text-purple-500 mx-auto mb-2" />
                  <div className="text-2xl font-bold">{odooData.summary?.total_contacts || 0}</div>
                  <p className="text-sm text-gray-500">Contacts</p>
                </div>
                <div className="card text-center">
                  <Building2 className="w-8 h-8 text-blue-500 mx-auto mb-2" />
                  <div className="text-2xl font-bold">{odooData.summary?.total_companies || 0}</div>
                  <p className="text-sm text-gray-500">Entreprises</p>
                </div>
                <div className="card text-center">
                  <Eye className="w-8 h-8 text-green-500 mx-auto mb-2" />
                  <div className="text-2xl font-bold">{odooData.summary?.total_users || 0}</div>
                  <p className="text-sm text-gray-500">Utilisateurs</p>
                </div>
              </div>

              {/* Users Table */}
              <div className="card">
                <h3 className="font-semibold mb-4">Utilisateurs Odoo</h3>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="bg-gray-50">
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">ID</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Nom</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Login</th>
                        <th className="px-4 py-3 text-center text-sm font-medium text-gray-500">Actif</th>
                      </tr>
                    </thead>
                    <tbody>
                      {odooData.users?.data?.map((u: any) => (
                        <tr key={u.id} className="border-t hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm">{u.id}</td>
                          <td className="px-4 py-3 text-sm font-medium">{u.name}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">{u.login}</td>
                          <td className="px-4 py-3 text-center">
                            {u.active ? (
                              <CheckCircle className="w-5 h-5 text-green-500 mx-auto" />
                            ) : (
                              <XCircle className="w-5 h-5 text-red-500 mx-auto" />
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Contacts Table */}
              <div className="card">
                <h3 className="font-semibold mb-4">Derniers contacts ({odooData.contacts?.count})</h3>
                <div className="overflow-x-auto max-h-96">
                  <table className="w-full">
                    <thead className="sticky top-0 bg-white">
                      <tr className="bg-gray-50">
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Nom</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Email</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Ville</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Fonction</th>
                      </tr>
                    </thead>
                    <tbody>
                      {odooData.contacts?.data?.slice(0, 30).map((c: any) => (
                        <tr key={c.id} className="border-t hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm font-medium">{c.name}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">{c.email || '-'}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">{c.city || '-'}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">{c.function || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : null}
        </div>
      )}

      {/* Search Tab */}
      {activeTab === 'search' && (
        <div className="space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Recherche d'utilisateur</h2>
            <div className="flex gap-4">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Email, username ou identifiant..."
                className="input flex-1"
              />
              <button
                onClick={handleSearch}
                disabled={searchMutation.isPending}
                className="btn-primary flex items-center gap-2"
              >
                {searchMutation.isPending ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Search className="w-4 h-4" />
                )}
                Rechercher
              </button>
            </div>
          </div>

          {/* Search Result */}
          {searchMutation.data && (
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold">Resultat pour: {searchMutation.data.identifier}</h3>
                {getSyncStatusBadge(searchMutation.data.sync_status)}
              </div>

              <p className="text-gray-600 mb-4">{searchMutation.data.message}</p>

              {searchMutation.data.found_in?.length > 0 && (
                <div className="space-y-4">
                  <p className="text-sm text-gray-500">
                    Trouve dans: <span className="font-medium">{searchMutation.data.found_in.join(', ')}</span>
                  </p>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* LDAP Data */}
                    <div className={`p-4 rounded-lg border ${searchMutation.data.data.ldap ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}>
                      <h4 className="font-medium mb-2 flex items-center gap-2">
                        <Database className="w-4 h-4" />
                        LDAP
                      </h4>
                      {searchMutation.data.data.ldap ? (
                        <div className="text-sm space-y-1">
                          <p><span className="text-gray-500">UID:</span> {searchMutation.data.data.ldap.uid}</p>
                          <p><span className="text-gray-500">CN:</span> {searchMutation.data.data.ldap.cn}</p>
                          <p><span className="text-gray-500">Mail:</span> {searchMutation.data.data.ldap.mail}</p>
                        </div>
                      ) : (
                        <p className="text-sm text-gray-400">Non trouve</p>
                      )}
                    </div>

                    {/* SQL Data */}
                    <div className={`p-4 rounded-lg border ${searchMutation.data.data.sql ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}>
                      <h4 className="font-medium mb-2 flex items-center gap-2">
                        <Database className="w-4 h-4" />
                        SQL
                      </h4>
                      {searchMutation.data.data.sql ? (
                        <div className="text-sm space-y-1">
                          <p><span className="text-gray-500">Username:</span> {searchMutation.data.data.sql.username}</p>
                          <p><span className="text-gray-500">Email:</span> {searchMutation.data.data.sql.email}</p>
                          <p><span className="text-gray-500">Dept:</span> {searchMutation.data.data.sql.department}</p>
                        </div>
                      ) : (
                        <p className="text-sm text-gray-400">Non trouve</p>
                      )}
                    </div>

                    {/* Odoo Data */}
                    <div className={`p-4 rounded-lg border ${searchMutation.data.data.odoo ? 'bg-purple-50 border-purple-200' : 'bg-gray-50 border-gray-200'}`}>
                      <h4 className="font-medium mb-2 flex items-center gap-2">
                        <Building2 className="w-4 h-4" />
                        Odoo
                      </h4>
                      {searchMutation.data.data.odoo ? (
                        <div className="text-sm space-y-1">
                          <p><span className="text-gray-500">ID:</span> {searchMutation.data.data.odoo.id}</p>
                          <p><span className="text-gray-500">Name:</span> {searchMutation.data.data.odoo.name}</p>
                          <p><span className="text-gray-500">Login:</span> {searchMutation.data.data.odoo.login}</p>
                        </div>
                      ) : (
                        <p className="text-sm text-gray-400">Non trouve</p>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {searchMutation.isError && (
            <div className="card bg-red-50 border-red-200">
              <p className="text-red-600">Erreur lors de la recherche</p>
            </div>
          )}
        </div>
      )}

      {/* Sync Tab - Odoo to MidPoint */}
      {activeTab === 'sync' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Server className="w-8 h-8 text-blue-600" />
              <div>
                <h2 className="text-lg font-semibold">LiveSync Odoo → MidPoint</h2>
                <p className="text-gray-500 text-sm">Synchronisez les employes Odoo vers MidPoint</p>
              </div>
            </div>
            <button
              onClick={() => refetchOdooMidpoint()}
              disabled={odooMidpointLoading}
              className="btn-secondary flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${odooMidpointLoading ? 'animate-spin' : ''}`} />
              Actualiser
            </button>
          </div>

          {/* Mode de synchronisation */}
          <div className="card border-2 border-blue-200 bg-blue-50/30">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <Shield className="w-5 h-5 text-blue-600" />
              Mode de Synchronisation
            </h3>

            <div className="space-y-4">
              {/* Toggle approbation */}
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="radio"
                    name="syncMode"
                    checked={!syncWithApproval}
                    onChange={() => setSyncWithApproval(false)}
                    className="w-4 h-4 text-blue-600"
                  />
                  <div>
                    <span className="font-medium">Synchronisation Directe</span>
                    <p className="text-sm text-gray-500">Creation immediate des comptes MidPoint</p>
                  </div>
                </label>
              </div>

              <div className="flex items-center gap-4">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="radio"
                    name="syncMode"
                    checked={syncWithApproval}
                    onChange={() => setSyncWithApproval(true)}
                    className="w-4 h-4 text-blue-600"
                  />
                  <div>
                    <span className="font-medium">Avec Workflow d'Approbation</span>
                    <p className="text-sm text-gray-500">Approbation multi-niveaux avant creation</p>
                  </div>
                </label>
              </div>

              {/* Options d'approbation */}
              {syncWithApproval && (
                <div className="mt-4 p-4 bg-white rounded-lg border border-blue-200 space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      <Mail className="w-4 h-4 inline mr-1" />
                      Email du Manager (premier approbateur)
                    </label>
                    <input
                      type="email"
                      value={managerEmail}
                      onChange={(e) => setManagerEmail(e.target.value)}
                      placeholder="manager@entreprise.com"
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Type de workflow
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      <button
                        onClick={() => setWorkflowType('full')}
                        className={`p-3 rounded-lg border text-sm transition-colors ${
                          workflowType === 'full'
                            ? 'bg-blue-500 text-white border-blue-500'
                            : 'bg-white text-gray-700 border-gray-300 hover:border-blue-300'
                        }`}
                      >
                        <div className="font-medium">Complet</div>
                        <div className="text-xs opacity-75 mt-1">Manager → RH → IT</div>
                      </button>
                      <button
                        onClick={() => setWorkflowType('manager_only')}
                        className={`p-3 rounded-lg border text-sm transition-colors ${
                          workflowType === 'manager_only'
                            ? 'bg-blue-500 text-white border-blue-500'
                            : 'bg-white text-gray-700 border-gray-300 hover:border-blue-300'
                        }`}
                      >
                        <div className="font-medium">Manager seul</div>
                        <div className="text-xs opacity-75 mt-1">1 niveau</div>
                      </button>
                      <button
                        onClick={() => setWorkflowType('rh_it')}
                        className={`p-3 rounded-lg border text-sm transition-colors ${
                          workflowType === 'rh_it'
                            ? 'bg-blue-500 text-white border-blue-500'
                            : 'bg-white text-gray-700 border-gray-300 hover:border-blue-300'
                        }`}
                      >
                        <div className="font-medium">RH + IT</div>
                        <div className="text-xs opacity-75 mt-1">2 niveaux</div>
                      </button>
                    </div>
                  </div>

                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-sm">
                    <p className="text-yellow-800">
                      <strong>Info:</strong> Les approbateurs recevront un email avec un lien securise pour approuver ou rejeter la demande.
                      Le compte MidPoint sera cree automatiquement apres approbation complete.
                    </p>
                  </div>
                </div>
              )}

              {/* Boutons d'action */}
              <div className="flex justify-end gap-2 pt-4 border-t">
                {syncWithApproval ? (
                  <button
                    onClick={() => syncWithApprovalMutation.mutate({
                      employee_ids: selectedEmployees.length > 0 ? selectedEmployees : undefined,
                      manager_email: managerEmail,
                      workflow_type: workflowType
                    })}
                    disabled={syncWithApprovalMutation.isPending || !managerEmail.trim()}
                    className="btn-primary flex items-center gap-2"
                  >
                    {syncWithApprovalMutation.isPending ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <Shield className="w-4 h-4" />
                    )}
                    {selectedEmployees.length > 0
                      ? `Demander approbation (${selectedEmployees.length})`
                      : 'Demander approbation pour tous'}
                  </button>
                ) : (
                  <button
                    onClick={() => syncMutation.mutate(selectedEmployees.length > 0 ? selectedEmployees : undefined)}
                    disabled={syncMutation.isPending}
                    className="btn-primary flex items-center gap-2"
                  >
                    {syncMutation.isPending ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <Upload className="w-4 h-4" />
                    )}
                    {selectedEmployees.length > 0 ? `Synchroniser (${selectedEmployees.length})` : 'Synchroniser tout'}
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Sync Result - Direct */}
          {syncMutation.data && (
            <div className="card bg-green-50 border-green-200">
              <h3 className="font-semibold text-green-800 mb-2">Synchronisation terminee</h3>
              <div className="grid grid-cols-4 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold text-gray-700">{syncMutation.data.summary?.total_employees || 0}</div>
                  <p className="text-xs text-gray-500">Total</p>
                </div>
                <div>
                  <div className="text-2xl font-bold text-green-600">{syncMutation.data.summary?.synced || 0}</div>
                  <p className="text-xs text-gray-500">Crees</p>
                </div>
                <div>
                  <div className="text-2xl font-bold text-yellow-600">{syncMutation.data.summary?.skipped || 0}</div>
                  <p className="text-xs text-gray-500">Ignores</p>
                </div>
                <div>
                  <div className="text-2xl font-bold text-red-600">{syncMutation.data.summary?.errors || 0}</div>
                  <p className="text-xs text-gray-500">Erreurs</p>
                </div>
              </div>
              {syncMutation.data.results?.length > 0 && (
                <div className="mt-4 pt-4 border-t border-green-200 max-h-40 overflow-y-auto">
                  {syncMutation.data.results.map((r: any, i: number) => (
                    <div key={i} className={`text-sm py-1 ${r.status === 'created' ? 'text-green-700' : r.status === 'error' ? 'text-red-700' : 'text-yellow-700'}`}>
                      {r.name}: {r.status} {r.error && `- ${r.error}`}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Sync Result - With Approval */}
          {syncWithApprovalMutation.data && (
            <div className="card bg-blue-50 border-blue-200">
              <h3 className="font-semibold text-blue-800 mb-2 flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Workflows d'approbation crees
              </h3>
              <div className="grid grid-cols-3 gap-4 text-center mb-4">
                <div>
                  <div className="text-2xl font-bold text-gray-700">{syncWithApprovalMutation.data.summary?.total || 0}</div>
                  <p className="text-xs text-gray-500">Total</p>
                </div>
                <div>
                  <div className="text-2xl font-bold text-blue-600">{syncWithApprovalMutation.data.summary?.workflows_created || 0}</div>
                  <p className="text-xs text-gray-500">Workflows crees</p>
                </div>
                <div>
                  <div className="text-2xl font-bold text-red-600">{syncWithApprovalMutation.data.summary?.errors || 0}</div>
                  <p className="text-xs text-gray-500">Erreurs</p>
                </div>
              </div>
              <div className="bg-white rounded-lg p-3 border border-blue-200">
                <p className="text-sm text-blue-800">
                  <strong>Prochaine etape:</strong> Un email a ete envoye a <strong>{syncWithApprovalMutation.data.summary?.first_approver}</strong> pour
                  demarrer le processus d'approbation. Suivez les workflows dans l'onglet <strong>Workflows</strong>.
                </p>
              </div>
              {syncWithApprovalMutation.data.workflows?.length > 0 && (
                <div className="mt-4 pt-4 border-t border-blue-200 max-h-40 overflow-y-auto">
                  {syncWithApprovalMutation.data.workflows.map((w: any, i: number) => (
                    <div key={i} className="text-sm py-1 text-blue-700 flex items-center gap-2">
                      <Shield className="w-3 h-3" />
                      {w.employee_name}: Workflow #{w.workflow_id?.substring(0, 8)}... ({w.levels} niveaux)
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {odooMidpointLoading ? (
            <div className="text-center py-8 text-gray-500">Chargement de la comparaison...</div>
          ) : odooMidpointComparison ? (
            <>
              {/* Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                <div className="card text-center">
                  <Building2 className="w-6 h-6 text-purple-500 mx-auto mb-2" />
                  <div className="text-2xl font-bold text-gray-700">{odooMidpointComparison.summary?.odoo_employees || 0}</div>
                  <p className="text-xs text-gray-500">Employes Odoo</p>
                </div>
                <div className="card text-center">
                  <Server className="w-6 h-6 text-blue-500 mx-auto mb-2" />
                  <div className="text-2xl font-bold text-gray-700">{odooMidpointComparison.summary?.midpoint_users || 0}</div>
                  <p className="text-xs text-gray-500">Users MidPoint</p>
                </div>
                <div className="card text-center bg-green-50">
                  <CheckCircle className="w-6 h-6 text-green-500 mx-auto mb-2" />
                  <div className="text-2xl font-bold text-green-600">{odooMidpointComparison.summary?.synced || 0}</div>
                  <p className="text-xs text-gray-500">Deja synchronises</p>
                </div>
                <div className="card text-center bg-orange-50 border-orange-200">
                  <Upload className="w-6 h-6 text-orange-500 mx-auto mb-2" />
                  <div className="text-2xl font-bold text-orange-600">{odooMidpointComparison.summary?.to_sync_from_odoo || 0}</div>
                  <p className="text-xs text-gray-500">A synchroniser</p>
                </div>
                <div className="card text-center">
                  <AlertTriangle className="w-6 h-6 text-gray-400 mx-auto mb-2" />
                  <div className="text-2xl font-bold text-gray-500">{odooMidpointComparison.summary?.midpoint_only || 0}</div>
                  <p className="text-xs text-gray-500">MidPoint seulement</p>
                </div>
              </div>

              {/* Employees to Sync */}
              {odooMidpointComparison.to_sync?.length > 0 && (
                <div className="card">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold flex items-center gap-2">
                      <Upload className="w-5 h-5 text-orange-500" />
                      Employes a synchroniser vers MidPoint ({odooMidpointComparison.to_sync.length})
                    </h3>
                    <button
                      onClick={() => {
                        if (selectedEmployees.length === odooMidpointComparison.to_sync.length) {
                          setSelectedEmployees([])
                        } else {
                          setSelectedEmployees(odooMidpointComparison.to_sync.map((e: any) => e.id))
                        }
                      }}
                      className="text-sm text-blue-600 hover:underline"
                    >
                      {selectedEmployees.length === odooMidpointComparison.to_sync.length ? 'Desélectionner tout' : 'Selectionner tout'}
                    </button>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="bg-gray-50">
                          <th className="px-4 py-3 text-left text-sm font-medium text-gray-500 w-10">
                            <input
                              type="checkbox"
                              checked={selectedEmployees.length === odooMidpointComparison.to_sync.length && selectedEmployees.length > 0}
                              onChange={() => {
                                if (selectedEmployees.length === odooMidpointComparison.to_sync.length) {
                                  setSelectedEmployees([])
                                } else {
                                  setSelectedEmployees(odooMidpointComparison.to_sync.map((e: any) => e.id))
                                }
                              }}
                              className="rounded"
                            />
                          </th>
                          <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Nom</th>
                          <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Email</th>
                          <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Departement</th>
                          <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Poste</th>
                        </tr>
                      </thead>
                      <tbody>
                        {odooMidpointComparison.to_sync.map((emp: any) => (
                          <tr key={emp.id} className="border-t hover:bg-orange-50">
                            <td className="px-4 py-3">
                              <input
                                type="checkbox"
                                checked={selectedEmployees.includes(emp.id)}
                                onChange={() => {
                                  if (selectedEmployees.includes(emp.id)) {
                                    setSelectedEmployees(selectedEmployees.filter(id => id !== emp.id))
                                  } else {
                                    setSelectedEmployees([...selectedEmployees, emp.id])
                                  }
                                }}
                                className="rounded"
                              />
                            </td>
                            <td className="px-4 py-3 text-sm font-medium">{emp.name}</td>
                            <td className="px-4 py-3 text-sm text-gray-600">{emp.email || '-'}</td>
                            <td className="px-4 py-3 text-sm text-gray-600">{emp.department || '-'}</td>
                            <td className="px-4 py-3 text-sm text-gray-600">{emp.job_title || '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Already Synced */}
              {odooMidpointComparison.synced?.length > 0 && (
                <div className="card">
                  <h3 className="font-semibold mb-4 flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-green-500" />
                    Deja synchronises ({odooMidpointComparison.synced.length})
                  </h3>
                  <div className="overflow-x-auto max-h-60">
                    <table className="w-full">
                      <thead className="sticky top-0 bg-white">
                        <tr className="bg-gray-50">
                          <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Odoo</th>
                          <th className="px-4 py-3 text-center text-sm font-medium text-gray-500">↔</th>
                          <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">MidPoint</th>
                        </tr>
                      </thead>
                      <tbody>
                        {odooMidpointComparison.synced.map((item: any, i: number) => (
                          <tr key={i} className="border-t hover:bg-green-50">
                            <td className="px-4 py-3 text-sm">
                              <div className="font-medium">{item.odoo?.name}</div>
                              <div className="text-xs text-gray-500">{item.odoo?.email}</div>
                            </td>
                            <td className="px-4 py-3 text-center">
                              <CheckCircle className="w-5 h-5 text-green-500 mx-auto" />
                            </td>
                            <td className="px-4 py-3 text-sm">
                              <div className="font-medium">{item.midpoint?.fullName || item.midpoint?.username}</div>
                              <div className="text-xs text-gray-500">{item.midpoint?.email}</div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {odooMidpointComparison.to_sync?.length === 0 && odooMidpointComparison.synced?.length === 0 && (
                <div className="card text-center py-12">
                  <CheckCircle className="w-12 h-12 text-green-300 mx-auto mb-4" />
                  <p className="text-gray-500">Aucun employe Odoo trouve ou tous sont deja synchronises</p>
                </div>
              )}
            </>
          ) : null}

          {syncMutation.isError && (
            <div className="card bg-red-50 border-red-200">
              <p className="text-red-600">Erreur lors de la synchronisation: {(syncMutation.error as any)?.message}</p>
            </div>
          )}

          {syncWithApprovalMutation.isError && (
            <div className="card bg-red-50 border-red-200">
              <p className="text-red-600">Erreur lors de la creation des workflows: {(syncWithApprovalMutation.error as any)?.message}</p>
            </div>
          )}
        </div>
      )}

      {/* Schedule Tab - Automatic Sync Configuration */}
      {activeTab === 'schedule' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Calendar className="w-8 h-8 text-indigo-600" />
              <div>
                <h2 className="text-lg font-semibold">Planification Automatique</h2>
                <p className="text-gray-500 text-sm">Configurez des synchronisations automatiques Odoo → MidPoint</p>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => refetchJobs()}
                disabled={jobsLoading}
                className="btn-secondary flex items-center gap-2"
              >
                <RefreshCw className={`w-4 h-4 ${jobsLoading ? 'animate-spin' : ''}`} />
                Actualiser
              </button>
              <button
                onClick={() => setShowAddJobModal(true)}
                className="btn-primary flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Nouveau Job
              </button>
            </div>
          </div>

          {/* Quick Presets */}
          <div className="card">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <Zap className="w-5 h-5 text-yellow-500" />
              Configurations Rapides
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button
                onClick={() => workdayPresetMutation.mutate()}
                disabled={workdayPresetMutation.isPending}
                className="p-4 border rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors text-left"
              >
                <div className="font-medium text-blue-700">Jours Ouvrables</div>
                <p className="text-sm text-gray-500 mt-1">8h, 12h et 18h du lundi au vendredi</p>
              </button>
              <button
                onClick={() => nightlyPresetMutation.mutate()}
                disabled={nightlyPresetMutation.isPending}
                className="p-4 border rounded-lg hover:bg-purple-50 hover:border-purple-300 transition-colors text-left"
              >
                <div className="font-medium text-purple-700">Nocturne</div>
                <p className="text-sm text-gray-500 mt-1">Tous les jours a 2h00 du matin</p>
              </button>
              <button
                onClick={() => hourlyPresetMutation.mutate()}
                disabled={hourlyPresetMutation.isPending}
                className="p-4 border rounded-lg hover:bg-green-50 hover:border-green-300 transition-colors text-left"
              >
                <div className="font-medium text-green-700">Horaire</div>
                <p className="text-sm text-gray-500 mt-1">Toutes les heures</p>
              </button>
            </div>
          </div>

          {/* Scheduled Jobs List */}
          <div className="card">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <Clock className="w-5 h-5 text-indigo-500" />
              Jobs Planifies ({scheduledJobs?.count || 0})
            </h3>

            {jobsLoading ? (
              <div className="text-center py-8 text-gray-500">Chargement des jobs...</div>
            ) : scheduledJobs?.jobs?.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="bg-gray-50">
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Job ID</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Type</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Configuration</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Prochaine execution</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Statut</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {scheduledJobs.jobs.map((job: any) => (
                      <tr key={job.job_id} className="border-t hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm font-medium">{job.job_id}</td>
                        <td className="px-4 py-3 text-sm">
                          <span className={`px-2 py-1 rounded text-xs ${
                            job.type === 'daily' ? 'bg-blue-100 text-blue-700' :
                            job.type === 'interval' ? 'bg-green-100 text-green-700' :
                            'bg-purple-100 text-purple-700'
                          }`}>
                            {job.type}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {job.type === 'daily' && `${String(job.hour).padStart(2, '0')}:${String(job.minute).padStart(2, '0')}`}
                          {job.type === 'interval' && `Toutes les ${job.hours}h ${job.minutes}min`}
                          {job.type === 'cron' && job.cron}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {job.next_run ? new Date(job.next_run).toLocaleString('fr-FR') : '-'}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-1 rounded text-xs ${
                            job.status === 'idle' ? 'bg-gray-100 text-gray-700' :
                            job.status === 'running' ? 'bg-blue-100 text-blue-700' :
                            job.status === 'disabled' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-red-100 text-red-700'
                          }`}>
                            {job.status}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => toggleJobMutation.mutate({ jobId: job.job_id, enabled: !job.enabled })}
                              className={`p-1 rounded ${job.enabled ? 'text-yellow-600 hover:bg-yellow-50' : 'text-green-600 hover:bg-green-50'}`}
                              title={job.enabled ? 'Desactiver' : 'Activer'}
                            >
                              {job.enabled ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                            </button>
                            <button
                              onClick={() => runNowMutation.mutate(job.job_id)}
                              disabled={runNowMutation.isPending}
                              className="p-1 rounded text-blue-600 hover:bg-blue-50"
                              title="Executer maintenant"
                            >
                              <Play className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => {
                                if (confirm('Supprimer ce job ?')) {
                                  deleteJobMutation.mutate(job.job_id)
                                }
                              }}
                              className="p-1 rounded text-red-600 hover:bg-red-50"
                              title="Supprimer"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p>Aucun job planifie</p>
                <p className="text-sm mt-2">Utilisez les configurations rapides ou creez un nouveau job</p>
              </div>
            )}
          </div>

          {/* Sync History */}
          {syncHistory?.history?.length > 0 && (
            <div className="card">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <History className="w-5 h-5 text-gray-500" />
                Historique des Synchronisations
              </h3>
              <div className="overflow-x-auto max-h-60">
                <table className="w-full">
                  <thead className="sticky top-0 bg-white">
                    <tr className="bg-gray-50">
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Date</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Job</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Statut</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Crees</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Ignores</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Erreurs</th>
                    </tr>
                  </thead>
                  <tbody>
                    {syncHistory.history.map((h: any, i: number) => (
                      <tr key={i} className="border-t hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm">
                          {new Date(h.started_at).toLocaleString('fr-FR')}
                        </td>
                        <td className="px-4 py-3 text-sm font-medium">{h.job_id}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-1 rounded text-xs ${
                            h.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                          }`}>
                            {h.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-green-600 font-medium">{h.synced}</td>
                        <td className="px-4 py-3 text-sm text-yellow-600">{h.skipped}</td>
                        <td className="px-4 py-3 text-sm text-red-600">{h.errors}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Add Job Modal */}
      {showAddJobModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-lg">
            <h3 className="text-lg font-semibold mb-4">Nouveau Job Planifie - LiveSync Odoo → MidPoint</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Type de planification
                </label>
                <select
                  value={newJobType}
                  onChange={(e) => setNewJobType(e.target.value as 'daily' | 'interval' | 'multi')}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="multi">Plusieurs heures (recommande)</option>
                  <option value="daily">Une seule heure fixe</option>
                  <option value="interval">Intervalle (toutes les X heures)</option>
                </select>
              </div>

              {newJobType === 'multi' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Selectionnez les heures de synchronisation
                  </label>
                  <div className="grid grid-cols-6 gap-2">
                    {Array.from({ length: 24 }, (_, i) => (
                      <button
                        key={i}
                        onClick={() => toggleHourSelection(i)}
                        className={`p-2 text-sm rounded-lg border transition-colors ${
                          selectedHours.includes(i)
                            ? 'bg-blue-500 text-white border-blue-500'
                            : 'bg-white text-gray-700 border-gray-300 hover:border-blue-300'
                        }`}
                      >
                        {String(i).padStart(2, '0')}h
                      </button>
                    ))}
                  </div>
                  <p className="text-sm text-gray-500 mt-2">
                    Heures selectionnees: {selectedHours.length > 0 ? selectedHours.map(h => `${h}h`).join(', ') : 'Aucune'}
                  </p>
                </div>
              )}

              {newJobType === 'daily' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      ID du Job
                    </label>
                    <input
                      type="text"
                      value={newJobConfig.job_id}
                      onChange={(e) => setNewJobConfig({ ...newJobConfig, job_id: e.target.value })}
                      placeholder="ex: sync-matin"
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Heure
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="23"
                        value={newJobConfig.hour}
                        onChange={(e) => setNewJobConfig({ ...newJobConfig, hour: parseInt(e.target.value) })}
                        className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Minute
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="59"
                        value={newJobConfig.minute}
                        onChange={(e) => setNewJobConfig({ ...newJobConfig, minute: parseInt(e.target.value) })}
                        className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </>
              )}

              {newJobType === 'interval' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      ID du Job
                    </label>
                    <input
                      type="text"
                      value={newJobConfig.job_id}
                      onChange={(e) => setNewJobConfig({ ...newJobConfig, job_id: e.target.value })}
                      placeholder="ex: sync-horaire"
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Heures
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="24"
                        value={newJobConfig.hours}
                        onChange={(e) => setNewJobConfig({ ...newJobConfig, hours: parseInt(e.target.value) })}
                        className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Minutes
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="59"
                        value={newJobConfig.minutes}
                        onChange={(e) => setNewJobConfig({ ...newJobConfig, minutes: parseInt(e.target.value) })}
                        className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </>
              )}
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowAddJobModal(false)}
                className="btn-secondary"
              >
                Annuler
              </button>
              <button
                onClick={handleCreateJob}
                disabled={
                  (newJobType === 'multi' && selectedHours.length === 0) ||
                  (newJobType !== 'multi' && !newJobConfig.job_id.trim()) ||
                  createDailyMutation.isPending ||
                  createIntervalMutation.isPending
                }
                className="btn-primary"
              >
                {newJobType === 'multi' ? `Creer ${selectedHours.length} job(s)` : 'Creer'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
