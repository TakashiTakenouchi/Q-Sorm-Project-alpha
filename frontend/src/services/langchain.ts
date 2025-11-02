import apiClient from './api';

export interface LangchainEvidenceStore {
  total: number;
  top_categories: Array<{
    category: string;
    value: number;
    share_pct: number;
  }>;
}

export interface LangchainEvidenceDifference {
  category: string;
  store_a: number;
  store_b: number;
  difference: number;
}

export interface LangchainEvidence {
  stores: Record<string, LangchainEvidenceStore>;
  differences: LangchainEvidenceDifference[];
}

export interface LangchainAnalysisRequest {
  session_id: string;
  store_a: string;
  store_b: string;
  category_columns?: string[];
}

export interface LangchainAnalysisResponse {
  success: boolean;
  data: {
    summary: string;
    stores: string[];
    evidence: LangchainEvidence;
  };
}

export const requestLangchainNarrative = async (
  payload: LangchainAnalysisRequest
): Promise<LangchainAnalysisResponse['data']> => {
  const response = await apiClient.post<LangchainAnalysisResponse>(
    '/v2/analysis/langchain',
    payload
  );
  if (!response.data.success) {
    throw new Error('LangChain API call failed');
  }
  return response.data.data;
};
