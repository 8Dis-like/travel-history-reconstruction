import type { AnalysisResponse } from "../types/types";


export async function analyze(sessionId: string): Promise<AnalysisResponse> {
  const response = await fetch(`/api/sessions/${sessionId}/analyze`, {
    method: "POST"
  })
  if (!response.ok) {
    throw new Error(`Analyze failed: ${response.status}`)
  }
  
  return await response.json()
}

