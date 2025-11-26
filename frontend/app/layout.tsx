import "./globals.css";

export const metadata = {
  title: "Travel Planner",
  description: "Your itinerary assistant",
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
