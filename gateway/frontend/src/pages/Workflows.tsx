import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getWorkflowInstances,
  getPendingApprovals,
  approveWorkflow,
  rejectWorkflow,
  getWorkflowDetails,
} from '../lib/api'
import { format } from 'date-fns'
import {
  CheckCircle,
  XCircle,
  Clock,
  MessageSquare,
  GitPullRequest,
  User,
  Users,
  Shield,
  ChevronRight,
  Eye,
  X,
} from 'lucide-react'

interface LevelStatus {
  level: number
  name: string
  description?: string
  status: string
  decided_by?: string
  decided_at?: string
  comments?: string
  approver_type?: string
  role_required?: string
}

interface WorkflowDetails {
  id: string
  operation_id: string
  operation_name: string
  user_name: string
  status: string
  current_level: number
  total_levels: number
  levels_status: LevelStatus[]
  history: any[]
  created_at: string
  context?: any
}

export default function Workflows() {
  const [selectedInstance, setSelectedInstance] = useState<any>(null)
  const [comments, setComments] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [detailsModalOpen, setDetailsModalOpen] = useState(false)
  const [workflowDetails, setWorkflowDetails] = useState<WorkflowDetails | null>(null)
  const [actionType, setActionType] = useState<'approve' | 'reject'>('approve')
  const queryClient = useQueryClient()

  const { data: instances, isLoading } = useQuery({
    queryKey: ['workflowInstances'],
    queryFn: () => getWorkflowInstances(),
    refetchInterval: 10000,
  })

  const { data: pending } = useQuery({
    queryKey: ['pendingApprovals'],
    queryFn: getPendingApprovals,
    refetchInterval: 10000,
  })

  const approveMutation = useMutation({
    mutationFn: ({ id, comments }: { id: string; comments?: string }) =>
      approveWorkflow(id, comments),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflowInstances'] })
      queryClient.invalidateQueries({ queryKey: ['pendingApprovals'] })
      setModalOpen(false)
    },
  })

  const rejectMutation = useMutation({
    mutationFn: ({ id, comments }: { id: string; comments: string }) =>
      rejectWorkflow(id, comments),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflowInstances'] })
      queryClient.invalidateQueries({ queryKey: ['pendingApprovals'] })
      setModalOpen(false)
    },
  })

  const handleAction = (instance: any, action: 'approve' | 'reject') => {
    setSelectedInstance(instance)
    setActionType(action)
    setComments('')
    setModalOpen(true)
  }

  const handleViewDetails = async (instance: any) => {
    try {
      const details = await getWorkflowDetails(instance.id)
      setWorkflowDetails(details)
      setDetailsModalOpen(true)
    } catch (error) {
      console.error('Failed to fetch workflow details:', error)
    }
  }

  const submitAction = () => {
    if (actionType === 'approve') {
      approveMutation.mutate({ id: selectedInstance.id, comments })
    } else {
      if (!comments.trim()) {
        alert('Veuillez fournir un commentaire pour le rejet')
        return
      }
      rejectMutation.mutate({ id: selectedInstance.id, comments })
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'approved':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            <CheckCircle className="w-3 h-3" />
            Approuve
          </span>
        )
      case 'rejected':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
            <XCircle className="w-3 h-3" />
            Rejete
          </span>
        )
      case 'pending':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
            <Clock className="w-3 h-3" />
            En attente
          </span>
        )
      case 'waiting':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
            <Clock className="w-3 h-3" />
            A venir
          </span>
        )
      case 'expired':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
            <Clock className="w-3 h-3" />
            Expire
          </span>
        )
      default:
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">{status}</span>
    }
  }

  const getLevelIcon = (level: number, approverType?: string) => {
    if (approverType === 'manager') {
      return <User className="w-4 h-4" />
    } else if (level === 2 || approverType === 'role' && level === 2) {
      return <Users className="w-4 h-4" />
    } else {
      return <Shield className="w-4 h-4" />
    }
  }

  const getLevelColor = (level: number, status: string) => {
    if (status === 'approved') return 'bg-green-500 text-white'
    if (status === 'rejected') return 'bg-red-500 text-white'
    if (status === 'pending') {
      if (level === 1) return 'bg-blue-500 text-white'
      if (level === 2) return 'bg-purple-500 text-white'
      return 'bg-emerald-500 text-white'
    }
    return 'bg-gray-200 text-gray-500'
  }

  const renderProgressSteps = (currentLevel: number, totalLevels: number, levelsStatus?: LevelStatus[]) => {
    const steps = []
    const levelNames = ['Manager', 'RH', 'IT Admin']

    for (let i = 1; i <= totalLevels; i++) {
      const levelData = levelsStatus?.find(l => l.level === i)
      const status = levelData?.status || (i < currentLevel ? 'approved' : i === currentLevel ? 'pending' : 'waiting')
      const name = levelData?.name || levelNames[i - 1] || `Niveau ${i}`

      steps.push(
        <div key={i} className="flex items-center">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${getLevelColor(i, status)}`}>
            {status === 'approved' ? (
              <CheckCircle className="w-4 h-4" />
            ) : status === 'rejected' ? (
              <XCircle className="w-4 h-4" />
            ) : (
              <span className="text-sm font-medium">{i}</span>
            )}
          </div>
          <span className={`ml-2 text-sm ${status === 'pending' ? 'font-medium text-gray-900' : 'text-gray-500'}`}>
            {name}
          </span>
          {i < totalLevels && (
            <ChevronRight className="w-4 h-4 mx-2 text-gray-300" />
          )}
        </div>
      )
    }

    return <div className="flex items-center">{steps}</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Workflows d'approbation</h1>
        <p className="text-gray-500 mt-1">
          Gerez les demandes d'approbation multi-niveaux pour le provisionnement
        </p>
      </div>

      {/* Pending count with level info */}
      {pending && pending.length > 0 && (
        <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Clock className="w-5 h-5 text-yellow-600 mr-2" />
              <span className="font-medium text-yellow-800">
                {pending.length} approbation(s) en attente de votre validation
              </span>
            </div>
            <div className="flex gap-2">
              {pending.map((p: any) => (
                <span key={p.id} className="text-xs bg-yellow-200 text-yellow-800 px-2 py-1 rounded">
                  Niveau {p.current_level}: {p.current_level_name || 'En attente'}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Chaine d'approbation</h3>
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center">
              <User className="w-4 h-4" />
            </div>
            <div>
              <span className="text-sm font-medium">Niveau 1</span>
              <span className="text-xs text-gray-500 block">Manager</span>
            </div>
          </div>
          <ChevronRight className="w-4 h-4 text-gray-300" />
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-purple-500 text-white flex items-center justify-center">
              <Users className="w-4 h-4" />
            </div>
            <div>
              <span className="text-sm font-medium">Niveau 2</span>
              <span className="text-xs text-gray-500 block">RH Manager</span>
            </div>
          </div>
          <ChevronRight className="w-4 h-4 text-gray-300" />
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-emerald-500 text-white flex items-center justify-center">
              <Shield className="w-4 h-4" />
            </div>
            <div>
              <span className="text-sm font-medium">Niveau 3</span>
              <span className="text-xs text-gray-500 block">IT Admin</span>
            </div>
          </div>
        </div>
      </div>

      {/* Workflow instances */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="text-left py-4 px-4 font-medium text-gray-500 text-sm">
                  Instance
                </th>
                <th className="text-left py-4 px-4 font-medium text-gray-500 text-sm">
                  Operation
                </th>
                <th className="text-left py-4 px-4 font-medium text-gray-500 text-sm">
                  Progression
                </th>
                <th className="text-left py-4 px-4 font-medium text-gray-500 text-sm">
                  Statut
                </th>
                <th className="text-left py-4 px-4 font-medium text-gray-500 text-sm">
                  Date
                </th>
                <th className="text-left py-4 px-4 font-medium text-gray-500 text-sm">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-gray-500">
                    Chargement...
                  </td>
                </tr>
              ) : instances?.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-gray-500">
                    <GitPullRequest className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                    Aucun workflow en cours
                  </td>
                </tr>
              ) : (
                instances?.map((instance: any) => (
                  <tr
                    key={instance.id}
                    className="border-b border-gray-100 hover:bg-gray-50"
                  >
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-2">
                        <GitPullRequest className="w-4 h-4 text-gray-400" />
                        <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                          {instance.id?.slice(0, 12)}
                        </code>
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex flex-col">
                        <span className="font-medium text-gray-900">
                          {instance.operation_name || instance.operation_id?.slice(0, 8)}
                        </span>
                        {instance.user_name && (
                          <span className="text-sm text-gray-500">
                            {instance.user_name}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      {renderProgressSteps(instance.current_level, instance.total_levels)}
                    </td>
                    <td className="py-4 px-4">{getStatusBadge(instance.status)}</td>
                    <td className="py-4 px-4 text-gray-500 text-sm">
                      {instance.created_at
                        ? format(new Date(instance.created_at), 'dd/MM/yyyy HH:mm')
                        : '-'}
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleViewDetails(instance)}
                          className="text-gray-600 hover:text-gray-800 flex items-center gap-1"
                          title="Voir les details"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        {instance.status === 'pending' && (
                          <>
                            <button
                              onClick={() => handleAction(instance, 'approve')}
                              className="text-green-600 hover:text-green-700 flex items-center gap-1"
                            >
                              <CheckCircle className="w-4 h-4" />
                              Approuver
                            </button>
                            <button
                              onClick={() => handleAction(instance, 'reject')}
                              className="text-red-600 hover:text-red-700 flex items-center gap-1"
                            >
                              <XCircle className="w-4 h-4" />
                              Rejeter
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Approval Modal */}
      {modalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">
                {actionType === 'approve' ? 'Approuver' : 'Rejeter'} le workflow
              </h2>
              <button onClick={() => setModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {selectedInstance && (
              <div className="bg-gray-50 rounded-lg p-3 mb-4">
                <p className="text-sm text-gray-600">
                  <strong>Operation:</strong> {selectedInstance.operation_name}
                </p>
                <p className="text-sm text-gray-600">
                  <strong>Utilisateur:</strong> {selectedInstance.user_name}
                </p>
                <p className="text-sm text-gray-600">
                  <strong>Niveau actuel:</strong> {selectedInstance.current_level} / {selectedInstance.total_levels}
                </p>
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <MessageSquare className="w-4 h-4 inline mr-1" />
                  Commentaire {actionType === 'reject' && '(obligatoire)'}
                </label>
                <textarea
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 h-24"
                  placeholder="Ajoutez un commentaire..."
                />
              </div>

              {actionType === 'approve' && selectedInstance?.current_level < selectedInstance?.total_levels && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
                  <strong>Note:</strong> En approuvant, la demande sera transmise au niveau suivant pour validation.
                </div>
              )}

              {actionType === 'reject' && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-800">
                  <strong>Attention:</strong> Le rejet annulera definitivement ce workflow.
                </div>
              )}

              <div className="flex justify-end gap-3 pt-2">
                <button
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Annuler
                </button>
                <button
                  onClick={submitAction}
                  disabled={
                    approveMutation.isPending || rejectMutation.isPending
                  }
                  className={`px-4 py-2 rounded-lg text-white ${
                    actionType === 'approve'
                      ? 'bg-green-600 hover:bg-green-700'
                      : 'bg-red-600 hover:bg-red-700'
                  } disabled:opacity-50`}
                >
                  {approveMutation.isPending || rejectMutation.isPending
                    ? 'En cours...'
                    : actionType === 'approve'
                    ? 'Approuver'
                    : 'Rejeter'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Details Modal */}
      {detailsModalOpen && workflowDetails && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold">Details du workflow</h2>
              <button onClick={() => setDetailsModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Summary */}
            <div className="bg-gray-50 rounded-lg p-4 mb-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-sm text-gray-500">Operation</span>
                  <p className="font-medium">{workflowDetails.operation_name}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-500">Utilisateur</span>
                  <p className="font-medium">{workflowDetails.user_name}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-500">Statut</span>
                  <p>{getStatusBadge(workflowDetails.status)}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-500">Date de creation</span>
                  <p className="font-medium">
                    {workflowDetails.created_at
                      ? format(new Date(workflowDetails.created_at), 'dd/MM/yyyy HH:mm')
                      : '-'}
                  </p>
                </div>
              </div>
            </div>

            {/* Levels status */}
            <div className="mb-6">
              <h3 className="text-lg font-medium mb-4">Progression des niveaux</h3>
              <div className="space-y-3">
                {workflowDetails.levels_status?.map((level) => (
                  <div
                    key={level.level}
                    className={`border rounded-lg p-4 ${
                      level.status === 'pending'
                        ? 'border-blue-300 bg-blue-50'
                        : level.status === 'approved'
                        ? 'border-green-300 bg-green-50'
                        : level.status === 'rejected'
                        ? 'border-red-300 bg-red-50'
                        : 'border-gray-200 bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${getLevelColor(level.level, level.status)}`}>
                          {level.status === 'approved' ? (
                            <CheckCircle className="w-5 h-5" />
                          ) : level.status === 'rejected' ? (
                            <XCircle className="w-5 h-5" />
                          ) : (
                            getLevelIcon(level.level, level.approver_type)
                          )}
                        </div>
                        <div>
                          <p className="font-medium">Niveau {level.level}: {level.name}</p>
                          {level.description && (
                            <p className="text-sm text-gray-500">{level.description}</p>
                          )}
                        </div>
                      </div>
                      {getStatusBadge(level.status)}
                    </div>
                    {level.decided_by && (
                      <div className="mt-3 pt-3 border-t border-gray-200 text-sm">
                        <p><strong>Decide par:</strong> {level.decided_by}</p>
                        {level.decided_at && (
                          <p><strong>Date:</strong> {format(new Date(level.decided_at), 'dd/MM/yyyy HH:mm')}</p>
                        )}
                        {level.comments && (
                          <p><strong>Commentaire:</strong> {level.comments}</p>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* History */}
            {workflowDetails.history && workflowDetails.history.length > 0 && (
              <div>
                <h3 className="text-lg font-medium mb-4">Historique</h3>
                <div className="space-y-2">
                  {workflowDetails.history.map((event: any, index: number) => (
                    <div key={index} className="flex items-start gap-3 text-sm">
                      <div className="w-2 h-2 mt-2 rounded-full bg-gray-400"></div>
                      <div>
                        <p className="text-gray-900">{event.details || event.action}</p>
                        <p className="text-gray-500 text-xs">
                          {event.timestamp
                            ? format(new Date(event.timestamp), 'dd/MM/yyyy HH:mm:ss')
                            : '-'}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setDetailsModalOpen(false)}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg"
              >
                Fermer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
