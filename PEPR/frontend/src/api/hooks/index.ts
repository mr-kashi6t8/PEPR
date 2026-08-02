import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../client';

export function useIndicators() {
  return useQuery({
    queryKey: ['indicators'],
    queryFn: api.getIndicators,
    staleTime: 1000 * 60 * 5,
  });
}

export function useIndicatorDetail(code: string) {
  return useQuery({
    queryKey: ['indicator', code],
    queryFn: () => api.getIndicatorByCode(code),
    enabled: Boolean(code),
  });
}

export function useTrends(timeframe?: string) {
  return useQuery({
    queryKey: ['trends', timeframe ?? 'all'],
    queryFn: () => api.getTrends(timeframe ?? 'all'),
    staleTime: 1000 * 60 * 5,
  });
}

export function useAnomalies(filter?: any) {
  return useQuery({
    queryKey: ['anomalies', filter],
    queryFn: api.getAnomalies,
    staleTime: 1000 * 60 * 5,
  });
}

export function usePolicyGaps() {
  return useQuery({
    queryKey: ['policy-gaps'],
    queryFn: api.getPolicyGaps,
    staleTime: 1000 * 60 * 5,
  });
}

export const useGaps = usePolicyGaps;

export function useNews() {
  return useQuery({
    queryKey: ['news'],
    queryFn: api.getNews,
    staleTime: 1000 * 60 * 5,
  });
}

export const useNewsArticles = useNews;

export function useResearchPapers(query?: string, topic?: string) {
  return useQuery({
    queryKey: ['research', query, topic],
    queryFn: api.getResearchPapers,
    staleTime: 1000 * 60 * 5,
  });
}

export const useResearch = useResearchPapers;

export function useUploadResearchPaperMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (formData: FormData) => api.uploadResearchPaper(formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['research'] });
    },
  });
}

export const useIngestPDFMutation = useUploadResearchPaperMutation;

export function useProblems() {
  return useQuery({
    queryKey: ['problems'],
    queryFn: api.getProblems,
    staleTime: 1000 * 60 * 5,
  });
}

export function useProblemDetail(id: string) {
  return useQuery({
    queryKey: ['problem', id],
    queryFn: () => api.getProblemDetail(id),
    enabled: Boolean(id),
  });
}

export function useAlerts() {
  return useQuery({
    queryKey: ['alerts'],
    queryFn: api.getAlerts,
    staleTime: 1000 * 30,
  });
}

export function useReports() {
  return useQuery({
    queryKey: ['reports'],
    queryFn: api.getReports,
    staleTime: 1000 * 60 * 5,
  });
}

export function useReportDetail(id: string) {
  return useQuery({
    queryKey: ['report', id],
    queryFn: () => api.getReportDetail(id),
    enabled: Boolean(id),
  });
}

export function useGenerateReportMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.generateReport,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
    },
  });
}

export function useDeleteReportMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deleteReport(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
    },
  });
}

export function useTriggerIngestionMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sourceId: string) => api.triggerIngestion(sourceId),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['admin-sources'], refetchType: 'active' }),
        queryClient.invalidateQueries({ queryKey: ['admin-jobs'], refetchType: 'active' }),
        queryClient.invalidateQueries({ queryKey: ['indicators'], refetchType: 'active' }),
        queryClient.invalidateQueries({ queryKey: ['trends'], refetchType: 'active' }),
        queryClient.invalidateQueries({ queryKey: ['anomalies'], refetchType: 'active' }),
      ]);
    },
  });
}

export function useTriggerAllIngestionMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.triggerAllIngestion,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['admin-sources'], refetchType: 'active' }),
        queryClient.invalidateQueries({ queryKey: ['admin-jobs'], refetchType: 'active' }),
        queryClient.invalidateQueries({ queryKey: ['indicators'], refetchType: 'active' }),
        queryClient.invalidateQueries({ queryKey: ['trends'], refetchType: 'active' }),
        queryClient.invalidateQueries({ queryKey: ['anomalies'], refetchType: 'active' }),
      ]);
    },
  });
}

export function useAdminDataSources() {
  return useQuery({
    queryKey: ['admin-sources'],
    queryFn: api.getDataSources,
    staleTime: 1000 * 30,
  });
}

export function useAdminIngestionJobs() {
  return useQuery({
    queryKey: ['admin-jobs'],
    queryFn: api.getIngestionJobs,
    staleTime: 1000 * 15,
  });
}

export function useSystemHealth() {
  return useQuery({
    queryKey: ['system-health'],
    queryFn: api.getSystemHealth,
    staleTime: 1000 * 30,
  });
}

export function useAdminData() {
  const sources = useAdminDataSources();
  const jobs = useAdminIngestionJobs();
  const health = useSystemHealth();

  return {
    sources: sources.data || [],
    jobs: jobs.data || [],
    health: health.data,
    isLoading: sources.isLoading || jobs.isLoading || health.isLoading,
    refetch: () => {
      sources.refetch();
      jobs.refetch();
      health.refetch();
    },
  };
}
