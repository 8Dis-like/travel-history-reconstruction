import React from 'react';
import { useState } from 'react';

import { InboxOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { Upload, Typography, message } from 'antd';

import type { UploadResponse, Page } from '../types/types';
import UploadPreviewGrid from './UploadPreviewGrid';
import AnalyzeButton from './AnalyzeButton';
import { truncateFilename } from '../utils/formatters';

const { Dragger } = Upload
const { Title } = Typography

interface UploadPanelProps {
  sessionId: string,
  handleAnalyze: () => void,
}

const UploadPanel: React.FC<UploadPanelProps> = ({ sessionId, handleAnalyze }) => {
  const [pages, setPages] = useState<Page[]>([])
  const [previewPageId, setPreviewPageId] = useState<string | null>(null)

  const handleRemovePage = async (deletedPage: Page) => {
    const response = await fetch(`/api/sessions/${sessionId}/delete-page/${deletedPage.pageId}`, {
      method: "DELETE"
    })
    if (response.ok) {
      setPages(prevPages => prevPages.filter(page => page.pageId !== deletedPage.pageId))
    } else {
      console.error(`Failed to delete ${deletedPage.sourceFilename}`)
    }
  }

  const processUpload: UploadProps['beforeUpload'] = async (file) => {

    if (file.type === 'application/pdf') {
      const pageId: string = crypto.randomUUID()

      const newPDF: Page = {
        pageId: pageId,
        status: "converting",
        sourceFilename: truncateFilename(file.name),
      }

      setPages(prevPages => [...prevPages, newPDF])

      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`/api/sessions/${sessionId}/upload-pdf`, {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        console.error(`Failed to upload ${file.name} to backend.`)
      }

      // const data = await response.json()
      // console.log(data.pages)
      const pages: UploadResponse[] = await response.json()

      const newPages: Page[] = pages.map((page) => {
        return {
          pageId: page.pageId,
          status: "ready",
          sourceFilename: page.sourceFilename,
          imageSrc: page.imageSrc,
        }
      })

      setPages(prevPages => {
        const desiredPages = prevPages.filter((page) => page.pageId !== pageId)
        const result = [...desiredPages, ...newPages]
        return result
      })
      
    } else if (file.type === "image/jpeg" || file.type === "image/png") {
      const pageId = crypto.randomUUID()
      const reader = new FileReader()

      reader.onload = () => {
        const newPage: Page = {
          pageId: pageId,
          status: "ready",
          sourceFilename: file.name,
          imageSrc: reader.result as string,
        }
        setPages(prevPages => [...prevPages, newPage])
      }

      reader.readAsDataURL(file)

      const formData = new FormData()
      formData.append('file', file)
      formData.append('page_id', pageId)

      const response = await fetch(`/api/sessions/${sessionId}/upload-image`, {
        method: "POST",
        body: formData,
      })
      if (!response.ok) {
        console.error(`Failed to upload ${file.name} to backend.`)
      }


    } else {
      message.error(`${file.name} is not a supported file type.`)
      return Upload.LIST_IGNORE
    }

    return false;
  }

  const props: UploadProps = {
    showUploadList: false,
    beforeUpload: processUpload,
    accept: ".pdf,image/jpeg,image/png",
    multiple: true,
  };

  return (
    <>
      <Dragger { ...props }> 
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">Upload passport files (.pdf, .jpeg, .png) by clicking on or dragging into this area</p>
      </Dragger>
      <Title level={5}>Pages Uploaded: {pages.length}</Title>
      <UploadPreviewGrid 
        pages={pages} 
        onRemove={handleRemovePage} 
        previewPageId={previewPageId} 
        onPreviewChange={setPreviewPageId}
      />
      <AnalyzeButton pages={pages} handleAnalyze={handleAnalyze}/>
    </>
  );
};

export default UploadPanel;