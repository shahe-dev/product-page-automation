import { create } from "zustand"
import { persist, createJSONStorage } from "zustand/middleware"

import { queryClient } from "@/lib/query-client"
import type { User } from "@/types"

// TODO: Long-term fix: migrate token delivery to httpOnly, Secure, SameSite=Strict
// cookies set by the backend. Remove the token from persisted state entirely.
// The browser will attach cookies automatically; the Axios interceptor should
// use withCredentials: true instead of manually setting the Authorization header.
// sessionStorage is the minimum short-term mitigation (cleared on tab close).

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (token: string, user: User) => void
  logout: () => void
  updateUser: (updates: Partial<User>) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: (token, user) => {
        set({ token, user, isAuthenticated: true })
      },

      logout: () => {
        queryClient.clear()
        set({ token: null, user: null, isAuthenticated: false })
      },

      updateUser: (updates) => {
        set((state) => ({
          user: state.user ? { ...state.user, ...updates } : null,
        }))
      },
    }),
    {
      name: "auth-storage",
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
)
