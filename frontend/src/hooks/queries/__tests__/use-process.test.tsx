import { describe, it, expect, vi } from "vitest"
import { renderHook, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useExtractPdf } from "../use-process"
import { api } from "@/lib/api"
import type { ReactNode } from "react"

vi.mock("@/lib/api", () => ({
  api: {
    process: {
      extract: vi.fn(),
    },
  },
}))

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )
  }
}

describe("useExtractPdf", () => {
  it("calls api.process.extract with correct payload", async () => {
    const mockResponse = {
      extraction_job_id: "job-123",
      status: "pending",
      template_ids: ["opr", "mpp"],
      message: "Created",
    }
    vi.mocked(api.process.extract).mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useExtractPdf(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({
      pdfUrl: "gs://bucket/test.pdf",
      templateIds: ["opr", "mpp"],
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(api.process.extract).toHaveBeenCalledWith({
      pdf_url: "gs://bucket/test.pdf",
      template_ids: ["opr", "mpp"],
    })
    expect(result.current.data?.extraction_job_id).toBe("job-123")
  })
})
