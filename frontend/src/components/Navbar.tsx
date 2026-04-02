'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Languages, Menu, Moon, Sun, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'

type Lang = 'en' | 'zh'
type Theme = 'dark' | 'light'

const navItems = [
  { href: '/#features', en: 'Features', zh: '功能' },
  { href: '/#architecture', en: 'Architecture', zh: '建筑' },
  { href: '/avatar', en: 'Avatar', zh: '数字人' },
  { href: '/lab', en: 'Advanced Lab', zh: '研究实验室' },
  { href: '/knowledge', en: 'Knowledge', zh: '知识' },
  { href: '/#about', en: 'About', zh: '关于' },
] as const

export function Navbar() {
  const pathname = usePathname()
  const [lang, setLang] = useState<Lang>('en')
  const [theme, setTheme] = useState<Theme>('dark')
  const [mobileOpen, setMobileOpen] = useState(false)
  const [logoFailed, setLogoFailed] = useState(false)

  useEffect(() => {
    const stored = window.localStorage.getItem('wenxinlens-lang')
    if (stored === 'en' || stored === 'zh') {
      setLang(stored)
      document.documentElement.lang = stored
    }

    const storedTheme = window.localStorage.getItem('wenxinlens-theme')
    const nextTheme: Theme = storedTheme === 'light' ? 'light' : 'dark'
    setTheme(nextTheme)
    document.documentElement.setAttribute('data-theme', nextTheme)
  }, [])

  const toggleLanguage = () => {
    const next: Lang = lang === 'en' ? 'zh' : 'en'
    setLang(next)
    window.localStorage.setItem('wenxinlens-lang', next)
    document.documentElement.lang = next
    window.dispatchEvent(new CustomEvent('wenxinlens-lang-change', { detail: next }))
  }

  const toggleTheme = () => {
    const next: Theme = theme === 'dark' ? 'light' : 'dark'
    setTheme(next)
    window.localStorage.setItem('wenxinlens-theme', next)
    document.documentElement.setAttribute('data-theme', next)
    window.dispatchEvent(new CustomEvent('wenxinlens-theme-change', { detail: next }))
  }

  return (
    <header className="wl-nav-shell">
      <div className="container-1200">
        <nav className="wl-nav" aria-label="Primary">
          <Link href="/" className="wl-brand">
            {logoFailed ? (
              <div className="wl-brand-mark" aria-hidden="true">
                <span className="font-zh wl-brand-mark-char">文</span>
              </div>
            ) : (
              <img
                src="/images/wenxinlens.png"
                alt="WenxinLens logo"
                className="wl-brand-logo"
                onError={() => setLogoFailed(true)}
              />
            )}
            <div className="wl-brand-text">
              <span className="font-zh wl-brand-zh">文心镜</span>
              <span className="wl-brand-dot">·</span>
              <span className="wl-brand-en">WenxinLens</span>
            </div>
          </Link>

          <div className="wl-nav-links" aria-label="Sections">
            {navItems.map((item) => {
              const active = (pathname.startsWith('/knowledge') && item.href === '/knowledge') ||
                (pathname.startsWith('/avatar') && item.href === '/avatar') ||
                (pathname.startsWith('/lab') && item.href === '/lab')
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
            <button onClick={toggleTheme} className="wl-theme-btn" aria-label="Toggle theme">
              {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}
              {theme === 'dark' ? 'Light' : 'Dark'}
            </button>
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
              <button onClick={toggleTheme} className="wl-theme-btn wl-lang-btn-mobile">
                {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}
                {theme === 'dark' ? 'Switch to Light Theme' : 'Switch to Dark Theme'}
              </button>

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
