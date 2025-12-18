import { useState, useRef, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { queryAI, getAIConfig, updateAIConfig } from '../lib/api'
import {
  Send,
  Bot,
  User,
  Loader2,
  Sparkles,
  Key,
  X,
  Save,
  CheckCircle,
  AlertTriangle,
  Eye,
  EyeOff,
  Shield,
} from 'lucide-react'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export default function AIAssistant() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [showTokenModal, setShowTokenModal] = useState(false)
  const [tokenConfig, setTokenConfig] = useState({
    provider: 'openai',
    api_key: '',
    model: 'gpt-4-turbo-preview',
  })
  const [showApiKey, setShowApiKey] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Charger la config actuelle
  const { data: aiConfig } = useQuery({
    queryKey: ['aiConfig'],
    queryFn: getAIConfig,
  })

  const queryMutation = useMutation({
    mutationFn: (query: string) => queryAI(query, undefined, conversationId || undefined),
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.response,
          timestamp: new Date(),
        },
      ])
      setConversationId(data.conversation_id)
    },
  })

  const updateConfigMutation = useMutation({
    mutationFn: updateAIConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['aiConfig'] })
      setShowTokenModal(false)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || queryMutation.isPending) return

    setMessages((prev) => [
      ...prev,
      {
        role: 'user',
        content: input,
        timestamp: new Date(),
      },
    ])

    queryMutation.mutate(input)
    setInput('')
  }

  const handleOpenTokenModal = () => {
    if (aiConfig) {
      setTokenConfig({
        provider: aiConfig.provider || 'openai',
        api_key: '',
        model: aiConfig.model || 'gpt-4-turbo-preview',
      })
    }
    setShowTokenModal(true)
  }

  const handleSaveToken = () => {
    updateConfigMutation.mutate(tokenConfig)
  }

  const suggestions = [
    'Comment creer une regle de mapping?',
    'Explique le workflow d\'approbation',
    'Comment diagnostiquer une erreur de provisionnement?',
    'Genere un connecteur pour une API REST',
  ]

  const providers = [
    { id: 'openai', name: 'OpenAI', models: ['gpt-4-turbo-preview', 'gpt-4', 'gpt-4o', 'gpt-3.5-turbo'] },
    { id: 'anthropic', name: 'Anthropic', models: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku', 'claude-3.5-sonnet'] },
    { id: 'mistral', name: 'Mistral AI', models: ['mistral-large-latest', 'mistral-medium', 'mistral-small', 'codestral-latest'] },
    { id: 'deepseek', name: 'DeepSeek', models: ['deepseek-chat', 'deepseek-coder'] },
    { id: 'azure', name: 'Azure OpenAI', models: ['gpt-4', 'gpt-4o', 'gpt-35-turbo'] },
  ]

  const selectedProvider = providers.find(p => p.id === tokenConfig.provider)

  return (
    <div className="h-[calc(100vh-12rem)] flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Bot className="w-8 h-8 text-blue-600" />
            Assistant IA
          </h1>
          <p className="text-gray-500 mt-1">
            Posez vos questions sur le provisionnement et l'IAM
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleOpenTokenModal}
            className="btn-secondary flex items-center gap-2"
          >
            <Key className="w-4 h-4" />
            Configurer Token IA
          </button>
          <button
            onClick={() => {
              setMessages([])
              setConversationId(null)
            }}
            className="btn-secondary"
          >
            Nouvelle conversation
          </button>
        </div>
      </div>

      {/* Status du token */}
      {aiConfig && (
        <div className={`mb-4 p-3 rounded-lg flex items-center gap-3 ${
          aiConfig.is_configured
            ? 'bg-green-50 border border-green-200'
            : 'bg-amber-50 border border-amber-200'
        }`}>
          {aiConfig.is_configured ? (
            <>
              <CheckCircle className="w-5 h-5 text-green-600" />
              <div className="flex-1">
                <span className="text-sm font-medium text-green-800">
                  Token IA configure - {aiConfig.provider_name}
                </span>
                <span className="text-xs text-green-600 ml-2">
                  ({aiConfig.model})
                </span>
              </div>
              <Shield className="w-4 h-4 text-green-600" />
              <span className="text-xs text-green-600">Donnees securisees</span>
            </>
          ) : (
            <>
              <AlertTriangle className="w-5 h-5 text-amber-600" />
              <div className="flex-1">
                <span className="text-sm font-medium text-amber-800">
                  Aucun token IA configure
                </span>
                <span className="text-xs text-amber-600 ml-2">
                  Configurez votre propre token pour securiser vos donnees
                </span>
              </div>
              <button
                onClick={handleOpenTokenModal}
                className="text-xs text-amber-700 underline hover:text-amber-900"
              >
                Configurer maintenant
              </button>
            </>
          )}
        </div>
      )}

      {/* Modal de configuration du token */}
      {showTokenModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b bg-gradient-to-r from-purple-600 to-purple-700">
              <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                <Key className="w-6 h-6" />
                Configuration Token IA
              </h2>
              <button
                onClick={() => setShowTokenModal(false)}
                className="text-white/80 hover:text-white"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Info securite */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <Shield className="w-5 h-5 text-blue-600 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-blue-800">
                      Securisez vos donnees d'entreprise
                    </p>
                    <p className="text-xs text-blue-600 mt-1">
                      En utilisant votre propre token IA, vos donnees restent privees
                      et ne transitent pas par des serveurs tiers non autorises.
                    </p>
                  </div>
                </div>
              </div>

              {/* Selection du provider */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Fournisseur IA
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {providers.map((provider) => (
                    <button
                      key={provider.id}
                      type="button"
                      onClick={() => setTokenConfig(prev => ({
                        ...prev,
                        provider: provider.id,
                        model: provider.models[0]
                      }))}
                      className={`p-3 rounded-lg border-2 transition-all text-left ${
                        tokenConfig.provider === provider.id
                          ? 'border-purple-500 bg-purple-50 text-purple-700'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="font-medium">{provider.name}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Selection du modele */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Modele
                </label>
                <select
                  value={tokenConfig.model}
                  onChange={(e) => setTokenConfig(prev => ({ ...prev, model: e.target.value }))}
                  className="input"
                >
                  {selectedProvider?.models.map((model) => (
                    <option key={model} value={model}>{model}</option>
                  ))}
                </select>
              </div>

              {/* Cle API */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Cle API / Token
                </label>
                <div className="relative">
                  <input
                    type={showApiKey ? 'text' : 'password'}
                    value={tokenConfig.api_key}
                    onChange={(e) => setTokenConfig(prev => ({ ...prev, api_key: e.target.value }))}
                    className="input pr-10"
                    placeholder={`Entrez votre cle API ${selectedProvider?.name || ''}`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowApiKey(!showApiKey)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  La cle sera stockee de maniere securisee et chiffree
                </p>
              </div>

              {/* Erreur */}
              {updateConfigMutation.isError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                  Erreur: {(updateConfigMutation.error as any)?.response?.data?.detail || 'Echec de la configuration'}
                </div>
              )}

              {/* Succes */}
              {updateConfigMutation.isSuccess && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" />
                  Configuration enregistree avec succes !
                </div>
              )}
            </div>

            <div className="flex justify-end gap-3 px-6 py-4 bg-gray-50 border-t">
              <button
                onClick={() => setShowTokenModal(false)}
                className="btn-secondary"
              >
                Annuler
              </button>
              <button
                onClick={handleSaveToken}
                disabled={updateConfigMutation.isPending || !tokenConfig.api_key}
                className="btn-primary flex items-center gap-2 disabled:opacity-50"
              >
                {updateConfigMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                Enregistrer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Messages area */}
      <div className="flex-1 bg-white rounded-xl border border-gray-200 overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-gray-500">
              <Sparkles className="w-12 h-12 mb-4 text-blue-200" />
              <p className="text-lg font-medium mb-2">Comment puis-je vous aider?</p>
              <p className="text-sm mb-6">
                Je peux vous assister avec la configuration IAM, les regles de
                mapping, et plus encore.
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {suggestions.map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => {
                      setInput(suggestion)
                    }}
                    className="text-sm px-4 py-2 bg-gray-100 rounded-full hover:bg-gray-200 transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((message, index) => (
              <div
                key={index}
                className={`flex gap-3 ${
                  message.role === 'user' ? 'flex-row-reverse' : ''
                }`}
              >
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {message.role === 'user' ? (
                    <User className="w-5 h-5" />
                  ) : (
                    <Bot className="w-5 h-5" />
                  )}
                </div>
                <div
                  className={`max-w-[70%] p-4 rounded-2xl ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white rounded-tr-none'
                      : 'bg-gray-100 text-gray-800 rounded-tl-none'
                  }`}
                >
                  <div className="whitespace-pre-wrap">{message.content}</div>
                  <div
                    className={`text-xs mt-2 ${
                      message.role === 'user' ? 'text-blue-200' : 'text-gray-400'
                    }`}
                  >
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))
          )}

          {queryMutation.isPending && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
                <Bot className="w-5 h-5 text-gray-600" />
              </div>
              <div className="p-4 bg-gray-100 rounded-2xl rounded-tl-none">
                <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <form
          onSubmit={handleSubmit}
          className="p-4 border-t border-gray-200 bg-gray-50"
        >
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Posez votre question..."
              className="flex-1 input"
              disabled={queryMutation.isPending}
            />
            <button
              type="submit"
              disabled={!input.trim() || queryMutation.isPending}
              className="btn-primary p-3"
            >
              {queryMutation.isPending ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
