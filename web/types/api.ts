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
  "FG%"?: number;
  "3P%"?: number;
  "FT%"?: number;
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
  last_fetched?: string;
  seasons_in_data: number[];
}

export interface ScrapingProgress {
  status: "idle" | "fetching" | "error";
  current: number;
  total: number;
  team: string;
  league: string;
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
  team_id?: string;
  season?: number;
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

export interface TimestralQuantiles {
  median: number;
  q10: number;
  q25?: number;
  q75?: number;
  q90: number;
}

export interface TimestralHistoryGame {
  date: string;
  season: number;
  opponent: string;
  home_away: string;
  team_score: number;
  opponent_score: number;
  point_diff: number;
  won: boolean;
}

export interface TimestralForecastGame {
  step: number;
  date: string;
  season: number;
  opponent: string;
  home_away: string;
  team_score: TimestralQuantiles;
  opponent_score: TimestralQuantiles;
  point_diff: TimestralQuantiles;
  win_probability: number;
  coaching_tag?: string;
  target_score_to_win?: number;
}

export interface TimestralTrajectoryResponse {
  model: string;
  team_name: string;
  league: string;
  historical_games_used: number;
  seasons_covered: number[];
  recent_avg_ppg: number;
  recent_avg_opp_ppg: number;
  expected_wins_next_n: number;
  horizon: number;
  schedule_coaching_insights?: string[];
  history: TimestralHistoryGame[];
  forecast: TimestralForecastGame[];
}

export interface TimestralMatchupRequest {
  team_a_id: string;
  team_b_id: string;
  league: string;
  team_a_home: boolean;
  pace_adjustment?: number;
  team_a_off_boost?: number;
  team_a_def_boost?: number;
}

export interface TimestralCoachBrief {
  target_score_to_win_50: number;
  target_score_to_win_75: number;
  defensive_hold_target: number;
  volatility_rating: string;
  spread_interval_width_80: number;
  pace_and_variance_advice: string;
  key_tactical_priorities: string[];
  suggested_coach_prompts: string[];
}

export interface TimestralMatchupResponse {
  model: string;
  league: string;
  team_a: string;
  team_b: string;
  venue: string;
  win_prob_a: number;
  win_prob_b: number;
  team_a_score: TimestralQuantiles;
  team_b_score: TimestralQuantiles;
  spread: TimestralQuantiles;
  total_points: TimestralQuantiles;
  coach_brief?: TimestralCoachBrief;
  head_to_head_history: {
    date: string;
    season: number;
    home_away: string;
    team_a_score: number;
    team_b_score: number;
  }[];
}

export interface TimestralBacktestResponse {
  model: string;
  league: string;
  teams_evaluated: number;
  games_evaluated: number;
  metrics: {
    timestral_209m: {
      win_accuracy_pct: number;
      spread_mae: number;
      score_mae: number;
      brier_score: number;
      interval_80_coverage_pct: number;
    };
    rolling_5_baseline: {
      win_accuracy_pct: number;
      spread_mae: number;
      score_mae: number;
    };
    season_avg_baseline: {
      win_accuracy_pct: number;
      spread_mae: number;
      score_mae: number;
    };
  };
  sample_predictions: {
    team: string;
    opponent: string;
    date: string;
    season: number;
    actual_score: string;
    actual_diff: number;
    predicted_diff: number;
    predicted_q10: number;
    predicted_q90: number;
    win_prob: number;
    correct: boolean;
  }[];
}

