import axios, { AxiosInstance, AxiosResponse } from 'axios';
import type {
  SearchRequest,
  SearchResponse,
  PatentDetails,
  SystemStats,
  ConfigWeights,
  MonitoringMetrics,
} from '@/types';

class APIClient {
  private client: AxiosInstance;

  constructor(baseURL: string = '/api') {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    this.client.interceptors.request.use(
      (config) => config,
      (error) => Promise.reject(error)
    );

    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error);
        return Promise.reject(error);
      }
    );
  }

  async search(request: SearchRequest): Promise<SearchResponse> {
    const response: AxiosResponse<SearchResponse> = await this.client.post(
      '/search',
      request
    );
    return response.data;
  }

  async getPatentDetails(patentId: string): Promise<PatentDetails | null> {
    try {
      const response: AxiosResponse<PatentDetails> = await this.client.get(
        `/patents/${patentId}`
      );
      return response.data;
    } catch {
      return null;
    }
  }

  async getSystemStats(): Promise<SystemStats> {
    const response: AxiosResponse<SystemStats> = await this.client.get(
      '/stats'
    );
    return response.data;
  }

  async updateWeights(weights: ConfigWeights): Promise<void> {
    await this.client.post('/config/weights', weights);
  }

  async getMonitoringMetrics(): Promise<MonitoringMetrics> {
    const response: AxiosResponse<MonitoringMetrics> = await this.client.get(
      '/monitoring/metrics'
    );
    return response.data;
  }
}

export const apiClient = new APIClient();
