import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { BrowserRouter } from "react-router-dom"
import { JobStatus } from "../JobStatus"
import type { Job } from "@/types"

const mockExtractionJob: Job = {
  id: "job-123",
  project_id: "proj-123",
  status: "processing",
  current_step: "extract_images",
  progress: 30,
  created_at: "2026-02-05T00:00:00Z",
  updated_at: "2026-02-05T00:00:00Z",
  job_type: "extraction",
}

const mockGenerationJob: Job = {
  id: "job-456",
  project_id: "proj-123",
  status: "processing",
  current_step: "generate_content",
  progress: 50,
  created_at: "2026-02-05T00:00:00Z",
  updated_at: "2026-02-05T00:00:00Z",
  job_type: "generation",
  template_type: "opr",
}

const mockLegacyJob: Job = {
  id: "job-789",
  project_id: "proj-123",
  status: "completed",
  current_step: "done",
  progress: 100,
  created_at: "2026-02-05T00:00:00Z",
  updated_at: "2026-02-05T00:00:00Z",
}

describe("JobStatus", () => {
  it("shows extraction badge for extraction jobs", () => {
    render(
      <BrowserRouter>
        <JobStatus job={mockExtractionJob} />
      </BrowserRouter>
    )
    expect(screen.getByText(/Extraction/i)).toBeInTheDocument()
  })

  it("shows generation badge with template for generation jobs", () => {
    render(
      <BrowserRouter>
        <JobStatus job={mockGenerationJob} />
      </BrowserRouter>
    )
    expect(screen.getByText(/Generation/i)).toBeInTheDocument()
    expect(screen.getByText(/opr/i)).toBeInTheDocument()
  })

  it("does not show job type badge for legacy jobs without job_type", () => {
    render(
      <BrowserRouter>
        <JobStatus job={mockLegacyJob} />
      </BrowserRouter>
    )
    // Should not have extraction or generation text
    expect(screen.queryByText(/Extraction/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Generation/i)).not.toBeInTheDocument()
  })

  it("shows job type badge in compact mode", () => {
    render(
      <BrowserRouter>
        <JobStatus job={mockExtractionJob} compact />
      </BrowserRouter>
    )
    expect(screen.getByText(/Extraction/i)).toBeInTheDocument()
  })
})
