import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { PipelineProgressTracker } from "../PipelineProgressTracker"

vi.mock("@/hooks", () => ({
  usePipelineProgress: () => ({
    data: {
      extraction_job_id: "ext-123",
      extraction_status: "processing",
      extraction_progress: 50,
      generation_jobs: [
        { job_id: "gen-1", template_type: "opr", status: "pending", progress: 0 },
        { job_id: "gen-2", template_type: "mpp", status: "pending", progress: 0 },
      ],
      overall_progress: 30,
    },
    isLoading: false,
  }),
}))

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient()
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  )
}

describe("PipelineProgressTracker", () => {
  it("shows extraction progress", () => {
    renderWithProviders(
      <PipelineProgressTracker extractionJobId="ext-123" startedAt="2026-02-05T00:00:00Z" />
    )

    expect(screen.getByText(/Extraction/i)).toBeInTheDocument()
    expect(screen.getByText(/50%/)).toBeInTheDocument()
  })

  it("shows generation jobs by template type", () => {
    renderWithProviders(
      <PipelineProgressTracker extractionJobId="ext-123" startedAt="2026-02-05T00:00:00Z" />
    )

    expect(screen.getByText(/Off-Plan Residential/i)).toBeInTheDocument()
    expect(screen.getByText(/Main Brand/i)).toBeInTheDocument()
  })

  it("shows overall progress", () => {
    renderWithProviders(
      <PipelineProgressTracker extractionJobId="ext-123" startedAt="2026-02-05T00:00:00Z" />
    )

    expect(screen.getByText(/Overall Progress/i)).toBeInTheDocument()
    expect(screen.getByText(/30%/)).toBeInTheDocument()
  })

  it("shows pipeline status heading", () => {
    renderWithProviders(
      <PipelineProgressTracker extractionJobId="ext-123" startedAt="2026-02-05T00:00:00Z" />
    )

    expect(screen.getByText(/Pipeline Status/i)).toBeInTheDocument()
  })
})
