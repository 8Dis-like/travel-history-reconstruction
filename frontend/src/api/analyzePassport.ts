import type { AnalysisResult, PageExtractionResponse, PageResult } from "../types/types";
import stampImg1 from '../../mock_data/detection_stamps/stamp1350.jpg'
import stampImg2 from '../../mock_data/detection_stamps/stamp1351.jpg'
import stampImg3 from '../../mock_data/detection_stamps/stamp1352.jpg'
import passportPage1 from '../../mock_data/detection_pages/detection_6.png'
import passportPage2 from '../../mock_data/detection_pages/detection_4.png'
import passportPage3 from '../../mock_data/detection_pages/detection_5.png'

const pageResult1: PageExtractionResponse = {
  sourceFilename: "page",
  pageNumber: 1,
  sourceImage: "",
  totalStamps_detected: 0,
  totalStamps_parsed: 0,
  unreadableStamps: 0,
  stamps: [
    {
      stampId: "1",
      sourceImage: stampImg1,
      boundingBox: [],
      mask: [],
      detectionConfidence: 0.9,
      extractedFields: {
        date: "2024-03-03",
        country: "Japan",
        direction: "arrival",
        rawText: "",
        extractionConfidence: 0.8
      },
      extractionTimestamp: "test"
    },
  ]
}


const analysisResult: AnalysisResult = {
  pages: [
    pageResult1,
    pageResult1,
    pageResult1,
    pageResult1,
    pageResult1,
    pageResult1,
    pageResult1,
    pageResult1,
    pageResult1,
  ],
  stays: [
    {
      id: '1',
      country: 'Japan',
      arrivalDate: '2024-03-03',
      departureDate: '2024-03-10',
      entryStamp: {
        country: 'Japan',
        date: '2024-03-03',
        type: 'arrival',
        sourceFilename: 'passport_scan.pdf',
        pageNumber: 4,
        stampImg: stampImg1
      },
      exitStamp: {
        country: 'Japan',
        date: '2024-03-10',
        type: 'departure',
        sourceFilename: 'passport_scan.pdf',
        pageNumber: 5,
        stampImg: stampImg1
      },
    },
    {
      id: '2',
      country: 'Thailand',
      arrivalDate: '2024-03-10',
      departureDate: '2024-03-15',
      entryStamp: {
        country: 'Thailand',
        date: '2024-03-10',
        type: 'arrival',
        sourceFilename: 'passport_scan.pdf',
        pageNumber: 6,
        stampImg: stampImg2
      },
      exitStamp: {
        country: 'Thailand',
        date: '2024-03-15',
        type: 'departure',
        sourceFilename: 'passport_scan.pdf',
        pageNumber: 6,
        stampImg: stampImg2
      },
    },
    {
      id: '3',
      country: 'Vietnam',
      arrivalDate: '2024-03-15',
      departureDate: null,
      entryStamp: {
        country: 'Vietnam',
        date: '2024-03-15',
        type: 'arrival',
        sourceFilename: 'passport_scan.pdf',
        pageNumber: 7,
        stampImg: stampImg3
      },
      exitStamp: null,
    },
  ],
};

export function mockAnalyze(): Promise<AnalysisResult> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(analysisResult)
    }, 2000)
  })
}


export async function analyze(session_id: string): Promise<AnalysisResult> {
  const formData = new FormData()
  formData.append("session_id", session_id)

  const response = await fetch("/api/analyze", {
    method: "POST",
    body: formData
  })
  
  const response_data = await response.json()

  return {"pages": response_data.pages, "stays": response_data.stays}
}

