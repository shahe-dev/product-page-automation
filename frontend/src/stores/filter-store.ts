import { create } from "zustand"
import { persist } from "zustand/middleware"

import type { ProjectFilters } from "@/types"

interface FilterState {
  projectFilters: ProjectFilters
  setProjectFilters: (filters: Partial<ProjectFilters>) => void
  clearProjectFilters: () => void
}

const defaultFilters: ProjectFilters = {
  search: "",
  emirate: undefined,
  developer: undefined,
  status: undefined,
}

export const useFilterStore = create<FilterState>()(
  persist(
    (set) => ({
      projectFilters: defaultFilters,

      setProjectFilters: (filters) => {
        set((state) => ({
          projectFilters: { ...state.projectFilters, ...filters },
        }))
      },

      clearProjectFilters: () => {
        set({ projectFilters: defaultFilters })
      },
    }),
    {
      name: "filter-storage",
    },
  ),
)
