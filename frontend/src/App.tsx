import { useState } from 'react'
import { Layout, Typography } from "antd"
import './App.css'

import UploadPanel from "./components/UploadPanel"
import ProcessingView from './components/ProcessingView'
import { TableView } from './components/TableView'
import type { AnalysisStatus, StampRecord, PageExtractionResponse, TravelHistoryResponse } from './types/types'
import { analyze } from './api/analyzePassport'

const { Title } = Typography;
const { Content } = Layout


function App() {
  const [sessionId] = useState<string>(() => crypto.randomUUID())
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisStatus>("idle")
  const [pages, setPages] = useState<PageExtractionResponse[] | null>(null)
  const [travelHistory, setTravelHistory] = useState<TravelHistoryResponse | null>(null)


  const handleAnalyze = async () => {
    if (sessionId === null) {
      return
    }

    setAnalysisStatus("processing")

    const analysisResult = await analyze(sessionId)

    setPages(analysisResult.pages)
    setTravelHistory(analysisResult.travelHistory)
    
    setAnalysisStatus("done")
  }


  const handleStampUpdate = async (updatedStamp: StampRecord) => {
    if (pages === null) {
      return
    }

    setPages(prevPages => {
      if (prevPages === null) {
        return null
      }

      return prevPages.map(page => (
        page.pageId === updatedStamp.pageId 
          ? {...page, stamps: page.stamps.map(stamp => (stamp.stampId === updatedStamp.stampId ? updatedStamp : stamp))} 
          : page
      ))
    })
  }


  const handleStampDelete = async (deletedStamp: StampRecord) => {
    if (pages === null) {
      return
    }

    setPages(prevPages => {
      if (prevPages === null) {
        return null
      }

      return prevPages.map(page => ({
        ...page,
        stamps: page.stamps.filter(stamp => stamp.stampId !== deletedStamp.stampId)
      }))
    })
  }


  const handleTimelineRebuild = async (newTravelHistory: TravelHistoryResponse) => {
    setTravelHistory(newTravelHistory)
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
          ) : analysisStatus === "done" && travelHistory && pages && (
            <TableView 
              sessionId={sessionId} 
              pages={pages} 
              stays={travelHistory.stays} 
              unattributableStamps={travelHistory.unattributableStamps}
              handleStampUpdate={handleStampUpdate}
              handleTimelineRebuild={handleTimelineRebuild}
              handleStampDelete={handleStampDelete}
            />
          )}
        </Content>
      </Layout>
    </>
  )

}

export default App
