import { InboxOutlined } from "@ant-design/icons";
import { Button, List, Tag, Upload } from "antd";
import type { UploadProps } from "antd";
import type { UploadFileItem, UploadStatus } from "../types";

const { Dragger } = Upload;

interface UploadPanelProps {
  files: UploadFileItem[];
  onAddFiles: (files: File[]) => void;
  onStartRecognition: () => void;
}

const STATUS_COLOR: Record<UploadStatus, string> = {
  pending: "default",
  processing: "processing",
  done: "success",
  error: "error",
};

export function UploadPanel({ files, onAddFiles, onStartRecognition }: UploadPanelProps) {
  const hasProcessable = files.some((f) => f.status === "pending" || f.status === "error");
  const isRecognizing = files.some((f) => f.status === "processing");

  const draggerProps: UploadProps = {
    multiple: true,
    accept: "application/pdf",
    showUploadList: false,
    beforeUpload: (file) => {
      onAddFiles([file]);
      return false;
    },
  };

  return (
    <section className="upload-panel">
      <Dragger {...draggerProps}>
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">Drag PDFs here, or click to select files</p>
      </Dragger>

      <List
        style={{ margin: "16px 0" }}
        dataSource={files}
        renderItem={(item) => (
          <List.Item key={item.id}>
            <List.Item.Meta title={item.file.name} />
            <Tag color={STATUS_COLOR[item.status]}>{item.status}</Tag>
          </List.Item>
        )}
      />

      <Button
        type="primary"
        disabled={!hasProcessable || isRecognizing}
        loading={isRecognizing}
        onClick={onStartRecognition}
      >
        Start recognition
      </Button>
    </section>
  );
}
