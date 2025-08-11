import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { QueryRequest, IngestRequest } from '@/types';

export const useRepos = () => {
  return useQuery({
    queryKey: ['repos'],
    queryFn: api.getRepos,
  });
};

export const useIngestRepo = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: IngestRequest) => api.ingestRepo(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repos'] });
    },
  });
};

export const useDeleteRepo = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (repoId: string) => api.deleteRepo(repoId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repos'] });
    },
  });
};

export const useQueryCodebase = () => {
  return useMutation({
    mutationFn: (data: QueryRequest) => api.query(data),
  });
};