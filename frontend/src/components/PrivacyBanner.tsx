interface PrivacyBannerProps {
  privacyMode?: 'standard' | 'strict'
  retentionDays?: number
}

export function PrivacyBanner({ privacyMode, retentionDays }: PrivacyBannerProps) {
  if (privacyMode !== 'strict') return null

  return (
    <div className="privacy-banner">
      PRIVACY MODE ACTIVE - Person crops blurred - Biometric attributes suppressed - Data
      retained for {retentionDays ?? 30} days
    </div>
  )
}
