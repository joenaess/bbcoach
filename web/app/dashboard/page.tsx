"use client";

import { useEffect, useState } from "react";
import { useDataStatus } from "@/hooks/use-api";
import api from "@/lib/api-client";
import type { ScrapingProgress } from "@/types/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dribbble, Users, TrendingUp, Activity, Download, Clock } from "lucide-react";
import Link from "next/link";
import { formatNumber } from "@/lib/utils";

export default function DashboardPage() {
  const { data: dataStatus, error, isLoading, mutate } = useDataStatus();
  const [isFetching, setIsFetching] = useState(false);
  const [progress, setProgress] = useState<ScrapingProgress | null>(null);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isFetching) {
      interval = setInterval(async () => {
        try {
          const res = await api.getFetchProgress();
          setProgress(res);
        } catch (e) {
          // silent error
        }
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isFetching]);

  const handleFetchData = async () => {
    setIsFetching(true);
    setProgress(null);
    try {
      await api.fetchLatestData();
      await mutate();
    } catch (err) {
      console.error("Failed to fetch latest data", err);
    } finally {
      setIsFetching(false);
      setProgress(null);
    }
  };

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
              <Dribbble className="w-8 h-8 text-primary" />
              <h1 className="text-2xl font-bold">BBCoach Dashboard</h1>
            </div>
            <div className="flex items-center space-x-4">
              {dataStatus && (
                <>
                  <div className="flex items-center text-sm text-muted-foreground mr-4">
                    <Clock className="w-4 h-4 mr-2" />
                    Last Fetched: {dataStatus.last_fetched ? new Date(dataStatus.last_fetched).toLocaleString() : "Never"}
                  </div>
                  <Badge variant={dataStatus.has_players ? "success" : "warning"}>
                    {dataStatus.has_players ? "Data Active" : "No Data"}
                  </Badge>
                  <Button 
                    size="sm" 
                    onClick={handleFetchData} 
                    disabled={isFetching}
                    className="ml-2"
                  >
                    {isFetching ? (
                      <span className="flex items-center">
                        <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                        Fetching...
                      </span>
                    ) : (
                      <span className="flex items-center">
                        <Download className="w-4 h-4 mr-2" />
                        Fetch Latest Data
                      </span>
                    )}
                  </Button>
                </>
              )}
            </div>
          </div>

          {/* Progress Bar Container */}
          {isFetching && progress && progress.total > 0 && (
            <div className="mt-6 flex flex-col space-y-2">
              <div className="flex justify-between text-sm">
                <span className="font-semibold text-primary">
                  Processing {progress.league}: {progress.team}
                </span>
                <span className="text-muted-foreground">
                  Team {progress.current} of {progress.total}
                </span>
              </div>
              <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
                <div 
                  className="h-full bg-primary transition-all duration-300 ease-in-out" 
                  style={{ width: `${Math.round((progress.current / progress.total) * 100)}%` }}
                />
              </div>
            </div>
          )}
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
              icon={<Dribbble className="w-5 h-5" />}
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
              <Link href="/stats" className="w-full">
                <Button variant="outline" className="h-20 w-full flex-col">
                  <Users className="w-6 h-6 mb-2" />
                  <span>View League Stats</span>
                </Button>
              </Link>
              <Link href="/predictor" className="w-full">
                <Button variant="outline" className="h-20 w-full flex-col">
                  <Activity className="w-6 h-6 mb-2" />
                  <span>Match Predictor</span>
                </Button>
              </Link>
              <Link href="/coach" className="w-full">
                <Button variant="outline" className="h-20 w-full flex-col">
                  <TrendingUp className="w-6 h-6 mb-2" />
                  <span>AI Coach</span>
                </Button>
              </Link>
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
