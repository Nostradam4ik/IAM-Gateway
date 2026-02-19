/**
 * auth.ts - Store d'authentification global (Zustand + persist).
 *
 * Stocke le JWT token et les infos utilisateur dans localStorage
 * sous la cle 'auth-storage'. Utilise par :
 *   - api.ts (intercepteur) pour ajouter le Bearer token
 *   - Layout.tsx pour afficher le username et les roles
 *   - App.tsx (PrivateRoute) pour proteger les routes
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  username: string
  roles: string[]
}

interface AuthState {
  token: string | null
  user: User | null
  isAuthenticated: boolean
  login: (token: string, user: User) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      login: (token, user) =>
        set({
          token,
          user,
          isAuthenticated: true,
        }),
      logout: () =>
        set({
          token: null,
          user: null,
          isAuthenticated: false,
        }),
    }),
    {
      name: 'auth-storage',
    }
  )
)
