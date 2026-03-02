import { describe, it, expect } from "vitest"
import type {
  JobType,
  ExtractRequest,
  ExtractResponse,
  GenerateRequest,
  GenerateResponse,
  MaterialPackage,
  GenerationRun,
  Job,
} from "@/types"

describe("Multi-template types", () => {
  it("JobType includes extraction and generation", () => {
    const types: JobType[] = ["extraction", "generation"]
    expect(types).toContain("extraction")
    expect(types).toContain("generation")
  })

  it("ExtractRequest has required fields", () => {
    const req: ExtractRequest = {
      pdf_url: "gs://bucket/test.pdf",
      template_ids: ["opr", "mpp"],
    }
    expect(req.template_ids.length).toBe(2)
  })

  it("ExtractResponse has extraction_job_id", () => {
    const res: ExtractResponse = {
      extraction_job_id: "uuid-123",
      status: "pending",
      template_ids: ["opr"],
      message: "Created",
    }
    expect(res.extraction_job_id).toBeDefined()
  })

  it("GenerateRequest has required fields", () => {
    const req: GenerateRequest = {
      material_package_id: "pkg-123",
      template_types: ["opr", "mpp"],
    }
    expect(req.template_types.length).toBe(2)
  })

  it("GenerateResponse has generation_job_ids array", () => {
    const res: GenerateResponse = {
      generation_job_ids: ["job-1", "job-2"],
      status: "dispatched",
      message: "Created 2 jobs",
    }
    expect(res.generation_job_ids.length).toBe(2)
  })

  it("MaterialPackage has required fields", () => {
    const pkg: MaterialPackage = {
      id: "pkg-123",
      project_id: "proj-123",
      source_job_id: "job-123",
      gcs_base_path: "gs://bucket/packages/123",
      package_version: "1.0.0",
      extraction_summary: {},
      structured_data: {},
      status: "ready",
      created_at: "2026-02-05T00:00:00Z",
      updated_at: "2026-02-05T00:00:00Z",
      expires_at: null,
    }
    expect(pkg.status).toBe("ready")
  })

  it("GenerationRun has required fields", () => {
    const run: GenerationRun = {
      id: "run-123",
      project_id: "proj-123",
      material_package_id: "pkg-123",
      template_type: "opr",
      job_id: "job-123",
      generated_content: null,
      sheet_url: null,
      drive_folder_url: null,
      status: "pending",
      created_at: "2026-02-05T00:00:00Z",
      completed_at: null,
    }
    expect(run.status).toBe("pending")
  })

  it("Job has optional job_type and material_package_id", () => {
    const job: Job = {
      id: "uuid",
      project_id: "proj-id",
      status: "pending",
      current_step: "upload",
      progress: 0,
      created_at: "2026-02-05T00:00:00Z",
      updated_at: "2026-02-05T00:00:00Z",
      job_type: "extraction",
      material_package_id: "pkg-id",
    }
    expect(job.job_type).toBe("extraction")
  })
})
