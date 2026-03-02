import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { BrowserRouter } from "react-router-dom"
import ProcessingPage from "../ProcessingPage"

// Mock the hooks
vi.mock("@/hooks", () => ({
  useJobs: () => ({ data: { jobs: [] }, isLoading: false }),
  useJobSteps: () => ({ data: [] }),
  usePipelineProgress: () => ({ data: null, isLoading: false }),
  useExtractPdf: () => ({
    mutateAsync: vi.fn().mockResolvedValue({
      extraction_job_id: "ext-123",
      status: "pending",
      template_ids: ["opr"],
    }),
    isPending: false,
  }),
}))

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{ui}</BrowserRouter>
    </QueryClientProvider>
  )
}

describe("ProcessingPage", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    sessionStorage.clear()
  })

  it("renders upload section", () => {
    renderWithProviders(<ProcessingPage />)
    expect(screen.getByText(/Upload & Process/i)).toBeInTheDocument()
  })

  it("renders template selection card", () => {
    renderWithProviders(<ProcessingPage />)
    expect(screen.getByText(/Select Template Types/i)).toBeInTheDocument()
  })

  it("renders upload new file heading", () => {
    renderWithProviders(<ProcessingPage />)
    expect(screen.getByText(/Upload New File/i)).toBeInTheDocument()
  })

  it("renders active jobs section heading", () => {
    renderWithProviders(<ProcessingPage />)
    // Use exact match for h2 heading "Active Jobs" (not h3 "No active jobs")
    expect(screen.getByRole("heading", { level: 2, name: /^Active Jobs$/i })).toBeInTheDocument()
  })

  it("shows empty state when no active jobs", () => {
    renderWithProviders(<ProcessingPage />)
    expect(screen.getByText(/No active jobs/i)).toBeInTheDocument()
  })

  it("renders page description mentioning multiple templates", () => {
    renderWithProviders(<ProcessingPage />)
    expect(screen.getByText(/multiple templates simultaneously/i)).toBeInTheDocument()
  })
})
