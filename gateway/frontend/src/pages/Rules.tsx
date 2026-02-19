/**
 * Rules.tsx - Page de gestion des regles de mapping d'attributs.
 *
 * Fonctionnalites :
 *   - Liste des regles avec filtre par systeme cible
 *   - Creation/edition de regles via modal avec formulaire :
 *     * Nom, type (mapping/calcul/validation/aggregation)
 *     * Systeme cible (dynamique : connecteurs configures + defaults LDAP/AD/SQL/ODOO)
 *     * Expression Jinja2 avec exemples cliquables (login, email, conditionnel, etc.)
 *     * Attributs source (separes par virgules) et attribut cible
 *     * Priorite (slider 1=basse a 100=haute)
 *   - Test de regles avec des donnees JSON d'exemple
 *   - Suppression de regles avec confirmation
 *
 * Les systemes cibles sont construits dynamiquement : on combine les defaults
 * (LDAP, AD, SQL, ODOO) avec les types de connecteurs configures dans la DB.
 * Ainsi, quand un nouveau connecteur est ajoute, il apparait automatiquement
 * dans le dropdown "Systeme cible".
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getRules, createRule, updateRule, deleteRule, testRule, getConnectors } from '../lib/api'
import { Plus, Edit, Trash2, Play, FileCode2, X, Save, Info } from 'lucide-react'

// Types de regles disponibles avec couleurs d'affichage
const RULE_TYPES = [
  { value: 'mapping', label: 'Mapping', color: 'bg-blue-100 text-blue-700' },
  { value: 'calculation', label: 'Calcul', color: 'bg-purple-100 text-purple-700' },
  { value: 'validation', label: 'Validation', color: 'bg-yellow-100 text-yellow-700' },
  { value: 'aggregation', label: 'Aggregation', color: 'bg-green-100 text-green-700' },
]

// Systemes cibles par defaut (completes dynamiquement par les connecteurs configures)
const DEFAULT_TARGET_SYSTEMS = ['LDAP', 'AD', 'SQL', 'ODOO']

// Exemples d'expressions Jinja2 cliquables dans le formulaire de creation
const JINJA2_EXAMPLES = [
  { label: 'Login (prenom.nom)', expr: '{{ firstname | normalize_name }}.{{ lastname | normalize_name }}' },
  { label: 'Email', expr: '{{ firstname | normalize_name }}.{{ lastname | normalize_name }}@example.com' },
  { label: 'Conditionnel', expr: "{% if department == 'IT' %}ADMIN{% else %}USER{% endif %}" },
  { label: 'Majuscule', expr: '{{ lastname | upper }}' },
]

// Formulaire vide par defaut (utilise pour la creation et le reset)
const emptyForm = {
  name: '',
  rule_type: 'mapping',
  target_system: 'LDAP',
  expression: '',
  source_attributes: '',
  target_attribute: '',
  priority: 50,
  description: '',
}

export default function Rules() {
  const [selectedTarget, setSelectedTarget] = useState('')
  const [testModalOpen, setTestModalOpen] = useState(false)
  const [formModalOpen, setFormModalOpen] = useState(false)
  const [editingRule, setEditingRule] = useState<any>(null)
  const [formData, setFormData] = useState(emptyForm)
  const [selectedRule, setSelectedRule] = useState<any>(null)
  const [testData, setTestData] = useState('{"firstname": "Jean", "lastname": "Dupont"}')
  const [testResult, setTestResult] = useState<any>(null)
  const [formError, setFormError] = useState('')
  const queryClient = useQueryClient()

  const { data: rules, isLoading } = useQuery({
    queryKey: ['rules', selectedTarget],
    queryFn: () => getRules({ target_system: selectedTarget || undefined }),
  })

  const { data: connectorsList } = useQuery({
    queryKey: ['connectors'],
    queryFn: () => getConnectors(),
  })

  // Build target systems from connectors + defaults
  const targetSystems = (() => {
    const systems = new Set(DEFAULT_TARGET_SYSTEMS)
    if (connectorsList) {
      connectorsList.forEach((c: any) => {
        if (c.connector_subtype) systems.add(c.connector_subtype.toUpperCase())
        if (c.connector_type) systems.add(c.connector_type.toUpperCase())
      })
    }
    return Array.from(systems)
  })()

  const deleteMutation = useMutation({
    mutationFn: deleteRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rules'] })
    },
  })

  const createMutation = useMutation({
    mutationFn: createRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rules'] })
      closeFormModal()
    },
    onError: (err: any) => {
      setFormError(err?.response?.data?.detail || 'Erreur lors de la creation')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => updateRule(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rules'] })
      closeFormModal()
    },
    onError: (err: any) => {
      setFormError(err?.response?.data?.detail || 'Erreur lors de la modification')
    },
  })

  const testMutation = useMutation({
    mutationFn: ({ ruleId, data }: { ruleId: string; data: any }) =>
      testRule(ruleId, data),
    onSuccess: (data) => {
      setTestResult(data)
    },
  })

  const openCreateModal = () => {
    setEditingRule(null)
    setFormData(emptyForm)
    setFormError('')
    setFormModalOpen(true)
  }

  const openEditModal = (rule: any) => {
    setEditingRule(rule)
    setFormData({
      name: rule.name || '',
      rule_type: rule.rule_type || 'mapping',
      target_system: rule.target_system || 'LDAP',
      expression: rule.expression || '',
      source_attributes: (() => {
        try { return JSON.parse(rule.source_attributes || '[]').join(', ') } catch { return '' }
      })(),
      target_attribute: rule.target_attribute || '',
      priority: rule.priority || 50,
      description: rule.description || '',
    })
    setFormError('')
    setFormModalOpen(true)
  }

  const closeFormModal = () => {
    setFormModalOpen(false)
    setEditingRule(null)
    setFormData(emptyForm)
    setFormError('')
  }

  const handleSubmit = () => {
    if (!formData.name.trim()) { setFormError('Le nom est requis'); return }
    if (!formData.expression.trim()) { setFormError("L'expression est requise"); return }
    if (!formData.target_attribute.trim()) { setFormError("L'attribut cible est requis"); return }

    const payload = {
      name: formData.name.trim(),
      rule_type: formData.rule_type,
      target_system: formData.target_system,
      expression: formData.expression.trim(),
      source_attributes: JSON.stringify(
        formData.source_attributes.split(',').map((s: string) => s.trim()).filter(Boolean)
      ),
      target_attribute: formData.target_attribute.trim(),
      priority: formData.priority,
      description: formData.description.trim(),
    }

    if (editingRule) {
      updateMutation.mutate({ id: editingRule.id, data: payload })
    } else {
      createMutation.mutate(payload)
    }
  }

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
    return RULE_TYPES.find(t => t.value === type)?.color || 'bg-gray-100 text-gray-700'
  }

  const isSaving = createMutation.isPending || updateMutation.isPending

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Regles de calcul</h1>
          <p className="text-gray-500 mt-1">
            Configurez les regles de mapping et calcul d'attributs
          </p>
        </div>
        <button onClick={openCreateModal} className="btn-primary flex items-center gap-2">
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
            {targetSystems.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
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
                      className={`px-2 py-1 text-xs rounded-full ${getRuleTypeColor(rule.rule_type)}`}
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
                    onClick={() => openEditModal(rule)}
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

      {/* Create/Edit Modal */}
      {formModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold">
                {editingRule ? 'Modifier la regle' : 'Nouvelle regle'}
              </h2>
              <button onClick={closeFormModal} className="p-1 hover:bg-gray-100 rounded-lg">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nom *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input"
                  placeholder="Ex: LDAP Login Generator"
                />
              </div>

              {/* Type + Target */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                  <select
                    value={formData.rule_type}
                    onChange={(e) => setFormData({ ...formData, rule_type: e.target.value })}
                    className="input"
                  >
                    {RULE_TYPES.map(t => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Systeme cible</label>
                  <select
                    value={formData.target_system}
                    onChange={(e) => setFormData({ ...formData, target_system: e.target.value })}
                    className="input"
                  >
                    {targetSystems.map(s => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Expression */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Expression Jinja2 *</label>
                <textarea
                  value={formData.expression}
                  onChange={(e) => setFormData({ ...formData, expression: e.target.value })}
                  className="input h-24 font-mono text-sm"
                  placeholder="{{ firstname | normalize_name }}.{{ lastname | normalize_name }}"
                />
                <div className="mt-2">
                  <div className="flex items-center gap-1 text-xs text-gray-400 mb-1">
                    <Info className="w-3 h-3" />
                    Exemples (cliquez pour inserer) :
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {JINJA2_EXAMPLES.map(ex => (
                      <button
                        key={ex.label}
                        type="button"
                        onClick={() => setFormData({ ...formData, expression: ex.expr })}
                        className="px-2 py-0.5 text-xs bg-gray-100 hover:bg-blue-100 text-gray-600 hover:text-blue-700 rounded transition-colors"
                      >
                        {ex.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Source + Target attributes */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Attributs source
                  </label>
                  <input
                    type="text"
                    value={formData.source_attributes}
                    onChange={(e) => setFormData({ ...formData, source_attributes: e.target.value })}
                    className="input"
                    placeholder="firstname, lastname, department"
                  />
                  <p className="text-xs text-gray-400 mt-1">Separes par des virgules</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Attribut cible *
                  </label>
                  <input
                    type="text"
                    value={formData.target_attribute}
                    onChange={(e) => setFormData({ ...formData, target_attribute: e.target.value })}
                    className="input"
                    placeholder="Ex: uid, mail, role"
                  />
                </div>
              </div>

              {/* Priority */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Priorite ({formData.priority})
                </label>
                <input
                  type="range"
                  min="1"
                  max="100"
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-400">
                  <span>1 (basse)</span>
                  <span>100 (haute)</span>
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="input h-16"
                  placeholder="Description optionnelle de la regle"
                />
              </div>

              {/* Error */}
              {formError && (
                <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                  {formError}
                </div>
              )}

              {/* Actions */}
              <div className="flex justify-end gap-3 pt-2">
                <button onClick={closeFormModal} className="btn-secondary">
                  Annuler
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={isSaving}
                  className="btn-primary flex items-center gap-2"
                >
                  <Save className="w-4 h-4" />
                  {isSaving ? 'Enregistrement...' : editingRule ? 'Modifier' : 'Creer'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

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
