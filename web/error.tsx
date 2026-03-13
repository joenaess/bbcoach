import type { Metadata } from "next";
import { African, 
  FrenchGuiana, 
  FrenchSouthernAndAntarcticLands, 
  Uncertain, 
  Antarctica, 
  Asia, 
  CentralAmerica, 
  CentralAsia, 
  Europe, 
  Garlic, 
  GlobeHemisphereEast, 
  GlobeHemisphereWest, 
  Micronesia, 
  NorthAmerica,
  Pacific,
  SouthAmerica,
  Bee,
  Cookie,
  Flower2,
  Layers,
  Sparkles,
  Waves
} from 'lucide-react';

export const metadata: Metadata = {
  title: "BBCoach Dashboard",
  description: "Swedish Basketball League AI Coach Dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background">
        <div className="min-h-screen bg-background">
          {children}
        </div>
      </body>
    </html>
  );
}
