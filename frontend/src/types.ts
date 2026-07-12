export type Direction = "ENTRY" | "EXIT";

export interface TimelineEntry {
  id: string;
  sourceFile: string;
  date: string | null;
  country: string | null;
  direction: Direction | null;
  rawText: string | null;
  confidence: number;
}

export type UploadStatus = "pending" | "processing" | "done" | "error";

export interface UploadFileItem {
  id: string;
  file: File;
  status: UploadStatus;
}
