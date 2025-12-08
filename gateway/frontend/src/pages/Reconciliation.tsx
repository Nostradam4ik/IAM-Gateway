import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  startReconciliation,
  getReconciliationJobs,
  getDiscrepancies,
} from '../lib/api'
import { format } from 'date-fns'
import { RefreshCw, Play, CheckCircle, AlertTriangle, Database } from 'lucide-react'

export default function Reconciliation() {
  const [selectedTargets, setSelectedTargets] = useState<string[]>([])
  const [fullSync, setFullSync] = useState(false)
  const [selectedJob, setSelectedJob] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const { data: jobs, isLoading } = useQuery({
    queryKey: ['reconciliationJobs'],
    queryFn: getReconciliationJobs,
    refetchInterval: 10000,
  })

  const { data: discrepancies } = useQuery({
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
          <h2 className="text-lg font-semibold mb-4">
            Divergences detectees ({discrepancies.length})
          </h2>

          {discrepancies.length === 0 ? (
            <p className="text-gray-500 text-center py-4">
              Aucune divergence detectee
            </p>
          ) : (
            <div className="space-y-3">
              {discrepancies.map((disc: any) => (
                <div
                  key={disc.id}
                  className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="font-medium">{disc.account_id}</span>
                      <span className="mx-2 text-gray-400">|</span>
                      <span className="text-sm text-gray-500">
                        {disc.target_system}
                      </span>
                    </div>
                    <span className="text-sm bg-yellow-200 text-yellow-800 px-2 py-1 rounded">
                      {disc.discrepancy_type?.replace('_', ' ')}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-gray-600">
                    {disc.recommendation}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
