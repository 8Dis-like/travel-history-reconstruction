import type { TimelineEntry } from "./types";

interface ExtractedFields {
  date: string | null;
  country: string | null;
  direction: "ENTRY" | "EXIT" | null;
  raw_text: string | null;
  extraction_confidence: number;
}

interface StampRecord {
  stamp_id: string;
  source_image: string;
  bounding_box: number[];
  detection_confidence: number;
  extracted_fields: ExtractedFields;
  extraction_timestamp: string;
}

interface PageExtractionResponse {
  source_image: string;
  total_stamps_detected: number;
  total_stamps_parsed: number;
  unreadable_stamps: number;
  stamps: StampRecord[];
}

export async function extractMockPdf(file: File): Promise<TimelineEntry[]> {
  const formData = new FormData();
  formData.append("file", file);

  // Calling the REAL backend pipeline instead of the mock endpoint
  const response = await fetch("/api/extract/page", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`extract failed with status ${response.status}`);
  }

  const data: PageExtractionResponse = await response.json();
  const batchToken = Math.random().toString(36).slice(2);

  return data.stamps.map((stamp, index) => ({
    id: `${batchToken}-${index}`,
    sourceFile: data.source_image,
    date: stamp.extracted_fields.date,
    country: stamp.extracted_fields.country,
    direction: stamp.extracted_fields.direction,
    rawText: stamp.extracted_fields.raw_text,
    confidence: stamp.extracted_fields.extraction_confidence,
  }));
}
