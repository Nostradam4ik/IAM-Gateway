import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  getLiveStats,
  compareSystems,
  getUserCrossReference,
  getOdooContacts,
  checkSystemsHealth,
} from '../lib/api'
import {
  RefreshCw,
  Database,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Search,
  Users,
  Building2,
  Zap,
  Eye,
  ArrowRightLeft,
} from 'lucide-react'

export default function LiveComparison() {
  const [searchQuery, setSearchQuery] = useState('')
  const [activeTab, setActiveTab] = useState<'stats' | 'compare' | 'odoo' | 'search'>('stats')

  // Live stats query
  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useQuery({
    queryKey: ['liveStats'],
    queryFn: getLiveStats,
    refetchInterval: 30000,
  })

  // Health check query
  const { data: health } = useQuery({
    queryKey: ['systemsHealth'],
    queryFn: checkSystemsHealth,
    refetchInterval: 60000,
  })

  // Comparison query (manual trigger)
  const { data: comparison, isLoading: compareLoading, refetch: runComparison } = useQuery({
    queryKey: ['systemComparison'],
    queryFn: compareSystems,
    enabled: false,
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
            { id: 'stats', label: 'Statistiques', icon: Database },
            { id: 'compare', label: 'Comparaison', icon: ArrowRightLeft },
            { id: 'odoo', label: 'Odoo', icon: Building2 },
            { id: 'search', label: 'Recherche', icon: Search },
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

      {/* Stats Tab */}
      {activeTab === 'stats' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold">Statistiques en temps reel</h2>
            <button
              onClick={() => refetchStats()}
              className="btn-secondary flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${statsLoading ? 'animate-spin' : ''}`} />
              Actualiser
            </button>
          </div>

          {statsLoading ? (
            <div className="text-center py-8 text-gray-500">Chargement...</div>
          ) : stats ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* LDAP Card */}
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-lg flex items-center gap-2">
                    <Database className="w-5 h-5 text-blue-500" />
                    LDAP
                  </h3>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(stats.systems?.LDAP?.status)}`}>
                    {stats.systems?.LDAP?.status || 'inconnu'}
                  </span>
                </div>
                <div className="text-3xl font-bold text-gray-900 mb-2">
                  {stats.systems?.LDAP?.total_users || 0}
                </div>
                <p className="text-gray-500 text-sm">utilisateurs</p>
                {stats.systems?.LDAP?.sample && (
                  <div className="mt-4 pt-4 border-t">
                    <p className="text-xs text-gray-500 mb-2">Exemples:</p>
                    {stats.systems.LDAP.sample.slice(0, 3).map((u: any, i: number) => (
                      <div key={i} className="text-sm text-gray-700 truncate">
                        {u.cn || u.uid}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* SQL Card */}
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-lg flex items-center gap-2">
                    <Database className="w-5 h-5 text-green-500" />
                    SQL (Intranet)
                  </h3>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(stats.systems?.SQL?.status)}`}>
                    {stats.systems?.SQL?.status || 'inconnu'}
                  </span>
                </div>
                <div className="text-3xl font-bold text-gray-900 mb-2">
                  {stats.systems?.SQL?.total_users || 0}
                </div>
                <p className="text-gray-500 text-sm">utilisateurs</p>
                {stats.systems?.SQL?.sample && (
                  <div className="mt-4 pt-4 border-t">
                    <p className="text-xs text-gray-500 mb-2">Exemples:</p>
                    {stats.systems.SQL.sample.slice(0, 3).map((u: any, i: number) => (
                      <div key={i} className="text-sm text-gray-700 truncate">
                        {u.username} ({u.department})
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Odoo Card */}
              <div className="card border-2 border-purple-200 bg-purple-50/30">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-lg flex items-center gap-2">
                    <Building2 className="w-5 h-5 text-purple-500" />
                    Odoo
                  </h3>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(stats.systems?.Odoo?.status)}`}>
                    {stats.systems?.Odoo?.status || 'inconnu'}
                  </span>
                </div>
                <div className="text-3xl font-bold text-gray-900 mb-2">
                  {stats.systems?.Odoo?.total_users || 0}
                </div>
                <p className="text-gray-500 text-sm">utilisateurs actifs</p>
                {stats.systems?.Odoo?.sample && (
                  <div className="mt-4 pt-4 border-t">
                    <p className="text-xs text-gray-500 mb-2">Exemples:</p>
                    {stats.systems.Odoo.sample.slice(0, 3).map((u: any, i: number) => (
                      <div key={i} className="text-sm text-gray-700 truncate">
                        {u.name} ({u.login})
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : null}

          {/* Total */}
          {stats && (
            <div className="card bg-gradient-to-r from-blue-500 to-purple-600 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-medium opacity-90">Total Identites</h3>
                  <p className="text-4xl font-bold mt-2">{stats.total_identities}</p>
                  <p className="text-sm opacity-75 mt-1">dans tous les systemes</p>
                </div>
                <Users className="w-16 h-16 opacity-30" />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Compare Tab */}
      {activeTab === 'compare' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold">Comparaison entre systemes</h2>
            <button
              onClick={() => runComparison()}
              disabled={compareLoading}
              className="btn-primary flex items-center gap-2"
            >
              {compareLoading ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <ArrowRightLeft className="w-4 h-4" />
              )}
              Lancer la comparaison
            </button>
          </div>

          {comparison && (
            <>
              {/* Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="card text-center">
                  <div className="text-3xl font-bold text-green-600">
                    {comparison.summary?.fully_synced || 0}
                  </div>
                  <p className="text-sm text-gray-500 mt-1">Totalement synchronises</p>
                </div>
                <div className="card text-center">
                  <div className="text-3xl font-bold text-yellow-600">
                    {comparison.summary?.partially_synced || 0}
                  </div>
                  <p className="text-sm text-gray-500 mt-1">Partiellement synchronises</p>
                </div>
                <div className="card text-center">
                  <div className="text-3xl font-bold text-orange-600">
                    {comparison.summary?.isolated || 0}
                  </div>
                  <p className="text-sm text-gray-500 mt-1">Isoles (1 systeme)</p>
                </div>
                <div className="card text-center bg-blue-50">
                  <div className="text-3xl font-bold text-blue-600">
                    {comparison.summary?.sync_rate || '0%'}
                  </div>
                  <p className="text-sm text-gray-500 mt-1">Taux de sync complete</p>
                </div>
              </div>

              {/* Discrepancies */}
              {comparison.discrepancies?.length > 0 && (
                <div className="card">
                  <h3 className="font-semibold mb-4 flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-yellow-500" />
                    Divergences detectees ({comparison.discrepancies.length})
                  </h3>
                  <div className="space-y-3">
                    {comparison.discrepancies.map((disc: any, i: number) => (
                      <div key={i} className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{disc.identifier}</span>
                          {getSyncStatusBadge(disc.sync_status)}
                        </div>
                        {disc.missing_in && (
                          <p className="text-sm text-gray-600 mt-1">
                            Manquant dans: <span className="font-medium text-red-600">{disc.missing_in.join(', ')}</span>
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Cross Reference Table */}
              {comparison.cross_reference && (
                <div className="card overflow-hidden">
                  <h3 className="font-semibold mb-4">Reference croisee (50 premiers)</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="bg-gray-50">
                          <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Identifiant</th>
                          <th className="px-4 py-3 text-center text-sm font-medium text-gray-500">LDAP</th>
                          <th className="px-4 py-3 text-center text-sm font-medium text-gray-500">SQL</th>
                          <th className="px-4 py-3 text-center text-sm font-medium text-gray-500">Odoo</th>
                          <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Statut</th>
                        </tr>
                      </thead>
                      <tbody>
                        {comparison.cross_reference.slice(0, 20).map((ref: any, i: number) => (
                          <tr key={i} className="border-t hover:bg-gray-50">
                            <td className="px-4 py-3 text-sm font-medium">{ref.identifier}</td>
                            <td className="px-4 py-3 text-center">
                              {ref.in_ldap ? (
                                <CheckCircle className="w-5 h-5 text-green-500 mx-auto" />
                              ) : (
                                <XCircle className="w-5 h-5 text-red-300 mx-auto" />
                              )}
                            </td>
                            <td className="px-4 py-3 text-center">
                              {ref.in_sql ? (
                                <CheckCircle className="w-5 h-5 text-green-500 mx-auto" />
                              ) : (
                                <XCircle className="w-5 h-5 text-red-300 mx-auto" />
                              )}
                            </td>
                            <td className="px-4 py-3 text-center">
                              {ref.in_odoo ? (
                                <CheckCircle className="w-5 h-5 text-green-500 mx-auto" />
                              ) : (
                                <XCircle className="w-5 h-5 text-red-300 mx-auto" />
                              )}
                            </td>
                            <td className="px-4 py-3">{getSyncStatusBadge(ref.sync_status)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}

          {!comparison && !compareLoading && (
            <div className="card text-center py-12">
              <ArrowRightLeft className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">Cliquez sur "Lancer la comparaison" pour analyser les systemes</p>
            </div>
          )}
        </div>
      )}

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
    </div>
  )
}
