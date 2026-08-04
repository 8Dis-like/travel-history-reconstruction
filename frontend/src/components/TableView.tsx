import React from 'react'
import { useState, useEffect, useRef } from 'react'

import { Table, Carousel, Card } from 'antd'
import { LeftOutlined, RightOutlined } from '@ant-design/icons'

import type { PageExtractionResponse, StayResponse } from '../types/types'
import '../components/TableView.css'
import { formatDate } from '../utils/formatters'

interface TimelineTableProps {
  stays: StayResponse[]
}

interface PageCarouselProps {
  pages: PageExtractionResponse[]
  setPageIndex: (index: number) => void
}

interface StampCarouselProps {
  data: PageExtractionResponse
}

interface TableViewProps {
  pages: PageExtractionResponse[]
  stays: StayResponse[]
}


export const CustomPageCarousel: React.FC<PageCarouselProps> = ({ pages, setPageIndex }) => {
  const [curPageIndex, setCurPageIndex] = useState(0)
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const thumbnailRefs = useRef<(HTMLImageElement | null)[]>([])
  const goPrev = () => setCurPageIndex((next) => (next - 1 + pages.length) % pages.length)
  const goNext = () => setCurPageIndex((prev) => (prev + 1) % pages.length)

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
    <div style={{ width: "65%", alignItems: "center" }}>
      <img 
        src={pages[curPageIndex].processedImage} 
        style={{ 
          height: "65vh",
          width: "auto",
          maxWidth: "100%",
          objectFit: "contain",
          display: "block",
          margin: "0 auto"
        }}
      />
      <div style={{ 
        display: "flex", 
        // justifyContent: "center", 
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
                onClick={() => setCurPageIndex(index)}
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


export const PageCarousel: React.FC<PageCarouselProps> = ({ pages, setPageIndex }) => {
  const carouselChildren = pages.map((page, index) => (
    <div key={index}>
      <img
        src={page.processedImage}
        alt={`Slide ${index + 1}`}
        style={{
          width: "100%",
          maxHeight: "70vh",
          objectFit: "contain",
        }}
      />
    </div>
  ))

  return (
    <div className='carousel-container'>
      <Carousel 
        afterChange={(index) => setPageIndex(index)}
      >
        {carouselChildren}
      </Carousel>
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
  const [pageIndex, setPageIndex] = useState(0)

  return (
    <div style={{ display: 'flex', gap: "2%" }}>
      <div style={{ flex: 1 }}>
        <TimelineTable stays={stays}/>
      </div>
      <div style={{ flex: 2 }}>
        <Card>
          <CustomPageCarousel pages={pages} setPageIndex={setPageIndex}/>
        </Card>
      </div>

      {/* <StampCarousel data={data.pages[pageIndex]}/> */}
    </div>
  )
}
