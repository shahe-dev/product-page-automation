import { create } from "zustand"
import { persist } from "zustand/middleware"

export interface Toast {
  id: string
  title: string
  description?: string
  variant?: "default" | "destructive" | "success"
}

interface UIState {
  sidebarOpen: boolean
  theme: "light" | "dark"
  toasts: Toast[]
  modalStack: string[]
  globalLoading: boolean
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
  setTheme: (theme: "light" | "dark") => void
  addToast: (toast: Omit<Toast, "id">) => void
  removeToast: (id: string) => void
  pushModal: (id: string) => void
  popModal: () => void
  clearModals: () => void
  setGlobalLoading: (loading: boolean) => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      theme: "light",
      toasts: [],
      modalStack: [],
      globalLoading: false,

      toggleSidebar: () => {
        set((state) => ({ sidebarOpen: !state.sidebarOpen }))
      },

      setSidebarOpen: (open) => {
        set({ sidebarOpen: open })
      },

      setTheme: (theme) => {
        set({ theme })
        document.documentElement.classList.toggle("dark", theme === "dark")
      },

      addToast: (toast) => {
        const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
        set((state) => ({
          toasts: [...state.toasts, { ...toast, id, variant: toast.variant || "default" }],
        }))
      },

      removeToast: (id) => {
        set((state) => ({
          toasts: state.toasts.filter((t) => t.id !== id),
        }))
      },

      pushModal: (id) => {
        set((state) => ({
          modalStack: [...state.modalStack, id],
        }))
      },

      popModal: () => {
        set((state) => ({
          modalStack: state.modalStack.slice(0, -1),
        }))
      },

      clearModals: () => {
        set({ modalStack: [] })
      },

      setGlobalLoading: (loading) => {
        set({ globalLoading: loading })
      },
    }),
    {
      name: "ui-storage",
      partialize: (state) => ({
        sidebarOpen: state.sidebarOpen,
        theme: state.theme,
      }),
    },
  ),
)
