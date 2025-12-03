import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getRules, deleteRule, testRule } from '../lib/api'
import { Plus, Edit, Trash2, Play, FileCode2 } from 'lucide-react'

export default function Rules() {
  const [selectedTarget, setSelectedTarget] = useState('')
  const [testModalOpen, setTestModalOpen] = useState(false)
  const [selectedRule, setSelectedRule] = useState<any>(null)
  const [testData, setTestData] = useState('{"firstname": "Jean", "lastname": "Dupont"}')
  const [testResult, setTestResult] = useState<any>(null)
  const queryClient = useQueryClient()

  const { data: rules, isLoading } = useQuery({
    queryKey: ['rules', selectedTarget],
    queryFn: () => getRules({ target_system: selectedTarget || undefined }),
  })

  const deleteMutation = useMutation({
    mutationFn: deleteRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rules'] })
    },
  })

  const testMutation = useMutation({
    mutationFn: ({ ruleId, data }: { ruleId: string; data: any }) =>
      testRule(ruleId, data),
    onSuccess: (data) => {
      setTestResult(data)
    },
  })

  const handleTest = () => {
    if (selectedRule) {
      try {
        const data = JSON.parse(testData)
        testMutation.mutate({ ruleId: selectedRule.id, data })
      } catch (e) {
        setTestResult({ error: 'JSON invalide' })
      }
    }
  }

  const getRuleTypeColor = (type: string) => {
    switch (type) {
      case 'mapping':
        return 'bg-blue-100 text-blue-700'
      case 'calculation':
        return 'bg-purple-100 text-purple-700'
      case 'aggregation':
        return 'bg-green-100 text-green-700'
      case 'validation':
        return 'bg-yellow-100 text-yellow-700'
      default:
        return 'bg-gray-100 text-gray-700'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Regles de calcul</h1>
          <p className="text-gray-500 mt-1">
            Configurez les regles de mapping et calcul d'attributs
          </p>
        </div>
        <button className="btn-primary flex items-center gap-2">
          <Plus className="w-5 h-5" />
          Nouvelle regle
        </button>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex gap-4">
          <select
            value={selectedTarget}
            onChange={(e) => setSelectedTarget(e.target.value)}
            className="input w-48"
          >
            <option value="">Tous les systemes</option>
            <option value="LDAP">LDAP</option>
            <option value="AD">Active Directory</option>
            <option value="SQL">SQL</option>
            <option value="ODOO">Odoo</option>
          </select>
        </div>
      </div>

      {/* Rules list */}
      <div className="grid gap-4">
        {isLoading ? (
          <div className="card text-center py-8 text-gray-500">Chargement...</div>
        ) : rules?.length === 0 ? (
          <div className="card text-center py-8 text-gray-500">
            Aucune regle trouvee
          </div>
        ) : (
          rules?.map((rule: any) => (
            <div key={rule.id} className="card">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <FileCode2 className="w-5 h-5 text-gray-400" />
                    <h3 className="font-semibold text-lg">{rule.name}</h3>
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${getRuleTypeColor(
                        rule.rule_type
                      )}`}
                    >
                      {rule.rule_type}
                    </span>
                    <span className="px-2 py-1 text-xs bg-gray-100 rounded-full">
                      {rule.target_system}
                    </span>
                  </div>
                  {rule.description && (
                    <p className="text-gray-500 mt-2">{rule.description}</p>
                  )}
                  <div className="mt-4 bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-500 mb-2">Expression:</p>
                    <code className="text-sm font-mono">{rule.expression}</code>
                  </div>
                  <div className="mt-3 flex items-center gap-4 text-sm text-gray-500">
                    <span>
                      Sources: {JSON.parse(rule.source_attributes || '[]').join(', ')}
                    </span>
                    <span>Cible: {rule.target_attribute}</span>
                    <span>Priorite: {rule.priority}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      setSelectedRule(rule)
                      setTestModalOpen(true)
                      setTestResult(null)
                    }}
                    className="p-2 text-green-600 hover:bg-green-50 rounded-lg"
                    title="Tester"
                  >
                    <Play className="w-5 h-5" />
                  </button>
                  <button
                    className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                    title="Modifier"
                  >
                    <Edit className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => {
                      if (confirm('Supprimer cette regle ?')) {
                        deleteMutation.mutate(rule.id)
                      }
                    }}
                    className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                    title="Supprimer"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Test Modal */}
      {testModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg p-6">
            <h2 className="text-xl font-bold mb-4">
              Tester la regle: {selectedRule?.name}
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Donnees de test (JSON)
                </label>
                <textarea
                  value={testData}
                  onChange={(e) => setTestData(e.target.value)}
                  className="input h-32 font-mono text-sm"
                />
              </div>

              {testResult && (
                <div
                  className={`p-4 rounded-lg ${
                    testResult.success
                      ? 'bg-green-50 text-green-700'
                      : 'bg-red-50 text-red-700'
                  }`}
                >
                  <p className="font-medium">
                    {testResult.success ? 'Succes' : 'Erreur'}
                  </p>
                  {testResult.output_value !== undefined && (
                    <p className="mt-2">
                      Resultat:{' '}
                      <code className="bg-white px-2 py-1 rounded">
                        {JSON.stringify(testResult.output_value)}
                      </code>
                    </p>
                  )}
                  {testResult.error && (
                    <p className="mt-2 text-sm">{testResult.error}</p>
                  )}
                  {testResult.execution_time_ms !== undefined && (
                    <p className="mt-2 text-sm">
                      Temps: {testResult.execution_time_ms.toFixed(2)}ms
                    </p>
                  )}
                </div>
              )}

              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setTestModalOpen(false)}
                  className="btn-secondary"
                >
                  Fermer
                </button>
                <button
                  onClick={handleTest}
                  disabled={testMutation.isPending}
                  className="btn-primary"
                >
                  {testMutation.isPending ? 'Test...' : 'Tester'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
