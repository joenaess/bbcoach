"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useTopPlayers, useSeasons } from "@/hooks/use-api";
import { formatNumber, formatPercentage } from "@/lib/utils";
import { useAppStore } from "@/hooks/use-app-store";

const METRICS = ["PPG", "RPG", "APG", "3P%", "FG%", "EFF"];

export default function StatsPage() {
  const { currentSeason, currentLeague, setCurrentSeason, setCurrentLeague } = useAppStore();
  const { data: seasonsData } = useSeasons(currentLeague);
  const [metric, setMetric] = useState("PPG");

  const topPlayers = useTopPlayers(currentSeason, currentLeague, metric, 10);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold">League Statistics</h1>
        </div>
      </header>

      {/* Controls */}
      <div className="container mx-auto px-4 py-6">
        <div className="flex flex-wrap gap-4 items-center">
          {/* League Toggle */}
          <div className="flex gap-2">
            <Button
              variant={currentLeague === "Men" ? "default" : "outline"}
              onClick={() => setCurrentLeague("Men")}
            >
              Men
            </Button>
            <Button
              variant={currentLeague === "Women" ? "default" : "outline"}
              onClick={() => setCurrentLeague("Women")}
            >
              Women
            </Button>
          </div>

          {/* Season Selector */}
          {seasonsData?.seasons && (
            <select
              className="px-4 py-2 rounded-md border border-input bg-background"
              value={currentSeason}
              onChange={(e) => setCurrentSeason(Number(e.target.value))}
            >
              {seasonsData.seasons.map((season) => (
                <option key={season} value={season}>
                  {season}
                </option>
              ))}
            </select>
          )}

          {/* Metric Selector */}
          <select
            className="px-4 py-2 rounded-md border border-input bg-background"
            value={metric}
            onChange={(e) => setMetric(e.target.value)}
          >
            {METRICS.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Leaderboard */}
      <div className="container mx-auto px-4 pb-8">
        <Card>
          <CardHeader>
            <CardTitle>
              Top Players by {metric} - {currentSeason} ({currentLeague})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {topPlayers.isLoading ? (
              <div className="text-center py-8 text-muted-foreground">Loading...</div>
            ) : topPlayers.error ? (
              <div className="text-center py-8 text-destructive">
                Error loading data
              </div>
            ) : !topPlayers.data?.players || topPlayers.data.players.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">No players found</div>
            ) : (
              <div className="space-y-2">
                {topPlayers.data.players.map((player, index) => (
                  <PlayerRow key={player.id} player={player} rank={index + 1} metric={metric} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function PlayerRow({
  player,
  rank,
  metric,
}: {
  player: any;
  rank: number;
  metric: string;
}) {
  const isPercentage = metric.includes("%");
  const value = formatNumber(player[metric], isPercentage ? 1 : 1);

  return (
    <div className="flex items-center justify-between p-4 rounded-lg hover:bg-accent transition-colors">
      <div className="flex items-center space-x-4 flex-1">
        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center font-bold text-primary">
          {rank}
        </div>
        <div className="flex-1">
          <div className="font-semibold">{player.name}</div>
          <div className="text-sm text-muted-foreground">
            GP: {player.GP} • MIN: {formatNumber(player.MIN, 1)}
          </div>
        </div>
      </div>
      <div className="text-right">
        <div className="text-2xl font-bold">{isPercentage ? `${value}%` : value}</div>
        <Badge variant="secondary">{metric}</Badge>
      </div>
    </div>
  );
}
