import type { TimelineEntry } from "./types";

interface MockExtractedRecord {
  date: string | null;
  country: string | null;
  direction: "ENTRY" | "EXIT" | null;
  raw_text: string | null;
  confidence: number;
}

interface MockPdfExtractionResponse {
  source_file: string;
  records: MockExtractedRecord[];
}

export async function extractMockPdf(file: File): Promise<TimelineEntry[]> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("/api/extract/mock/pdf", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`extractMockPdf failed with status ${response.status}`);
  }

  const data: MockPdfExtractionResponse = await response.json();

  const batchToken = Math.random().toString(36).slice(2);

  return data.records.map((record, index) => ({
    id: `${batchToken}-${index}`,
    sourceFile: data.source_file,
    date: record.date,
    country: record.country,
    direction: record.direction,
    rawText: record.raw_text,
    confidence: record.confidence,
  }));
}
