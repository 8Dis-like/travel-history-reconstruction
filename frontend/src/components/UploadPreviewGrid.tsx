import React from 'react'
// import { useState } from 'react'

import { Card, Spin, Image } from 'antd'
import { LoadingOutlined, ExclamationCircleOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons'

import type { Page } from '../types/types'
import './UploadPreviewGrid.css'
import { truncateFilename } from '../utils/formatters'


interface PageGridProps {
    pages: Page[],
    onRemove: (deletedPage: Page) => void,
    previewPageId: string | null,
    onPreviewChange: (id: string | null) => void,
}

const UploadPreviewGrid: React.FC<PageGridProps> = ({ pages, onRemove, previewPageId, onPreviewChange }) => {
    return (
      <Card 
        styles={{
          root: { border: '1px solid rgb(0, 0, 0)'}
        }}
        style={{ 
          height: 'calc(100vh - 425px)', 
          overflowY: 'auto', 
          backgroundColor: 'rgb(238, 238, 238)', 
        }}
        className='grid-container'
      >
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', justifyContent: 'center' }}>
          {pages.map((page) => (
            <Card
              key={page.pageId}
              style={{ width: 104, height: 104 }}
              styles={{ body: { padding: 0, width: '100%', height: '100%' } }}
              className="page-tile"
            >
              {page.status === 'ready' && (
                <Image
                  src={page.imageSrc}
                  alt={truncateFilename(page.sourceFilename)}
                  width="100%"
                  height="100%"
                  style={{ objectFit: 'contain' }}
                  preview={{
                    open: previewPageId === page.pageId,
                    onOpenChange: (open) => onPreviewChange(open ? page.pageId : null)
                  }}
                />
              )}
              {page.status === 'converting' && (
                <div style={{ position: 'relative', height: '100%' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                    <Spin indicator={<LoadingOutlined spin />} />
                  </div>
                  <p style={{ 
                    position: 'absolute', 
                    top: '65%', 
                    width: '100%', 
                    textAlign: 'center', 
                    lineHeight: 1.1, 
                    fontSize: '11px',
                    boxSizing: 'border-box',
                    padding: '0px 3px'
                  }}>
                    Processing {truncateFilename(page.sourceFilename)}
                  </p>
                </div>
              )}
              {page.status === 'error' && (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                  <ExclamationCircleOutlined style={{ color: '#ff4d4f', fontSize: '20px' }} />
                </div>
              )}
              {page.status === "ready" && (
                <div className='hover-overlay'>
                  <span className='overlay-icon'>
                    <EyeOutlined 
                      onClick={() => onPreviewChange(page.pageId)}
                    />
                  </span>
                  <span className='overlay-icon'>
                    <DeleteOutlined 
                      onClick={() => onRemove(page)}
                    />
                  </span>
                </div>
              )}
            </Card>
          ))}
        </div>
      </Card>
    )
}

export default UploadPreviewGrid