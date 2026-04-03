'use client'

import Link from 'next/link'
import {
  ArrowRight,
  Camera,
  BookOpen,
  Map,
  MessageCircle,
  Landmark,
  Github,
  Instagram,
  Youtube,
  Mail,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion, useReducedMotion } from 'framer-motion'
import { Navbar } from '../components/Navbar'
import { knowledgeApi } from '@/services/api'
import type { DynastyCatalogItem } from '@/types'

type Lang = 'en' | 'zh'
type Theme = 'dark' | 'light'

function preferTimelineJpg(imageUrl?: string): string {
  if (!imageUrl) return '/images/hero-architecture.svg'
  if (imageUrl.startsWith('/images/timeline-') && imageUrl.endsWith('.svg')) {
    return `${imageUrl.slice(0, -4)}.jpg`
  }
  return imageUrl
}

const features = [
  {
    icon: Camera,
    titleEn: 'AI Recognition',
    titleZh: '建筑识别',
    descriptionEn: 'Recognize temples, palaces, and historic structures instantly from a single photo.',
    descriptionZh: '通过一张照片即时识别古代建筑、宫殿与寺庙。',
    href: '/recognize',
  },
  {
    icon: MessageCircle,
    titleEn: 'Interactive Storytelling',
    titleZh: '互动讲述',
    descriptionEn: 'Chat with an AI cultural guide that explains symbolism, ritual meaning, and historical context.',
    descriptionZh: '与 AI 文化导览对话，理解建筑背后的礼制与历史故事。',
    href: '/chat',
  },
  {
    icon: Map,
    titleEn: 'Cultural Tour',
    titleZh: '文化游览',
    descriptionEn: 'Plan intelligent routes to nearby heritage sites with context-aware recommendations.',
    descriptionZh: '获取智能路线推荐，探索周边文化遗产景点。',
    href: '/tour',
  },
  {
    icon: BookOpen,
    titleEn: 'Knowledge Base',
    titleZh: '知识库',
    descriptionEn: 'Search dynasties, styles, and architectural systems in one connected knowledge graph.',
    descriptionZh: '在统一知识图谱中检索朝代、风格与建筑体系。',
    href: '/knowledge',
  },
]

const fallbackDynastyCatalog: DynastyCatalogItem[] = [
  {
    dynasty: 'Tang Dynasty',
    dynasty_zh: '唐朝',
    period: '618-907 CE',
    places: [
      {
        id: 'fallback_tang',
        name: 'Giant Wild Goose Pagoda',
        name_zh: '大雁塔',
        location: "Xi'an, Shaanxi",
        coordinates: null,
        architecture_type: 'Buddhist Pagoda',
        year_built: '652',
        image_url: '/images/timeline-tang.jpg',
        description: 'A Tang-era pagoda preserving scriptures and structural knowledge of masonry religious architecture.',
        details: [],
      },
    ],
  },
  {
    dynasty: 'Song Dynasty',
    dynasty_zh: '宋朝',
    period: '960-1279 CE',
    places: [
      {
        id: 'fallback_song',
        name: 'Fogong Temple Wooden Pagoda',
        name_zh: '应县木塔',
        location: 'Ying County, Shanxi',
        coordinates: null,
        architecture_type: 'Timber Pagoda',
        year_built: '1056',
        image_url: '/images/timeline-song.jpg',
        description: 'A Song landmark known for advanced timber structure and layered bracket engineering.',
        details: [],
      },
    ],
  },
  {
    dynasty: 'Yuan Dynasty',
    dynasty_zh: '元朝',
    period: '1271-1368 CE',
    places: [
      {
        id: 'fallback_yuan',
        name: 'White Stupa of Miaoying Temple',
        name_zh: '妙应寺白塔',
        location: 'Beijing',
        coordinates: null,
        architecture_type: 'Lamaist Stupa',
        year_built: '1271',
        image_url: '/images/timeline-yuan.jpg',
        description: 'A Yuan-period monument showing cross-cultural religious architecture in the imperial capital.',
        details: [],
      },
    ],
  },
  {
    dynasty: 'Ming Dynasty',
    dynasty_zh: '明朝',
    period: '1368-1644 CE',
    places: [
      {
        id: 'fallback_ming',
        name: 'Forbidden City',
        name_zh: '故宫',
        location: 'Beijing',
        coordinates: null,
        architecture_type: 'Imperial Palace Architecture',
        year_built: '1406',
        image_url: '/images/timeline-ming.jpg',
        description: 'A mature expression of Ming palace planning, ritual hierarchy, and timber-hall construction.',
        details: [],
      },
    ],
  },
  {
    dynasty: 'Qing Dynasty',
    dynasty_zh: '清朝',
    period: '1644-1912 CE',
    places: [
      {
        id: 'fallback_qing',
        name: 'Summer Palace',
        name_zh: '颐和园',
        location: 'Beijing',
        coordinates: null,
        architecture_type: 'Imperial Garden Architecture',
        year_built: '1750',
        image_url: '/images/timeline-qing.jpg',
        description: 'A Qing imperial garden where architecture, topography, and symbolic landscape are integrated.',
        details: [],
      },
    ],
  },
]

export default function HomePage() {
  const reduceMotion = useReducedMotion()
  const [lang, setLang] = useState<Lang>('en')
  const [theme, setTheme] = useState<Theme>('dark')
  const { data: dynastyCatalog } = useQuery({
    queryKey: ['home-dynasty-catalog'],
    queryFn: () => knowledgeApi.getDynastyCatalog(),
  })

  useEffect(() => {
    const stored = window.localStorage.getItem('wenxinlens-lang')
    if (stored === 'en' || stored === 'zh') {
      setLang(stored)
    }

    const storedTheme = window.localStorage.getItem('wenxinlens-theme')
    if (storedTheme === 'light' || storedTheme === 'dark') {
      setTheme(storedTheme)
    }

    const onLangChange = (event: Event) => {
      const custom = event as CustomEvent<Lang>
      if (custom.detail === 'en' || custom.detail === 'zh') {
        setLang(custom.detail)
      }
    }

    const onThemeChange = (event: Event) => {
      const custom = event as CustomEvent<Theme>
      if (custom.detail === 'light' || custom.detail === 'dark') {
        setTheme(custom.detail)
      }
    }

    window.addEventListener('wenxinlens-lang-change', onLangChange as EventListener)
    window.addEventListener('wenxinlens-theme-change', onThemeChange as EventListener)
    return () => {
      window.removeEventListener('wenxinlens-lang-change', onLangChange as EventListener)
      window.removeEventListener('wenxinlens-theme-change', onThemeChange as EventListener)
    }
  }, [])

  const t = {
    heroTitle: lang === 'en' ? 'AI Cultural Heritage, Reimagined' : '用 AI 重构文化遗产体验',
    heroDesc:
      lang === 'en'
        ? 'WenxinLens brings Chinese ancient architecture to life through visual recognition, storytelling, and contextual exploration.'
        : '文心镜通过视觉识别、互动讲述与知识探索，让中国古建筑真正“活起来”。',
    start: lang === 'en' ? 'Start Recognizing' : '开始识别',
    explore: lang === 'en' ? 'Explore Architecture' : '探索建筑',
    featuresTitle: lang === 'en' ? 'Core Platform Features' : '核心平台能力',
    timelineTitle: lang === 'en' ? 'Architecture Through Dynasties' : '历代建筑演进',
    aboutTitle: lang === 'en' ? 'About WenxinLens' : '关于文心镜',
    aboutBody:
      lang === 'en'
        ? 'A modern AI-tech platform inspired by cultural heritage preservation, designed for students, travelers, and researchers.'
        : '以文化遗产保护为灵感的现代 AI 平台，面向学习者、旅行者与研究者。',
    openFeature: lang === 'en' ? 'Open Feature' : '进入功能',
  }

  const timelineCatalog = dynastyCatalog && dynastyCatalog.length > 0 ? dynastyCatalog : fallbackDynastyCatalog

  return (
    <div className="app-shell">
      <Navbar />

      <main>
        <section className="section-block" aria-labelledby="hero-title">
          <div className="container-1200 relative">
            <div className="grid-12 items-center">
              <motion.div
                className="col-span-12 lg:col-span-7"
                initial={{ opacity: 0, y: 18 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: reduceMotion ? 0.01 : 0.5, ease: [0.22, 1, 0.36, 1] }}
              >
                <p className="text-caption" style={{ letterSpacing: '0.08em', color: '#00D1B2' }}>
                  WenxinLens · 文心镜
                </p>
                <h1 id="hero-title" className="title-hero mt-4">
                  {t.heroTitle}
                </h1>
                <p className="text-body mt-6 max-w-xl">{t.heroDesc}</p>
                <div className="mt-8 flex flex-wrap gap-3">
                  <Link href="/recognize" className="btn btn-primary subtle-shine">
                    <Camera size={16} />
                    {t.start}
                  </Link>
                  <Link href="/#architecture" className="btn btn-secondary">
                    <Landmark size={16} />
                    {t.explore}
                  </Link>
                </div>
              </motion.div>
            </div>

            <motion.div
              className="mt-8 lg:mt-0 lg:absolute lg:top-0 lg:right-0 w-full lg:w-[min(36vw,460px)]"
              initial={{ opacity: 0, y: 22 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: reduceMotion ? 0 : 0.08, duration: reduceMotion ? 0.01 : 0.55 }}
            >
              <article className="panel p-4 md:p-5 subtle-shine">
                <div className="relative rounded-xl overflow-hidden">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src="/images/hero-architecture.svg"
                    alt="Chinese ancient architecture"
                    className="hero-image"
                  />
                  <div
                    className="absolute inset-0"
                    style={{ background: 'linear-gradient(180deg, rgba(11,15,26,0.15) 0%, rgba(11,15,26,0.82) 100%)' }}
                  />
                  <div className="absolute left-5 right-5 bottom-5">
                    <p className="text-caption">{lang === 'en' ? 'Featured Scene' : '精选场景'}</p>
                    <p className="title-card mt-2">
                      {lang === 'en' ? 'Temple and Palace Heritage' : '寺庙与宫殿文化遗产'}
                    </p>
                  </div>
                </div>
              </article>
            </motion.div>
          </div>
        </section>

        <section id="features" className="section-block" aria-labelledby="features-title">
          <div className="container-1200">
            <div className="mb-10">
              <h2 id="features-title" className="title-section">
                {t.featuresTitle}
              </h2>
            </div>

            <div className="grid-12">
              {features.map((item, idx) => {
                const Icon = item.icon
                return (
                  <motion.article
                    key={item.href}
                    className="col-span-12 md:col-span-6 panel p-6 hover-rise"
                    initial={{ opacity: 0, y: 16 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: reduceMotion ? 0 : idx * 0.05, duration: reduceMotion ? 0.01 : 0.4 }}
                  >
                    <div className="w-11 h-11 rounded-xl flex items-center justify-center"
                      style={{ background: 'rgba(255, 77, 79, 0.14)', border: '1px solid rgba(255, 77, 79, 0.32)' }}>
                      <Icon size={20} style={{ color: '#FF4D4F' }} />
                    </div>
                    <h3 className="title-card mt-5">{item.titleEn} ({item.titleZh})</h3>
                    <p className="text-body mt-4">
                      {lang === 'en' ? item.descriptionEn : item.descriptionZh}
                    </p>
                    <Link href={item.href} className="btn btn-ghost mt-6">
                      {t.openFeature}
                      <ArrowRight size={15} />
                    </Link>
                  </motion.article>
                )
              })}
            </div>
          </div>
        </section>

        <section id="architecture" className="section-block" aria-labelledby="architecture-title">
          <div className="container-1200">
            <h2 id="architecture-title" className="title-section mb-10">
              {t.timelineTitle}
            </h2>

            <div className="grid-12">
              {timelineCatalog.map((item, idx) => {
                const featured = item.places?.[0]
                const subtitle = `${item.dynasty} (${item.dynasty_zh})`
                const periodText = item.period
                const image = preferTimelineJpg(featured?.image_url)
                const description = featured?.description || (lang === 'en' ? 'No details yet.' : '暂无详情。')
                const meta = [featured?.architecture_type, featured?.location, featured?.year_built].filter(Boolean).join(' · ')

                return (
                  <Link
                    key={item.dynasty}
                    href={`/knowledge/dynasty/${encodeURIComponent(item.dynasty)}`}
                    className="col-span-12 md:col-span-6 xl:col-span-4 block"
                    aria-label={`Open ${item.dynasty} details`}
                  >
                    <motion.article
                      className="panel overflow-hidden hover-rise h-full"
                      initial={{ opacity: 0, y: 14 }}
                      whileInView={{ opacity: 1, y: 0 }}
                      viewport={{ once: true }}
                      transition={{ delay: reduceMotion ? 0 : idx * 0.05, duration: reduceMotion ? 0.01 : 0.42 }}
                    >
                      <div className="relative">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src={image} alt={item.dynasty} className="w-full h-48 object-cover" />
                        <div
                          className="absolute inset-0"
                          style={{ background: 'linear-gradient(180deg, rgba(11,15,26,0.05), rgba(11,15,26,0.72))' }}
                        />
                        <div className="absolute left-4 bottom-4 right-4">
                          <p className="text-caption" style={{ color: '#00D1B2' }}>
                            {subtitle}
                          </p>
                          <p className="text-caption mt-1" style={{ color: 'rgba(255,255,255,0.75)' }}>
                            {periodText}
                          </p>
                        </div>
                      </div>
                      <div className="p-5">
                        <p className="text-body">
                          {description}
                        </p>
                        {meta && (
                          <p className="text-caption mt-3" style={{ color: 'rgba(255,255,255,0.72)' }}>
                            {meta}
                          </p>
                        )}
                        {featured?.details?.length > 0 && (
                          <p className="text-caption mt-2" style={{ color: 'rgba(255,255,255,0.65)' }}>
                            {featured.details[0]}
                          </p>
                        )}
                        <p className="text-caption mt-2" style={{ color: 'rgba(0,209,178,0.85)' }}>
                          {lang === 'en' ? `Featured place: ${featured?.name || 'Unknown'}` : `代表建筑：${featured?.name_zh || featured?.name || '未知'}`}
                        </p>
                      </div>
                    </motion.article>
                  </Link>
                )})}
            </div>
          </div>
        </section>

        <section id="about" className="section-block wl-about-section" aria-labelledby="about-title">
          <div className="container-1200">
            <article className="panel p-8 md:p-10 wl-about-panel">
              <div className="wl-about-grid">
                <div>
                  <h2 id="about-title" className="title-section">{t.aboutTitle}</h2>
                  <p className="text-body mt-4 max-w-3xl">{t.aboutBody}</p>
                  <div className="wl-about-tags mt-6">
                    <span className="wl-about-tag">AI Vision</span>
                    <span className="wl-about-tag">Heritage Data</span>
                    <span className="wl-about-tag">Cultural Storytelling</span>
                  </div>
                </div>

                <div className="wl-about-highlights" aria-label="Platform highlights">
                  <article className="wl-about-stat-card">
                    <p className="wl-about-stat-value">5+</p>
                    <p className="wl-about-stat-label">Core Dynasty Tracks</p>
                  </article>
                  <article className="wl-about-stat-card">
                    <p className="wl-about-stat-value">24/7</p>
                    <p className="wl-about-stat-label">Interactive AI Guide</p>
                  </article>
                  <article className="wl-about-stat-card">
                    <p className="wl-about-stat-value">Vision + RAG</p>
                    <p className="wl-about-stat-label">Recognition and Knowledge Layer</p>
                  </article>
                </div>
              </div>
            </article>
          </div>
        </section>
      </main>

      <footer className="wl-home-footer">
        <div className="container-1200">
          <div className="panel p-8 md:p-10 wl-footer-panel wl-footer-redesign">
            <div className="wl-footer-topbar">
              <p className="wl-footer-top-copy">Built to make Chinese architectural heritage vivid, searchable, and explorable.</p>
              <Link href="/recognize" className="wl-footer-cta">
                {lang === 'en' ? 'Start Exploring' : '开始探索'}
                <ArrowRight size={15} />
              </Link>
            </div>

            <div className="grid-12 wl-footer-grid">
              <div className="col-span-12 md:col-span-4 wl-footer-col wl-footer-col-brand">
                <p className="title-card">WenxinLens</p>
                <p className="text-body mt-3 wl-footer-brand-copy">AI cultural interpretation platform for Chinese architectural heritage.</p>
              </div>

              <div className="col-span-6 md:col-span-2 wl-footer-col">
                <p className="wl-footer-heading">Explore</p>
                <ul className="wl-footer-links">
                  <li><Link href="/#features" className="wl-footer-link">Features</Link></li>
                  <li><Link href="/#architecture" className="wl-footer-link">Architecture</Link></li>
                  <li><Link href="/tour" className="wl-footer-link">Tour</Link></li>
                </ul>
              </div>

              <div className="col-span-6 md:col-span-2 wl-footer-col">
                <p className="wl-footer-heading">Resources</p>
                <ul className="wl-footer-links">
                  <li><Link href="/knowledge" className="wl-footer-link">Knowledge</Link></li>
                  <li><Link href="/chat" className="wl-footer-link">AI Guide</Link></li>
                  <li><Link href="/recognize" className="wl-footer-link">Recognition</Link></li>
                </ul>
              </div>

              <div className="col-span-6 md:col-span-2 wl-footer-col">
                <p className="wl-footer-heading">About</p>
                <ul className="wl-footer-links">
                  <li><Link href="/#about" className="wl-footer-link">Mission</Link></li>
                  <li><Link href="/#about" className="wl-footer-link">Design</Link></li>
                  <li><Link href="/#about" className="wl-footer-link">Team</Link></li>
                </ul>
              </div>

              <div className="col-span-12 sm:col-span-6 md:col-span-2 wl-footer-col wl-footer-col-contact">
                <p className="wl-footer-heading">Contact</p>
                <div className="wl-social-row wl-social-grid">
                  <a href="#" aria-label="GitHub" className="wl-social-btn"><Github size={18} /></a>
                  <a href="#" aria-label="Instagram" className="wl-social-btn"><Instagram size={18} /></a>
                  <a href="#" aria-label="YouTube" className="wl-social-btn"><Youtube size={18} /></a>
                  <a href="#" aria-label="Email" className="wl-social-btn"><Mail size={18} /></a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
