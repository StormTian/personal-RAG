import React, { useState, useCallback } from 'react';
import { Row, Col, Typography, Tag, Space, message } from 'antd';
import { useTranslation } from 'react-i18next';
import { SearchForm } from '@/features/search/components/SearchForm';
import { SearchHistory } from '@/features/search/components/SearchHistory';
import { FavoritesList } from '@/features/search/components/FavoritesList';
import { LibraryPanel } from '@/features/library/components/LibraryPanel';
import { ResultPanel } from '@/features/result/components/ResultPanel';
import { useLibraryQuery } from '@/hooks/useLibraryQuery';
import { useReloadMutation } from '@/hooks/useReloadMutation';
import { useSearchStore } from '@/features/search/stores/searchStore';
import { searchApi } from '@/services/api';
import type { SearchParams, SearchResponse } from '@/types';

const { Title, Paragraph } = Typography;

export const Home: React.FC = () => {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useState<SearchParams | null>(null);
  const [searchResult, setSearchResult] = useState<SearchResponse | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<Error | null>(null);
  
  const { data: libraryData, isLoading: isLibraryLoading, error: libraryError, refetch: _refetchLibrary } = useLibraryQuery();
  const { mutate: reloadLibrary, isPending: isReloading } = useReloadMutation();
  const { addToHistory } = useSearchStore();
  
  const handleSearch = useCallback(async (query: string, topK: number) => {
    setIsSearching(true);
    setSearchError(null);
    setSearchParams({ query, top_k: topK });
    
    try {
      const result = await searchApi.query({ query, top_k: topK });
      setSearchResult(result);
      addToHistory(query, result.hits.length);
    } catch (err) {
      setSearchError(err as Error);
      message.error(t('error.unknown'));
    } finally {
      setIsSearching(false);
    }
  }, [addToHistory, t]);
  
  const handleHistorySelect = useCallback((query: string) => {
    handleSearch(query, 3);
  }, [handleSearch]);
  
  const handleRetrySearch = useCallback(() => {
    if (searchParams) {
      handleSearch(searchParams.query, searchParams.top_k);
    }
  }, [searchParams, handleSearch]);
  
  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 16px' }}>
      {/* Hero Section */}
      <Space direction="vertical" size="small" style={{ marginBottom: 32 }}>
        <Tag color="orange">Offline Retrieval-Augmented Generation</Tag>
        <Title level={1} style={{ margin: 0 }}>{t('app.subtitle')}</Title>
        <Paragraph type="secondary" style={{ maxWidth: 720 }}>
          {t('app.description')}
        </Paragraph>
      </Space>
      
      {/* Main Content */}
      <Row gutter={[24, 24]}>
        {/* Left Column - Search & Library */}
        <Col xs={24} lg={10}>
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <SearchForm onSearch={handleSearch} loading={isSearching} />
            <SearchHistory onSelect={handleHistorySelect} />
            <FavoritesList onSelect={handleHistorySelect} />
            <LibraryPanel
              data={libraryData}
              loading={isLibraryLoading || isReloading}
              error={libraryError}
              onReload={() => reloadLibrary()}
            />
          </Space>
        </Col>
        
        {/* Right Column - Results */}
        <Col xs={24} lg={14}>
          <ResultPanel
            data={searchResult ?? undefined}
            loading={isSearching}
            error={searchError}
            query={searchParams?.query}
            onRetry={handleRetrySearch}
          />
        </Col>
      </Row>
    </div>
  );
};
