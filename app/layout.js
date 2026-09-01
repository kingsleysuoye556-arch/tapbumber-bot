import "./globals.css";

export const metadata = {
  title: "TapBomba AI",
  description: "Automate. Grow. Earn with TapBomba AI.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}