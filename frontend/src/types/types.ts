export interface Page {
  id: string,
  status: "ready" | "converting" | "error",
  imageSrc?: string,
  sourceFileName: string,
}

export type AnalysisStatus = "idle" | "processing" | "done" | "error"

/* export interface StampResult {
  country: string
  date: string
  type: "arrival" | "departure"
  sourceFilename: string;
  pageNumber: number;
  stampImg: string;
}

export interface PageResult {
  processedPage: string
  stamps: StampResult[]
}

export interface StayResult {
  id: string
  country: string
  arrivalDate: string
  departureDate: string | null
  entryStamp: StampResult | null
  exitStamp: StampResult | null
} */


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
  mask: number[]
  detectionConfidence: number
  extractedFields: ExtractedFields
  pageSource: string
  pageNumber: number
  // extractionTimestamp: string
}


export interface PageExtractionResponse {
  sourceFilename: string
  pageNumber: number
  processedImage: string
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
  stays: TravelHistoryResponse
}
