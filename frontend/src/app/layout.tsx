import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Mentor",
  description: "Personal AI Architecture Learning System",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
