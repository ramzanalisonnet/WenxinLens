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
  title: 'WenxinLens — AI Cultural Guide for Chinese Architecture',
  description:
    'Point your camera at Chinese ancient architecture to discover its history, symbolism, and cultural significance through AI.',
  keywords: ['Chinese architecture', 'AI', 'cultural heritage', 'ancient buildings', 'history'],
  openGraph: {
    title: 'WenxinLens',
    description: 'AI Cultural Interpretation for Chinese Ancient Architecture',
    type: 'website',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${notoSansSC.variable}`}>
      <body className="text-white antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
