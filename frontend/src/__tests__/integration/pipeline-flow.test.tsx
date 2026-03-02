/**
 * Integration test for multi-template pipeline flow.
 *
 * Tests the complete flow from template selection through upload initiation.
 */
import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { BrowserRouter } from "react-router-dom"
import ProcessingPage from "@/pages/ProcessingPage"

// Mock API
vi.mock("@/lib/api", () => ({
  api: {
    upload: {
      file: vi.fn().mockResolvedValue({ gcs_url: "gs://bucket/test.pdf" }),
    },
    process: {
      extract: vi.fn().mockResolvedValue({
        extraction_job_id: "ext-123",
        status: "pending",
        template_ids: ["opr", "mpp"],
        message: "Created",
      }),
    },
    jobs: {
      list: vi.fn().mockResolvedValue({ jobs: [], total: 0 }),
      get: vi.fn(),
    },
  },
}))

// Mock hooks
vi.mock("@/hooks", () => ({
  useJobs: () => ({ data: { jobs: [] }, isLoading: false }),
  useJobSteps: () => ({ data: [] }),
  usePipelineProgress: () => ({ data: null, isLoading: false }),
  useExtractPdf: () => ({
    mutateAsync: vi.fn().mockResolvedValue({
      extraction_job_id: "ext-123",
      status: "pending",
      template_ids: ["opr", "mpp"],
      message: "Created",
    }),
    isPending: false,
  }),
}))

describe("Pipeline Flow Integration", () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    })
    vi.clearAllMocks()
  })

  it("renders the processing page with template selection", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <ProcessingPage />
        </BrowserRouter>
      </QueryClientProvider>
    )

    expect(screen.getByText(/Upload & Process/i)).toBeInTheDocument()
    expect(screen.getByText(/Select Template Types/i)).toBeInTheDocument()
  })

  it("shows all template options", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <ProcessingPage />
        </BrowserRouter>
      </QueryClientProvider>
    )

    // Check template checkboxes are present
    expect(screen.getByLabelText(/Off-Plan Residential/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Main Brand Site/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Aggregators/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/ADOP/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/ADRE/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Commercial/i)).toBeInTheDocument()
  })

  it("allows selecting multiple templates", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <ProcessingPage />
        </BrowserRouter>
      </QueryClientProvider>
    )

    const oprCheckbox = screen.getByLabelText(/Off-Plan Residential/i)
    const mppCheckbox = screen.getByLabelText(/Main Brand Site/i)

    // OPR should be selected by default
    expect(oprCheckbox).toBeChecked()

    // Select MPP as well
    fireEvent.click(mppCheckbox)
    expect(mppCheckbox).toBeChecked()
    expect(oprCheckbox).toBeChecked()

    // Verify count updates
    expect(screen.getByText(/Selected: 2 template/i)).toBeInTheDocument()
  })

  it("prevents deselecting the last template", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <ProcessingPage />
        </BrowserRouter>
      </QueryClientProvider>
    )

    const oprCheckbox = screen.getByLabelText(/Off-Plan Residential/i)

    // Try to deselect the only selected template
    fireEvent.click(oprCheckbox)

    // Should still be checked (can't deselect last one)
    expect(oprCheckbox).toBeChecked()
    expect(screen.getByText(/Selected: 1 template/i)).toBeInTheDocument()
  })

  it("shows file upload zone", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <ProcessingPage />
        </BrowserRouter>
      </QueryClientProvider>
    )

    expect(screen.getByText(/Drag and drop a PDF file here/i)).toBeInTheDocument()
    expect(screen.getByText(/Maximum file size/i)).toBeInTheDocument()
  })
})
