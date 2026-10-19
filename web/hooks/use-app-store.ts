import { create } from "zustand";
import type { Player, Team } from "@/types/api";

export const DEFAULT_FOCUS_CLUB = "Högsbo";

/**
 * Resolve the active focus team (defaulting to Högsbo Lions / Högsbo Basket)
 * for any season and league (Men or Women), even when Genius Sports team IDs
 * change across seasons.
 */
export function resolveFocusTeam(
  teams: Team[],
  focusClub: string = DEFAULT_FOCUS_CLUB,
  myTeamId?: string | null
): Team | undefined {
  if (!teams || teams.length === 0) return undefined;

  if (myTeamId) {
    const exact = teams.find((t) => t.id === myTeamId);
    if (exact) return exact;
  }

  const normalizedFocus = (focusClub || DEFAULT_FOCUS_CLUB).toLowerCase();
  const clubMatch = teams.find((t) =>
    t.name.toLowerCase().includes(normalizedFocus)
  );
  return clubMatch || teams[0];
}

interface AppState {
  // Data state
  players: Player[];
  teams: Team[];
  currentSeason: number;
  currentLeague: "Men" | "Women";
  focusClub: string;
  myTeamId: string | null;

  // UI state
  isLoading: boolean;
  error: string | null;

  // Actions
  setPlayers: (players: Player[]) => void;
  setTeams: (teams: Team[]) => void;
  setCurrentSeason: (season: number) => void;
  setCurrentLeague: (league: "Men" | "Women") => void;
  setFocusClub: (club: string) => void;
  setMyTeamId: (teamId: string | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Initial state: anchored to 2026-2027 season & Högsbo as primary focus club
  players: [],
  teams: [],
  currentSeason: 2026,
  currentLeague: "Men",
  focusClub: DEFAULT_FOCUS_CLUB,
  myTeamId: null,
  isLoading: false,
  error: null,

  // Actions
  setPlayers: (players) => set({ players }),
  setTeams: (teams) => set({ teams }),
  setCurrentSeason: (season) => set({ currentSeason: season }),
  setCurrentLeague: (league) => set({ currentLeague: league }),
  setFocusClub: (club) => set({ focusClub: club, myTeamId: null }),
  setMyTeamId: (teamId) => set({ myTeamId: teamId }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
}));
