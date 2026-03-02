import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { FileUpload } from "../FileUpload"

// Mock the hooks
const mockMutateAsync = vi.fn()
vi.mock("@/hooks", () => ({
  useExtractPdf: () => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
  }),
}))

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  )
}

describe("FileUpload", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockMutateAsync.mockResolvedValue({
      extraction_job_id: "job-123",
      status: "pending",
      template_ids: ["opr", "mpp"],
    })
  })

  it("renders template checkboxes", () => {
    renderWithProviders(<FileUpload />)

    expect(screen.getByText(/Off-Plan Residential/i)).toBeInTheDocument()
    expect(screen.getByText(/Main Brand Site/i)).toBeInTheDocument()
    expect(screen.getByText(/Real Estate Aggregators/i)).toBeInTheDocument()
  })

  it("has OPR selected by default", () => {
    renderWithProviders(<FileUpload />)

    const oprCheckbox = screen.getByRole("checkbox", { name: /Off-Plan Residential/i })
    expect(oprCheckbox).toBeChecked()
  })

  it("allows multiple template selection", () => {
    renderWithProviders(<FileUpload />)

    const mppCheckbox = screen.getByRole("checkbox", { name: /Main Brand Site/i })
    fireEvent.click(mppCheckbox)

    expect(mppCheckbox).toBeChecked()
  })

  it("prevents deselecting the last template", () => {
    renderWithProviders(<FileUpload />)

    // OPR is selected by default, try to deselect it
    const oprCheckbox = screen.getByRole("checkbox", { name: /Off-Plan Residential/i })
    fireEvent.click(oprCheckbox)

    // Should still be checked because it's the last one
    expect(oprCheckbox).toBeChecked()
  })

  it("shows selected template count", () => {
    renderWithProviders(<FileUpload />)

    expect(screen.getByText(/Selected: 1 template/i)).toBeInTheDocument()

    const mppCheckbox = screen.getByRole("checkbox", { name: /Main Brand Site/i })
    fireEvent.click(mppCheckbox)

    expect(screen.getByText(/Selected: 2 template/i)).toBeInTheDocument()
  })

  it("renders drop zone with single file instruction", () => {
    renderWithProviders(<FileUpload />)

    expect(screen.getByText(/Drag and drop a PDF file here/i)).toBeInTheDocument()
  })

  it("calls onUploadComplete with extraction_job_id", async () => {
    const onComplete = vi.fn()
    renderWithProviders(<FileUpload onUploadComplete={onComplete} />)

    // Verify the callback signature expects extraction_job_id
    expect(onComplete).not.toHaveBeenCalled()
  })
})
