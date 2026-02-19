/**
 * Reconciliation.tsx - Page de reconciliation MidPoint vs systemes cibles.
 *
 * Permet de :
 *   - Lancer un job de reconciliation (en tache de fond)
 *   - Voir la liste des jobs passes avec progression
 *   - Consulter les divergences trouvees (missing, extra, mismatch)
 *   - Resoudre les divergences : use_midpoint, use_target, delete_orphan, ignore
 *   - Voir le detail de chaque divergence (valeur MidPoint vs valeur cible)
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  startReconciliation,
  getReconciliationJobs,
  getDiscrepancies,
  resolveDiscrepancies,
} from '../lib/api'
import { format } from 'date-fns'
import { RefreshCw, Play, CheckCircle, AlertTriangle, Database, ArrowRight, Trash2, XCircle } from 'lucide-react'

export default function Reconciliation() {
  const [selectedTargets, setSelectedTargets] = useState<string[]>([])
  const [fullSync, setFullSync] = useState(false)
  const [selectedJob, setSelectedJob] = useState<string | null>(null)
  const [selectedDiscrepancies, setSelectedDiscrepancies] = useState<string[]>([])
  const [resolveResult, setResolveResult] = useState<any>(null)
  const queryClient = useQueryClient()

  const { data: jobs, isLoading } = useQuery({
    queryKey: ['reconciliationJobs'],
    queryFn: getReconciliationJobs,
    refetchInterval: 10000,
  })

  const { data: discrepancies, refetch: refetchDiscrepancies } = useQuery({
    queryKey: ['discrepancies', selectedJob],
    queryFn: () => (selectedJob ? getDiscrepancies(selectedJob) : null),
    enabled: !!selectedJob,
  })

  const [lastResult, setLastResult] = useState<any>(null)

  const startMutation = useMutation({
    mutationFn: () =>
      startReconciliation(
        selectedTargets.length > 0 ? selectedTargets : undefined,
        fullSync
      ),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['reconciliationJobs'] })
      setLastResult(data)
    },
  })

  const resolveMutation = useMutation({
    mutationFn: ({ action, ids }: { action: 'use_midpoint' | 'use_target' | 'delete_orphan' | 'ignore', ids?: string[] }) =>
      resolveDiscrepancies(selectedJob!, action, ids),
    onSuccess: (data) => {
      setResolveResult(data)
      setSelectedDiscrepancies([])
      refetchDiscrepancies()
      queryClient.invalidateQueries({ queryKey: ['reconciliationJobs'] })
    },
  })

  const toggleDiscrepancy = (id: string) => {
    setSelectedDiscrepancies(prev =>
      prev.includes(id) ? prev.filter(d => d !== id) : [...prev, id]
    )
  }

  const selectAllDiscrepancies = () => {
    if (discrepancies) {
      setSelectedDiscrepancies(discrepancies.map((d: any) => d.id))
    }
  }

  const clearSelection = () => {
    setSelectedDiscrepancies([])
  }

  const toggleTarget = (target: string) => {
    setSelectedTargets((prev) =>
      prev.includes(target)
        ? prev.filter((t) => t !== target)
        : [...prev, target]
    )
  }

  const targets = ['LDAP', 'SQL', 'ODOO']

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <span className="badge badge-success flex items-center gap-1">
            <CheckCircle className="w-3 h-3" />
            Termine
          </span>
        )
      case 'in_progress':
        return (
          <span className="badge badge-info flex items-center gap-1">
            <RefreshCw className="w-3 h-3 animate-spin" />
            En cours
          </span>
        )
      case 'failed':
        return (
          <span className="badge badge-danger flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" />
            Echec
          </span>
        )
      default:
        return <span className="badge badge-warning">{status}</span>
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Reconciliation</h1>
        <p className="text-gray-500 mt-1">
          Synchronisez et verifiez les comptes entre MidPoint et les systemes cibles
        </p>
      </div>

      {/* Start reconciliation */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Nouvelle reconciliation</h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Systemes cibles
            </label>
            <div className="flex gap-3">
              {targets.map((target) => (
                <button
                  key={target}
                  onClick={() => toggleTarget(target)}
                  className={`px-4 py-2 rounded-lg border transition-colors ${
                    selectedTargets.includes(target)
                      ? 'bg-blue-50 border-blue-300 text-blue-700'
                      : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <Database className="w-4 h-4 inline mr-2" />
                  {target}
                </button>
              ))}
            </div>
            <p className="text-sm text-gray-500 mt-2">
              Laissez vide pour reconcilier tous les systemes
            </p>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="fullSync"
              checked={fullSync}
              onChange={(e) => setFullSync(e.target.checked)}
              className="w-4 h-4 text-blue-600 rounded border-gray-300"
            />
            <label htmlFor="fullSync" className="ml-2 text-sm text-gray-700">
              Synchronisation complete (plus long mais plus precis)
            </label>
          </div>

          <button
            onClick={() => startMutation.mutate()}
            disabled={startMutation.isPending}
            className="btn-primary flex items-center gap-2"
          >
            {startMutation.isPending ? (
              <RefreshCw className="w-5 h-5 animate-spin" />
            ) : (
              <Play className="w-5 h-5" />
            )}
            Demarrer la reconciliation
          </button>

          {startMutation.isError && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              <AlertTriangle className="w-5 h-5 inline mr-2" />
              Erreur: {(startMutation.error as any)?.response?.data?.detail || 'Echec de la reconciliation'}
            </div>
          )}

          {lastResult && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center gap-2 text-green-700 font-medium">
                <CheckCircle className="w-5 h-5" />
                Reconciliation demarree avec succes !
              </div>
              <div className="mt-2 text-sm text-green-600 space-y-1">
                <p><strong>Job ID:</strong> {lastResult.id}</p>
                <p><strong>Statut:</strong> {lastResult.status}</p>
                <p><strong>Systemes:</strong> {lastResult.target_systems?.join(', ')}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Jobs list */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Historique des reconciliations</h2>

        <div className="space-y-4">
          {isLoading ? (
            <p className="text-gray-500 text-center py-4">Chargement...</p>
          ) : jobs?.length === 0 ? (
            <p className="text-gray-500 text-center py-4">
              Aucune reconciliation effectuee
            </p>
          ) : (
            jobs?.map((job: any) => (
              <div
                key={job.id}
                className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                  selectedJob === job.id
                    ? 'border-blue-300 bg-blue-50'
                    : 'border-gray-200 hover:bg-gray-50'
                }`}
                onClick={() => setSelectedJob(job.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    {getStatusBadge(job.status)}
                    <span className="text-sm text-gray-500">
                      {job.target_systems?.join(', ')}
                    </span>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">
                      {job.processed_accounts} / {job.total_accounts} comptes
                    </p>
                    <p className="text-xs text-gray-500">
                      {job.discrepancies_found} divergences
                    </p>
                  </div>
                </div>
                <div className="mt-2 text-sm text-gray-500">
                  {job.started_at &&
                    format(new Date(job.started_at), 'dd/MM/yyyy HH:mm')}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Discrepancies */}
      {selectedJob && discrepancies && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">
              Divergences detectees ({discrepancies.length})
            </h2>
            {discrepancies.length > 0 && (
              <div className="flex gap-2">
                <button
                  onClick={selectAllDiscrepancies}
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  Tout selectionner
                </button>
                {selectedDiscrepancies.length > 0 && (
                  <button
                    onClick={clearSelection}
                    className="text-sm text-gray-600 hover:text-gray-800"
                  >
                    Effacer selection ({selectedDiscrepancies.length})
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Action buttons */}
          {discrepancies.length > 0 && (
            <div className="mb-4 p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-3">
                {selectedDiscrepancies.length > 0
                  ? `Actions pour ${selectedDiscrepancies.length} divergence(s) selectionnee(s):`
                  : 'Actions pour toutes les divergences:'}
              </p>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => resolveMutation.mutate({
                    action: 'use_midpoint',
                    ids: selectedDiscrepancies.length > 0 ? selectedDiscrepancies : undefined
                  })}
                  disabled={resolveMutation.isPending}
                  className="btn-primary flex items-center gap-2 text-sm"
                >
                  <ArrowRight className="w-4 h-4" />
                  Sync MidPoint → Cibles
                </button>
                <button
                  onClick={() => resolveMutation.mutate({
                    action: 'use_target',
                    ids: selectedDiscrepancies.length > 0 ? selectedDiscrepancies : undefined
                  })}
                  disabled={resolveMutation.isPending}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2 text-sm"
                >
                  <ArrowRight className="w-4 h-4 rotate-180" />
                  Importer Cibles → MidPoint
                </button>
                <button
                  onClick={() => resolveMutation.mutate({
                    action: 'delete_orphan',
                    ids: selectedDiscrepancies.length > 0 ? selectedDiscrepancies : undefined
                  })}
                  disabled={resolveMutation.isPending}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center gap-2 text-sm"
                >
                  <Trash2 className="w-4 h-4" />
                  Supprimer orphelins
                </button>
                <button
                  onClick={() => resolveMutation.mutate({
                    action: 'ignore',
                    ids: selectedDiscrepancies.length > 0 ? selectedDiscrepancies : undefined
                  })}
                  disabled={resolveMutation.isPending}
                  className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 flex items-center gap-2 text-sm"
                >
                  <XCircle className="w-4 h-4" />
                  Ignorer
                </button>
              </div>

              {resolveMutation.isPending && (
                <div className="mt-3 flex items-center gap-2 text-blue-600">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Resolution en cours...
                </div>
              )}

              {resolveMutation.isError && (
                <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                  <AlertTriangle className="w-4 h-4 inline mr-2" />
                  Erreur: {(resolveMutation.error as any)?.response?.data?.detail || 'Echec de la resolution'}
                </div>
              )}

              {resolveResult && (
                <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded text-green-700 text-sm">
                  <CheckCircle className="w-4 h-4 inline mr-2" />
                  {resolveResult.resolved} divergence(s) resolue(s) sur {resolveResult.total_processed}
                  {resolveResult.errors?.length > 0 && (
                    <span className="text-red-600 ml-2">
                      ({resolveResult.errors.length} erreur(s))
                    </span>
                  )}
                </div>
              )}
            </div>
          )}

          {discrepancies.length === 0 ? (
            <p className="text-gray-500 text-center py-4">
              Aucune divergence detectee
            </p>
          ) : (
            <div className="space-y-3">
              {discrepancies.map((disc: any) => (
                <div
                  key={disc.id}
                  onClick={() => toggleDiscrepancy(disc.id)}
                  className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                    selectedDiscrepancies.includes(disc.id)
                      ? 'bg-blue-50 border-blue-300'
                      : disc.resolved
                      ? 'bg-green-50 border-green-200'
                      : 'bg-yellow-50 border-yellow-200 hover:bg-yellow-100'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={selectedDiscrepancies.includes(disc.id)}
                        onChange={() => toggleDiscrepancy(disc.id)}
                        onClick={(e) => e.stopPropagation()}
                        className="w-4 h-4 text-blue-600 rounded"
                      />
                      <div>
                        <span className="font-medium">{disc.account_id}</span>
                        <span className="mx-2 text-gray-400">|</span>
                        <span className="text-sm text-gray-500">
                          {disc.target_system}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {disc.resolved && (
                        <span className="text-xs bg-green-200 text-green-800 px-2 py-1 rounded">
                          Resolu
                        </span>
                      )}
                      <span className={`text-sm px-2 py-1 rounded ${
                        disc.discrepancy_type === 'missing_in_target'
                          ? 'bg-orange-200 text-orange-800'
                          : disc.discrepancy_type === 'missing_in_midpoint'
                          ? 'bg-purple-200 text-purple-800'
                          : 'bg-yellow-200 text-yellow-800'
                      }`}>
                        {disc.discrepancy_type === 'missing_in_target'
                          ? 'Absent dans cible'
                          : disc.discrepancy_type === 'missing_in_midpoint'
                          ? 'Absent dans MidPoint'
                          : 'Attributs differents'}
                      </span>
                    </div>
                  </div>
                  <p className="mt-2 text-sm text-gray-600 ml-7">
                    {disc.recommendation}
                  </p>
                  {disc.midpoint_value && (
                    <div className="mt-2 ml-7 text-xs text-gray-500">
                      <strong>MidPoint:</strong> {disc.midpoint_value.name || disc.midpoint_value.fullName || JSON.stringify(disc.midpoint_value).slice(0, 100)}
                    </div>
                  )}
                  {disc.target_value && (
                    <div className="mt-1 ml-7 text-xs text-gray-500">
                      <strong>Cible:</strong> {disc.target_value.name || disc.target_value.login || JSON.stringify(disc.target_value).slice(0, 100)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
