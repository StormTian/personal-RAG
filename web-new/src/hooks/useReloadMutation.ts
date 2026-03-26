import { useMutation, useQueryClient } from '@tanstack/react-query';
import { libraryApi } from '@/services/api';

export function useReloadMutation() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: () => libraryApi.reload(),
    onSuccess: (data) => {
      queryClient.setQueryData(['library'], data);
    },
  });
}
