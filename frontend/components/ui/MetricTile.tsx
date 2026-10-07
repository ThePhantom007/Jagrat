'use client';

import { LucideIcon, TrendingUp, TrendingDown, ArrowRight } from 'lucide-react';

type Trend = 'up' | 'down' | 'steady';

interface MetricTileProps {
  icon: LucideIcon;
  label: string;
  trend: Trend;
  description: string;
}

/**
 * MetricTile — For Growth dashboard metrics
 * Shows icon, label, trend arrow, and description
 * Meaning never depends on color alone (arrows + text)
 */
export function MetricTile({ icon: Icon, label, trend, description }: MetricTileProps) {
  const trendConfig = {
    up: { icon: TrendingUp, color: 'var(--up)', label: 'Improving' },
    down: { icon: TrendingDown, color: 'var(--down)', label: 'Easing' },
    steady: { icon: ArrowRight, color: 'var(--steady)', label: 'Steady' },
  };

  const config = trendConfig[trend];
  const TrendIcon = config.icon;

  return (
    <div
      className="flex items-start gap-4 p-4 rounded-2xl transition-all hover:scale-[1.02]"
      style={{
        background: 'var(--card-surface)',
        border: '1px solid var(--card-border)',
        boxShadow: 'var(--card-shadow)',
      }}
    >
      {/* Icon */}
      <div
        className="shrink-0 w-12 h-12 rounded-xl flex items-center justify-center"
        style={{
          background: 'var(--saffron-soft)',
          color: 'var(--saffron)',
        }}
      >
        <Icon className="w-6 h-6" aria-hidden="true" />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <h3 className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>
            {label}
          </h3>
          <TrendIcon
            className="w-4 h-4 shrink-0"
            style={{ color: config.color }}
            aria-label={config.label}
          />
        </div>
        <p className="text-xs leading-relaxed" style={{ color: 'var(--text-muted)' }}>
          {description}
        </p>
      </div>
    </div>
  );
}
