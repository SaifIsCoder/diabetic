/**
 * Design Tokens for Diabetic Retinopathy Application
 * Confirmed Palette: Clinical Teal & Midnight Slate Navy
 * WCAG 2.2 AA Compliant Contrast Ratios
 */

export const SeverityColors = {
  grade0: {
    badgeBg: "#ECFDF5",
    badgeBorder: "#A7F3D0",
    text: "#047857",
    indicator: "#10B981",
    label: "No Diabetic Retinopathy",
  },
  grade1: {
    badgeBg: "#F0FDFA",
    badgeBorder: "#99F6E4",
    text: "#0F766E",
    indicator: "#14B8A6",
    label: "Mild NPDR",
  },
  grade2: {
    badgeBg: "#FFFBEB",
    badgeBorder: "#FDE68A",
    text: "#B45309",
    indicator: "#F59E0B",
    label: "Moderate NPDR",
  },
  grade3: {
    badgeBg: "#FFF7ED",
    badgeBorder: "#FED7AA",
    text: "#C2410C",
    indicator: "#EA580C",
    label: "Severe NPDR",
  },
  grade4: {
    badgeBg: "#FEF2F2",
    badgeBorder: "#FECACA",
    text: "#B91C1C",
    indicator: "#DC2626",
    label: "Proliferative DR",
  },
};

export const DarkSeverityColors = {
  grade0: {
    badgeBg: "#064E3B",
    badgeBorder: "#047857",
    text: "#A7F3D0",
    indicator: "#34D399",
    label: "No Diabetic Retinopathy",
  },
  grade1: {
    badgeBg: "#134E4A",
    badgeBorder: "#0F766E",
    text: "#99F6E4",
    indicator: "#2DD4BF",
    label: "Mild NPDR",
  },
  grade2: {
    badgeBg: "#78350F",
    badgeBorder: "#B45309",
    text: "#FDE68A",
    indicator: "#FBBF24",
    label: "Moderate NPDR",
  },
  grade3: {
    badgeBg: "#7C2D12",
    badgeBorder: "#C2410C",
    text: "#FED7AA",
    indicator: "#FB923C",
    label: "Severe NPDR",
  },
  grade4: {
    badgeBg: "#7F1D1D",
    badgeBorder: "#B91C1C",
    text: "#FECACA",
    indicator: "#F87171",
    label: "Proliferative DR",
  },
};

export const getSeverityColors = (grade: number, isDark = false) => {
  const palette = isDark ? DarkSeverityColors : SeverityColors;
  switch (grade) {
    case 0: return palette.grade0;
    case 1: return palette.grade1;
    case 2: return palette.grade2;
    case 3: return palette.grade3;
    case 4: return palette.grade4;
    default: return palette.grade0;
  }
};

export default {
  light: {
    primary: "#007A78",
    primaryHover: "#006666",
    secondary: "#0F1E36",
    accent: "#007A87",
    background: "#F4F8FA",
    surface: "#FFFFFF",
    surfaceSubtle: "#F8FAFC",
    cardBorder: "#E2E8F0",
    text: "#0B1A2C",
    textMuted: "#475569",
    tint: "#007A78",
    tabIconDefault: "#64748B",
    tabIconSelected: "#007A78",
    headerBackground: "#FFFFFF",
    border: "#CBD5E1",
    error: "#B91C1C",
    success: "#047857",
    warning: "#B45309",
  },
  dark: {
    primary: "#007A78",
    primaryHover: "#006666",
    secondary: "#CBD5E1",
    accent: "#38BDF8",
    background: "#0A111E",
    surface: "#111C2E",
    surfaceSubtle: "#162238",
    cardBorder: "#1E2D44",
    text: "#F1F5F9",
    textMuted: "#94A3B8",
    tint: "#2DD4BF",
    tabIconDefault: "#94A3B8",
    tabIconSelected: "#2DD4BF",
    headerBackground: "#111C2E",
    border: "#334155",
    error: "#F87171",
    success: "#34D399",
    warning: "#FBBF24",
  },
};
