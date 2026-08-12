import React from 'react'
import { useState, useEffect, useRef } from 'react'

import { Table, Card, ConfigProvider, Form, Button, Input, Select, message } from 'antd'
import { LeftOutlined, RightOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'

import type { PageExtractionResponse, StayResponse, StampRecord, StampFieldUpdate, TravelHistoryResponse } from '../types/types'
import '../components/TableView.css'
import { formatDate } from '../utils/formatters'

interface TimelineTableProps {
  stays: StayResponse[]
  handleClickedStamp: (stamp: StampRecord | null) => void
  selectedCell: { stayId: string; field: "entryStamp" | "exitStamp" } | null
  curTablePage: number
  setCurTablePage: (pageNumber: number) => void
  pageSize: number
  sessionId: string
  onTimelineRebuild: (travelHistory: TravelHistoryResponse) => void
}

interface PageCarouselProps {
  pages: PageExtractionResponse[]
  curPageIndex: number
  setCurPageIndex: React.Dispatch<React.SetStateAction<number>>
  clickStampId: string
  onStampSelected: (stamp: StampRecord | null) => void
}

interface StampDetailViewProps {
  sessionId: string
  stamp: StampRecord | null
  handleStampUpdate: (updatedStamp: StampRecord) => void
  handleStampDelete: (deletedStamp: StampRecord) => void
  handleStampSelected: (stamp: StampRecord | null) => void
}

interface TableViewProps {
  sessionId: string
  pages: PageExtractionResponse[]
  stays: StayResponse[]
  handleStampUpdate: (updatedStamp: StampRecord) => void
  handleTimelineRebuild: (travelHistory: TravelHistoryResponse) => void
  handleStampDelete: (deletedStamp: StampRecord) => void
}


const CustomPageCarousel: React.FC<PageCarouselProps> = ({ pages, curPageIndex, setCurPageIndex, clickStampId, onStampSelected }) => {
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const thumbnailRefs = useRef<(HTMLImageElement | null)[]>([])
  const imgContainerRef = useRef<HTMLImageElement>(null)

  const goPrev = () => {
    setCurPageIndex((next) => (next - 1 + pages.length) % pages.length)
    onStampSelected(null)
  }
  const goNext = () => {
    setCurPageIndex((prev) => (prev + 1) % pages.length)
    onStampSelected(null)
  }

  const [hoverStampId, setHoverStampId] = useState('')
  // const [clickStampId, setClickStampId] = useState('')

  const [imageLoaded, setImageLoaded] = useState<Boolean>(false)


  useEffect(() => {
    const container = scrollContainerRef.current
    const activeThumbnail = thumbnailRefs.current[curPageIndex]

    if (container && activeThumbnail) {
      const containerCenter = container.offsetWidth / 2
      const thumbnailCenter = activeThumbnail.offsetLeft + activeThumbnail.offsetWidth / 2

      container.scrollTo({ left: thumbnailCenter - containerCenter, behavior: "smooth"})
    }
  }, [curPageIndex])


  useEffect(() => {
    setImageLoaded(false)
  }, [curPageIndex])


  return (
    <div style={{ width: "100%", alignItems: "center", textAlign: "center" }}>
      <div 
        style={{ 
          position: "relative", 
          display: "inline-block", 
          margin: "0 auto" 
        }}
      >
        <img 
          src={pages[curPageIndex].origImage} // processedImage} 
          ref={imgContainerRef}
          style={{ 
            height: "65vh",
            width: "auto",
            maxWidth: "100%",
            display: "block",
            margin: "0 auto"
          }}
          onLoad={() => setImageLoaded(true)}
        />
        {imageLoaded && (
          <svg 
            viewBox={`0 0 ${pages[curPageIndex].imageWidth} ${pages[curPageIndex].imageHeight}`} 
            preserveAspectRatio="none"
            style={{ 
              position: "absolute", 
              top: 0, 
              left: 0, 
              width: "100%", 
              height: "100%" 
            }}
          >
            {pages[curPageIndex].stamps.map((stamp) => (
              <polygon 
                key={stamp.stampId}
                points={stamp.mask.map(([x, y]) =>`${x},${y}`).join(' ')}
                fill={clickStampId === stamp.stampId ? "orange" : (hoverStampId === stamp.stampId ? "red" : "transparent")}
                fillOpacity={0.25}
                stroke={clickStampId === stamp.stampId ? "orange" : "red"}
                strokeWidth={pages[curPageIndex].imageHeight * 0.005}
                onMouseEnter={() => setHoverStampId(stamp.stampId)}
                onMouseLeave={() => setHoverStampId('')}
                onClick={() => {
                  onStampSelected(stamp)
                }}
                style={{ cursor: "pointer" }}
                opacity={imageLoaded ? 1 : 0}
              />
            ))}
          </svg>
        )}
      </div>
      <div style={{ 
        display: "flex", 
        alignItems: "center",
        gap: "2px", 
        width: "100%", 
      }}>
        <div style={{ cursor: "pointer", flexShrink: 0 }}>
          <LeftOutlined onClick={goPrev}/>
        </div>
        <div style={{ width: "95%", overflow: "hidden", position: "relative" }}>
          <div 
            ref={scrollContainerRef} 
            className="processed-page-scroll-container"
            style={{ display: "flex", overflowX: "auto", paddingLeft: "50%", paddingRight: "50%" }}
          >
            {pages.map((page, index) => 
              <img 
                key={index}
                src={page.processedImage}
                ref={(el) => { thumbnailRefs.current[index] = el; }}
                style={{ 
                  width: "48px", 
                  height: "48px",
                  border: index === curPageIndex ? "2px solid green" : "2px solid transparent",
                  cursor: "pointer"
                }}
                onClick={() => {
                  if (index !== curPageIndex) {
                    setCurPageIndex(index)
                    onStampSelected(null)
                  }
                }}
              />
            )}
          </div>
        </div>
        <div style={{ cursor: "pointer", flexShrink: 0 }}>
          <RightOutlined onClick={goNext}/>
        </div>
      </div>
    </div>
  )
}


const StampDetailView: React.FC<StampDetailViewProps> = ({ sessionId, stamp, handleStampUpdate, handleStampDelete, handleStampSelected }) => {
  const [editing, setEditing] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    setEditing(false)
  }, [stamp])


  const handleEdit = () => {
    if (stamp) {
      form.setFieldsValue({
        country: stamp.extractedFields.country,
        date: stamp.extractedFields.date ?? null,
        direction: stamp.extractedFields.direction ?? "Unknown",
      })
    }
    setEditing(true)
  }

  if (stamp === null) {
    return null
  }

  const handleSave = async () => {
    try {
      const values = await form.validateFields()
      const response = await fetch(`/api/sessions/${sessionId}/stamps/${stamp.stampId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          country: values.country,
          direction: values.direction !== "Unknown" ? values.direction : null,
          date: values.date || null
        })
      })
      if (!response.ok) {
        throw new Error("Update failed")
      }
      const updatedStamp: StampRecord = await response.json()
      handleStampUpdate(updatedStamp)
      setEditing(false)
    } catch (e) {
      console.log("Could not save changes")
    }
  }


  const handleDelete = async () => {
    try {
      const response = await fetch(`/api/sessions/${sessionId}/delete-stamp/${stamp.stampId}`, {
        method: "DELETE"
      })
      if (!response.ok) {
        throw new Error("Delete failed")
      }
      const deletedStamp: StampRecord = await response.json()
      handleStampDelete(deletedStamp)
      handleStampSelected(null)
    } catch (e) {
      console.log("Could not delete stamp")
    }
  }

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <div 
        style={{ 
          display: "flex", 
          width: "100%", 
          alignItems: "center", 
          border: "2px solid black", 
          borderRadius: "30px",
          overflow: "hidden",
        }}>
        <img 
          src={stamp.stampImage}
          style={{
            height: "30vh",
            width: "auto",
            maxWidth: "100%",
            margin: "0 auto",
            objectFit: "contain"
          }}
        />
      </div>
      {!editing ? (
        <>
          <div style={{ textAlign: "center", marginTop: "12px" }}>
            <div>Country: {stamp.extractedFields.country !== null ? stamp.extractedFields.country : "Unknown"}</div>
            <div>Date: {stamp.extractedFields.date !== null ? formatDate(stamp.extractedFields.date) : "Unknown"}</div>
            <div>Entry/Exit: {stamp.extractedFields.direction !== null ? stamp.extractedFields.direction : "Unknown"}</div>
          </div>
          <div style={{ textAlign: "center", marginTop: "auto", display: "flex", flexDirection: "column", gap: "8px" }}>
            <Button 
              type="primary"
              style={{ width: "100%" }}
              onClick={handleEdit}
            >
              Edit Stamp
            </Button>
            <Button 
              type="primary"
              style={{ width: "100%" }}
              onClick={handleDelete}
            >
              Delete Stamp
            </Button>
          </div>
        </>
      ) : (
        <>
          <Form 
            form={form} 
            labelAlign="right"
            labelCol={{ flex: "110px" }}
            style={{ 
              marginTop: "12px", 
            }}
          >
            <Form.Item name="country" label="Country">
              <Input />
            </Form.Item>
            <Form.Item name="date" label="Date">
              <Input type="date"/>
            </Form.Item>
            <Form.Item name="direction" label="Direction">
              <Select
                options={[
                  {value: "Unknown", label: "Unknown"},
                  {value: "ENTRY", label: "ENTRY"},
                  {value: "EXIT", label: "EXIT"}
                ]}
              />
            </Form.Item>
          </Form>

          <div style={{ textAlign: "center", marginTop: "auto", display: "flex", flexDirection: "column", gap: "8px" }}>
            <Button 
              type="primary"
              style={{ width: "100%" }}
              onClick={handleSave}
            >
              Save Edit
            </Button>
            <Button 
              type="primary"
              style={{ width: "100%" }}
              onClick={() => setEditing(false)}
            >
              Cancel Edit
            </Button>
          </div>
        </>
      )}
    </div>
  )
}


const TimelineTable: React.FC<TimelineTableProps> = ({ 
  stays, 
  handleClickedStamp, 
  selectedCell, 
  curTablePage, 
  setCurTablePage, 
  pageSize, 
  sessionId,
  onTimelineRebuild
}) => {
  const [rebuildingTimeline, setRebuildingTimeline] = useState(false)

  const columns: ColumnsType<StayResponse> = [
    {
      title: 'Country',
      dataIndex: 'country',
      key: 'country',
      render: (country: string | null) => country ?? 'Unknown',
    },
    {
      title: 'Date of Entry',
      dataIndex: 'entryDate',
      key: 'entryDate',
      render: (entryDate: string | null) => (entryDate ? formatDate(entryDate) : 'Unknown'),
      onCell: (record) => {
        const isSelected = selectedCell?.stayId === record.stayId && selectedCell.field === "entryStamp"
        return record.entryStamp !== null
          ? {
            onClick: () => { handleClickedStamp(record.entryStamp) },
            className: isSelected ? "clickable-cell selected-cell" : "clickable-cell",
          } : {}
      }
    },
    {
      title: 'Date of Exit',
      dataIndex: 'exitDate',
      key: 'exitDate',
      render: (exitDate: string | null, record: StayResponse) => (
        exitDate ? formatDate(exitDate) : (record.flags.includes('ongoing') ? 'Ongoing': 'Unknown')
      ),
      onCell: (record) => {
        const isSelected = selectedCell?.stayId === record.stayId && selectedCell.field === "exitStamp"
        return record.exitStamp !== null
          ? {
            onClick: () => { handleClickedStamp(record.exitStamp) },
            className: isSelected ? "clickable-cell selected-cell" : "clickable-cell",
          } : {}
      }
    }
  ]

  const rebuildTimeline = async () => {
    setRebuildingTimeline(true)
    try {
      const response = await fetch(`/api/sessions/${sessionId}/rebuild-travel-history`, {
        method: "POST"
      })
      if (!response.ok) {
        throw new Error("Timeline rebuild failed")
      }
      const newTimeline: TravelHistoryResponse = await response.json()
      onTimelineRebuild(newTimeline)
    } catch (e) {
      console.log("Could not rebuild timeline")
    } finally {
      setRebuildingTimeline(false)
    }
  }

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <ConfigProvider
        theme={{
          components: {
            Table: {
              rowHoverBg: "transparent",
            }
          }
        }}
      >
        <Table 
          bordered 
          columns={columns} 
          dataSource={stays} 
          rowKey="stayId"
          pagination={{ current: curTablePage, pageSize: pageSize, onChange: setCurTablePage }}
        />
      </ConfigProvider>
      <div style={{ textAlign: "center", marginTop: "auto" }}>
        <Button 
          type="primary"
          style={{ width: "100%" }}
          onClick={rebuildTimeline}
        >
          Reconstruct Travel Timeline
        </Button>
      </div>
    </div>
  )
}


export const TableView: React.FC<TableViewProps> = ({ sessionId, pages, stays, handleStampUpdate, handleTimelineRebuild, handleStampDelete }) => {
  // const [clickedStamp, setClickedStamp] = useState<StampRecord | null>(null)
  const [curPageIndex, setCurPageIndex] = useState(0)
  const [clickStampId, setClickStampId] = useState('')
  const [selectedTableCell, setSelectedTableCell] = useState<{ stayId: string; field: "entryStamp" | "exitStamp" } | null>(null)
  const [curTablePage, setCurTablePage] = useState(1)
  const pageSize = 10

  const clickedStamp = clickStampId
    ? pages?.flatMap(page => page.stamps).find(stamp => stamp.stampId === clickStampId) ?? null
    : null

  const handleStampSelected = (stamp: StampRecord | null) => {
    setClickStampId(stamp?.stampId ?? "")

    if (stamp == null) {
      setSelectedTableCell(null)
      return
    }

    const targetIndex = pages.findIndex((page) => page.pageId === stamp.pageId)
    if (targetIndex !== -1) {
      setCurPageIndex(targetIndex)
    }

    const stayIndex = stays.findIndex(s =>
      s.entryStamp?.stampId === stamp.stampId || s.exitStamp?.stampId === stamp.stampId
    )

    if (stayIndex === -1) {
      setSelectedTableCell(null)
      return
    }

    const stay = stays[stayIndex]
    const field = stay.entryStamp?.stampId === stamp.stampId ? "entryStamp" : "exitStamp"

    setSelectedTableCell({ stayId: stay.stayId, field: field })
    setCurTablePage(Math.floor(stayIndex / pageSize) + 1)
  }


  return (
    <div style={{ display: "flex", gap: "2%" }}>
      <div style={{ flex: 1 }}>
        <TimelineTable 
          stays={stays} 
          handleClickedStamp={handleStampSelected} 
          selectedCell={selectedTableCell}
          curTablePage={curTablePage}
          setCurTablePage={setCurTablePage}
          pageSize={pageSize}
          sessionId={sessionId}
          onTimelineRebuild={handleTimelineRebuild}
        />
      </div>
      <div style={{ flex: 2 }}>
        <Card style={{ height: "100%" }}>
          <div style={{ display: "flex", gap: "2%" }}>
            <div style={{ flex: 13 }}>
              <CustomPageCarousel 
                pages={pages} 
                curPageIndex={curPageIndex} 
                setCurPageIndex={setCurPageIndex}
                clickStampId={clickStampId}
                onStampSelected={handleStampSelected}
              />
            </div>
            <div style={{ flex: 7 }}>
              <StampDetailView 
                sessionId={sessionId} 
                stamp={clickedStamp} 
                handleStampUpdate={handleStampUpdate}
                handleStampDelete={handleStampDelete}
                handleStampSelected={handleStampSelected}
              />
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
