import { describe, it, expect, vi } from "vitest"
import { api } from "@/lib/api"

// Mock axios
vi.mock("axios", () => ({
  default: {
    create: () => ({
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      patch: vi.fn(),
      delete: vi.fn(),
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
    }),
  },
}))

describe("api cleanup", () => {
  it("upload.pdf is removed", () => {
    // Old single-template upload should not exist
    expect((api.upload as Record<string, unknown>).pdf).toBeUndefined()
  })

  it("upload.file exists for GCS upload", () => {
    expect(api.upload.file).toBeDefined()
    expect(typeof api.upload.file).toBe("function")
  })
})

describe("api.process", () => {
  it("has extract method", () => {
    expect(api.process).toBeDefined()
    expect(api.process.extract).toBeDefined()
    expect(typeof api.process.extract).toBe("function")
  })

  it("has generate method", () => {
    expect(api.process.generate).toBeDefined()
    expect(typeof api.process.generate).toBe("function")
  })

  it("has getMaterialPackage method", () => {
    expect(api.process.getMaterialPackage).toBeDefined()
    expect(typeof api.process.getMaterialPackage).toBe("function")
  })

  it("has getGenerationRuns method", () => {
    expect(api.process.getGenerationRuns).toBeDefined()
    expect(typeof api.process.getGenerationRuns).toBe("function")
  })
})
