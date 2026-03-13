/**
 * Type definitions for BBCoach API
 */

export interface Player {
  id: string;
  name: string;
  team_id: string;
  season: number;
  league: string;
  PPG?: number;
  RPG?: number;
  APG?: number;
  GP?: number;
  MIN?: number;
  FG%?: number;
  "3P%"?: number;
  FT%?: number;
  EFF?: number;
  [key: string]: any;
}

export interface Team {
  id: string;
  name: string;
  season: number;
  league: string;
  url?: string;
}

export interface TeamStats {
  total_ppg: number;
  total_rpg: number;
  total_apg: number;
  avg_3p_pct: number;
  total_to: number;
  total_min: number;
  top_scorer: string;
  top_playmaker: string;
  top_rebounder: string;
  roster_size: number;
  rotation?: Player[];
  top_8?: Player[];
}

export interface HealthResponse {
  status: "healthy";
  service: string;
}

export interface DataStatusResponse {
  players_count: number;
  teams_count: number;
  schedule_count: number;
  has_players: boolean;
  has_teams: boolean;
  has_schedule: boolean;
  seasons_in_data: number[];
}

export interface SeasonsResponse {
  league: string;
  seasons: number[];
}

export interface TeamsResponse {
  season: number;
  league: string;
  teams: Team[];
}

export interface TopPlayersResponse {
  season: number;
  league: string;
  metric: string;
  players: Player[];
}

export interface MatchupRequest {
  team_a_id: string;
  team_b_id: string;
  season: number;
}

export interface MatchupResponse {
  team_a_id: string;
  team_b_id: string;
  season: number;
  analysis: string;
}

export interface CoachRequest {
  question: string;
  context?: string;
  provider?: string;
  api_key?: string;
  model_name?: string;
}

export interface CoachResponse {
  question: string;
  response: string;
  model: string;
}

export interface ScoutRequest {
  opponent_name: string;
  stats_summary: string;
}

export interface ScoutResponse {
  opponent: string;
  report: string;
  model: string;
}

export interface ModelInfoResponse {
  model: string;
  error?: string;
}
