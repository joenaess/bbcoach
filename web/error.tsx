import type { Metadata } from "next";
// Remove deleted icons

export const metadata: Metadata = {
  title: "BBCoach Dashboard",
  description: "Swedish Dribbble League AI Coach Dashboard",
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
