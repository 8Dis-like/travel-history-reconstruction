import React from 'react';
// import { useState } from 'react';

import type { Page } from '../types/types';
import { Button } from 'antd'
import './AnalyzeButton.css'

interface AnalyzeButtonProps {
  pages: Page[]
  handleAnalyze: () => void
}

const AnalyzeButton: React.FC<AnalyzeButtonProps> = ({ pages, handleAnalyze }) => {
  return (
    <div style={{ position: 'fixed', bottom: 0, left: 0, width: '100%', padding: '0px 48px 30px 48px', zIndex: 10 }}>
      <Button 
        type="primary" 
        onClick={handleAnalyze}
        disabled={
          pages.length === 0 || pages.some((page) => (page.status === "converting" || page.status === "error"))
        }
        style={{ width: '100%' }}
      >
        Process Passport
      </Button>
    </div>
  )
}

export default AnalyzeButton;