import { create } from "zustand";
import type { Player, Team } from "@/types/api";

interface AppState {
  // Data state
  players: Player[];
  teams: Team[];
  currentSeason: number;
  currentLeague: "Men" | "Women";
  myTeamId: string | null;

  // UI state
  isLoading: boolean;
  error: string | null;

  // Actions
  setPlayers: (players: Player[]) => void;
  setTeams: (teams: Team[]) => void;
  setCurrentSeason: (season: number) => void;
  setCurrentLeague: (league: "Men" | "Women") => void;
  setMyTeamId: (teamId: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Initial state
  players: [],
  teams: [],
  currentSeason: new Date().getFullYear(),
  currentLeague: "Men",
  myTeamId: null,
  isLoading: false,
  error: null,

  // Actions
  setPlayers: (players) => set({ players }),
  setTeams: (teams) => set({ teams }),
  setCurrentSeason: (season) => set({ currentSeason: season }),
  setCurrentLeague: (league) => set({ currentLeague: league }),
  setMyTeamId: (teamId) => set({ myTeamId: teamId }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
}));
