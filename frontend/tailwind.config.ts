import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        imperial: {
          red:    '#C0392B',
          red2:   '#E74C3C',
          gold:   '#D4AC0D',
          gold2:  '#F5D020',
          jade:   '#1A6B3A',
          sky:    '#1E6B9A',
          dark:   '#08080F',
          darker: '#05050A',
          ink:    '#0D0D1A',
          panel:  '#111122',
          card:   '#13131F',
          border: '#1E1E35',
          muted:  '#3A3A5C',
        },
      },
      fontFamily: {
        chinese: ['Noto Serif SC', 'serif'],
        display: ['Inter', 'sans-serif'],
        body:    ['Inter', 'sans-serif'],
      },
      backgroundImage: {
        'gradient-imperial':  'linear-gradient(135deg, #08080F 0%, #0D0D1A 50%, #0a0a18 100%)',
        'gradient-gold':      'linear-gradient(135deg, #D4AC0D 0%, #F39C12 100%)',
        'gradient-hero':      'radial-gradient(ellipse at 50% 0%, rgba(192,57,43,0.15) 0%, transparent 60%), radial-gradient(ellipse at 90% 80%, rgba(212,172,13,0.08) 0%, transparent 50%), linear-gradient(180deg, #08080F 0%, #05050A 100%)',
        'gradient-card':      'linear-gradient(135deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%)',
        'gradient-red-glow':  'radial-gradient(circle, rgba(192,57,43,0.3) 0%, transparent 70%)',
        'gradient-gold-glow': 'radial-gradient(circle, rgba(212,172,13,0.25) 0%, transparent 70%)',
        'shimmer':            'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.04) 50%, transparent 100%)',
      },
      boxShadow: {
        'glow-red':   '0 0 30px rgba(192,57,43,0.25), 0 0 60px rgba(192,57,43,0.1)',
        'glow-gold':  '0 0 30px rgba(212,172,13,0.2), 0 0 60px rgba(212,172,13,0.08)',
        'card':       '0 4px 24px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.06)',
        'card-hover': '0 8px 40px rgba(0,0,0,0.5), 0 0 0 1px rgba(212,172,13,0.2), inset 0 1px 0 rgba(255,255,255,0.08)',
        'elevation':  '0 20px 60px rgba(0,0,0,0.5)',
      },
      borderRadius: {
        '4xl': '2rem',
        '5xl': '2.5rem',
      },
      animation: {
        'fade-in':      'fadeIn 0.6s ease-out',
        'fade-up':      'fadeUp 0.5s ease-out',
        'slide-up':     'slideUp 0.4s ease-out',
        'pulse-glow':   'pulseGlow 3s ease-in-out infinite',
        'shimmer':      'shimmer 2.5s ease-in-out infinite',
        'float':        'float 6s ease-in-out infinite',
        'border-spin':  'borderSpin 4s linear infinite',
        'orb-1':        'orb1 12s ease-in-out infinite',
        'orb-2':        'orb2 15s ease-in-out infinite',
        'orb-3':        'orb3 10s ease-in-out infinite',
        'typing':       'typing 1.5s steps(3) infinite',
        'scale-in':     'scaleIn 0.3s ease-out',
        'scan-line':    'scanLine 2s linear infinite',
      },
      keyframes: {
        fadeIn:     { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        fadeUp:     { '0%': { opacity: '0', transform: 'translateY(24px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
        slideUp:    { '0%': { transform: 'translateY(20px)', opacity: '0' }, '100%': { transform: 'translateY(0)', opacity: '1' } },
        pulseGlow:  { '0%, 100%': { opacity: '0.6' }, '50%': { opacity: '1' } },
        shimmer:    { '0%': { backgroundPosition: '-200% 0' }, '100%': { backgroundPosition: '200% 0' } },
        float:      { '0%, 100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-12px)' } },
        borderSpin: { '0%': { transform: 'rotate(0deg)' }, '100%': { transform: 'rotate(360deg)' } },
        orb1:       { '0%, 100%': { transform: 'translate(0,0) scale(1)' }, '33%': { transform: 'translate(60px,-40px) scale(1.1)' }, '66%': { transform: 'translate(-30px,50px) scale(0.9)' } },
        orb2:       { '0%, 100%': { transform: 'translate(0,0) scale(1)' }, '40%': { transform: 'translate(-80px,30px) scale(1.15)' }, '70%': { transform: 'translate(50px,-60px) scale(0.85)' } },
        orb3:       { '0%, 100%': { transform: 'translate(0,0)' }, '50%': { transform: 'translate(40px,20px)' } },
        scaleIn:    { '0%': { transform: 'scale(0.9)', opacity: '0' }, '100%': { transform: 'scale(1)', opacity: '1' } },
        scanLine:   { '0%': { top: '0%' }, '100%': { top: '100%' } },
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}

export default config
