import React from 'react';
import { Upload, message } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { uploadApi } from '@/services/api';
import { useUploadProgress } from '@/features/upload/hooks/useUploadProgress';
import { UploadProgressList } from '@/features/upload/components/UploadProgressList';

const { Dragger } = Upload;

interface UploadAreaProps {
  onUploadSuccess: () => void;
}

const ACCEPTED_FORMATS = '.md,.txt,.doc,.docx,.pdf';

export const UploadArea: React.FC<UploadAreaProps> = ({ onUploadSuccess }) => {
  const { t } = useTranslation();
  const {
    uploads,
    addFiles,
    updateProgress,
    markSuccess,
    markError,
    clearCompleted,
    clearAll,
    hasActiveUploads,
  } = useUploadProgress();

  const handleBeforeUpload = (file: File): boolean => {
    // Add file to queue
    addFiles([file]);

    // Start upload
    handleUpload(file);

    // Prevent default upload behavior
    return false;
  };

  const handleUpload = async (file: File) => {
    const uploadId = uploads.find((u) => u.file === file)?.id;
    if (!uploadId) return;

    try {
      const result = await uploadApi.uploadFile(file, (progressEvent) => {
        // Calculate bytes uploaded
        const bytesUploaded = (progressEvent.percentage / 100) * file.size;
        updateProgress(uploadId, progressEvent.percentage, bytesUploaded);
      });

      if (result.status === 'success' || result.success) {
        markSuccess(uploadId);
        message.success(t('library.uploadSuccess', { filename: file.name }));
        onUploadSuccess();
      } else {
        markError(uploadId, result.message || t('library.uploadError'));
        message.error(result.message || t('library.uploadError'));
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : t('library.uploadError');
      markError(uploadId, errorMessage);
      message.error(errorMessage);
    }
  };

  return (
    <div style={{ marginTop: 16 }}>
      <Dragger
        name="file"
        multiple={true}
        beforeUpload={handleBeforeUpload}
        accept={ACCEPTED_FORMATS}
        showUploadList={false}
        disabled={hasActiveUploads}
      >
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">{t('library.uploadDragText')}</p>
        <p className="ant-upload-hint">{t('library.uploadHint')}</p>
      </Dragger>

      {uploads.length > 0 && (
        <UploadProgressList
          uploads={uploads}
          onClearCompleted={clearCompleted}
          onClearAll={clearAll}
        />
      )}
    </div>
  );
};
