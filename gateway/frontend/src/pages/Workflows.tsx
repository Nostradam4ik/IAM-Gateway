import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getWorkflowInstances,
  getPendingApprovals,
  approveWorkflow,
  rejectWorkflow,
} from '../lib/api'
import { format } from 'date-fns'
import {
  CheckCircle,
  XCircle,
  Clock,
  MessageSquare,
  GitPullRequest,
} from 'lucide-react'

export default function Workflows() {
  const [selectedInstance, setSelectedInstance] = useState<any>(null)
  const [comments, setComments] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
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
          <span className="badge badge-success flex items-center gap-1">
            <CheckCircle className="w-3 h-3" />
            Approuve
          </span>
        )
      case 'rejected':
        return (
          <span className="badge badge-danger flex items-center gap-1">
            <XCircle className="w-3 h-3" />
            Rejete
          </span>
        )
      case 'pending':
        return (
          <span className="badge badge-warning flex items-center gap-1">
            <Clock className="w-3 h-3" />
            En attente
          </span>
        )
      default:
        return <span className="badge badge-info">{status}</span>
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Workflows d'approbation</h1>
        <p className="text-gray-500 mt-1">
          Gerez les demandes d'approbation pour le provisionnement
        </p>
      </div>

      {/* Pending count */}
      {pending && pending.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center">
            <Clock className="w-5 h-5 text-yellow-600 mr-2" />
            <span className="font-medium text-yellow-800">
              {pending.length} approbation(s) en attente
            </span>
          </div>
        </div>
      )}

      {/* Workflow instances */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-4 px-4 font-medium text-gray-500">
                  Instance
                </th>
                <th className="text-left py-4 px-4 font-medium text-gray-500">
                  Operation
                </th>
                <th className="text-left py-4 px-4 font-medium text-gray-500">
                  Niveau
                </th>
                <th className="text-left py-4 px-4 font-medium text-gray-500">
                  Statut
                </th>
                <th className="text-left py-4 px-4 font-medium text-gray-500">
                  Date
                </th>
                <th className="text-left py-4 px-4 font-medium text-gray-500">
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
                          {instance.id?.slice(0, 8)}
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
                      <span className="text-sm">
                        {instance.current_level} / {instance.total_levels}
                      </span>
                    </td>
                    <td className="py-4 px-4">{getStatusBadge(instance.status)}</td>
                    <td className="py-4 px-4 text-gray-500 text-sm">
                      {instance.created_at
                        ? format(new Date(instance.created_at), 'dd/MM/yyyy HH:mm')
                        : '-'}
                    </td>
                    <td className="py-4 px-4">
                      {instance.status === 'pending' && (
                        <div className="flex items-center gap-2">
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
                        </div>
                      )}
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
            <h2 className="text-xl font-bold mb-4">
              {actionType === 'approve' ? 'Approuver' : 'Rejeter'} le workflow
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <MessageSquare className="w-4 h-4 inline mr-1" />
                  Commentaire {actionType === 'reject' && '(obligatoire)'}
                </label>
                <textarea
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                  className="input h-24"
                  placeholder="Ajoutez un commentaire..."
                />
              </div>

              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setModalOpen(false)}
                  className="btn-secondary"
                >
                  Annuler
                </button>
                <button
                  onClick={submitAction}
                  disabled={
                    approveMutation.isPending || rejectMutation.isPending
                  }
                  className={actionType === 'approve' ? 'btn-primary' : 'btn-danger'}
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
    </div>
  )
}
