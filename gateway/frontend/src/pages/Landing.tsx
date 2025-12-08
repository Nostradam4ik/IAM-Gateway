import { Link } from 'react-router-dom'
import {
  Shield, Users, Workflow, Lock, Zap, Globe, CheckCircle, ArrowRight,
  Database, Key, Server, Activity, Layers, GitBranch, Clock, Eye,
  ChevronRight, Star, Play
} from 'lucide-react'

export default function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white overflow-hidden">
      {/* Animated background elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse" style={{animationDelay: '0.5s'}}></div>
        <div className="absolute top-1/2 left-1/2 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl animate-pulse" style={{animationDelay: '0.3s'}}></div>
      </div>

      {/* Header */}
      <header className="relative z-50 border-b border-white/10 bg-black/30 backdrop-blur-xl sticky top-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="absolute inset-0 bg-blue-500 rounded-xl blur-lg opacity-50"></div>
                <div className="relative bg-gradient-to-br from-blue-500 to-purple-600 p-2.5 rounded-xl">
                  <Shield className="h-7 w-7 text-white" />
                </div>
              </div>
              <div>
                <span className="text-2xl font-bold text-white">
                  Gateway IAM
                </span>
                <span className="block text-[10px] uppercase tracking-widest text-blue-400 font-medium -mt-1">
                  Enterprise Edition
                </span>
              </div>
            </div>

            <nav className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-gray-300 hover:text-white transition-colors text-sm font-medium">Features</a>
              <a href="#architecture" className="text-gray-300 hover:text-white transition-colors text-sm font-medium">Architecture</a>
              <a href="#services" className="text-gray-300 hover:text-white transition-colors text-sm font-medium">Services</a>
              <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer"
                 className="text-gray-300 hover:text-white transition-colors text-sm font-medium flex items-center gap-1">
                API Docs
                <ArrowRight className="h-3 w-3" />
              </a>
            </nav>

            <div className="flex items-center gap-4">
              <Link
                to="/login"
                className="group relative px-6 py-2.5 rounded-xl text-sm font-semibold overflow-hidden bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 transition-all"
              >
                <span className="relative flex items-center gap-2 text-white">
                  Sign In
                  <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                </span>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-32">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          <div className="space-y-8">
            <div className="inline-flex items-center gap-2 bg-white/5 border border-white/10 text-blue-300 px-4 py-2 rounded-full text-sm font-medium">
              <Zap className="h-4 w-4" />
              Enterprise Identity & Access Management
              <ChevronRight className="h-4 w-4" />
            </div>

            <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold leading-tight">
              <span className="text-white">Unified IAM</span>
              <br />
              <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                Gateway Platform
              </span>
            </h1>

            <p className="text-xl text-gray-400 leading-relaxed max-w-xl">
              Orchestrate identity provisioning across <span className="text-white font-medium">LDAP</span>, <span className="text-white font-medium">SQL</span>, <span className="text-white font-medium">Odoo</span>, and more.
              Powered by <span className="text-blue-400 font-medium">MidPoint</span>, with AI-driven rules and advanced workflows.
            </p>

            <div className="flex flex-wrap gap-4">
              <Link
                to="/login"
                className="group relative inline-flex items-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-4 rounded-xl text-lg font-semibold hover:shadow-2xl hover:shadow-blue-500/25 transition-all hover:-translate-y-0.5"
              >
                <Play className="h-5 w-5" />
                Get Started
                <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </Link>
              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 bg-white/5 border border-white/10 text-white px-8 py-4 rounded-xl text-lg font-semibold hover:bg-white/10 transition-all hover:-translate-y-0.5"
              >
                <Eye className="h-5 w-5" />
                View API Docs
              </a>
            </div>

            {/* Trust badges */}
            <div className="flex items-center gap-6 pt-4">
              <div className="flex items-center gap-2 text-gray-500 text-sm">
                <Shield className="h-4 w-4 text-green-500" />
                Enterprise Ready
              </div>
              <div className="flex items-center gap-2 text-gray-500 text-sm">
                <Lock className="h-4 w-4 text-blue-500" />
                SOC2 Compliant
              </div>
              <div className="flex items-center gap-2 text-gray-500 text-sm">
                <Star className="h-4 w-4 text-yellow-500" />
                Open Source
              </div>
            </div>
          </div>

          {/* Hero Visual */}
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-3xl blur-3xl"></div>
            <div className="relative bg-gradient-to-br from-white/5 to-white/0 border border-white/10 rounded-3xl p-8 backdrop-blur-sm">
              {/* Architecture diagram */}
              <div className="space-y-6">
                {/* Source systems */}
                <div className="text-center">
                  <span className="text-xs uppercase tracking-wider text-gray-500 font-medium">Source Systems</span>
                  <div className="flex justify-center gap-4 mt-3">
                    {['HR', 'ERP', 'CRM'].map((sys, i) => (
                      <div key={sys} className="flex flex-col items-center gap-2" style={{animation: 'float 3s ease-in-out infinite', animationDelay: `${i * 0.2}s`}}>
                        <div className="bg-gradient-to-br from-emerald-500/20 to-emerald-600/20 border border-emerald-500/30 p-3 rounded-xl">
                          <Database className="h-5 w-5 text-emerald-400" />
                        </div>
                        <span className="text-xs text-gray-400">{sys}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Arrows down */}
                <div className="flex justify-center">
                  <div className="h-8 w-px bg-gradient-to-b from-emerald-500/50 to-blue-500/50"></div>
                </div>

                {/* Gateway core */}
                <div className="relative">
                  <div className="absolute inset-0 bg-blue-500/20 rounded-2xl blur-xl animate-pulse"></div>
                  <div className="relative bg-gradient-to-br from-blue-600/30 to-purple-600/30 border-2 border-blue-500/30 rounded-2xl p-6 text-center">
                    <div className="flex justify-center mb-3">
                      <div className="bg-gradient-to-br from-blue-500 to-purple-500 p-3 rounded-xl shadow-lg shadow-blue-500/30">
                        <Shield className="h-8 w-8 text-white" />
                      </div>
                    </div>
                    <h3 className="text-lg font-bold text-white">Gateway IAM</h3>
                    <p className="text-xs text-gray-400 mt-1">Identity Orchestration Engine</p>
                    <div className="flex justify-center gap-2 mt-4">
                      {['Rules', 'Workflows', 'Sync'].map((feat) => (
                        <span key={feat} className="text-xs bg-white/10 px-2 py-1 rounded-full text-blue-300">{feat}</span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Arrows down */}
                <div className="flex justify-center">
                  <div className="h-8 w-px bg-gradient-to-b from-blue-500/50 to-orange-500/50"></div>
                </div>

                {/* Target systems */}
                <div className="text-center">
                  <span className="text-xs uppercase tracking-wider text-gray-500 font-medium">Target Systems</span>
                  <div className="flex justify-center gap-3 mt-3 flex-wrap">
                    <div className="flex flex-col items-center gap-2" style={{animation: 'float 3s ease-in-out infinite'}}>
                      <div className="bg-gradient-to-br from-blue-500/20 to-blue-600/20 border border-blue-500/30 p-2.5 rounded-lg">
                        <Users className="h-4 w-4 text-blue-400" />
                      </div>
                      <span className="text-[10px] text-gray-400">LDAP</span>
                    </div>
                    <div className="flex flex-col items-center gap-2" style={{animation: 'float 3s ease-in-out infinite', animationDelay: '0.15s'}}>
                      <div className="bg-gradient-to-br from-purple-500/20 to-purple-600/20 border border-purple-500/30 p-2.5 rounded-lg">
                        <Server className="h-4 w-4 text-purple-400" />
                      </div>
                      <span className="text-[10px] text-gray-400">Odoo</span>
                    </div>
                    <div className="flex flex-col items-center gap-2" style={{animation: 'float 3s ease-in-out infinite', animationDelay: '0.3s'}}>
                      <div className="bg-gradient-to-br from-green-500/20 to-green-600/20 border border-green-500/30 p-2.5 rounded-lg">
                        <Database className="h-4 w-4 text-green-400" />
                      </div>
                      <span className="text-[10px] text-gray-400">SQL</span>
                    </div>
                    <div className="flex flex-col items-center gap-2" style={{animation: 'float 3s ease-in-out infinite', animationDelay: '0.45s'}}>
                      <div className="bg-gradient-to-br from-orange-500/20 to-orange-600/20 border border-orange-500/30 p-2.5 rounded-lg">
                        <Key className="h-4 w-4 text-orange-400" />
                      </div>
                      <span className="text-[10px] text-gray-400">Keycloak</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-24">
          <div className="group relative">
            <div className="relative bg-white/5 border border-white/10 rounded-2xl p-6 text-center hover:border-white/20 transition-colors hover:bg-white/5">
              <div className="inline-flex p-3 rounded-xl bg-blue-500/10 mb-4">
                <Server className="h-6 w-6 text-blue-400" />
              </div>
              <div className="text-3xl font-bold text-blue-400">6+</div>
              <div className="text-gray-400 mt-1 text-sm">Target Systems</div>
            </div>
          </div>
          <div className="group relative">
            <div className="relative bg-white/5 border border-white/10 rounded-2xl p-6 text-center hover:border-white/20 transition-colors hover:bg-white/5">
              <div className="inline-flex p-3 rounded-xl bg-purple-500/10 mb-4">
                <Zap className="h-6 w-6 text-purple-400" />
              </div>
              <div className="text-3xl font-bold text-purple-400">AI</div>
              <div className="text-gray-400 mt-1 text-sm">Powered Rules</div>
            </div>
          </div>
          <div className="group relative">
            <div className="relative bg-white/5 border border-white/10 rounded-2xl p-6 text-center hover:border-white/20 transition-colors hover:bg-white/5">
              <div className="inline-flex p-3 rounded-xl bg-green-500/10 mb-4">
                <GitBranch className="h-6 w-6 text-green-400" />
              </div>
              <div className="text-3xl font-bold text-green-400">Multi</div>
              <div className="text-gray-400 mt-1 text-sm">Level Workflows</div>
            </div>
          </div>
          <div className="group relative">
            <div className="relative bg-white/5 border border-white/10 rounded-2xl p-6 text-center hover:border-white/20 transition-colors hover:bg-white/5">
              <div className="inline-flex p-3 rounded-xl bg-orange-500/10 mb-4">
                <Activity className="h-6 w-6 text-orange-400" />
              </div>
              <div className="text-3xl font-bold text-orange-400">Real-time</div>
              <div className="text-gray-400 mt-1 text-sm">Reconciliation</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="relative z-10 py-32 border-t border-white/5">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-blue-950/20 to-transparent"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-20">
            <span className="inline-flex items-center gap-2 bg-blue-500/10 text-blue-400 px-4 py-2 rounded-full text-sm font-medium mb-6">
              <Layers className="h-4 w-4" />
              Core Capabilities
            </span>
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Powerful Features for
              <span className="block bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Enterprise IAM
              </span>
            </h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              Everything you need to manage identities at scale with security and compliance
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="group relative transition-transform duration-300 hover:-translate-y-2">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl opacity-0 group-hover:opacity-10 transition-opacity blur-xl"></div>
              <div className="relative h-full bg-white/5 border border-white/10 rounded-2xl p-8 hover:border-blue-500/30 transition-all">
                <div className="inline-flex p-4 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 mb-6">
                  <Users className="h-6 w-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">Multi-System Provisioning</h3>
                <p className="text-gray-400 leading-relaxed">Provision user accounts across LDAP, SQL, Odoo, Keycloak, and more from a single unified API.</p>
              </div>
            </div>

            {/* Feature 2 */}
            <div className="group relative transition-transform duration-300 hover:-translate-y-2">
              <div className="absolute inset-0 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl opacity-0 group-hover:opacity-10 transition-opacity blur-xl"></div>
              <div className="relative h-full bg-white/5 border border-white/10 rounded-2xl p-8 hover:border-purple-500/30 transition-all">
                <div className="inline-flex p-4 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 mb-6">
                  <Workflow className="h-6 w-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">Smart Workflows</h3>
                <p className="text-gray-400 leading-relaxed">Configure multi-level approval workflows with conditional routing and real-time notifications.</p>
              </div>
            </div>

            {/* Feature 3 */}
            <div className="group relative transition-transform duration-300 hover:-translate-y-2">
              <div className="absolute inset-0 bg-gradient-to-br from-green-500 to-emerald-500 rounded-2xl opacity-0 group-hover:opacity-10 transition-opacity blur-xl"></div>
              <div className="relative h-full bg-white/5 border border-white/10 rounded-2xl p-8 hover:border-green-500/30 transition-all">
                <div className="inline-flex p-4 rounded-xl bg-gradient-to-br from-green-500 to-emerald-500 mb-6">
                  <Zap className="h-6 w-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">AI Rule Engine</h3>
                <p className="text-gray-400 leading-relaxed">Use Jinja2 templates and AI to dynamically calculate user attributes based on business rules.</p>
              </div>
            </div>

            {/* Feature 4 */}
            <div className="group relative transition-transform duration-300 hover:-translate-y-2">
              <div className="absolute inset-0 bg-gradient-to-br from-orange-500 to-amber-500 rounded-2xl opacity-0 group-hover:opacity-10 transition-opacity blur-xl"></div>
              <div className="relative h-full bg-white/5 border border-white/10 rounded-2xl p-8 hover:border-orange-500/30 transition-all">
                <div className="inline-flex p-4 rounded-xl bg-gradient-to-br from-orange-500 to-amber-500 mb-6">
                  <Lock className="h-6 w-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">MidPoint Integration</h3>
                <p className="text-gray-400 leading-relaxed">Powered by Evolveum MidPoint 4.8 with PostgreSQL for enterprise-grade identity orchestration.</p>
              </div>
            </div>

            {/* Feature 5 */}
            <div className="group relative transition-transform duration-300 hover:-translate-y-2">
              <div className="absolute inset-0 bg-gradient-to-br from-red-500 to-rose-500 rounded-2xl opacity-0 group-hover:opacity-10 transition-opacity blur-xl"></div>
              <div className="relative h-full bg-white/5 border border-white/10 rounded-2xl p-8 hover:border-red-500/30 transition-all">
                <div className="inline-flex p-4 rounded-xl bg-gradient-to-br from-red-500 to-rose-500 mb-6">
                  <Globe className="h-6 w-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">Reconciliation</h3>
                <p className="text-gray-400 leading-relaxed">Detect and resolve discrepancies between source and target systems automatically.</p>
              </div>
            </div>

            {/* Feature 6 */}
            <div className="group relative transition-transform duration-300 hover:-translate-y-2">
              <div className="absolute inset-0 bg-gradient-to-br from-indigo-500 to-violet-500 rounded-2xl opacity-0 group-hover:opacity-10 transition-opacity blur-xl"></div>
              <div className="relative h-full bg-white/5 border border-white/10 rounded-2xl p-8 hover:border-indigo-500/30 transition-all">
                <div className="inline-flex p-4 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-500 mb-6">
                  <CheckCircle className="h-6 w-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">Audit & Compliance</h3>
                <p className="text-gray-400 leading-relaxed">Complete audit trail with searchable logs for compliance and security analysis.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Architecture Section */}
      <section id="architecture" className="relative z-10 py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div>
              <span className="inline-flex items-center gap-2 bg-purple-500/10 text-purple-400 px-4 py-2 rounded-full text-sm font-medium mb-6">
                <Server className="h-4 w-4" />
                Technical Architecture
              </span>
              <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
                Built for Scale &
                <span className="block bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                  Reliability
                </span>
              </h2>
              <p className="text-xl text-gray-400 mb-8">
                Modern microservices architecture with containerized deployment and comprehensive monitoring.
              </p>

              <div className="space-y-4">
                <div className="flex items-center gap-4 text-gray-300">
                  <div className="p-2 bg-white/5 rounded-lg">
                    <Database className="h-5 w-5 text-purple-400" />
                  </div>
                  <span>PostgreSQL for persistent data storage</span>
                </div>
                <div className="flex items-center gap-4 text-gray-300">
                  <div className="p-2 bg-white/5 rounded-lg">
                    <Activity className="h-5 w-5 text-purple-400" />
                  </div>
                  <span>Redis for caching and sessions</span>
                </div>
                <div className="flex items-center gap-4 text-gray-300">
                  <div className="p-2 bg-white/5 rounded-lg">
                    <Layers className="h-5 w-5 text-purple-400" />
                  </div>
                  <span>Qdrant for AI vector embeddings</span>
                </div>
                <div className="flex items-center gap-4 text-gray-300">
                  <div className="p-2 bg-white/5 rounded-lg">
                    <Clock className="h-5 w-5 text-purple-400" />
                  </div>
                  <span>Real-time event processing</span>
                </div>
              </div>
            </div>

            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-3xl blur-3xl"></div>
              <div className="relative bg-white/5 border border-white/10 rounded-3xl p-8">
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-white/5 border border-white/10 rounded-xl p-4 text-center hover:bg-white/10 transition-colors">
                    <div className="text-sm font-semibold text-white">FastAPI</div>
                    <div className="text-xs text-gray-500 mt-1">Backend</div>
                  </div>
                  <div className="bg-white/5 border border-white/10 rounded-xl p-4 text-center hover:bg-white/10 transition-colors">
                    <div className="text-sm font-semibold text-white">React</div>
                    <div className="text-xs text-gray-500 mt-1">Frontend</div>
                  </div>
                  <div className="bg-white/5 border border-white/10 rounded-xl p-4 text-center hover:bg-white/10 transition-colors">
                    <div className="text-sm font-semibold text-white">MidPoint</div>
                    <div className="text-xs text-gray-500 mt-1">IAM Core</div>
                  </div>
                  <div className="bg-white/5 border border-white/10 rounded-xl p-4 text-center hover:bg-white/10 transition-colors">
                    <div className="text-sm font-semibold text-white">PostgreSQL</div>
                    <div className="text-xs text-gray-500 mt-1">Database</div>
                  </div>
                  <div className="bg-white/5 border border-white/10 rounded-xl p-4 text-center hover:bg-white/10 transition-colors">
                    <div className="text-sm font-semibold text-white">Redis</div>
                    <div className="text-xs text-gray-500 mt-1">Cache</div>
                  </div>
                  <div className="bg-white/5 border border-white/10 rounded-xl p-4 text-center hover:bg-white/10 transition-colors">
                    <div className="text-sm font-semibold text-white">Qdrant</div>
                    <div className="text-xs text-gray-500 mt-1">Vector DB</div>
                  </div>
                  <div className="bg-white/5 border border-white/10 rounded-xl p-4 text-center hover:bg-white/10 transition-colors">
                    <div className="text-sm font-semibold text-white">OpenLDAP</div>
                    <div className="text-xs text-gray-500 mt-1">Directory</div>
                  </div>
                  <div className="bg-white/5 border border-white/10 rounded-xl p-4 text-center hover:bg-white/10 transition-colors">
                    <div className="text-sm font-semibold text-white">Keycloak</div>
                    <div className="text-xs text-gray-500 mt-1">SSO</div>
                  </div>
                  <div className="bg-white/5 border border-white/10 rounded-xl p-4 text-center hover:bg-white/10 transition-colors">
                    <div className="text-sm font-semibold text-white">Odoo</div>
                    <div className="text-xs text-gray-500 mt-1">ERP</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Services Section */}
      <section id="services" className="relative z-10 py-32 border-t border-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <span className="inline-flex items-center gap-2 bg-green-500/10 text-green-400 px-4 py-2 rounded-full text-sm font-medium mb-6">
              <Globe className="h-4 w-4" />
              Connected Services
            </span>
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Access All Your
              <span className="block bg-gradient-to-r from-green-400 to-cyan-400 bg-clip-text text-transparent">
                Management Tools
              </span>
            </h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              Quick access to all integrated services and management interfaces
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* MidPoint */}
            <a
              href="http://localhost:8080/midpoint"
              target="_blank"
              rel="noopener noreferrer"
              className="group relative transition-transform duration-300 hover:-translate-y-2"
            >
              <div className="relative bg-white/5 border border-white/10 rounded-2xl p-6 hover:border-blue-500/30 transition-all h-full">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 rounded-xl bg-blue-500/10">
                    <Shield className="h-6 w-6 text-blue-400" />
                  </div>
                  <span className="text-xs font-mono text-gray-500 bg-white/5 px-2 py-1 rounded">:8080</span>
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">MidPoint</h3>
                <p className="text-gray-400 text-sm mb-4">Identity orchestration and governance platform</p>
                <div className="text-sm font-medium text-blue-400 flex items-center gap-1 group-hover:gap-2 transition-all">
                  Open Interface
                  <ArrowRight className="h-4 w-4" />
                </div>
              </div>
            </a>

            {/* Gateway API */}
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="group relative transition-transform duration-300 hover:-translate-y-2"
            >
              <div className="relative bg-white/5 border border-white/10 rounded-2xl p-6 hover:border-purple-500/30 transition-all h-full">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 rounded-xl bg-purple-500/10">
                    <Zap className="h-6 w-6 text-purple-400" />
                  </div>
                  <span className="text-xs font-mono text-gray-500 bg-white/5 px-2 py-1 rounded">:8000</span>
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Gateway API</h3>
                <p className="text-gray-400 text-sm mb-4">RESTful API for provisioning and management</p>
                <div className="text-sm font-medium text-purple-400 flex items-center gap-1 group-hover:gap-2 transition-all">
                  Open Interface
                  <ArrowRight className="h-4 w-4" />
                </div>
              </div>
            </a>

            {/* Odoo ERP */}
            <a
              href="http://localhost:8069"
              target="_blank"
              rel="noopener noreferrer"
              className="group relative transition-transform duration-300 hover:-translate-y-2"
            >
              <div className="relative bg-white/5 border border-white/10 rounded-2xl p-6 hover:border-green-500/30 transition-all h-full">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 rounded-xl bg-green-500/10">
                    <Users className="h-6 w-6 text-green-400" />
                  </div>
                  <span className="text-xs font-mono text-gray-500 bg-white/5 px-2 py-1 rounded">:8069</span>
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Odoo ERP</h3>
                <p className="text-gray-400 text-sm mb-4">Enterprise resource planning system</p>
                <div className="text-sm font-medium text-green-400 flex items-center gap-1 group-hover:gap-2 transition-all">
                  Open Interface
                  <ArrowRight className="h-4 w-4" />
                </div>
              </div>
            </a>

            {/* Keycloak */}
            <a
              href="http://localhost:8081"
              target="_blank"
              rel="noopener noreferrer"
              className="group relative transition-transform duration-300 hover:-translate-y-2"
            >
              <div className="relative bg-white/5 border border-white/10 rounded-2xl p-6 hover:border-orange-500/30 transition-all h-full">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 rounded-xl bg-orange-500/10">
                    <Key className="h-6 w-6 text-orange-400" />
                  </div>
                  <span className="text-xs font-mono text-gray-500 bg-white/5 px-2 py-1 rounded">:8081</span>
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Keycloak</h3>
                <p className="text-gray-400 text-sm mb-4">Identity and access management solution</p>
                <div className="text-sm font-medium text-orange-400 flex items-center gap-1 group-hover:gap-2 transition-all">
                  Open Interface
                  <ArrowRight className="h-4 w-4" />
                </div>
              </div>
            </a>

            {/* phpLDAPadmin */}
            <a
              href="http://localhost:8088"
              target="_blank"
              rel="noopener noreferrer"
              className="group relative transition-transform duration-300 hover:-translate-y-2"
            >
              <div className="relative bg-white/5 border border-white/10 rounded-2xl p-6 hover:border-red-500/30 transition-all h-full">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 rounded-xl bg-red-500/10">
                    <Database className="h-6 w-6 text-red-400" />
                  </div>
                  <span className="text-xs font-mono text-gray-500 bg-white/5 px-2 py-1 rounded">:8088</span>
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">phpLDAPadmin</h3>
                <p className="text-gray-400 text-sm mb-4">Web-based LDAP directory management</p>
                <div className="text-sm font-medium text-red-400 flex items-center gap-1 group-hover:gap-2 transition-all">
                  Open Interface
                  <ArrowRight className="h-4 w-4" />
                </div>
              </div>
            </a>

            {/* Gateway Portal Card - Special */}
            <Link
              to="/login"
              className="group relative transition-transform duration-300 hover:-translate-y-2"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl opacity-80 group-hover:opacity-100 transition-opacity"></div>
              <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl blur-xl opacity-50 group-hover:opacity-70 transition-opacity"></div>
              <div className="relative p-6 h-full flex flex-col justify-between">
                <div>
                  <div className="flex items-start justify-between mb-4">
                    <div className="p-3 rounded-xl bg-white/20">
                      <Shield className="h-6 w-6 text-white" />
                    </div>
                    <span className="text-xs font-mono text-white/70 bg-white/10 px-2 py-1 rounded">:3000</span>
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">Gateway Portal</h3>
                  <p className="text-white/80 text-sm mb-4">Access the IAM Gateway management interface</p>
                </div>
                <div className="text-sm font-medium text-white flex items-center gap-1 group-hover:gap-2 transition-all">
                  Sign In Now
                  <ArrowRight className="h-4 w-4" />
                </div>
              </div>
            </Link>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative z-10 py-32">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-600/20 to-purple-600/20 rounded-3xl blur-3xl"></div>
            <div className="relative bg-gradient-to-br from-white/5 to-white/0 border border-white/10 rounded-3xl p-12 md:p-16">
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
                Ready to Transform Your
                <span className="block bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                  Identity Management?
                </span>
              </h2>
              <p className="text-xl text-gray-400 mb-8 max-w-2xl mx-auto">
                Start managing identities across all your systems with a unified, intelligent platform.
              </p>
              <div className="flex flex-wrap justify-center gap-4">
                <Link
                  to="/login"
                  className="group inline-flex items-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-4 rounded-xl text-lg font-semibold hover:shadow-2xl hover:shadow-blue-500/25 transition-all hover:-translate-y-0.5"
                >
                  Get Started Free
                  <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
                </Link>
                <a
                  href="http://localhost:8000/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 bg-white/5 border border-white/10 text-white px-8 py-4 rounded-xl text-lg font-semibold hover:bg-white/10 transition-all"
                >
                  Explore API
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/10 py-16 bg-black/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-12">
            <div className="md:col-span-2">
              <div className="flex items-center gap-3 mb-6">
                <div className="bg-gradient-to-br from-blue-500 to-purple-600 p-2 rounded-xl">
                  <Shield className="h-6 w-6 text-white" />
                </div>
                <div>
                  <span className="text-xl font-bold text-white">Gateway IAM</span>
                  <span className="block text-xs text-gray-500">Enterprise Edition</span>
                </div>
              </div>
              <p className="text-gray-400 max-w-sm">
                Enterprise-grade Identity & Access Management platform. Unified identity orchestration for modern organizations.
              </p>
            </div>

            <div>
              <h4 className="font-semibold text-white mb-4">Resources</h4>
              <ul className="space-y-3 text-sm text-gray-400">
                <li><a href="http://localhost:8000/docs" className="hover:text-white transition">API Documentation</a></li>
                <li><a href="#features" className="hover:text-white transition">Features</a></li>
                <li><a href="#architecture" className="hover:text-white transition">Architecture</a></li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-white mb-4">Quick Links</h4>
              <ul className="space-y-3 text-sm text-gray-400">
                <li><Link to="/login" className="hover:text-white transition">Sign In</Link></li>
                <li><a href="http://localhost:8080/midpoint" className="hover:text-white transition">MidPoint</a></li>
                <li><a href="http://localhost:8081" className="hover:text-white transition">Keycloak</a></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-white/10 mt-12 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-sm text-gray-500">
              © 2025 Gateway IAM. Powered by MidPoint, FastAPI & React.
            </p>
            <div className="flex items-center gap-6 text-sm text-gray-500">
              <span className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                All Systems Operational
              </span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
