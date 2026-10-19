"use client";

import { useState, useEffect, useMemo, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  useTeams,
  useSeasons,
  useTimestralForecast,
  useTimestralEvaluation,
} from "@/hooks/use-api";
import { useAppStore, resolveFocusTeam } from "@/hooks/use-app-store";
import api from "@/lib/api-client";
import type { TimestralMatchupResponse } from "@/types/api";
import Link from "next/link";
import {
  Dribbble,
  TrendingUp,
  MessageSquare,
  Sparkles,
  Calendar,
  Award,
  Activity,
  CheckCircle2,
  XCircle,
  Home,
  Plane,
  Shield,
  Target,
  Sliders,
  Zap,
  ArrowRight,
  RotateCcw,
  Lock,
  Unlock,
} from "lucide-react";
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

export default function PredictorPage() {
  const {
    currentSeason,
    setCurrentSeason,
    currentLeague,
    setCurrentLeague,
    focusClub,
    myTeamId,
    setMyTeamId,
  } = useAppStore();

  const [activeTab, setActiveTab] = useState("matchup");
  const [selectedTeamA, setSelectedTeamA] = useState("");
  const [selectedTeamB, setSelectedTeamB] = useState("");
  const [teamAHome, setTeamAHome] = useState(true);
  const [unlockFocusTeam, setUnlockFocusTeam] = useState(false);

  // Coach What-If tactical adjustments
  const [offBoost, setOffBoost] = useState(0);
  const [defBoost, setDefBoost] = useState(0);
  const [paceAdj, setPaceAdj] = useState(0);

  const [analysis, setAnalysis] = useState<string>("");
  const [multiSeasonAnalysis, setMultiSeasonAnalysis] = useState("");
  const [timestralMatchup, setTimestralMatchup] =
    useState<TimestralMatchupResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Inline AI Coach tactical game plan state
  const [coachGamePlan, setCoachGamePlan] = useState<string>("");
  const [coachGamePlanModel, setCoachGamePlanModel] = useState<string>("");
  const [isCoachLoading, setIsCoachLoading] = useState(false);
  const [activeCoachPrompt, setActiveCoachPrompt] = useState<string>("");

  // Trajectory state
  const [trajectoryTeamId, setTrajectoryTeamId] = useState("");
  const [horizon, setHorizon] = useState(6);
  const autoRanKeyRef = useRef<string>("");

  const { data: seasonsData } = useSeasons(currentLeague);
  const seasons = seasonsData?.seasons?.length
    ? seasonsData.seasons
    : [2026, 2025, 2024];

  const { data: teamsData } = useTeams(currentSeason, currentLeague);
  const teams = useMemo(() => teamsData?.teams || [], [teamsData]);

  // Resolve Högsbo (or user's focus club) for the active season & league
  const focusTeam = useMemo(
    () => resolveFocusTeam(teams, focusClub, myTeamId),
    [teams, focusClub, myTeamId]
  );

  // Keep Högsbo anchored as Team A & Trajectory Team whenever season/league changes
  useEffect(() => {
    if (!focusTeam) return;
    setSelectedTeamA(focusTeam.id);
    setTrajectoryTeamId(focusTeam.id);
  }, [focusTeam]);

  const { data: trajectoryData, isLoading: isTrajectoryLoading } =
    useTimestralForecast(
      trajectoryTeamId || focusTeam?.id,
      currentLeague,
      horizon
    );

  const { data: evalData, isLoading: isEvalLoading } = useTimestralEvaluation(
    currentLeague,
    6
  );

  const runMatchupForecast = async (
    teamAId: string,
    teamBId: string,
    isHome: boolean,
    customOffBoost = offBoost,
    customDefBoost = defBoost,
    customPace = paceAdj
  ) => {
    if (!teamAId || !teamBId || teamAId === teamBId || !currentSeason) return;

    setIsLoading(true);
    setCoachGamePlan("");

    try {
      const [tsResult, matchupResult, multiResult] = await Promise.allSettled([
        api.predictTimestralMatchup({
          team_a_id: teamAId,
          team_b_id: teamBId,
          league: currentLeague,
          team_a_home: isHome,
          pace_adjustment: customPace,
          team_a_off_boost: customOffBoost,
          team_a_def_boost: customDefBoost,
        }),
        api.predictMatchup({
          team_a_id: teamAId,
          team_b_id: teamBId,
          season: currentSeason,
        }),
        api.predictMatchupMultiSeason(teamAId, teamBId),
      ]);

      if (tsResult.status === "fulfilled") {
        setTimestralMatchup(tsResult.value);
      }
      if (matchupResult.status === "fulfilled") {
        setAnalysis(matchupResult.value.analysis);
      }
      if (multiResult.status === "fulfilled") {
        setMultiSeasonAnalysis(multiResult.value);
      }
    } catch (error) {
      console.error("Error predicting matchup:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // Auto-select Högsbo's next scheduled opponent and run initial forecast automatically
  useEffect(() => {
    if (!focusTeam || teams.length < 2) return;

    const opponents = teams.filter((t) => t.id !== focusTeam.id);
    if (opponents.length === 0) return;

    const nextGame = trajectoryData?.forecast?.[0];
    let targetOpp = opponents[0];
    let nextIsHome = true;

    if (nextGame) {
      const matchedOpp = opponents.find(
        (t) =>
          t.name.toLowerCase().includes(nextGame.opponent.toLowerCase()) ||
          nextGame.opponent.toLowerCase().includes(t.name.toLowerCase())
      );
      if (matchedOpp) {
        targetOpp = matchedOpp;
        nextIsHome = nextGame.home_away === "Home";
      }
    }

    const runKey = `${currentLeague}-${currentSeason}-${focusTeam.id}-${
      nextGame ? nextGame.opponent : "init"
    }`;
    if (autoRanKeyRef.current !== runKey) {
      autoRanKeyRef.current = runKey;
      setSelectedTeamA(focusTeam.id);
      setSelectedTeamB(targetOpp.id);
      setTeamAHome(nextIsHome);
      setOffBoost(0);
      setDefBoost(0);
      setPaceAdj(0);
      runMatchupForecast(focusTeam.id, targetOpp.id, nextIsHome, 0, 0, 0);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusTeam, teams, trajectoryData, currentLeague, currentSeason]);

  const disabled =
    !selectedTeamA || !selectedTeamB || selectedTeamA === selectedTeamB;

  const handlePredict = () => {
    runMatchupForecast(
      selectedTeamA,
      selectedTeamB,
      teamAHome,
      offBoost,
      defBoost,
      paceAdj
    );
  };

  const handleResetWhatIf = () => {
    setOffBoost(0);
    setDefBoost(0);
    setPaceAdj(0);
    if (timestralMatchup) {
      runMatchupForecast(selectedTeamA, selectedTeamB, teamAHome, 0, 0, 0);
    }
  };

  // Generate an inline AI Coach tactical plan using Timestral-209M + Roster context
  const handleAskInlineCoach = async (questionPrompt: string) => {
    if (!timestralMatchup || isCoachLoading) return;
    setIsCoachLoading(true);
    setActiveCoachPrompt(questionPrompt);

    const richContext = [
      `Primary Focus Team: ${timestralMatchup.team_a} (${currentLeague})`,
      `Timestral-209M Probabilistic Forecast (${timestralMatchup.venue}):`,
      `- ${timestralMatchup.team_a} Win Probability: ${timestralMatchup.win_prob_a}% vs ${timestralMatchup.team_b}: ${timestralMatchup.win_prob_b}%`,
      `- Projected Score: ${timestralMatchup.team_a} ${timestralMatchup.team_a_score.median} (80% CI [${timestralMatchup.team_a_score.q10}, ${timestralMatchup.team_a_score.q90}]) vs ${timestralMatchup.team_b} ${timestralMatchup.team_b_score.median} (80% CI [${timestralMatchup.team_b_score.q10}, ${timestralMatchup.team_b_score.q90}])`,
      `- Projected Spread: ${timestralMatchup.spread.median} pts (80% CI [${timestralMatchup.spread.q10}, ${timestralMatchup.spread.q90}])`,
      timestralMatchup.coach_brief
        ? `- Coach Brief: Target Score for 75% Win Prob = ${timestralMatchup.coach_brief.target_score_to_win_75} pts; Defensive Hold Target = ${timestralMatchup.coach_brief.defensive_hold_target} pts; ${timestralMatchup.coach_brief.pace_and_variance_advice}`
        : "",
      analysis ? `\nRoster & Statistical Breakdown:\n${analysis}` : "",
    ]
      .filter(Boolean)
      .join("\n");

    try {
      const res = await api.askCoach({
        question: questionPrompt,
        context: richContext,
        team_id: selectedTeamA,
        season: currentSeason,
      });
      setCoachGamePlan(res.response);
      setCoachGamePlanModel(res.model);
    } catch (error) {
      console.error("Error generating inline coach plan:", error);
      setCoachGamePlan(
        "Unable to reach AI Coach model right now. You can still use the Coach's Tactical Brief and What-If Simulator above."
      );
    } finally {
      setIsCoachLoading(false);
    }
  };

  // Jump from a 2026-2027 trajectory game card or chip straight into the Head-to-Head Matchup simulator
  const handlePrepUpcomingGame = (opponentName: string, homeAway: string) => {
    const oppTeam = teams.find(
      (t) =>
        t.name.toLowerCase().includes(opponentName.toLowerCase()) ||
        opponentName.toLowerCase().includes(t.name.toLowerCase())
    );
    const teamAId = focusTeam?.id || selectedTeamA;
    const teamBId = oppTeam?.id || selectedTeamB;
    const isHome = homeAway === "Home";

    setSelectedTeamA(teamAId);
    if (oppTeam) {
      setSelectedTeamB(oppTeam.id);
    }
    setTeamAHome(isHome);
    setOffBoost(0);
    setDefBoost(0);
    setPaceAdj(0);
    setActiveTab("matchup");

    if (teamAId && teamBId && teamAId !== teamBId) {
      runMatchupForecast(teamAId, teamBId, isHome, 0, 0, 0);
    }
  };

  const teamA = teams.find((t) => t.id === selectedTeamA) || focusTeam;
  const teamB = teams.find((t) => t.id === selectedTeamB);
  const nextScheduledGame = trajectoryData?.forecast?.[0];

  // Build unified fan chart data (last 12 completed games + N upcoming forecast games)
  const fanChartData = trajectoryData
    ? [
        ...trajectoryData.history.map((g, idx) => ({
          label: `H-${trajectoryData.history.length - idx}`,
          fullDate: g.date,
          opponent: g.opponent,
          type: "Historical",
          actualScore: g.team_score,
          actualOppScore: g.opponent_score,
          medianScore:
            idx === trajectoryData.history.length - 1 ? g.team_score : null,
          q10: idx === trajectoryData.history.length - 1 ? g.team_score : null,
          q90: idx === trajectoryData.history.length - 1 ? g.team_score : null,
          qBand80:
            idx === trajectoryData.history.length - 1
              ? [g.team_score, g.team_score]
              : null,
        })),
        ...trajectoryData.forecast.map((f) => ({
          label: `+${f.step} (${f.opponent.slice(0, 8)})`,
          fullDate: f.date,
          opponent: f.opponent,
          type: "Forecast (2026-27)",
          actualScore: null,
          actualOppScore: null,
          medianScore: f.team_score.median,
          oppMedianScore: f.opponent_score.median,
          q10: f.team_score.q10,
          q90: f.team_score.q90,
          qBand80: [f.team_score.q10, f.team_score.q90],
          winProb: f.win_probability,
        })),
      ]
    : [];

  // Build evaluation comparison bar chart data
  const evalChartData = evalData
    ? [
        {
          model: "Timestral-209M",
          "Win Accuracy (%)": evalData.metrics.timestral_209m.win_accuracy_pct,
          "Spread MAE (pts)": evalData.metrics.timestral_209m.spread_mae,
          "Score MAE (pts)": evalData.metrics.timestral_209m.score_mae,
        },
        {
          model: "Season Avg Baseline",
          "Win Accuracy (%)":
            evalData.metrics.season_avg_baseline.win_accuracy_pct,
          "Spread MAE (pts)": evalData.metrics.season_avg_baseline.spread_mae,
          "Score MAE (pts)": evalData.metrics.season_avg_baseline.score_mae,
        },
        {
          model: "Rolling-5 Baseline",
          "Win Accuracy (%)":
            evalData.metrics.rolling_5_baseline.win_accuracy_pct,
          "Spread MAE (pts)": evalData.metrics.rolling_5_baseline.spread_mae,
          "Score MAE (pts)": evalData.metrics.rolling_5_baseline.score_mae,
        },
      ]
    : [];

  const getCoachingTagStyle = (tag?: string) => {
    if (!tag) return "bg-muted text-muted-foreground";
    if (tag.includes("Must-Prep"))
      return "bg-red-500/20 text-red-400 border-red-500/30";
    if (tag.includes("Swing"))
      return "bg-amber-500/20 text-amber-400 border-amber-500/30";
    if (tag.includes("Trap"))
      return "bg-purple-500/20 text-purple-400 border-purple-500/30";
    return "bg-green-500/20 text-green-400 border-green-500/30";
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div className="flex items-center space-x-3">
              <TrendingUp className="w-8 h-8 text-primary" />
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h1 className="text-3xl font-bold">
                    Högsbo Coaching Predictor
                  </h1>
                  <Badge
                    variant="default"
                    className="bg-primary/20 text-primary border-primary/30"
                  >
                    <Sparkles className="w-3.5 h-3.5 mr-1" />
                    mistralai/Timestral-209M
                  </Badge>
                  {focusTeam && (
                    <Badge variant="secondary" className="text-xs">
                      Focus Team: {focusTeam.name} ({currentLeague})
                    </Badge>
                  )}
                </div>
                <p className="text-sm text-muted-foreground mt-1">
                  All forecasts, quantile targets, and AI coaching game plans are automatically anchored to{" "}
                  <span className="text-foreground font-medium">
                    {focusTeam?.name || "Högsbo"}
                  </span>
                </p>
              </div>
            </div>

            {/* League & Season Controls */}
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex gap-1 bg-muted p-1 rounded-lg">
                <Button
                  size="sm"
                  variant={currentLeague === "Men" ? "default" : "ghost"}
                  onClick={() => {
                    setCurrentLeague("Men");
                    setMyTeamId(null);
                  }}
                >
                  SBL Herr (Men)
                </Button>
                <Button
                  size="sm"
                  variant={currentLeague === "Women" ? "default" : "ghost"}
                  onClick={() => {
                    setCurrentLeague("Women");
                    setMyTeamId(null);
                  }}
                >
                  SBL Dam (Women)
                </Button>
              </div>

              <select
                className="px-3 py-1.5 rounded-md border border-input bg-background text-sm font-medium"
                value={currentSeason}
                onChange={(e) => {
                  setCurrentSeason(Number(e.target.value));
                  setMyTeamId(null);
                }}
              >
                {seasons.map((s) => (
                  <option key={s} value={s}>
                    Season {s}–{s + 1}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 space-y-6">
        {/* HÖGSBO NEXT SCHEDULED GAME SPOTLIGHT BANNER */}
        {nextScheduledGame && focusTeam && (
          <Card className="bg-gradient-to-r from-primary/15 via-card to-card border-primary/40">
            <CardContent className="p-4 sm:p-5 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
              <div className="space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="default" className="text-xs">
                    Next 2026–2027 Scheduled Game
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {nextScheduledGame.date} • {nextScheduledGame.home_away}
                  </span>
                  {nextScheduledGame.coaching_tag && (
                    <span
                      className={`text-[11px] px-2 py-0.5 rounded border font-medium ${getCoachingTagStyle(
                        nextScheduledGame.coaching_tag
                      )}`}
                    >
                      {nextScheduledGame.coaching_tag}
                    </span>
                  )}
                </div>
                <div className="text-xl font-bold">
                  {focusTeam.name}{" "}
                  {nextScheduledGame.home_away === "Home" ? "vs" : "@"}{" "}
                  {nextScheduledGame.opponent}
                </div>
                <div className="text-xs text-muted-foreground">
                  Timestral-209M Projection:{" "}
                  <span className="text-foreground font-semibold">
                    {nextScheduledGame.team_score.median} –{" "}
                    {nextScheduledGame.opponent_score.median}
                  </span>{" "}
                  ({nextScheduledGame.win_probability}% Win Prob) • Target Score:{" "}
                  <span className="text-green-400 font-semibold">
                    {nextScheduledGame.target_score_to_win}+ pts
                  </span>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <Button
                  size="sm"
                  onClick={() =>
                    handlePrepUpcomingGame(
                      nextScheduledGame.opponent,
                      nextScheduledGame.home_away
                    )
                  }
                >
                  <Sparkles className="w-4 h-4 mr-1.5" />
                  Prep Next Game ({nextScheduledGame.opponent})
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setActiveTab("trajectory")}
                >
                  <Calendar className="w-4 h-4 mr-1.5" />
                  View Next {horizon} Games
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        <Tabs
          value={activeTab}
          onValueChange={setActiveTab}
          className="space-y-6"
        >
          <TabsList className="grid w-full grid-cols-3 max-w-2xl">
            <TabsTrigger value="matchup" className="flex items-center gap-2">
              <Dribbble className="w-4 h-4" />
              Högsbo Matchup &amp; Simulator
            </TabsTrigger>
            <TabsTrigger value="trajectory" className="flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              Högsbo 2026–27 Schedule Prep
            </TabsTrigger>
            <TabsTrigger value="evaluation" className="flex items-center gap-2">
              <Award className="w-4 h-4" />
              Model Evaluation (Backtest)
            </TabsTrigger>
          </TabsList>

          {/* TAB 1: HÖGSBO HEAD-TO-HEAD MATCHUP & COACH SIMULATOR */}
          <TabsContent value="matchup" className="space-y-8">
            <Card>
              <CardHeader>
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                  <CardTitle className="flex items-center gap-2">
                    <span>
                      {teamA?.name || "Högsbo"} Matchup Preparation (
                      {currentSeason}–{currentSeason + 1})
                    </span>
                  </CardTitle>

                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant={teamAHome ? "default" : "outline"}
                      onClick={() => {
                        setTeamAHome(true);
                        if (selectedTeamA && selectedTeamB) {
                          runMatchupForecast(
                            selectedTeamA,
                            selectedTeamB,
                            true,
                            offBoost,
                            defBoost,
                            paceAdj
                          );
                        }
                      }}
                    >
                      <Home className="w-3.5 h-3.5 mr-1.5" />
                      Home (Gothia Arena)
                    </Button>
                    <Button
                      size="sm"
                      variant={!teamAHome ? "default" : "outline"}
                      onClick={() => {
                        setTeamAHome(false);
                        if (selectedTeamA && selectedTeamB) {
                          runMatchupForecast(
                            selectedTeamA,
                            selectedTeamB,
                            false,
                            offBoost,
                            defBoost,
                            paceAdj
                          );
                        }
                      }}
                    >
                      <Plane className="w-3.5 h-3.5 mr-1.5" />
                      Away Game
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-5">
                {/* Quick Upcoming Opponent Chips */}
                {trajectoryData && trajectoryData.forecast.length > 0 && (
                  <div className="space-y-2">
                    <div className="text-xs font-medium text-muted-foreground">
                      Quick-Select Upcoming 2026–2027 Opponents:
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {trajectoryData.forecast.slice(0, 5).map((g) => (
                        <Button
                          key={g.step}
                          size="sm"
                          variant={
                            teamB &&
                            (teamB.name
                              .toLowerCase()
                              .includes(g.opponent.toLowerCase()) ||
                              g.opponent
                                .toLowerCase()
                                .includes(teamB.name.toLowerCase()))
                              ? "default"
                              : "outline"
                          }
                          onClick={() =>
                            handlePrepUpcomingGame(g.opponent, g.home_away)
                          }
                          className="text-xs"
                        >
                          {g.home_away === "Home" ? "vs" : "@"} {g.opponent} (
                          {g.date.split(",")[0]})
                        </Button>
                      ))}
                    </div>
                  </div>
                )}

                <div className="grid md:grid-cols-2 gap-6">
                  {/* Left: Anchored Focus Team (Högsbo) */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium flex items-center gap-1.5">
                        <Lock className="w-3.5 h-3.5 text-primary" />
                        Focus Team (My Team) {teamAHome ? "• Home" : "• Away"}
                      </label>
                      <button
                        type="button"
                        onClick={() => setUnlockFocusTeam(!unlockFocusTeam)}
                        className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 underline"
                      >
                        <Unlock className="w-3 h-3" />
                        {unlockFocusTeam ? "Lock to Högsbo" : "Change Focus Team"}
                      </button>
                    </div>

                    {unlockFocusTeam ? (
                      <select
                        className="w-full px-4 py-2 rounded-md border border-input bg-background"
                        value={selectedTeamA}
                        onChange={(e) => {
                          setSelectedTeamA(e.target.value);
                          setMyTeamId(e.target.value);
                        }}
                      >
                        {teams.map((team) => (
                          <option key={team.id} value={team.id}>
                            {team.name}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <div className="w-full px-4 py-2 rounded-md border border-primary/40 bg-primary/10 font-semibold flex items-center justify-between">
                        <span>{teamA?.name || "Högsbo Lions"}</span>
                        <Badge variant="default" className="text-xs">
                          Primary Focus
                        </Badge>
                      </div>
                    )}
                  </div>

                  {/* Right: Opponent Selection */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium">
                      Select Opponent {!teamAHome ? "• Home" : "• Away"}
                    </label>
                    <select
                      className="w-full px-4 py-2 rounded-md border border-input bg-background"
                      value={selectedTeamB}
                      onChange={(e) => {
                        const newOppId = e.target.value;
                        setSelectedTeamB(newOppId);
                        if (selectedTeamA && newOppId && selectedTeamA !== newOppId) {
                          runMatchupForecast(
                            selectedTeamA,
                            newOppId,
                            teamAHome,
                            offBoost,
                            defBoost,
                            paceAdj
                          );
                        }
                      }}
                    >
                      <option value="">Select opponent...</option>
                      {teams
                        .filter((t) => t.id !== selectedTeamA)
                        .map((team) => (
                          <option key={team.id} value={team.id}>
                            {team.name}
                          </option>
                        ))}
                    </select>
                  </div>
                </div>

                <div className="pt-2 flex justify-center">
                  <Button
                    size="lg"
                    onClick={handlePredict}
                    disabled={disabled || isLoading}
                    className="px-8"
                  >
                    {isLoading ? (
                      <>
                        <TrendingUp className="w-5 h-5 mr-2 animate-spin" />
                        Running Timestral-209M Forecast...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-5 h-5 mr-2" />
                        Refresh Matchup &amp; Coaching Brief
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Timestral-209M Probabilistic Matchup Output */}
            {timestralMatchup && (
              <>
                <Card className="border-primary/40">
                  <CardHeader className="flex flex-row items-center justify-between border-b border-border/60">
                    <div>
                      <CardTitle className="flex items-center gap-2 text-xl">
                        <Sparkles className="w-5 h-5 text-primary" />
                        Timestral-209M Probabilistic Forecast:{" "}
                        {timestralMatchup.team_a} vs {timestralMatchup.team_b}
                      </CardTitle>
                      <p className="text-sm text-muted-foreground mt-1">
                        Venue: {timestralMatchup.venue} • 21-Quantile Distribution Forecast
                        {(offBoost !== 0 || defBoost !== 0 || paceAdj !== 0) && (
                          <span className="ml-2 text-primary font-medium">
                            (What-If Active: Off{" "}
                            {offBoost >= 0 ? `+${offBoost}` : offBoost}, Def{" "}
                            {defBoost >= 0 ? `+${defBoost}` : defBoost}, Pace{" "}
                            {paceAdj >= 0 ? `+${paceAdj}` : paceAdj})
                          </span>
                        )}
                      </p>
                    </div>
                    <Badge variant="secondary">{timestralMatchup.model}</Badge>
                  </CardHeader>
                  <CardContent className="pt-6 space-y-6">
                    {/* Win Probability Bar */}
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm font-semibold">
                        <span className="text-primary">
                          {timestralMatchup.team_a}: {timestralMatchup.win_prob_a}%
                        </span>
                        <span className="text-xs text-muted-foreground uppercase tracking-wider">
                          Win Probability
                        </span>
                        <span className="text-blue-400">
                          {timestralMatchup.team_b}: {timestralMatchup.win_prob_b}%
                        </span>
                      </div>
                      <div className="w-full h-4 bg-blue-500/30 rounded-full overflow-hidden flex">
                        <div
                          className="bg-primary h-full transition-all duration-500"
                          style={{ width: `${timestralMatchup.win_prob_a}%` }}
                        />
                      </div>
                    </div>

                    {/* Score & Quantile Cards */}
                    <div className="grid md:grid-cols-4 gap-4">
                      <div className="p-4 rounded-lg bg-muted/40 border border-border">
                        <div className="text-xs text-muted-foreground">
                          {timestralMatchup.team_a} Projected Score
                        </div>
                        <div className="text-3xl font-bold text-primary mt-1">
                          {timestralMatchup.team_a_score.median}
                        </div>
                        <div className="text-xs text-muted-foreground mt-2">
                          80% CI: [{timestralMatchup.team_a_score.q10},{" "}
                          {timestralMatchup.team_a_score.q90}]
                        </div>
                        <div className="text-xs text-muted-foreground">
                          50% CI: [{timestralMatchup.team_a_score.q25},{" "}
                          {timestralMatchup.team_a_score.q75}]
                        </div>
                      </div>

                      <div className="p-4 rounded-lg bg-muted/40 border border-border">
                        <div className="text-xs text-muted-foreground">
                          {timestralMatchup.team_b} Projected Score
                        </div>
                        <div className="text-3xl font-bold text-blue-400 mt-1">
                          {timestralMatchup.team_b_score.median}
                        </div>
                        <div className="text-xs text-muted-foreground mt-2">
                          80% CI: [{timestralMatchup.team_b_score.q10},{" "}
                          {timestralMatchup.team_b_score.q90}]
                        </div>
                        <div className="text-xs text-muted-foreground">
                          50% CI: [{timestralMatchup.team_b_score.q25},{" "}
                          {timestralMatchup.team_b_score.q75}]
                        </div>
                      </div>

                      <div className="p-4 rounded-lg bg-muted/40 border border-border">
                        <div className="text-xs text-muted-foreground">
                          Projected Point Spread ({timestralMatchup.team_a})
                        </div>
                        <div className="text-3xl font-bold mt-1">
                          {timestralMatchup.spread.median > 0 ? "+" : ""}
                          {timestralMatchup.spread.median}
                        </div>
                        <div className="text-xs text-muted-foreground mt-2">
                          80% CI: [{timestralMatchup.spread.q10},{" "}
                          {timestralMatchup.spread.q90}]
                        </div>
                      </div>

                      <div className="p-4 rounded-lg bg-muted/40 border border-border">
                        <div className="text-xs text-muted-foreground">
                          Projected Total Points
                        </div>
                        <div className="text-3xl font-bold mt-1">
                          {timestralMatchup.total_points.median}
                        </div>
                        <div className="text-xs text-muted-foreground mt-2">
                          80% CI: [{timestralMatchup.total_points.q10},{" "}
                          {timestralMatchup.total_points.q90}]
                        </div>
                      </div>
                    </div>

                    {/* Head to Head History */}
                    {timestralMatchup.head_to_head_history.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold mb-3">
                          Recent Head-to-Head Meetings
                        </h4>
                        <div className="grid sm:grid-cols-3 gap-3">
                          {timestralMatchup.head_to_head_history.map((g, i) => (
                            <div
                              key={i}
                              className="p-3 rounded-md bg-background border border-border text-xs flex justify-between items-center"
                            >
                              <div>
                                <div className="font-medium">{g.date}</div>
                                <div className="text-muted-foreground">
                                  Season {g.season} • {g.home_away}
                                </div>
                              </div>
                              <Badge
                                variant={
                                  g.team_a_score > g.team_b_score
                                    ? "default"
                                    : "secondary"
                                }
                              >
                                {g.team_a_score} – {g.team_b_score}
                              </Badge>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* COACH'S TACTICAL BRIEF & INTERACTIVE WHAT-IF SIMULATOR */}
                <div className="grid lg:grid-cols-2 gap-6">
                  {/* Left: Coach's Tactical Brief derived from Quantiles */}
                  {timestralMatchup.coach_brief && (
                    <Card className="border-green-500/30">
                      <CardHeader className="border-b border-border/60">
                        <div className="flex items-center justify-between">
                          <CardTitle className="flex items-center gap-2 text-lg">
                            <Target className="w-5 h-5 text-green-400" />
                            {timestralMatchup.team_a} Coach&apos;s Tactical Brief
                          </CardTitle>
                          <Badge variant="secondary">
                            {timestralMatchup.coach_brief.volatility_rating}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="pt-5 space-y-5">
                        {/* Target Benchmarks */}
                        <div className="grid grid-cols-3 gap-3">
                          <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20">
                            <div className="text-xs text-muted-foreground">
                              75% Win Target Score
                            </div>
                            <div className="text-2xl font-bold text-green-400 mt-1">
                              {timestralMatchup.coach_brief.target_score_to_win_75}+ pts
                            </div>
                            <div className="text-[11px] text-muted-foreground mt-0.5">
                              50% threshold:{" "}
                              {timestralMatchup.coach_brief.target_score_to_win_50} pts
                            </div>
                          </div>

                          <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
                            <div className="text-xs text-muted-foreground">
                              Defensive Hold Goal
                            </div>
                            <div className="text-2xl font-bold text-blue-400 mt-1">
                              &le; {timestralMatchup.coach_brief.defensive_hold_target} pts
                            </div>
                            <div className="text-[11px] text-muted-foreground mt-0.5">
                              Caps opponent below q50
                            </div>
                          </div>

                          <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                            <div className="text-xs text-muted-foreground">
                              80% Spread Width
                            </div>
                            <div className="text-2xl font-bold text-amber-400 mt-1">
                              &plusmn;
                              {Math.round(
                                timestralMatchup.coach_brief.spread_interval_width_80 /
                                  2
                              )}{" "}
                              pts
                            </div>
                            <div className="text-[11px] text-muted-foreground mt-0.5">
                              Full 80% range:{" "}
                              {timestralMatchup.coach_brief.spread_interval_width_80} pts
                            </div>
                          </div>
                        </div>

                        {/* Pace & Variance Strategy */}
                        <div className="p-3.5 rounded-lg bg-muted/50 border border-border text-sm">
                          <div className="font-semibold flex items-center gap-1.5 mb-1 text-primary">
                            <Zap className="w-4 h-4" />
                            Pace &amp; Variance Prescription
                          </div>
                          <p className="text-muted-foreground leading-relaxed">
                            {timestralMatchup.coach_brief.pace_and_variance_advice}
                          </p>
                        </div>

                        {/* 3 Key Tactical Priorities */}
                        <div className="space-y-2">
                          <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                            Key Coaching Priorities for {timestralMatchup.team_a}
                          </div>
                          <ul className="space-y-2 text-sm">
                            {timestralMatchup.coach_brief.key_tactical_priorities.map(
                              (item, idx) => (
                                <li
                                  key={idx}
                                  className="flex items-start gap-2 text-muted-foreground"
                                >
                                  <Shield className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                                  <span>{item}</span>
                                </li>
                              )
                            )}
                          </ul>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Right: Coach's Interactive "What-If" Tactical Simulator */}
                  <Card className="border-primary/30">
                    <CardHeader className="border-b border-border/60">
                      <div className="flex items-center justify-between">
                        <CardTitle className="flex items-center gap-2 text-lg">
                          <Sliders className="w-5 h-5 text-primary" />
                          {timestralMatchup.team_a} &ldquo;What-If&rdquo; Simulator
                        </CardTitle>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={handleResetWhatIf}
                          disabled={
                            offBoost === 0 && defBoost === 0 && paceAdj === 0
                          }
                        >
                          <RotateCcw className="w-3.5 h-3.5 mr-1" />
                          Reset
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent className="pt-5 space-y-5">
                      <p className="text-xs text-muted-foreground">
                        Simulate how{" "}
                        <span className="text-foreground font-medium">
                          {timestralMatchup.team_a}
                        </span>{" "}
                        lineup adjustments, defensive clamps on{" "}
                        <span className="text-foreground font-medium">
                          {timestralMatchup.team_b}
                        </span>
                        , or tempo shifts change win probability.
                      </p>

                      {/* Slider 1: Offensive Boost / Lineup Impact */}
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="font-medium">
                            {timestralMatchup.team_a} Offensive / Lineup Impact
                          </span>
                          <span className="font-bold text-primary">
                            {offBoost > 0 ? `+${offBoost}` : offBoost} pts
                          </span>
                        </div>
                        <input
                          type="range"
                          min={-12}
                          max={12}
                          step={1}
                          value={offBoost}
                          onChange={(e) => setOffBoost(Number(e.target.value))}
                          className="w-full accent-primary cursor-pointer"
                        />
                        <div className="flex justify-between text-[11px] text-muted-foreground">
                          <button
                            type="button"
                            onClick={() => setOffBoost(-7)}
                            className="hover:text-foreground underline"
                          >
                            Star Out (-7)
                          </button>
                          <button
                            type="button"
                            onClick={() => setOffBoost(0)}
                            className="hover:text-foreground underline"
                          >
                            Baseline (0)
                          </button>
                          <button
                            type="button"
                            onClick={() => setOffBoost(5)}
                            className="hover:text-foreground underline"
                          >
                            Hot 3PT / ATO Boost (+5)
                          </button>
                        </div>
                      </div>

                      {/* Slider 2: Defensive Clamp Target */}
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="font-medium">
                            Defensive Clamp on {timestralMatchup.team_b}
                          </span>
                          <span className="font-bold text-blue-400">
                            {defBoost > 0
                              ? `Hold -${defBoost} pts`
                              : defBoost < 0
                              ? `Allow +${Math.abs(defBoost)} pts`
                              : "0 pts"}
                          </span>
                        </div>
                        <input
                          type="range"
                          min={-12}
                          max={12}
                          step={1}
                          value={defBoost}
                          onChange={(e) => setDefBoost(Number(e.target.value))}
                          className="w-full accent-primary cursor-pointer"
                        />
                        <div className="flex justify-between text-[11px] text-muted-foreground">
                          <button
                            type="button"
                            onClick={() => setDefBoost(-6)}
                            className="hover:text-foreground underline"
                          >
                            Foul Trouble (-6)
                          </button>
                          <button
                            type="button"
                            onClick={() => setDefBoost(0)}
                            className="hover:text-foreground underline"
                          >
                            Baseline (0)
                          </button>
                          <button
                            type="button"
                            onClick={() => setDefBoost(6)}
                            className="hover:text-foreground underline"
                          >
                            Zone / Box-and-1 Clamp (+6)
                          </button>
                        </div>
                      </div>

                      {/* Slider 3: Game Tempo / Pace */}
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="font-medium">
                            Game Tempo / Pace Shift
                          </span>
                          <span className="font-bold">
                            {paceAdj > 0 ? `+${paceAdj}` : paceAdj} pts
                          </span>
                        </div>
                        <input
                          type="range"
                          min={-10}
                          max={10}
                          step={1}
                          value={paceAdj}
                          onChange={(e) => setPaceAdj(Number(e.target.value))}
                          className="w-full accent-primary cursor-pointer"
                        />
                        <div className="flex justify-between text-[11px] text-muted-foreground">
                          <button
                            type="button"
                            onClick={() => setPaceAdj(-6)}
                            className="hover:text-foreground underline"
                          >
                            Grind Half-Court (-6)
                          </button>
                          <button
                            type="button"
                            onClick={() => setPaceAdj(0)}
                            className="hover:text-foreground underline"
                          >
                            Normal Pace (0)
                          </button>
                          <button
                            type="button"
                            onClick={() => setPaceAdj(6)}
                            className="hover:text-foreground underline"
                          >
                            Push Transition (+6)
                          </button>
                        </div>
                      </div>

                      <Button
                        onClick={handlePredict}
                        disabled={isLoading}
                        className="w-full"
                      >
                        <Sliders className="w-4 h-4 mr-2" />
                        Apply &ldquo;What-If&rdquo; Adjustments to Timestral-209M
                      </Button>
                    </CardContent>
                  </Card>
                </div>

                {/* ONE-CLICK AI COACH TACTICAL GAME PLAN GENERATOR */}
                <Card>
                  <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                    <div>
                      <CardTitle className="flex items-center gap-2 text-lg">
                        <MessageSquare className="w-5 h-5 text-primary" />
                        {timestralMatchup.team_a} AI Coach Tactical Game Plan
                      </CardTitle>
                      <p className="text-xs text-muted-foreground mt-1">
                        Click a tactical question below to generate an instant game plan grounded in{" "}
                        <span className="font-medium text-foreground">
                          Timestral-209M
                        </span>{" "}
                        quantiles &amp; {timestralMatchup.team_a} roster statistics
                      </p>
                    </div>

                    <Link
                      href={`/coach?context=${encodeURIComponent(
                        `Primary Focus Team: ${timestralMatchup.team_a} (${currentLeague})\nTimestral-209M Forecast (${timestralMatchup.venue}): ${timestralMatchup.team_a} ${timestralMatchup.team_a_score.median} (${timestralMatchup.win_prob_a}% win prob) vs ${timestralMatchup.team_b} ${timestralMatchup.team_b_score.median}. Target Score for 75% win prob: ${timestralMatchup.coach_brief?.target_score_to_win_75}. Defensive hold target: ${timestralMatchup.coach_brief?.defensive_hold_target}.\n\n${analysis}`
                      )}&prompt=${encodeURIComponent(
                        timestralMatchup.coach_brief?.suggested_coach_prompts?.[0] ||
                          `Create a full tactical game plan for ${timestralMatchup.team_a} against ${timestralMatchup.team_b}.`
                      )}`}
                    >
                      <Button variant="outline" size="sm">
                        <MessageSquare className="w-4 h-4 mr-2" />
                        Open Full Chat in Coach&apos;s Corner
                      </Button>
                    </Link>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Suggested Coach Prompts */}
                    {timestralMatchup.coach_brief?.suggested_coach_prompts && (
                      <div className="flex flex-wrap gap-2">
                        {timestralMatchup.coach_brief.suggested_coach_prompts.map(
                          (promptText, i) => (
                            <Button
                              key={i}
                              variant={
                                activeCoachPrompt === promptText
                                  ? "default"
                                  : "outline"
                              }
                              size="sm"
                              disabled={isCoachLoading}
                              onClick={() => handleAskInlineCoach(promptText)}
                              className="text-xs h-auto py-2 px-3 text-left whitespace-normal"
                            >
                              <Sparkles className="w-3.5 h-3.5 mr-1.5 shrink-0" />
                              {promptText}
                            </Button>
                          )
                        )}
                      </div>
                    )}

                    {isCoachLoading && (
                      <div className="p-6 rounded-lg bg-muted/30 border border-border text-sm text-muted-foreground animate-pulse">
                        Generating {timestralMatchup.team_a} tactical coaching plan from Timestral-209M forecast &amp; roster statistics...
                      </div>
                    )}

                    {coachGamePlan && !isCoachLoading && (
                      <div className="p-5 rounded-lg bg-muted/40 border border-primary/30 space-y-3">
                        <div className="flex items-center justify-between border-b border-border/60 pb-2">
                          <span className="text-xs font-semibold text-primary">
                            Question: {activeCoachPrompt}
                          </span>
                          {coachGamePlanModel && (
                            <Badge variant="secondary" className="text-xs">
                              {coachGamePlanModel}
                            </Badge>
                          )}
                        </div>
                        <div className="prose prose-invert max-w-none text-sm whitespace-pre-wrap leading-relaxed">
                          {coachGamePlan}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </>
            )}

            {/* Roster & Multi-Season Analysis */}
            {analysis && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Dribbble className="w-6 h-6" />
                    {teamA?.name || "Högsbo"} vs {teamB?.name || "Opponent"} Roster &amp; Statistical Breakdown
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Tabs defaultValue="single" className="w-full">
                    <TabsList>
                      <TabsTrigger value="single">
                        Season {currentSeason}–{currentSeason + 1} Roster Breakdown
                      </TabsTrigger>
                      {multiSeasonAnalysis && (
                        <TabsTrigger value="multi">
                          Multi-Season Trend
                        </TabsTrigger>
                      )}
                    </TabsList>

                    <TabsContent value="single" className="mt-4">
                      <div className="prose prose-invert max-w-none space-y-1">
                        {analysis.split("\n").map((line, i) => {
                          if (line.startsWith("#")) {
                            const text = line.replace(/^#+\s*/, "");
                            return (
                              <h3
                                key={i}
                                className="text-lg font-semibold mt-4 mb-2"
                              >
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
                          if (line.trim() === "")
                            return <div key={i} className="h-2" />;
                          return <p key={i}>{line}</p>;
                        })}
                      </div>
                    </TabsContent>

                    {multiSeasonAnalysis && (
                      <TabsContent value="multi" className="mt-4">
                        <div className="prose prose-invert max-w-none space-y-1">
                          {multiSeasonAnalysis.split("\n").map((line, i) => {
                            if (line.startsWith("#")) {
                              const text = line.replace(/^#+\s*/, "");
                              return (
                                <h3
                                  key={i}
                                  className="text-lg font-semibold mt-4 mb-2"
                                >
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
                            if (line.trim() === "")
                              return <div key={i} className="h-2" />;
                            return <p key={i}>{line}</p>;
                          })}
                        </div>
                      </TabsContent>
                    )}
                  </Tabs>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* TAB 2: 2026-2027 TRAJECTORY & SCHEDULE PREP */}
          <TabsContent value="trajectory" className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Activity className="w-5 h-5 text-primary" />
                      {trajectoryData?.team_name || focusTeam?.name || "Högsbo"}{" "}
                      2026–2027 Trajectory &amp; Schedule Prep
                    </CardTitle>
                    <p className="text-sm text-muted-foreground mt-1">
                      Identify swing games, trap alerts, and target scores across the upcoming 2026–2027 schedule
                    </p>
                  </div>

                  <div className="flex items-center gap-3">
                    <select
                      className="px-3 py-2 rounded-md border border-input bg-background text-sm"
                      value={trajectoryTeamId}
                      onChange={(e) => setTrajectoryTeamId(e.target.value)}
                    >
                      {teams.map((t) => (
                        <option key={t.id} value={t.id}>
                          {t.name}
                        </option>
                      ))}
                    </select>

                    <select
                      className="px-3 py-2 rounded-md border border-input bg-background text-sm"
                      value={horizon}
                      onChange={(e) => setHorizon(Number(e.target.value))}
                    >
                      <option value={4}>Next 4 Games</option>
                      <option value={6}>Next 6 Games</option>
                      <option value={8}>Next 8 Games</option>
                      <option value={10}>Next 10 Games</option>
                    </select>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="space-y-6">
                {isTrajectoryLoading && (
                  <div className="py-12 text-center text-muted-foreground">
                    Running Timestral-209M trajectory forecast...
                  </div>
                )}

                {trajectoryData && (
                  <>
                    {/* Summary KPI Cards */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="p-4 rounded-lg bg-muted/40 border border-border">
                        <div className="text-xs text-muted-foreground">
                          Historical Context Games
                        </div>
                        <div className="text-2xl font-bold mt-1">
                          {trajectoryData.historical_games_used} games
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          Seasons: {trajectoryData.seasons_covered.join(", ")}
                        </div>
                      </div>

                      <div className="p-4 rounded-lg bg-muted/40 border border-border">
                        <div className="text-xs text-muted-foreground">
                          Recent 10-Game Scoring Avg
                        </div>
                        <div className="text-2xl font-bold text-primary mt-1">
                          {trajectoryData.recent_avg_ppg} PPG
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          Allowed: {trajectoryData.recent_avg_opp_ppg} Opp PPG
                        </div>
                      </div>

                      <div className="p-4 rounded-lg bg-muted/40 border border-border">
                        <div className="text-xs text-muted-foreground">
                          Expected Wins (Next {trajectoryData.horizon} Games)
                        </div>
                        <div className="text-2xl font-bold text-green-400 mt-1">
                          {trajectoryData.expected_wins_next_n} /{" "}
                          {trajectoryData.horizon}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          Implied Win Rate:{" "}
                          {Math.round(
                            (trajectoryData.expected_wins_next_n /
                              trajectoryData.horizon) *
                              100
                          )}
                          %
                        </div>
                      </div>

                      <div className="p-4 rounded-lg bg-muted/40 border border-border">
                        <div className="text-xs text-muted-foreground">
                          Foundation Model
                        </div>
                        <div className="text-lg font-bold mt-1 truncate">
                          Timestral-209M
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          21-Quantile Zero-Shot
                        </div>
                      </div>
                    </div>

                    {/* Stretch-Level Schedule Coaching Takeaways */}
                    {trajectoryData.schedule_coaching_insights && (
                      <div className="p-4 rounded-lg bg-primary/10 border border-primary/30 space-y-2">
                        <div className="text-sm font-semibold flex items-center gap-2 text-primary">
                          <Target className="w-4 h-4" />
                          {trajectoryData.team_name} {trajectoryData.horizon}-Game Stretch Planning Insights
                        </div>
                        <ul className="grid md:grid-cols-3 gap-3 text-xs text-muted-foreground">
                          {trajectoryData.schedule_coaching_insights.map(
                            (insight, idx) => (
                              <li
                                key={idx}
                                className="p-2.5 rounded bg-background/80 border border-border/60"
                              >
                                {insight}
                              </li>
                            )
                          )}
                        </ul>
                      </div>
                    )}

                    {/* Recharts Fan Chart */}
                    <div className="h-80 w-full pt-4">
                      <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={fanChartData}>
                          <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                          <XAxis
                            dataKey="label"
                            tick={{ fontSize: 11 }}
                            interval={0}
                            angle={-20}
                            textAnchor="end"
                            height={55}
                          />
                          <YAxis domain={[50, 125]} tick={{ fontSize: 12 }} />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: "#18181b",
                              border: "1px solid #27272a",
                              borderRadius: "8px",
                            }}
                          />
                          <Legend />
                          <Area
                            type="monotone"
                            dataKey="qBand80"
                            name="80% Confidence Interval [q10, q90]"
                            fill="#f97316"
                            fillOpacity={0.2}
                            stroke="#f97316"
                            strokeDasharray="2 2"
                          />
                          <Line
                            type="monotone"
                            dataKey="actualScore"
                            name="Actual Team Score (Last 12)"
                            stroke="#22c55e"
                            strokeWidth={2.5}
                            dot={{ r: 4 }}
                          />
                          <Line
                            type="monotone"
                            dataKey="medianScore"
                            name="Forecasted Score (Median q50)"
                            stroke="#f97316"
                            strokeWidth={3}
                            strokeDasharray="5 5"
                            dot={{ r: 5 }}
                          />
                          <Line
                            type="monotone"
                            dataKey="oppMedianScore"
                            name="Projected Opponent Score"
                            stroke="#60a5fa"
                            strokeWidth={2}
                            strokeDasharray="3 3"
                            dot={{ r: 4 }}
                          />
                        </ComposedChart>
                      </ResponsiveContainer>
                    </div>

                    {/* Upcoming 2026-2027 Schedule Forecast Cards with Coaching Tags & Prep Button */}
                    <div>
                      <h3 className="text-lg font-semibold mb-3">
                        Upcoming 2026–2027 Scheduled Games Forecast (
                        {trajectoryData.team_name})
                      </h3>
                      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {trajectoryData.forecast.map((g) => (
                          <div
                            key={g.step}
                            className="p-4 rounded-lg border border-border bg-card flex flex-col justify-between space-y-3"
                          >
                            <div className="space-y-2">
                              <div className="flex items-center justify-between">
                                <span className="text-xs text-muted-foreground">
                                  {g.date}
                                </span>
                                <Badge
                                  variant={
                                    g.home_away === "Home"
                                      ? "default"
                                      : "secondary"
                                  }
                                >
                                  {g.home_away}
                                </Badge>
                              </div>

                              <div className="flex items-center justify-between gap-2">
                                <div className="font-semibold text-base">
                                  vs {g.opponent}
                                </div>
                                {g.coaching_tag && (
                                  <span
                                    className={`text-[11px] px-2 py-0.5 rounded border font-medium ${getCoachingTagStyle(
                                      g.coaching_tag
                                    )}`}
                                  >
                                    {g.coaching_tag}
                                  </span>
                                )}
                              </div>

                              <div className="flex items-baseline justify-between pt-1">
                                <div>
                                  <div className="text-xs text-muted-foreground">
                                    Projected Score
                                  </div>
                                  <div className="text-xl font-bold">
                                    {g.team_score.median} –{" "}
                                    {g.opponent_score.median}
                                  </div>
                                </div>
                                <div className="text-right">
                                  <div className="text-xs text-muted-foreground">
                                    Win Prob
                                  </div>
                                  <div
                                    className={`text-xl font-bold ${
                                      g.win_probability >= 50
                                        ? "text-green-400"
                                        : "text-amber-400"
                                    }`}
                                  >
                                    {g.win_probability}%
                                  </div>
                                </div>
                              </div>

                              <div className="text-xs text-muted-foreground pt-1 border-t border-border/60 flex justify-between">
                                <span>
                                  80% CI: [{g.team_score.q10},{" "}
                                  {g.team_score.q90}]
                                </span>
                                {g.target_score_to_win && (
                                  <span className="text-green-400 font-medium">
                                    Target: {g.target_score_to_win}+ pts
                                  </span>
                                )}
                              </div>
                            </div>

                            <Button
                              variant="outline"
                              size="sm"
                              className="w-full text-xs mt-2"
                              onClick={() =>
                                handlePrepUpcomingGame(g.opponent, g.home_away)
                              }
                            >
                              Prep Matchup &amp; What-If Simulator
                              <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* TAB 3: MODEL EVALUATION & HISTORICAL BACKTEST */}
          <TabsContent value="evaluation" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Award className="w-5 h-5 text-primary" />
                    Historical Backtest Evaluation (
                    {currentLeague === "Men" ? "SBL Herr" : "SBL Dam"})
                  </div>
                  {evalData && (
                    <Badge variant="secondary">
                      {evalData.games_evaluated} Held-Out Games (
                      {evalData.teams_evaluated} Teams)
                    </Badge>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-8">
                {isEvalLoading && (
                  <div className="py-12 text-center text-muted-foreground">
                    Evaluating mistralai/Timestral-209M on held-out SBL historical games...
                  </div>
                )}

                {evalData && (
                  <>
                    {/* Highlight Metrics */}
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                      <div className="p-4 rounded-lg bg-primary/10 border border-primary/30">
                        <div className="text-xs text-muted-foreground">
                          Timestral Win Accuracy
                        </div>
                        <div className="text-2xl font-bold text-primary mt-1">
                          {evalData.metrics.timestral_209m.win_accuracy_pct}%
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          vs{" "}
                          {evalData.metrics.season_avg_baseline.win_accuracy_pct}
                          % Season Avg
                        </div>
                      </div>

                      <div className="p-4 rounded-lg bg-muted/40 border border-border">
                        <div className="text-xs text-muted-foreground">
                          Timestral Score MAE
                        </div>
                        <div className="text-2xl font-bold mt-1">
                          {evalData.metrics.timestral_209m.score_mae} pts
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          vs {evalData.metrics.rolling_5_baseline.score_mae}{" "}
                          Rolling-5
                        </div>
                      </div>

                      <div className="p-4 rounded-lg bg-muted/40 border border-border">
                        <div className="text-xs text-muted-foreground">
                          Timestral Spread MAE
                        </div>
                        <div className="text-2xl font-bold mt-1">
                          {evalData.metrics.timestral_209m.spread_mae} pts
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          vs {evalData.metrics.rolling_5_baseline.spread_mae}{" "}
                          Rolling-5
                        </div>
                      </div>

                      <div className="p-4 rounded-lg bg-muted/40 border border-border">
                        <div className="text-xs text-muted-foreground">
                          Brier Score (Calibration)
                        </div>
                        <div className="text-2xl font-bold text-green-400 mt-1">
                          {evalData.metrics.timestral_209m.brier_score}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          Lower is better (0.25 = random)
                        </div>
                      </div>

                      <div className="p-4 rounded-lg bg-muted/40 border border-border">
                        <div className="text-xs text-muted-foreground">
                          80% Interval Coverage
                        </div>
                        <div className="text-2xl font-bold text-blue-400 mt-1">
                          {
                            evalData.metrics.timestral_209m
                              .interval_80_coverage_pct
                          }
                          %
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          Empirical [q10, q90] coverage
                        </div>
                      </div>
                    </div>

                    {/* Bar Chart Comparison */}
                    <div className="h-72 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={evalChartData}>
                          <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                          <XAxis dataKey="model" />
                          <YAxis />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: "#18181b",
                              border: "1px solid #27272a",
                              borderRadius: "8px",
                            }}
                          />
                          <Legend />
                          <Bar
                            dataKey="Win Accuracy (%)"
                            fill="#22c55e"
                            radius={[4, 4, 0, 0]}
                          />
                          <Bar
                            dataKey="Spread MAE (pts)"
                            fill="#f97316"
                            radius={[4, 4, 0, 0]}
                          />
                          <Bar
                            dataKey="Score MAE (pts)"
                            fill="#60a5fa"
                            radius={[4, 4, 0, 0]}
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>

                    {/* Sample Backtest Predictions Table */}
                    <div>
                      <h3 className="text-lg font-semibold mb-3">
                        Sample Held-Out Game Evaluations
                      </h3>
                      <div className="overflow-x-auto rounded-lg border border-border">
                        <table className="w-full text-sm text-left">
                          <thead className="bg-muted/60 text-muted-foreground text-xs uppercase">
                            <tr>
                              <th className="px-4 py-3">Date</th>
                              <th className="px-4 py-3">Team vs Opponent</th>
                              <th className="px-4 py-3">Actual Score</th>
                              <th className="px-4 py-3">Actual Diff</th>
                              <th className="px-4 py-3">
                                Timestral Diff (80% CI)
                              </th>
                              <th className="px-4 py-3">Win Prob</th>
                              <th className="px-4 py-3">Outcome</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-border">
                            {evalData.sample_predictions.map((row, idx) => (
                              <tr key={idx} className="hover:bg-muted/20">
                                <td className="px-4 py-3 text-xs text-muted-foreground">
                                  {row.date}
                                </td>
                                <td className="px-4 py-3 font-medium">
                                  {row.team} vs {row.opponent}
                                </td>
                                <td className="px-4 py-3">
                                  {row.actual_score}
                                </td>
                                <td className="px-4 py-3">
                                  {row.actual_diff > 0 ? "+" : ""}
                                  {row.actual_diff}
                                </td>
                                <td className="px-4 py-3">
                                  <span className="font-semibold">
                                    {row.predicted_diff > 0 ? "+" : ""}
                                    {row.predicted_diff}
                                  </span>{" "}
                                  <span className="text-xs text-muted-foreground">
                                    [{row.predicted_q10}, {row.predicted_q90}]
                                  </span>
                                </td>
                                <td className="px-4 py-3">{row.win_prob}%</td>
                                <td className="px-4 py-3">
                                  {row.correct ? (
                                    <span className="inline-flex items-center text-green-400 text-xs font-medium">
                                      <CheckCircle2 className="w-4 h-4 mr-1" />
                                      Hit
                                    </span>
                                  ) : (
                                    <span className="inline-flex items-center text-red-400 text-xs font-medium">
                                      <XCircle className="w-4 h-4 mr-1" />
                                      Miss
                                    </span>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
