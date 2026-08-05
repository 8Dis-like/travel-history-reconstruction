import React from 'react'

import { Card, Spin } from 'antd'
import { LoadingOutlined } from '@ant-design/icons'


const ProcessingView: React.FC = () => {
  return (
    <Card style={{ maxWidth: '400px', margin: '80px auto' }} styles={{ body: { height: '250px' }}}>
      <div style={{ position: 'relative', height: '100%' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
          <Spin indicator={<LoadingOutlined style={{ fontSize: 48 }} spin />} />
        </div>
        <p style={{ 
          position: 'absolute', 
          // top: '65%', 
          bottom: '10%',
          width: '100%', 
          textAlign: 'center', 
          lineHeight: 1.1, 
          fontSize: '16px',
        }}>
          Analyzing Passport...
        </p>
      </div>
    </Card>
  )
}

export default ProcessingView