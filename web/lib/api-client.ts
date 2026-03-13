/**
 * API client for BBCoach backend
 */
import axios, { AxiosInstance } from "axios";
import type {
  HealthResponse,
  DataStatusResponse,
  SeasonsResponse,
  TeamsResponse,
  TeamStats,
  TopPlayersResponse,
  Player,
  MatchupRequest,
  MatchupResponse,
  CoachRequest,
  CoachResponse,
  ScoutRequest,
  ScoutResponse,
  ModelInfoResponse,
} from "@/types/api";

class ApiClient {
  private client: AxiosInstance;

  constructor(baseUrl: string = "http://localhost:8000") {
    this.client = axios.create({
      baseURL: baseUrl,
      timeout: 30000,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Add request/response interceptors for logging
    this.client.interceptors.request.use((config) => {
      console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
      return config;
    });

    this.client.interceptors.response.use(
      (response) => {
        console.log(`[API] Response: ${response.status}`);
        return response;
      },
      (error) => {
        console.error(`[API] Error:`, error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  // Health & Data
  async health(): Promise<HealthResponse> {
    const { data } = await this.client.get<HealthResponse>("/health");
    return data;
  }

  async dataStatus(): Promise<DataStatusResponse> {
    const { data } = await this.client.get<DataStatusResponse>("/api/data/status");
    return data;
  }

  async refreshData(): Promise<{ message: string; status: DataStatusResponse }> {
    const { data } = await this.client.get("/api/data/refresh");
    return data;
  }

  // Statistics
  async getSeasons(league: string = "Men"): Promise<SeasonsResponse> {
    const { data } = await this.client.get<SeasonsResponse>("/api/stats/seasons", {
      params: { league },
    });
    return data;
  }

  async getTeams(season: number, league: string = "Men"): Promise<TeamsResponse> {
    const { data } = await this.client.get<TeamsResponse>("/api/stats/teams", {
      params: { season, league },
    });
    return data;
  }

  async getTopPlayers(
    season: number,
    league: string = "Men",
    metric: string = "PPG",
    limit: number = 10
  ): Promise<TopPlayersResponse> {
    const { data } = await this.client.get<TopPlayersResponse>(
      "/api/stats/top-players",
      {
        params: { season, league, metric, limit },
      }
    );
    return data;
  }

  async getTeamStats(teamId: string, season: number): Promise<TeamStats | null> {
    try {
      const { data } = await this.client.get<TeamStats>(`/api/stats/team/${teamId}`, {
        params: { season },
      });
      return data;
    } catch (error) {
      console.error(`Failed to get team stats for ${teamId}:`, error);
      return null;
    }
  }

  async comparePlayers(
    playerNames: string[],
    season: number,
    league: string = "Men"
  ): Promise<Player[]> {
    const { data } = await this.client.post<Player[]>("/api/stats/compare-players", {
      player_names: playerNames,
      season,
      league,
    });
    return data;
  }

  // Analytics
  async predictMatchup(request: MatchupRequest): Promise<MatchupResponse> {
    const { data } = await this.client.post<MatchupResponse>(
      "/api/analytics/predict-matchup",
      request
    );
    return data;
  }

  async predictMatchupMultiSeason(teamAId: string, teamBId: string): Promise<string> {
    const { data } = await this.client.post<{ team_a_id: string; team_b_id: string; analysis: string }>(
      "/api/analytics/predict-matchup-multi-season",
      { team_a_id: teamAId, team_b_id: teamBId }
    );
    return data.analysis;
  }

  // Coach/AI
  async askCoach(request: CoachRequest): Promise<CoachResponse> {
    const { data } = await this.client.post<CoachResponse>("/api/coach/ask", request);
    return data;
  }

  async generateScoutingReport(request: ScoutRequest): Promise<ScoutResponse> {
    const { data } = await this.client.post<ScoutResponse>(
      "/api/coach/scouting-report",
      request
    );
    return data;
  }

  async getModelInfo(): Promise<ModelInfoResponse> {
    const { data } = await this.client.get<ModelInfoResponse>("/api/coach/model-info");
    return data;
  }
}

// Create singleton instance
export const api = new ApiClient();
export default api;
