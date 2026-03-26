import { useQuery, useQueryClient } from '@tanstack/react-query';
import { libraryApi } from '@/services/api';

const LIBRARY_QUERY_KEY = 'library';

export function useLibraryQuery() {
  return useQuery({
    queryKey: [LIBRARY_QUERY_KEY],
    queryFn: () => libraryApi.getInfo(),
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}

export function useLibraryInvalidation() {
  const queryClient = useQueryClient();
  
  return {
    invalidate: () => {
      queryClient.invalidateQueries({ queryKey: [LIBRARY_QUERY_KEY] });
    },
  };
}
