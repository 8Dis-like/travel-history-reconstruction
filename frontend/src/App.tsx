import { useState } from 'react'
import { Layout, Typography } from "antd"
import './App.css'

import UploadPanel from "./components/UploadPanel"
import ProcessingView from './components/ProcessingView'
import { TableView } from './components/TableView'
import type { AnalysisStatus, AnalysisResponse } from './types/types'
import { analyze } from './api/analyzePassport'

const { Title } = Typography;
const { Content } = Layout


function App() {
  const [sessionId] = useState<string>(() => crypto.randomUUID())
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisStatus>("idle")
  const [analysisResponse, setAnalysisResponse] = useState<AnalysisResponse | null>(null)


  const handleAnalyze = async () => {
    if (sessionId === null) {
      return
    }

    setAnalysisStatus("processing")

    const analysisResult = await analyze(sessionId)
    setAnalysisResponse(analysisResult)

    console.log(analysisResult)

    console.log(`There are ${analysisResult.travelHistory.stays.length} stays in the result`)

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
            <TableView stays={analysisResponse.travelHistory.stays} pages={analysisResponse.pages}/>
          )}
        </Content>
      </Layout>
    </>
  )

}

export default App
