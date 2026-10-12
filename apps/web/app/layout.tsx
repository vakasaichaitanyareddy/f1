import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "APEX GP — Formula 1 Intelligence & Racing Platform",
  description: "Live timing, exact championship calculations, circuit performance analytics, and strategy simulation.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#0D0E12] text-[#F5F6F8] antialiased">
        {children}
      </body>
    </html>
  );
}
