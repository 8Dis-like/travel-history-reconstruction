import type { AnalysisResponse } from "../types/types";


export async function analyze(session_id: string): Promise<AnalysisResponse> {
  const formData = new FormData()
  formData.append("session_id", session_id)

  const response = await fetch("/api/analyze", {
    method: "POST",
    body: formData
  })
  
  const response_data = await response.json()

  return {"pages": response_data.pages, "travelHistory": response_data.stays}
}

