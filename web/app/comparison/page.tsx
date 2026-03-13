"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useTeams, useSeasons } from "@/hooks/use-api";
import { useAppStore } from "@/hooks/use-app-store";
import api from "@/lib/api-client";
import { TrendingUp, Users, Activity } from "lucide-react";

export default function ComparisonPage() {
  const { currentSeason, currentLeague } = useAppStore();
  const [selectedPlayers, setSelectedPlayers] = useState<string[]>([]);
  const [comparisonData, setComparisonData] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [availablePlayers, setAvailablePlayers] = useState<any[]>([]);

  const { data: teamsData } = useTeams(currentSeason, currentLeague);

  useEffect(() => {
    loadAvailablePlayers();
  }, [currentSeason, currentLeague]);

  const loadAvailablePlayers = async () => {
    if (!currentSeason) return;

    try {
      const data = await api.getTopPlayers(currentSeason, currentLeague, "PPG", 100);
      setAvailablePlayers(data.players);
    } catch (error) {
      console.error("Error loading players:", error);
    }
  };

  const handleAddPlayer = (playerId: string) => {
    if (selectedPlayers.includes(playerId)) {
      setSelectedPlayers(selectedPlayers.filter((id) => id !== playerId));
    } else if (selectedPlayers.length < 2) {
      setSelectedPlayers([...selectedPlayers, playerId]);
    }
  };

  const handleCompare = async () => {
    if (selectedPlayers.length !== 2 || !currentSeason) return;

    setIsLoading(true);
    try {
      const selectedPlayerObjects = availablePlayers
        .filter((p) => selectedPlayers.includes(p.id))
        .map((p) => p.name);

      const data = await api.comparePlayers(selectedPlayerObjects, currentSeason, currentLeague);
      setComparisonData(data);
    } catch (error) {
      console.error("Error comparing players:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const player1 = comparisonData[0];
  const player2 = comparisonData[1];

  const metrics = ["PPG", "RPG", "APG", "3P%", "FG%", "MIN"];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center space-x-3">
            <TrendingUp className="w-8 h-8 text-primary" />
            <h1 className="text-3xl font-bold">Player Comparison</h1>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Player Selection */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Select Players to Compare</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="mb-4">
              <div className="flex items-center gap-2 mb-2">
                <Badge variant="secondary">
                  {selectedPlayers.length}/2 selected
                </Badge>
                {selectedPlayers.length === 2 && (
                  <span className="text-sm text-muted-foreground">
                    Ready to compare!
                  </span>
                )}
              </div>
              <div className="max-h-64 overflow-y-auto space-y-2">
                {availablePlayers.slice(0, 50).map((player) => (
                  <div
                    key={player.id}
                    className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedPlayers.includes(player.id)
                        ? "bg-primary/20 border-primary"
                        : "border-border hover:bg-accent"
                    }`}
                    onClick={() => handleAddPlayer(player.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-semibold">{player.name}</div>
                        <div className="text-sm text-muted-foreground">
                          GP: {player.GP} • MIN: {player.MIN}
                        </div>
                      </div>
                      <div className="text-xl font-bold text-primary">
                        {player.PPG}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <Button
              onClick={handleCompare}
              disabled={selectedPlayers.length !== 2 || isLoading}
              className="w-full"
            >
              {isLoading ? (
                <>
                  <Activity className="w-4 h-4 mr-2 animate-spin" />
                  Comparing...
                </>
              ) : (
                "Compare Players"
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Comparison Results */}
        {comparisonData.length === 2 && (
          <Card>
            <CardHeader>
              <CardTitle>
                {player1?.name} vs {player2?.name}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {/* Player Names */}
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div />
                <div className="text-center">
                  <div className="text-2xl font-bold text-primary">{player1?.name}</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-primary">{player2?.name}</div>
                </div>
              </div>

              {/* Metrics Comparison */}
              <div className="space-y-4">
                {metrics.map((metric) => {
                  const value1 = player1?.[metric] ?? 0;
                  const value2 = player2?.[metric] ?? 0;
                  const higherValue = value1 > value2 ? value1 : value2;

                  return (
                    <div key={metric}>
                      <div className="text-sm font-medium mb-2 text-center">{metric}</div>
                      <div className="grid grid-cols-3 gap-4 items-center">
                        <div className="text-right">
                          <span
                            className={`text-2xl font-bold ${
                              value1 === higherValue && value1 !== 0 ? "text-primary" : ""
                            }`}
                          >
                            {metric.includes("%") ? `${value1.toFixed(1)}%` : value1.toFixed(1)}
                          </span>
                        </div>
                        <div className="flex justify-center">
                          <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                            <div
                              className="h-full bg-primary"
                              style={{
                                width: `${
                                  value1 > value2
                                    ? 75
                                    : value2 > 0
                                    ? (value1 / value2) * 50 + 25
                                    : 25
                                }%`,
                                marginLeft: `${value1 < value2 ? 0 : 25}%`,
                              }}
                            />
                          </div>
                        </div>
                        <div className="text-left">
                          <span
                            className={`text-2xl font-bold ${
                              value2 === higherValue && value2 !== 0 ? "text-primary" : ""
                            }`}
                          >
                            {metric.includes("%") ? `${value2.toFixed(1)}%` : value2.toFixed(1)}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Key Stats Summary */}
              <div className="mt-8 grid md:grid-cols-2 gap-4">
                <div className="p-4 rounded-lg bg-card border border-border">
                  <h3 className="font-semibold mb-2">{player1?.name}</h3>
                  <div className="space-y-1 text-sm">
                    <div>Games Played: {player1?.GP}</div>
                    <div>Minutes: {player1?.MIN}</div>
                    <div>Efficiency: {player1?.EFF || "N/A"}</div>
                  </div>
                </div>
                <div className="p-4 rounded-lg bg-card border border-border">
                  <h3 className="font-semibold mb-2">{player2?.name}</h3>
                  <div className="space-y-1 text-sm">
                    <div>Games Played: {player2?.GP}</div>
                    <div>Minutes: {player2?.MIN}</div>
                    <div>Efficiency: {player2?.EFF || "N/A"}</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  );
}
