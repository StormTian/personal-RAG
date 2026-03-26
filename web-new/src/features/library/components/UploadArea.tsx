import React, { useState } from 'react';
import { Upload, Progress, message } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { uploadApi } from '@/services/api';

const { Dragger } = Upload;

interface UploadAreaProps {
  onUploadSuccess: () => void;
}

const ACCEPTED_FORMATS = '.md,.txt,.doc,.docx,.pdf';

export const UploadArea: React.FC<UploadAreaProps> = ({ onUploadSuccess }) => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const { t } = useTranslation();

  const handleUpload = async (file: File): Promise<boolean> => {
    setUploading(true);
    setProgress(0);

    try {
      const result = await uploadApi.uploadFile(file, (percent) => {
        setProgress(percent);
      });

      if (result.success) {
        message.success(t('library.uploadSuccess'));
        onUploadSuccess();
      } else {
        message.error(result.message || t('library.uploadError'));
      }
    } catch (error) {
      message.error(error instanceof Error ? error.message : t('library.uploadError'));
    } finally {
      setUploading(false);
      setProgress(0);
    }

    return false;
  };

  return (
    <div style={{ marginTop: 16 }}>
      <Dragger
        name="file"
        multiple={false}
        beforeUpload={handleUpload}
        accept={ACCEPTED_FORMATS}
        showUploadList={false}
        disabled={uploading}
      >
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">{t('library.uploadDragText')}</p>
        <p className="ant-upload-hint">{t('library.uploadHint')}</p>
      </Dragger>

      {uploading && (
        <div style={{ marginTop: 16 }}>
          <Progress percent={progress} status="active" />
        </div>
      )}
    </div>
  );
};
