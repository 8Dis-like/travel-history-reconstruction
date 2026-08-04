import { useEffect, useState } from 'react'
import { Layout, Typography, Segmented } from "antd"
import './App.css'

import UploadPanel from "./components/UploadPanel"
import ProcessingView from './components/ProcessingView'
import { TableView, TimelineTable, PageCarousel, StampCarousel, CustomPageCarousel } from './components/TableView'
import type { AnalysisStatus, TravelHistoryResponse, AnalysisResponse } from './types/types'
import { mockAnalyze, analyze } from './api/analyzePassport'
import TimelineView from './components/TimelineView'

const { Title } = Typography;
const { Content } = Layout


function App() {
  const [sessionId] = useState<string>(() => crypto.randomUUID())
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisStatus>("idle")// ("idle")
  const [analysisResponse, setAnalysisResponse] = useState<AnalysisResponse | null>(null)
  const [resultView, setResultView] = useState<"table" | "timeline">("table")

/*   useEffect(() => {
    console.log(analysisStatus)
  }, [analysisStatus]) */

  const handleAnalyze = async () => {
    if (sessionId === null) {
      return
    }

    setAnalysisStatus("processing")

    const analysisResult = await analyze(sessionId) // mockAnalyze()
    setAnalysisResponse(analysisResult)

    console.log(analysisResult)

    console.log(`There are ${analysisResult.stays.length} stays in the result`)

    setAnalysisStatus("done")
  }

  return (
    <>
      <Layout>
        <Content style={{ padding: "0 48px"}}>
          <Title>Travel History Reconstruction</Title>
          {analysisStatus === "idle" ? (
            <UploadPanel sessionId={sessionId} handleAnalyze={handleAnalyze}/>
          ) : analysisStatus === "processing" ? (
            <ProcessingView />
          ) : analysisStatus === "done" && analysisResponse && (
            <>
              <Segmented 
                options={["Table", "Timeline"]}
                value={resultView === "table" ? "Table" : "Timeline"}
                onChange={(value) => setResultView(value === "Table" ? "table" : "timeline")}
                style={{ marginBottom: '10px' }}
              />
              {resultView === "table" ? (
                <TableView stays={analysisResponse.stays.stays} pages={analysisResponse.pages}/>
                // <CustomPageCarousel data={analysisResult} setPageIndex={() => {}}/>
                // <PageCarousel data={analysisResult}/>
                // <StampCarousel data={analysisResult.pages[0]}/>
              ) : (
                <TimelineView data={analysisResponse} />
              )}
            </>
          )}
        </Content>
      </Layout>
    </>
  )

}

export default App
