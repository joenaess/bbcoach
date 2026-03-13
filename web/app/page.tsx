import { Basketball, Home, Users, TrendingUp, MessageSquare, Calendar, GitCompare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import Link from "next/link";

export default function Home() {
  const features = [
    {
      icon: <Users className="w-8 h-8" />,
      title: "League Statistics",
      description: "View top players, team stats, and detailed analytics",
      href: "/stats",
      color: "text-blue-500",
    },
    {
      icon: <TrendingUp className="w-8 h-8" />,
      title: "Game Predictor",
      description: "AI-powered matchup predictions and analysis",
      href: "/predictor",
      color: "text-green-500",
    },
    {
      icon: <MessageSquare className="w-8 h-8" />,
      title: "AI Coach",
      description: "Interactive coaching assistant with tactical advice",
      href: "/coach",
      color: "text-purple-500",
    },
    {
      icon: <GitCompare className="w-8 h-8" />,
      title: "Player Comparison",
      description: "Compare players across multiple metrics",
      href: "/comparison",
      color: "text-orange-500",
    },
    {
      icon: <Calendar className="w-8 h-8" />,
      title: "Schedule",
      description: "View team schedules and game history",
      href: "/schedule",
      color: "text-pink-500",
    },
    {
      icon: <Home className="w-8 h-8" />,
      title: "Dashboard",
      description: "Overview of data and quick access to all features",
      href: "/dashboard",
      color: "text-yellow-500",
    },
  ];

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="max-w-6xl w-full text-center space-y-12">
        {/* Hero Section */}
        <div className="space-y-6">
          <div className="flex items-center justify-center space-x-6">
            <Basketball className="w-20 h-20 text-primary animate-bounce" />
            <h1 className="text-7xl font-bold tracking-tight">BBCoach</h1>
          </div>

          <p className="text-2xl text-muted-foreground max-w-3xl mx-auto">
            AI-powered analytics and tactical assistant for the Swedish Basketball League
          </p>

          <div className="flex items-center justify-center gap-4">
            <Button size="lg" className="text-lg px-8" asChild>
              <Link href="/dashboard">
                Get Started
              </Link>
            </Button>
            <Button size="lg" variant="outline" className="text-lg px-8" asChild>
              <Link href="/stats">
                View Statistics
              </Link>
            </Button>
          </div>
        </div>

        {/* Feature Grid */}
        <div className="grid md:grid-cols-3 gap-6 text-left">
          {features.map((feature) => (
            <Link key={feature.href} href={feature.href}>
              <Card className="h-full hover:border-primary/50 transition-all hover:shadow-lg cursor-pointer">
                <CardContent className="p-6">
                  <div className={`${feature.color} mb-4`}>{feature.icon}</div>
                  <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>

        {/* Tech Stack */}
        <div className="pt-8 border-t border-border">
          <p className="text-sm text-muted-foreground">
            Powered by{" "}
            <span className="font-semibold text-foreground">FastAPI</span> +{" "}
            <span className="font-semibold text-foreground">Next.js</span> • Built with{" "}
            <span className="font-semibold text-foreground">TypeScript</span> • Charts by{" "}
            <span className="font-semibold text-foreground">Recharts</span>
          </p>
        </div>
      </div>
    </main>
  );
}
