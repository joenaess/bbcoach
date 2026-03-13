import useSWR from "swr";
import api from "@/lib/api-client";

export function useDataStatus() {
  return useSWR("/data/status", () => api.dataStatus(), {
    refreshInterval: 60000, // Refresh every minute
  });
}

export function useSeasons(league: string = "Men") {
  return useSWR(`/seasons/${league}`, () => api.getSeasons(league));
}

export function useTeams(season: number | undefined, league: string = "Men") {
  return useSWR(
    season ? `/teams/${season}/${league}` : null,
    () => (season ? api.getTeams(season, league) : Promise.resolve({ teams: [] }))
  );
}

export function useTopPlayers(
  season: number | undefined,
  league: string = "Men",
  metric: string = "PPG",
  limit: number = 10
) {
  return useSWR(
    season ? `/top-players/${season}/${league}/${metric}` : null,
    () =>
      season ? api.getTopPlayers(season, league, metric, limit) : Promise.resolve({ players: [] })
  );
}

export function useModelInfo() {
  return useSWR("/model-info", () => api.getModelInfo(), {
    refreshInterval: 300000, // Refresh every 5 minutes
  });
}
