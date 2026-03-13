"use client";

import { useEffect, useState } from "react";
import { useDataStatus } from "@/hooks/use-api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Basketball, Users, TrendingUp, Activity } from "lucide-react";
import { formatNumber } from "@/lib/utils";

export default function DashboardPage() {
  const { data: dataStatus, error, isLoading } = useDataStatus();

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <h2 className="text-2xl font-bold text-destructive">Error Loading Data</h2>
          <p className="text-muted-foreground">{error.message}</p>
          <Button onClick={() => window.location.reload()}>Retry</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Basketball className="w-8 h-8 text-primary" />
              <h1 className="text-2xl font-bold">BBCoach Dashboard</h1>
            </div>
            <div className="flex items-center space-x-4">
              {dataStatus && (
                <Badge variant={dataStatus.has_players ? "success" : "warning"}>
                  {dataStatus.has_players ? "Data Active" : "No Data"}
                </Badge>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Stats Cards */}
        {dataStatus && (
          <div className="grid md:grid-cols-4 gap-6 mb-8">
            <StatsCard
              title="Players"
              value={dataStatus.players_count}
              icon={<Users className="w-5 h-5" />}
              loading={isLoading}
            />
            <StatsCard
              title="Teams"
              value={dataStatus.teams_count}
              icon={<Activity className="w-5 h-5" />}
              loading={isLoading}
            />
            <StatsCard
              title="Games"
              value={dataStatus.schedule_count}
              icon={<TrendingUp className="w-5 h-5" />}
              loading={isLoading}
            />
            <StatsCard
              title="Seasons"
              value={dataStatus.seasons_in_data.length}
              icon={<Basketball className="w-5 h-5" />}
              loading={isLoading}
            />
          </div>
        )}

        {/* Quick Actions */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-3 gap-4">
              <Button variant="outline" className="h-20 flex-col" asChild>
                <a href="/stats">
                  <Users className="w-6 h-6 mb-2" />
                  <span>View League Stats</span>
                </a>
              </Button>
              <Button variant="outline" className="h-20 flex-col" asChild>
                <a href="/predictor">
                  <TrendingUp className="w-6 h-6 mb-2" />
                  <span>Game Predictor</span>
                </a>
              </Button>
              <Button variant="outline" className="h-20 flex-col" asChild>
                <a href="/coach">
                  <Basketball className="w-6 h-6 mb-2" />
                  <span>Ask AI Coach</span>
                </a>
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Available Seasons */}
        {dataStatus && dataStatus.seasons_in_data.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Available Seasons</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {dataStatus.seasons_in_data.map((season) => (
                  <Badge key={season} variant="secondary">
                    {season}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  );
}

function StatsCard({
  title,
  value,
  icon,
  loading,
}: {
  title: string;
  value: number;
  icon: React.ReactNode;
  loading?: boolean;
}) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <p className="text-3xl font-bold mt-1">
              {loading ? "-" : formatNumber(value)}
            </p>
          </div>
          <div className="p-3 rounded-lg bg-primary/10 text-primary">
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
