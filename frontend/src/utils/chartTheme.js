const THEME = {
  bg: '#0a0e17',
  bgCard: '#111722',
  grid: '#1c2433',
  border: '#243044',
  textPrimary: '#e4e7ed',
  textSecondary: '#8a93a6',
  textWeak: '#5a6478',

  up: '#fa3e3e',
  down: '#00b07c',
  upAlpha: 'rgba(250, 62, 62, 0.15)',
  downAlpha: 'rgba(0, 176, 124, 0.15)',
  upShadow: 'rgba(250, 62, 62, 0.6)',
  sellBlue: '#3a8eff',

  ma5: '#ffd400',
  ma10: '#ff6ec7',
  ma20: '#00d4ff',
  ma60: '#a78bfa',

  boll: '#7a8aa0',
  bollArea: 'rgba(122, 138, 160, 0.04)',

  dif: '#ffd400',
  dea: '#00d4ff',

  titleGold: '#e4b96a',

  support: '#00b07c',
  resistance: '#fa3e3e',
};

export const MOMENTUM_COLORS = {
  extreme: THEME.up,
  strong: '#f97316',
  medium: '#fbbf24',
  weak: '#06b6d4',
  cold: THEME.down,
};

export function getMomentumColor(score) {
  if (score === null || score === undefined) return '#6b7280';
  if (score >= 80) return MOMENTUM_COLORS.extreme;
  if (score >= 60) return MOMENTUM_COLORS.strong;
  if (score >= 40) return MOMENTUM_COLORS.medium;
  if (score >= 20) return MOMENTUM_COLORS.weak;
  return MOMENTUM_COLORS.cold;
}

export function formatVolume(val) {
  if (val === null || val === undefined) return '-';
  if (val >= 1e8) return (val / 1e8).toFixed(2) + '亿';
  if (val >= 1e4) return (val / 1e4).toFixed(0) + '万';
  return val.toString();
}

export default THEME;
