type IconProps = { size?: number; className?: string }

const base = (size: number, className?: string) => ({
  width: size,
  height: size,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.8,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
  className,
  'aria-hidden': true,
})

export function MapPinIcon({ size = 20, className }: IconProps) {
  return <svg {...base(size, className)}><path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/></svg>
}

export function ListIcon({ size = 20, className }: IconProps) {
  return <svg {...base(size, className)}><path d="M8 6h12M8 12h12M8 18h12"/><circle cx="4" cy="6" r=".7" fill="currentColor"/><circle cx="4" cy="12" r=".7" fill="currentColor"/><circle cx="4" cy="18" r=".7" fill="currentColor"/></svg>
}

export function MenuIcon({ size = 20, className }: IconProps) {
  return <svg {...base(size, className)}><path d="M4 6h16M4 12h16M4 18h16"/></svg>
}

export function LocateIcon({ size = 20, className }: IconProps) {
  return <svg {...base(size, className)}><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/><circle cx="12" cy="12" r="8"/></svg>
}

export function SearchAreaIcon({ size = 20, className }: IconProps) {
  return <svg {...base(size, className)}><path d="M4 8V4h4M16 4h4v4M20 16v4h-4M8 20H4v-4"/><circle cx="11" cy="11" r="4"/><path d="m14 14 3 3"/></svg>
}

export function ParkingIcon({ size = 20, className }: IconProps) {
  return <svg {...base(size, className)}><rect x="3" y="3" width="18" height="18" rx="4"/><path d="M9 17V7h4a3.5 3.5 0 0 1 0 7H9M9 14h4"/></svg>
}

export function ChevronIcon({ size = 18, className }: IconProps) {
  return <svg {...base(size, className)}><path d="m9 18 6-6-6-6"/></svg>
}

export function CloseIcon({ size = 20, className }: IconProps) {
  return <svg {...base(size, className)}><path d="M6 6l12 12M18 6 6 18"/></svg>
}

export function SunIcon({ size = 18, className }: IconProps) {
  return <svg {...base(size, className)}><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
}

export function MoonIcon({ size = 18, className }: IconProps) {
  return <svg {...base(size, className)}><path d="M20.5 14.2A8 8 0 0 1 9.8 3.5 8.5 8.5 0 1 0 20.5 14.2Z"/></svg>
}
