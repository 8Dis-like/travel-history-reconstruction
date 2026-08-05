import React from 'react';
import { useState } from 'react';

import { InboxOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { Upload, Typography, message } from 'antd';

import type { Page } from '../types/types';
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
  // const [fileList, setFileList] = useState<UploadFile[]>([])
  const [pages, setPages] = useState<Page[]>([])
  const [previewPageId, setPreviewPageId] = useState<string | null>(null)

  /*const handleChange: UploadProps['onChange'] = ({fileList: newFileList}) => {
    setFileList(newFileList);
  }*/

  /*  const truncateFilename = (filename: string, maxLength: number = 15) => {
    if (filename.length <= maxLength) {
      return filename
    }   

    const lastDotIndex = filename.lastIndexOf(".")
    const extension = filename.slice(lastDotIndex)
    const name = filename.slice(0, lastDotIndex)

    const truncatedName = name.slice(0, maxLength - extension.length - 3)
    return `${truncatedName}...${extension}`
  } */

  const handleRemovePage = (id: string) => {
    setPages(prevPages => prevPages.filter(page => page.id !== id))
  }

  const processUpload: UploadProps['beforeUpload'] = async (file) => {

    if (file.type === 'application/pdf') {
      const pageID: string = crypto.randomUUID()

      const newPDF: Page = {
        id: pageID,
        status: "converting",
        sourceFileName: truncateFilename(file.name),
      }

      setPages(prevPages => [...prevPages, newPDF])

      const formData = new FormData();
      formData.append('file', file);
      formData.append('session_id', sessionId);

      const response = await fetch("/api/upload-pdf", {
        method: "POST",
        body: formData,
      })

      const data = await response.json()
      // console.log(data.pages)

      const newPages = data.pages.map((page: {pageNumber: number, imgUrl: string}) => {
        return {
          id: crypto.randomUUID(),
          status: "ready",
          imageSrc: page.imgUrl,
          sourceFileName: `${file.name}_pg${page.pageNumber + 1}`,
        }
      })

      setPages(prevPages => {
        const desiredPages = prevPages.filter((page) => page.id !== pageID)
        const result = [...desiredPages, ...newPages]
        return result
      })
      
    } else if (file.type === "image/jpeg" || file.type === "image/png") {
      const reader = new FileReader()

      reader.onload = () => {
        const newPage: Page = {
          id: file.uid,
          status: "ready",
          imageSrc: reader.result as string,
          sourceFileName: file.name,
        }
        setPages(prevPages => [...prevPages, newPage])
      }

      reader.readAsDataURL(file)

      const formData = new FormData()
      formData.append('file', file)
      formData.append('session_id', sessionId)

      const response = await fetch("/api/upload-image", {
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
    // listType: "picture-card",
    // fileList: fileList,
    // onChange: handleChange,
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