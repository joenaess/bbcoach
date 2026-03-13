"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useTeams, useSeasons } from "@/hooks/use-api";
import { useAppStore } from "@/hooks/use-app-store";
import api from "@/lib/api-client";
import { Basketball, TrendingUp, Users, BarChart3 } from "lucide-react";

export default function PredictorPage() {
  const { currentSeason, currentLeague, myTeamId } = useAppStore();
  const [selectedTeamA, setSelectedTeamA] = useState("");
  const [selectedTeamB, setSelectedTeamB] = useState("");
  const [analysis, setAnalysis] = useState<string>("");
  const [multiSeasonAnalysis, setMultiSeasonAnalysis] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const { data: teamsData } = useTeams(currentSeason, currentLeague);
  const teams = teamsData?.teams || [];

  const disabled = !selectedTeamA || !selectedTeamB || selectedTeamA === selectedTeamB;

  const handlePredict = async () => {
    if (disabled || !currentSeason) return;

    setIsLoading(true);
    setAnalysis("");
    setMultiSeasonAnalysis("");

    try {
      // Single season analysis
      const matchupResponse = await api.predictMatchup({
        team_a_id: selectedTeamA,
        team_b_id: selectedTeamB,
        season: currentSeason,
      });
      setAnalysis(matchupResponse.analysis);

      // Multi-season analysis
      try {
        const multiResponse = await api.predictMatchupMultiSeason(selectedTeamA, selectedTeamB);
        setMultiSeasonAnalysis(multiResponse);
      } catch (e) {
        console.warn("Multi-season analysis not available:", e);
      }
    } catch (error) {
      console.error("Error predicting matchup:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const teamA = teams.find((t) => t.id === selectedTeamA);
  const teamB = teams.find((t) => t.id === selectedTeamB);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center space-x-3">
            <TrendingUp className="w-8 h-8 text-primary" />
            <h1 className="text-3xl font-bold">Game Predictor</h1>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Team Selection */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Select Teams</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-6">
              {/* Team A */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Team A</label>
                <select
                  className="w-full px-4 py-2 rounded-md border border-input bg-background"
                  value={selectedTeamA}
                  onChange={(e) => setSelectedTeamA(e.target.value)}
                >
                  <option value="">Select team...</option>
                  {teams.map((team) => (
                    <option key={team.id} value={team.id}>
                      {team.name}
                    </option>
                  ))}
                </select>
                {teamA && (
                  <Badge variant="secondary">{teamA.name}</Badge>
                )}
              </div>

              {/* Team B */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Team B</label>
                <select
                  className="w-full px-4 py-2 rounded-md border border-input bg-background"
                  value={selectedTeamB}
                  onChange={(e) => setSelectedTeamB(e.target.value)}
                >
                  <option value="">Select team...</option>
                  {teams.map((team) => (
                    <option key={team.id} value={team.id}>
                      {team.name}
                    </option>
                  ))}
                </select>
                {teamB && (
                  <Badge variant="secondary">{teamB.name}</Badge>
                )}
              </div>
            </div>

            <div className="mt-6 flex justify-center">
              <Button
                size="lg"
                onClick={handlePredict}
                disabled={disabled || isLoading}
                className="px-8"
              >
                {isLoading ? (
                  <>
                    <TrendingUp className="w-5 h-5 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <BarChart3 className="w-5 h-5 mr-2" />
                    Analyze Matchup
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Results */}
        {analysis && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Basketball className="w-6 h-6" />
                Matchup Analysis
                {teamA && teamB && (
                  <span className="text-xl font-normal text-muted-foreground">
                    {teamA.name} vs {teamB.name}
                  </span>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="single" className="w-full">
                <TabsList>
                  <TabsTrigger value="single">Single Season</TabsTrigger>
                  {multiSeasonAnalysis && (
                    <TabsTrigger value="multi">Multi-Season</TabsTrigger>
                  )}
                </TabsList>

                <TabsContent value="single" className="mt-4">
                  <div className="prose prose-invert max-w-none">
                    {analysis.split("\n").map((line, i) => {
                      if (line.startsWith("#")) {
                        const headingLevel = (line.match(/^#+/) || [])[0].length;
                        const text = line.replace(/^#+\s*/, "");
                        const Tag = `h${Math.min(headingLevel, 6)}` as keyof JSX.IntrinsicElements;
                        return (
                          <Tag key={i} className={`text-lg font-semibold mt-${headingLevel * 2} mb-2`}>
                            {text}
                          </Tag>
                        );
                      }
                      if (line.startsWith("-")) {
                        return (
                          <li key={i} className="ml-4 list-disc">
                            {line.substring(1).trim()}
                          </li>
                        );
                      }
                      if (line.trim() === "") {
                        return <div key={i} className="h-2" />;
                      }
                      return <p key={i}>{line}</p>;
                    })}
                  </div>
                </TabsContent>

                {multiSeasonAnalysis && (
                  <TabsContent value="multi" className="mt-4">
                    <div className="prose prose-invert max-w-none">
                      {multiSeasonAnalysis.split("\n").map((line, i) => {
                        if (line.startsWith("#")) {
                          const text = line.replace(/^#+\s*/, "");
                          return (
                            <h3 key={i} className="text-lg font-semibold mt-4 mb-2">
                              {text}
                            </h3>
                          );
                        }
                        if (line.startsWith("-")) {
                          return (
                            <li key={i} className="ml-4 list-disc">
                              {line.substring(1).trim()}
                            </li>
                          );
                        }
                        if (line.trim() === "") return <div className="h-2" />;
                        return <p key={i}>{line}</p>;
                      })}
                    </div>
                  </TabsContent>
                )}
              </Tabs>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  );
}
