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
import { motion, useReducedMotion } from 'framer-motion'
import { Navbar } from '../components/Navbar'

type Lang = 'en' | 'zh'

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

const dynasties = [
  {
    eraEn: 'Tang Dynasty',
    eraZh: '唐代',
    descriptionEn: 'Monumental timber halls, axial planning, and imperial ceremonial architecture reached new maturity.',
    descriptionZh: '木构大殿与中轴礼制空间达到高峰。',
    image: '/images/timeline-tang.svg',
  },
  {
    eraEn: 'Song Dynasty',
    eraZh: '宋代',
    descriptionEn: 'Refined proportions and modular systems highlighted technical precision and scholarly aesthetics.',
    descriptionZh: '比例精炼、营造法式体系化，凸显工艺与文人审美。',
    image: '/images/timeline-song.svg',
  },
  {
    eraEn: 'Yuan Dynasty',
    eraZh: '元代',
    descriptionEn: 'Cross-regional influences shaped spatial composition, religious architecture, and urban identity.',
    descriptionZh: '多元文化影响下，宗教建筑与城市空间呈现新融合。',
    image: '/images/timeline-yuan.svg',
  },
  {
    eraEn: 'Ming Dynasty',
    eraZh: '明代',
    descriptionEn: 'Large palace compounds and ritual symbolism expanded with stronger construction standards.',
    descriptionZh: '宫殿群规模扩大，礼制符号与营建规范更加明确。',
    image: '/images/timeline-ming.svg',
  },
  {
    eraEn: 'Qing Dynasty',
    eraZh: '清代',
    descriptionEn: 'Imperial architecture emphasized decorative richness, layered courtyards, and cultural continuity.',
    descriptionZh: '装饰层次更丰富，院落系统强化，延续皇家建筑传统。',
    image: '/images/timeline-qing.svg',
  },
]

export default function HomePage() {
  const reduceMotion = useReducedMotion()
  const [lang, setLang] = useState<Lang>('en')

  useEffect(() => {
    const stored = window.localStorage.getItem('wenxinlens-lang')
    if (stored === 'en' || stored === 'zh') {
      setLang(stored)
    }

    const onLangChange = (event: Event) => {
      const custom = event as CustomEvent<Lang>
      if (custom.detail === 'en' || custom.detail === 'zh') {
        setLang(custom.detail)
      }
    }

    window.addEventListener('wenxinlens-lang-change', onLangChange as EventListener)
    return () => window.removeEventListener('wenxinlens-lang-change', onLangChange as EventListener)
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
    learnMore: lang === 'en' ? 'Learn More' : '了解更多',
    openFeature: lang === 'en' ? 'Open Feature' : '进入功能',
  }

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
              {dynasties.map((item, idx) => (
                <motion.article
                  key={item.eraEn}
                  className="col-span-12 md:col-span-6 xl:col-span-4 panel overflow-hidden hover-rise"
                  initial={{ opacity: 0, y: 14 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: reduceMotion ? 0 : idx * 0.05, duration: reduceMotion ? 0.01 : 0.42 }}
                >
                  <div className="relative">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={item.image} alt={item.eraEn} className="w-full h-48 object-cover" />
                    <div
                      className="absolute inset-0"
                      style={{ background: 'linear-gradient(180deg, rgba(11,15,26,0.05), rgba(11,15,26,0.72))' }}
                    />
                    <div className="absolute left-4 bottom-4 right-4">
                      <p className="text-caption" style={{ color: '#00D1B2' }}>
                        {item.eraEn} ({item.eraZh})
                      </p>
                    </div>
                  </div>
                  <div className="p-5">
                    <p className="text-body">
                      {lang === 'en' ? item.descriptionEn : item.descriptionZh}
                    </p>
                    <Link href="/knowledge" className="btn btn-secondary mt-5">
                      {t.learnMore}
                    </Link>
                  </div>
                </motion.article>
              ))}
            </div>
          </div>
        </section>

        <section className="section-block" aria-labelledby="recognition-title">
          <div className="container-1200">
            <div className="grid-12 items-center">
              <article className="col-span-12 lg:col-span-6 panel p-8">
                <h2 id="recognition-title" className="title-section">
                  AI Recognition (建筑识别)
                </h2>
                <p className="text-body mt-4">
                  {lang === 'en'
                    ? 'Capture a building image and get instant insights on dynasty, structure, and symbolic elements.'
                    : '拍摄建筑图像后，即时获得朝代、结构与文化符号解析。'}
                </p>
                <Link href="/recognize" className="btn btn-primary mt-6">
                  {lang === 'en' ? 'Try AI Recognition' : '体验建筑识别'}
                </Link>
              </article>

              <div className="col-span-12 lg:col-span-6">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src="/images/section-recognition.svg"
                  alt="Temple of Heaven"
                  className="card-image"
                />
              </div>
            </div>
          </div>
        </section>

        <section className="section-block" aria-labelledby="knowledge-title">
          <div className="container-1200">
            <div className="grid-12 items-center">
              <div className="col-span-12 lg:col-span-6 order-2 lg:order-1">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src="/images/section-knowledge.svg"
                  alt="Ancient Chinese timber architecture"
                  className="card-image"
                />
              </div>

              <article className="col-span-12 lg:col-span-6 panel p-8 order-1 lg:order-2">
                <h2 id="knowledge-title" className="title-section">
                  Knowledge Base (知识库)
                </h2>
                <p className="text-body mt-4">
                  {lang === 'en'
                    ? 'Explore structured cultural data across dynasties, building typologies, and historical narratives.'
                    : '探索跨朝代、建筑类型与历史叙事的结构化文化知识数据。'}
                </p>
                <Link href="/knowledge" className="btn btn-secondary mt-6">
                  {lang === 'en' ? 'Open Knowledge Base' : '打开知识库'}
                </Link>
              </article>
            </div>
          </div>
        </section>

        <section id="about" className="section-block" aria-labelledby="about-title">
          <div className="container-1200">
            <article className="panel p-8 md:p-10">
              <h2 id="about-title" className="title-section">{t.aboutTitle}</h2>
              <p className="text-body mt-4 max-w-3xl">{t.aboutBody}</p>
            </article>
          </div>
        </section>
      </main>

      <footer className="section-block" style={{ paddingTop: '64px', paddingBottom: '48px' }}>
        <div className="container-1200">
          <div className="panel p-8">
            <div className="grid-12">
              <div className="col-span-12 md:col-span-4">
                <p className="title-card">WenxinLens</p>
                <p className="text-body mt-3">AI cultural interpretation platform for Chinese architectural heritage.</p>
              </div>

              <div className="col-span-6 md:col-span-2">
                <p className="text-caption" style={{ color: '#E6EAF2' }}>Explore</p>
                <ul className="mt-3 space-y-2 text-caption">
                  <li><Link href="/#features">Features</Link></li>
                  <li><Link href="/#architecture">Architecture</Link></li>
                  <li><Link href="/tour">Tour</Link></li>
                </ul>
              </div>

              <div className="col-span-6 md:col-span-2">
                <p className="text-caption" style={{ color: '#E6EAF2' }}>Resources</p>
                <ul className="mt-3 space-y-2 text-caption">
                  <li><Link href="/knowledge">Knowledge</Link></li>
                  <li><Link href="/chat">AI Guide</Link></li>
                  <li><Link href="/recognize">Recognition</Link></li>
                </ul>
              </div>

              <div className="col-span-6 md:col-span-2">
                <p className="text-caption" style={{ color: '#E6EAF2' }}>About</p>
                <ul className="mt-3 space-y-2 text-caption">
                  <li><Link href="/#about">Mission</Link></li>
                  <li><Link href="/#about">Design</Link></li>
                  <li><Link href="/#about">Team</Link></li>
                </ul>
              </div>

              <div className="col-span-6 md:col-span-2">
                <p className="text-caption" style={{ color: '#E6EAF2' }}>Contact</p>
                <div className="mt-3 flex items-center justify-start gap-3">
                  <a href="#" aria-label="GitHub" className="btn btn-secondary p-2"><Github size={16} /></a>
                  <a href="#" aria-label="Instagram" className="btn btn-secondary p-2"><Instagram size={16} /></a>
                  <a href="#" aria-label="YouTube" className="btn btn-secondary p-2"><Youtube size={16} /></a>
                  <a href="#" aria-label="Email" className="btn btn-secondary p-2"><Mail size={16} /></a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
