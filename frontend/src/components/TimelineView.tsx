import React from 'react'

import { Collapse } from 'antd'

import type { AnalysisResponse, StayResponse } from '../types/types'
import { formatDate } from '../utils/formatters'
// import '../components/TimelineView.css'


interface TimelineViewProps {
  data: AnalysisResponse
}

interface TimelineLabelProps {
  stay: StayResponse
}

interface CustomTimelineItem {
  key: string;
  content: React.ReactNode;
}

interface CustomTimelineProps {
  items: CustomTimelineItem[];
}


const CustomTimeline: React.FC<CustomTimelineProps> = ({ items }) => {
  return (
    <div style={{ paddingLeft: '20px' }}>
      {items.map((item, index) => (
        <div
          key={item.key}
          style={{
            position: 'relative',
            marginLeft: '-20px',
            paddingLeft: '20px',
            paddingBottom: index < items.length - 1 ? '16px' : '0',
          }}
        >
          {index < items.length - 1 && (
            <div
              style={{
                position: 'absolute',
                left: '-2px',
                top: '25px',
                bottom: '-25px',
                width: '2px',
                background: '#d9d9d9',
              }}
            />
          )}
          <div
            style={{
              position: 'absolute',
              left: '-6px',
              top: '25px',
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              background: '#1890ff',
            }}
          />
          {item.content}
        </div>
      ))}
    </div>
  );
};


const TimelineLabel: React.FC<TimelineLabelProps> = ({ stay }) => {
  return (
    <Collapse 
      size="small"
      items={[
        {
          key: stay.stayId,
          label: (
            <div>
              <strong>{stay.country}</strong>
              <p>{formatDate(stay.entryDate)} - {stay.departureDate ? formatDate(stay.departureDate) : "ongoing"}</p>
            </div>
          ),
          children: (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {[stay.entryStamp, stay.exitStamp].filter(Boolean).map((stamp) => (
                <div key={stamp!.type} style={{ display: 'flex', gap: '12px', alignItems: 'center', border: '1px solid #f0f0f0', borderRadius: '6px', padding: '8px 10px' }}>
                  <img src={stamp!.stampImg} style={{ width: '48px', height: '48px', borderRadius: '6px', objectFit: 'cover' }} />
                  <div style={{ flex: 1 }}>
                    <p style={{ fontSize: '13px', color: '#888', margin: 0 }}>
                      {stamp!.type === 'arrival' ? 'Entry' : 'Exit'}
                    </p>
                    <p style={{ fontSize: '14px', margin: '2px 0 0' }}>
                      {formatDate(stamp!.date)}
                    </p>
                  </div>
                  <p style={{ fontSize: '12px', color: '#aaa', margin: 0 }}>
                    {stamp!.sourceFilename.toLowerCase().endsWith('.pdf')
                     ? `${stamp!.sourceFilename}, pg ${stamp!.pageNumber}`
                     : stamp!.sourceFilename }
                  </p>
                </div>
              ))}
            </div>
          )
        }
      ]}
    />
  )
}


const TimelineView: React.FC<TimelineViewProps> = ({ data }) => {

  const timelineItems = data.stays.map((stay) => ({
    key: stay.id,
    content: <TimelineLabel stay={stay} />
  }))

  return (
    <CustomTimeline items={timelineItems}/>
  )
}

export default TimelineView
