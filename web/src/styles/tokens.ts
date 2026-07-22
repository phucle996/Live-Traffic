// ==============================================================================
// Design Tokens Module (web/src/styles/tokens.ts)
// Core Design System Tokens: Semantic Colors, Spacing, Typography & Radii
// Map-First Minimalist Aesthetics Compliance (Google Maps Style)
// ==============================================================================

export const designTokens = {
  // 1. Semantic Color Tokens
  colors: {
    // Traffic Status Colors
    traffic: {
      good: "#22c55e",       // 🟢 Lưu thông tốt (>= 35 km/h)
      moderate: "#eab308",   // 🟡 Đông xe (20 - 35 km/h)
      congested: "#ef4444",  // 🔴 Ùn tắc nghiêm trọng (< 20 km/h)
      unknown: "#94a3b8",    // ⚪ Không có dữ liệu
    },
    // Background & Surfaces (Light & Dark Neutral Shades)
    bg: {
      primary: "#f8fafc",    // Nền trang xám rất nhạt
      surface: "#ffffff",    // Panel nền trắng tinh tế
      surfaceDark: "rgba(15, 23, 42, 0.85)", // Glassmorphism Dark Surface
      overlay: "rgba(0, 0, 0, 0.4)",
    },
    // Text Color Scale
    text: {
      primary: "#0f172a",    // Chữ xám đậm
      secondary: "#64748b",  // Chữ phụ
      muted: "#94a3b8",      // Chữ mờ
      inverse: "#ffffff",    // Chữ màu tương phản
    },
    // Primary Actions & Accent Colors
    brand: {
      primary: "#1e40af",    // Xanh dương đậm (Primary Action)
      primaryHover: "#1d4ed8",
      accent: "#38bdf8",     // Xanh ngọc
    },
    // Status Indicators
    status: {
      live: "#22c55e",
      stale: "#f59e0b",
      offline: "#ef4444",
    }
  },

  // 2. Spacing Scale (8pt Grid System)
  spacing: {
    xs: "4px",
    sm: "8px",
    md: "16px",
    lg: "24px",
    xl: "32px",
    xxl: "48px",
  },

  // 3. Border Radius Tokens
  radii: {
    sm: "6px",
    md: "12px",
    lg: "16px",
    full: "9999px",
  },

  // 4. Typography Scale
  typography: {
    fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
    headings: "'Outfit', 'Inter', sans-serif",
    fontSizes: {
      xs: "11px",
      sm: "13px",
      base: "15px",
      lg: "18px",
      xl: "22px",
      h1: "28px",
    },
    fontWeights: {
      regular: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    }
  },

  // 5. Shadows
  shadows: {
    panel: "0 4px 20px -2px rgba(0, 0, 0, 0.1), 0 2px 6px -1px rgba(0, 0, 0, 0.06)",
    floating: "0 10px 30px -5px rgba(0, 0, 0, 0.2)",
  }
} as const;

export type DesignTokens = typeof designTokens;
