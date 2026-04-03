import type { Metadata } from 'next'
import { Inter, Noto_Sans_SC } from 'next/font/google'
import './globals.css'
import { Providers } from './providers'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const notoSansSC = Noto_Sans_SC({
  subsets: ['latin'],
  weight: ['400', '500', '700'],
  variable: '--font-noto-sans-sc',
})

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:5173'),
  title: 'WenxinLens — AI Cultural Guide for Chinese Architecture',
  description:
    'Point your camera at Chinese ancient architecture to discover its history, symbolism, and cultural significance through AI.',
  keywords: ['Chinese architecture', 'AI', 'cultural heritage', 'ancient buildings', 'history'],
  icons: {
    icon: '/images/wenxinlens.png',
    shortcut: '/images/wenxinlens.png',
    apple: '/images/wenxinlens.png',
  },
  openGraph: {
    title: 'WenxinLens',
    description: 'AI Cultural Interpretation for Chinese Ancient Architecture',
    type: 'website',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${notoSansSC.variable}`}>
      <body className="antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
