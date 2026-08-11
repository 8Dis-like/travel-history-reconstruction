import React from 'react'
import { useState, useEffect, useRef } from 'react'

import { Table, Card, ConfigProvider } from 'antd'
import { LeftOutlined, RightOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'

import type { PageExtractionResponse, StayResponse, StampRecord } from '../types/types'
import '../components/TableView.css'
import { formatDate } from '../utils/formatters'

interface TimelineTableProps {
  stays: StayResponse[]
  handleClickedStamp: (stamp: StampRecord | null) => void
}

interface PageCarouselProps {
  pages: PageExtractionResponse[]
  setClickedStamp: (stamp: StampRecord | null) => void
  curPageIndex: number
  setCurPageIndex: React.Dispatch<React.SetStateAction<number>>
  clickStampId: string
  setClickStampId: React.Dispatch<React.SetStateAction<string>>
}

interface StampDetailViewProps {
  stamp: StampRecord | null
}

interface TableViewProps {
  pages: PageExtractionResponse[]
  stays: StayResponse[]
}


const CustomPageCarousel: React.FC<PageCarouselProps> = ({ pages, setClickedStamp, curPageIndex, setCurPageIndex, clickStampId, setClickStampId }) => {
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const thumbnailRefs = useRef<(HTMLImageElement | null)[]>([])
  const imgContainerRef = useRef<HTMLImageElement>(null)

  const goPrev = () => {
    setCurPageIndex((next) => (next - 1 + pages.length) % pages.length)
    setClickStampId('')
    setClickedStamp(null)
  }
  const goNext = () => {
    setCurPageIndex((prev) => (prev + 1) % pages.length)
    setClickStampId('')
    setClickedStamp(null)
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
                  setClickStampId(stamp.stampId)
                  setClickedStamp(stamp)
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
                    setClickStampId('')
                    setClickedStamp(null)
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


const StampDetailView: React.FC<StampDetailViewProps> = ({ stamp }) => {
  if (stamp === null) {
    return
  }

  return (
    <div>
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
      <div style={{ textAlign: 'center', marginTop: '12px' }}>
        <div>Country: {stamp.extractedFields.country !== null ? stamp.extractedFields.country : "Unknown"}</div>
        <div>Date: {stamp.extractedFields.date !== null ? formatDate(stamp.extractedFields.date) : "Unknown"}</div>
        <div>Entry/Exit: {stamp.extractedFields.direction !== null ? stamp.extractedFields.direction : "Unknown"}</div>
      </div>
    </div>
    
  )
}


const TimelineTable: React.FC<TimelineTableProps> = ({ stays, handleClickedStamp }) => {
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
      onCell: (record) => (
        record.entryStamp !== null
          ? {
            onClick: () => {
              handleClickedStamp(record.entryStamp)
            },
            className: "clickable-cell",
          } : {}
      )
    },
    {
      title: 'Date of Exit',
      dataIndex: 'exitDate',
      key: 'exitDate',
      render: (exitDate: string | null, record: StayResponse) => (
        exitDate ? formatDate(exitDate) : (record.flags.includes('ongoing') ? 'Ongoing': 'Unknown')
      ),
      onCell: (record) => (
        record.exitStamp !== null
          ? {
            onClick: () => {
              handleClickedStamp(record.exitStamp)
            },
            className: "clickable-cell",
          } : {}
      )
    }
  ]

  return (
    <div>
      <ConfigProvider
        theme={{
          components: {
            Table: {
              rowHoverBg: "transparent",
            }
          }
        }}
      >
        <Table bordered columns={columns} dataSource={stays} rowKey="stayId"/>
      </ConfigProvider>
    </div>
  )
}


export const TableView: React.FC<TableViewProps> = ({ pages, stays }) => {
  const [clickedStamp, setClickedStamp] = useState<StampRecord | null>(null)
  const [curPageIndex, setCurPageIndex] = useState(0)
  const [clickStampId, setClickStampId] = useState('')

  const handleTableStampClick = (stamp: StampRecord | null) => {
    setClickedStamp(stamp)
    if (stamp !== null) {
      const targetIndex = pages.findIndex((page) =>
        page.pageNumber === stamp.pageNumber
      )
      if (targetIndex !== -1) {
        setCurPageIndex(targetIndex)
      }
      setClickStampId(stamp.stampId)
    } else {
      setClickStampId('')
    }
  }

  return (
    <div style={{ display: "flex", gap: "2%" }}>
      <div style={{ flex: 1 }}>
        <TimelineTable stays={stays} handleClickedStamp={handleTableStampClick}/>
      </div>
      <div style={{ flex: 2 }}>
        <Card>
          <div style={{ display: "flex", gap: "2%" }}>
            <div style={{ flex: 13 }}>
              <CustomPageCarousel 
                pages={pages} 
                setClickedStamp={setClickedStamp} 
                curPageIndex={curPageIndex} 
                setCurPageIndex={setCurPageIndex}
                clickStampId={clickStampId}
                setClickStampId={setClickStampId}
              />
            </div>
            <div style={{ flex: 7 }}>
              <StampDetailView stamp={clickedStamp} />
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
