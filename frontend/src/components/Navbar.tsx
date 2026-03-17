'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Languages, Menu, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'

type Lang = 'en' | 'zh'

const navItems = [
  { href: '/#features', en: 'Features', zh: '功能' },
  { href: '/#architecture', en: 'Architecture', zh: '建筑' },
  { href: '/knowledge', en: 'Knowledge', zh: '知识' },
  { href: '/#about', en: 'About', zh: '关于' },
] as const

export function Navbar() {
  const pathname = usePathname()
  const [lang, setLang] = useState<Lang>('en')
  const [mobileOpen, setMobileOpen] = useState(false)

  useEffect(() => {
    const stored = window.localStorage.getItem('wenxinlens-lang')
    if (stored === 'en' || stored === 'zh') {
      setLang(stored)
      document.documentElement.lang = stored
    }
  }, [])

  const toggleLanguage = () => {
    const next: Lang = lang === 'en' ? 'zh' : 'en'
    setLang(next)
    window.localStorage.setItem('wenxinlens-lang', next)
    document.documentElement.lang = next
    window.dispatchEvent(new CustomEvent('wenxinlens-lang-change', { detail: next }))
  }

  return (
    <header className="wl-nav-shell">
      <div className="container-1200">
        <nav className="wl-nav" aria-label="Primary">
          <Link href="/" className="wl-brand">
            <div className="wl-brand-mark">
              <span className="font-zh wl-brand-mark-char">文</span>
            </div>
            <div className="wl-brand-text">
              <span className="font-zh wl-brand-zh">文心镜</span>
              <span className="wl-brand-dot">·</span>
              <span className="wl-brand-en">WenxinLens</span>
            </div>
          </Link>

          <div className="wl-nav-links" aria-label="Sections">
            {navItems.map((item) => {
              const active = pathname.startsWith('/knowledge') && item.href === '/knowledge'
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`wl-nav-link ${active ? 'is-active' : ''}`}
                >
                  {lang === 'en' ? item.en : item.zh}
                </Link>
              )
            })}
          </div>

          <div className="wl-nav-actions">
            <button onClick={toggleLanguage} className="wl-lang-btn" aria-label="Toggle language">
              <Languages size={14} />
              {lang === 'en' ? 'EN / 中' : '中 / EN'}
            </button>
          </div>

          <button
            className="wl-nav-mobile-toggle"
            onClick={() => setMobileOpen((v) => !v)}
            aria-label="Toggle menu"
          >
            <AnimatePresence mode="wait">
              {mobileOpen ? (
                <motion.span key="close" initial={{ rotate: -90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: 90, opacity: 0 }}>
                  <X size={18} />
                </motion.span>
              ) : (
                <motion.span key="menu" initial={{ rotate: 90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: -90, opacity: 0 }}>
                  <Menu size={18} />
                </motion.span>
              )}
            </AnimatePresence>
          </button>
        </nav>
      </div>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="wl-nav-mobile"
          >
            <div className="container-1200 wl-nav-mobile-inner">
              <button onClick={toggleLanguage} className="wl-lang-btn wl-lang-btn-mobile">
                <Languages size={14} />
                {lang === 'en' ? 'Switch to Chinese' : '切换到英文'}
              </button>

              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className="wl-nav-mobile-link"
                >
                  <span>{lang === 'en' ? item.en : item.zh}</span>
                  <span className="wl-nav-mobile-link-alt">{lang === 'en' ? item.zh : item.en}</span>
                </Link>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  )
}
