import React from 'react'
import { useState, useEffect, useRef } from 'react'

import { Table, Carousel, Card } from 'antd'
import { LeftOutlined, RightOutlined } from '@ant-design/icons'

import type { PageExtractionResponse, StayResponse, StampRecord } from '../types/types'
import '../components/TableView.css'
import { formatDate } from '../utils/formatters'

interface TimelineTableProps {
  stays: StayResponse[]
}

interface PageCarouselProps {
  pages: PageExtractionResponse[]
  setClickedStamp: (stamp: StampRecord | null) => void
}

interface StampCarouselProps {
  data: PageExtractionResponse
}

interface StampDetailViewProps {
  stamp: StampRecord | null
}

interface TableViewProps {
  pages: PageExtractionResponse[]
  stays: StayResponse[]
}


export const CustomPageCarousel: React.FC<PageCarouselProps> = ({ pages, setClickedStamp }) => {
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const thumbnailRefs = useRef<(HTMLImageElement | null)[]>([])
  const imgContainerRef = useRef<HTMLImageElement>(null)

  const [curPageIndex, setCurPageIndex] = useState(0)
  const goPrev = () => {
    setCurPageIndex((next) => (next - 1 + pages.length) % pages.length)
    setImageLoaded(false)
    setClickStampId('')
    setClickedStamp(null)
  }
  const goNext = () => {
    setCurPageIndex((prev) => (prev + 1) % pages.length)
    setImageLoaded(false)
    setClickStampId('')
    setClickedStamp(null)
  }

  const [hoverStampId, setHoverStampId] = useState('')
  const [clickStampId, setClickStampId] = useState('')

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
                  setCurPageIndex(index)
                  setImageLoaded(false)
                  setClickStampId('')
                  setClickedStamp(null)
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


export const StampDetailView: React.FC<StampDetailViewProps> = ({ stamp }) => {
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


export const StampCarousel: React.FC<StampCarouselProps> = ({ data }) => {
  const [stampIndex, setStampIndex] = useState(0);

  const carouselChildren = data.stamps.map((stamp, index) => (
    <div key={index} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
      <img
        src={stamp.stampImage}
        alt={`Slide ${index + 1}`}
        style={{
          width: "100%",
          maxHeight: "20vh",
          objectFit: "contain",
        }}
      />
    </div>
  ))

  const currentStamp = data.stamps[stampIndex].extractedFields

  return (
    <div className='carousel-container'>
      <Carousel 
        afterChange={(index) => setStampIndex(index)}
      >
        {carouselChildren}
      </Carousel>
      <div style={{ textAlign: 'center', marginTop: '12px' }}>
        <div>Country: {currentStamp.country}</div>
        <div>Date: {currentStamp.date !== null ? formatDate(currentStamp.date) : "Unreadable"}</div>
        <div>Entry/Exit: {currentStamp.direction === "arrival" ? "Entry" : "Exit"}</div>
      </div>
    </div>
  )
}



export const TimelineTable: React.FC<TimelineTableProps> = ({ stays }) => {
  const columns = [
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
    },
    {
      title: 'Date of Exit',
      dataIndex: 'exitDate',
      key: 'exitDate',
      render: (exitDate: string | null, record: StayResponse) => (
        exitDate ? formatDate(exitDate) : (record.flags.includes('ongoing') ? 'Ongoing': 'Unknown')
      ),
    }
  ]

  return (
    <div>
      <Table columns={columns} dataSource={stays} rowKey="stayId"/>
    </div>
  )
}


export const TableView: React.FC<TableViewProps> = ({ pages, stays }) => {
  const [clickedStamp, setClickedStamp] = useState<StampRecord | null>(null)

  return (
    <div style={{ display: "flex", gap: "2%" }}>
      <div style={{ flex: 1 }}>
        <TimelineTable stays={stays}/>
      </div>
      <div style={{ flex: 2 }}>
        <Card>
          <div style={{ display: "flex", gap: "2%" }}>
            <div style={{ flex: 13 }}>
              <CustomPageCarousel pages={pages} setClickedStamp={setClickedStamp}/>
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
