"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useTeams, useSeasons } from "@/hooks/use-api";
import { useAppStore } from "@/hooks/use-app-store";
import api from "@/lib/api-client";
import { Calendar, Trophy, Home, Plane, FileText } from "lucide-react";

export default function SchedulePage() {
  const { currentSeason, currentLeague, myTeamId } = useAppStore();
  const [schedule, setSchedule] = useState<any>([]);
  const [selectedTeamId, setSelectedTeamId] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const { data: teamsData } = useTeams(currentSeason, currentLeague);
  const teams = teamsData?.teams || [];

  useEffect(() => {
    if (myTeamId && !selectedTeamId) {
      setSelectedTeamId(myTeamId);
    }
  }, [myTeamId]);

  useEffect(() => {
    if (selectedTeamId && currentSeason) {
      loadSchedule(selectedTeamId);
    }
  }, [selectedTeamId, currentSeason]);

  const loadSchedule = async (teamId: string) => {
    setIsLoading(true);
    try {
      const games = await api.getTeamSchedule(teamId, currentSeason);
      if (games && games.length > 0) {
        setSchedule(games);
        return;
      }
      const data = await api.getTeamStats(teamId, currentSeason);
      if (data && data.rotation) {
        setSchedule(data.rotation);
      } else {
        setSchedule([]);
      }
    } catch (error) {
      console.error("Error loading schedule:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const selectedTeam = teams.find((t) => t.id === selectedTeamId);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Calendar className="w-8 h-8 text-primary" />
              <h1 className="text-3xl font-bold">Schedule</h1>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Team Selector */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Select Team</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4 items-center">
              <select
                className="px-4 py-2 rounded-md border border-input bg-background flex-1"
                value={selectedTeamId}
                onChange={(e) => setSelectedTeamId(e.target.value)}
              >
                <option value="">Select a team...</option>
                {teams.map((team) => (
                  <option key={team.id} value={team.id}>
                    {team.name}
                  </option>
                ))}
              </select>
              {selectedTeam && (
                <Badge variant="secondary" className="text-sm py-2">
                  {selectedTeam.name} - {currentSeason}
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Schedule Display */}
        <Card>
          <CardHeader>
            <CardTitle>
              {selectedTeam ? `${selectedTeam.name} Schedule` : "Team Schedule"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="text-center py-8 text-muted-foreground">Loading schedule...</div>
            ) : !selectedTeam ? (
              <div className="text-center py-8 text-muted-foreground">
                Select a team to view their schedule
              </div>
            ) : schedule.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No schedule data available for {selectedTeam.name}
              </div>
            ) : (
              <div className="space-y-3">
                {schedule.map((game: any, index: number) => (
                  <ScheduleItem key={index} game={game} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}

function ScheduleItem({ game }: { game: any }) {
  if (game.opponent) {
    return (
      <div className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-accent transition-colors">
        <div className="flex items-center space-x-4 flex-1">
          <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-primary">
            {game.home_away === "Home" ? (
              <Home className="w-6 h-6" />
            ) : (
              <Plane className="w-6 h-6" />
            )}
          </div>
          <div className="flex-1">
            <div className="font-semibold">
              {game.home_away === "Home" ? "vs" : "@"} {game.opponent}
            </div>
            <div className="text-sm text-muted-foreground">
              {game.date} • {game.home_away}
            </div>
          </div>
        </div>
        <Badge variant={game.result === "Scheduled" ? "secondary" : "default"}>
          {game.result || "Scheduled"}
        </Badge>
      </div>
    );
  }

  const ppg = game.PPG ?? game.ppg ?? 0;
  const rpg = game.RPG ?? game.rpg ?? 0;
  const apg = game.APG ?? game.apg ?? 0;
  const gp = game.GP ?? game.gp ?? 0;
  const min = game.MIN ?? game.min ?? 0;

  return (
    <div className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-accent transition-colors">
      <div className="flex items-center space-x-4 flex-1">
        {/* Team Icon */}
        <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-primary">
          <Trophy className="w-6 h-6" />
        </div>

        {/* Game Info */}
        <div className="flex-1">
          <div className="font-semibold">{game.name || "Player"}</div>
          <div className="text-sm text-muted-foreground">
            Games: {gp} • {min} minutes played
          </div>
        </div>

        {/* Metrics */}
        <div className="flex gap-4 text-right mr-4">
          <div>
            <div className="text-lg font-bold">{ppg}</div>
            <div className="text-xs text-muted-foreground">PPG</div>
          </div>
          <div>
            <div className="text-lg font-bold">{rpg}</div>
            <div className="text-xs text-muted-foreground">RPG</div>
          </div>
          <div>
            <div className="text-lg font-bold">{apg}</div>
            <div className="text-xs text-muted-foreground">APG</div>
          </div>
        </div>
      </div>

      {/* Result Badge */}
      <Badge variant={ppg > 15 ? "default" : "secondary"}>
        {ppg > 15 ? "Key Player" : "Rotation"}
      </Badge>
    </div>
  );
}
