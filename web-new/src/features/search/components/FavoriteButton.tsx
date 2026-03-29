import React, { useState } from 'react';
import { Button, Modal, Input, message } from 'antd';
import { StarOutlined, StarFilled } from '@ant-design/icons';
import { useSearchStore } from '../stores/searchStore';
import { useTranslation } from 'react-i18next';
import type { SearchHit } from '@/types';

interface FavoriteButtonProps {
  query: string;
  hits: SearchHit[];
}

export const FavoriteButton: React.FC<FavoriteButtonProps> = ({ query, hits }) => {
  const { t } = useTranslation();
  const { isFavorited, addToFavorites, removeFromFavorites, getFavoriteByQuery } = useSearchStore();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [notes, setNotes] = useState('');

  const favorited = isFavorited(query);
  const existingFavorite = getFavoriteByQuery(query);

  const handleToggleFavorite = () => {
    if (favorited && existingFavorite) {
      removeFromFavorites(existingFavorite.id);
      message.success(t('search.removedFromFavorites'));
    } else {
      setIsModalOpen(true);
    }
  };

  const handleSave = () => {
    addToFavorites(query, hits, notes || undefined);
    setIsModalOpen(false);
    setNotes('');
    message.success(t('search.addedToFavorites'));
  };

  const handleCancel = () => {
    setIsModalOpen(false);
    setNotes('');
  };

  return (
    <>
      <Button
        type={favorited ? 'primary' : 'default'}
        icon={favorited ? <StarFilled /> : <StarOutlined />}
        onClick={handleToggleFavorite}
      >
        {favorited ? t('search.favorited') : t('search.favorite')}
      </Button>

      <Modal
        title={t('search.addToFavorites')}
        open={isModalOpen}
        onOk={handleSave}
        onCancel={handleCancel}
        okText={t('common.save')}
        cancelText={t('common.cancel')}
      >
        <p>{t('search.favoriteDescription', { query })}</p>
        <Input.TextArea
          placeholder={t('search.favoriteNotesPlaceholder')}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={3}
        />
      </Modal>
    </>
  );
};
