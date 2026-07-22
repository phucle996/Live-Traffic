import type { Metadata } from "next";
import "./globals.css";

// Cấu hình Metadata hiển thị SEO và tiêu đề hệ thống giám sát giao thông TP.HCM
export const metadata: Metadata = {
  title: "Traffic View — Hệ Thống Giám Sát & Dự Đoán Giao Thông TP.HCM",
  description: "Cloud-Native Real-Time Traffic Stream (Go API) & AI Prediction Engine (Rust Engine)",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" className="h-full antialiased dark">
      {/* Thẻ body thiết lập màu nền tối slate-950 và font chữ sans-serif mặc định */}
      <body className="min-h-full flex flex-col bg-slate-950 text-slate-100 font-sans">
        {/* Render trực tiếp giao diện con công khai không cần bọc qua AuthProvider */}
        {children}
      </body>
    </html>
  );
}
