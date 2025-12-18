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
