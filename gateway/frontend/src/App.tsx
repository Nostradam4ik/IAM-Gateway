/**
 * App.tsx - Point d'entree du routage de l'application Gateway IAM.
 *
 * Structure des routes :
 *   / -> Landing (page d'accueil publique)
 *   /login -> Login (formulaire d'authentification)
 *   /dashboard/* -> Routes protegees (necessitent authentification)
 *     /dashboard -> Dashboard (vue d'ensemble connecteurs + services)
 *     /dashboard/operations -> Operations (provisionnement via formulaire)
 *     /dashboard/rules -> Rules (regles de mapping Jinja2)
 *     /dashboard/workflows -> Workflows (approbation multi-niveaux)
 *     /dashboard/reconciliation -> Reconciliation (comparaison source/cible)
 *     /dashboard/live -> LiveComparison (Odoo, recherche, sync, planification)
 *     /dashboard/permissions -> Permissions (niveaux de droits 1-5)
 *     /dashboard/connectors -> Connectors (CRUD connecteurs dynamiques)
 *     /dashboard/midpoint-users -> MidpointUsers (CRUD utilisateurs MidPoint)
 *     /dashboard/gateway-users -> Users (CRUD utilisateurs gateway + chaine approbation)
 *     /dashboard/ai -> AIAssistant (chat IA - necessite cle API)
 *     /dashboard/audit -> AuditLogs (logs + recherche semantique)
 *     /dashboard/settings -> Settings (etat systeme, arret urgence, connecteurs)
 */
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/auth'
import Layout from './components/Layout'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Operations from './pages/Operations'
import Rules from './pages/Rules'
import Workflows from './pages/Workflows'
import Reconciliation from './pages/Reconciliation'
import AIAssistant from './pages/AIAssistant'
import Settings from './pages/Settings'
import AuditLogs from './pages/AuditLogs'
import LiveComparison from './pages/LiveComparison'
import Permissions from './pages/Permissions'
import Connectors from './pages/Connectors'
import MidpointUsers from './pages/MidpointUsers'
import Users from './pages/Users'

/**
 * Garde de route privee - redirige vers /login si l'utilisateur n'est pas authentifie.
 * Utilise le store Zustand (useAuthStore) pour verifier l'etat d'authentification.
 */
function PrivateRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route
        path="/dashboard/*"
        element={
          <PrivateRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/operations" element={<Operations />} />
                <Route path="/rules" element={<Rules />} />
                <Route path="/workflows" element={<Workflows />} />
                <Route path="/reconciliation" element={<Reconciliation />} />
                <Route path="/live" element={<LiveComparison />} />
                <Route path="/permissions" element={<Permissions />} />
                <Route path="/connectors" element={<Connectors />} />
                <Route path="/midpoint-users" element={<MidpointUsers />} />

                <Route path="/gateway-users" element={<Users />} />
                <Route path="/ai" element={<AIAssistant />} />
                <Route path="/audit" element={<AuditLogs />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </Layout>
          </PrivateRoute>
        }
      />
    </Routes>
  )
}

export default App
