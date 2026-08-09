export interface Page {
  id: string,
  status: "ready" | "converting" | "error",
  imageSrc?: string,
  sourceFileName: string,
}

export type AnalysisStatus = "idle" | "processing" | "done" | "error"


export interface ExtractedFields {
  date: string | null
  country: string | null
  direction: string | null
  rawText: string | null
  extractionConfidence: number
}
    

export interface StampRecord {
  stampId: string
  stampImage: string
  boundingBox: number[]
  mask: [number, number][]
  detectionConfidence: number
  extractedFields: ExtractedFields
  pageSource: string
  pageNumber: number
  // extractionTimestamp: string
}


export interface PageExtractionResponse {
  sourceFilename: string
  pageNumber: number
  origImage: string
  processedImage: string
  imageWidth: number
  imageHeight: number
  totalStampsDetected: number
  totalStampsParsed: number
  unreadableStamps: number
  stamps: StampRecord[]
}


export interface StayResponse {
    stayId: string
    country: string | null
    entryDate: string | null
    exitDate: string | null
    entryStamp: StampRecord | null
    exitStamp: StampRecord | null
    status: "confirmed" | "inferred" | "flagged"
    flags: string[]
}


export interface TravelHistoryResponse {
  stays: StayResponse[]
  unattributableStamps: StampRecord[]
}


export interface AnalysisResponse {
  pages: PageExtractionResponse[]
  travelHistory: TravelHistoryResponse
}
