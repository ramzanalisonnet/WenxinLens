"""
Knowledge Base Initializer — seeds the vector store with curated
Chinese architecture knowledge for the RAG pipeline.

Run once:
    python -m rag.knowledge_base_init
"""
from __future__ import annotations

import asyncio
from loguru import logger

from rag.document_processor import DocumentProcessor
from rag.vector_store import VectorStore, Document


# ── Curated seed knowledge ─────────────────────────────────────
# Production: replace/augment with actual documents from datasets/

SEED_DOCUMENTS: list[dict] = [
    {
        "building": "Temple of Heaven",
        "dynasty": "Ming Dynasty",
        "language": "en",
        "source": "architecture_encyclopedia",
        "text": (
            "The Temple of Heaven (天坛, Tiāntán) is an imperial complex of religious buildings situated "
            "in southeastern Beijing, China. Built in 1420 during the reign of the Yongle Emperor of the "
            "Ming dynasty, it was used by the emperors of the Ming and Qing dynasties for annual ceremonies "
            "of prayer to Heaven for a good harvest. The temple is regarded as a masterpiece of architecture "
            "and landscape design and expresses the relationship between Earth and Heaven — the human world "
            "and the divine — which stands at the heart of Chinese cosmology."
        ),
    },
    {
        "building": "Temple of Heaven",
        "dynasty": "Ming Dynasty",
        "language": "en",
        "source": "architectural_analysis",
        "text": (
            "The Hall of Prayer for Good Harvests (祈年殿, Qínián Diàn) is a triple-gabled circular building "
            "built on three levels of marble stone base. The circular form symbolises Heaven, while the square "
            "form of the outer enclosure symbolises Earth. The blue tiles represent the sky. The construction "
            "is remarkable: the wooden structure uses no nails or cement — it is held together by interlocking "
            "bracketing systems (dougong). The 28 massive pillars support the roof: 4 central pillars (Dragon "
            "Well pillars) represent the four seasons, 12 inner pillars represent the twelve months, and 12 "
            "outer pillars represent the twelve traditional Chinese hours."
        ),
    },
    {
        "building": "Temple of Heaven",
        "dynasty": "Ming Dynasty",
        "language": "zh",
        "source": "chinese_architecture_encyclopedia",
        "text": (
            "天坛是中国明清两代皇帝祭祀天地的场所，位于北京南部。天坛建于明朝永乐十八年（1420年），"
            "由明成祖朱棣下令修建。天坛的建筑布局体现了中国传统的「天圆地方」理念，"
            "圆形的祈年殿象征天，方形的外围代表地。祈年殿高38.2米，直径24.2米，"
            "采用三重攒尖顶设计，覆以蓝色琉璃瓦，象征蓝天。天坛是中国现存最大的古代祭祀性建筑群，"
            "1998年被列为世界文化遗产。"
        ),
    },
    {
        "building": "Forbidden City",
        "dynasty": "Ming Dynasty",
        "language": "en",
        "source": "world_heritage_guide",
        "text": (
            "The Forbidden City (故宫, Gùgōng), also known as the Palace Museum, was built between 1406 and 1420 "
            "and served as the imperial palace for 24 emperors of both the Ming and Qing dynasties. "
            "The complex consists of 980 surviving buildings with 8,886 bays of rooms. "
            "The palace is an exemplary example of traditional Chinese palatial architecture and has influenced "
            "cultural and architectural developments across East Asia and Southeast Asia. "
            "The name 'Forbidden City' comes from the fact that no one could enter or leave without the "
            "emperor's permission. The outer wall is 7.9 metres high and surrounded by a 52-metre wide moat."
        ),
    },
    {
        "building": "Forbidden City",
        "dynasty": "Ming Dynasty",
        "language": "en",
        "source": "architectural_symbolism",
        "text": (
            "The architectural symbolism of the Forbidden City is extensive. Yellow, the color of the Emperor, "
            "dominates the complex — roofs are covered with yellow glazed tiles. The number nine appears "
            "throughout: gates have nine rows of nine studs, considered the most auspicious number. "
            "The Hall of Supreme Harmony (太和殿, Tàihé Diàn) is the largest surviving wooden structure in China. "
            "Its three-tiered marble terrace (三台, Sāntái) symbolize the three sacred mountains of Chinese mythology. "
            "Dragons, symbols of imperial power, appear on nearly every decorated surface."
        ),
    },
    {
        "building": "Giant Wild Goose Pagoda",
        "dynasty": "Tang Dynasty",
        "language": "en",
        "source": "buddhist_architecture_guide",
        "text": (
            "The Giant Wild Goose Pagoda (大雁塔, Dàyàn Tǎ) is a Buddhist pagoda built in 652 CE during the "
            "reign of Emperor Gaozong of the Tang dynasty, located in Yanta District, Xi'an. It was built to "
            "house Buddhist scriptures and relics brought to China from India by the Buddhist monk Xuanzang, "
            "who traveled to India to retrieve them — a journey immortalized in the classic novel Journey to the West. "
            "The pagoda has seven storeys and stands 64.5 metres tall. It is constructed of rammed earth faced "
            "with brick, a defining characteristic of Tang period pagoda architecture."
        ),
    },
    {
        "building": "Summer Palace",
        "dynasty": "Qing Dynasty",
        "language": "en",
        "source": "imperial_gardens_guide",
        "text": (
            "The Summer Palace (颐和园, Yíhé Yuán) is an ensemble of lakes, gardens, and palaces in Beijing, "
            "China. It was an imperial garden in the Qing dynasty. Dominated by Longevity Hill and Kunming Lake, "
            "it covers an expanse of 2.9 square kilometres, three quarters of which is water. "
            "Originating from the Garden of Clear Ripples built in 1750, it was later rebuilt during the reign "
            "of Emperor Guangxu and renamed the Summer Palace. "
            "The Long Corridor (长廊) stretching 728 metres is the world's longest painted corridor, "
            "with over 14,000 paintings depicting scenes from Chinese history, mythology and nature."
        ),
    },
    {
        "building": "Zhaozhou Bridge",
        "dynasty": "Sui Dynasty",
        "language": "en",
        "source": "engineering_heritage",
        "text": (
            "Zhaozhou Bridge (赵州桥, Zhàozhōu Qiáo), also known as Anji Bridge (安济桥), is the world's oldest "
            "open-spandrel stone segmental arch bridge, built in the Sui dynasty (595–605 CE) by master craftsman "
            "Li Chun. The bridge spans 50.82 metres with a rise of only 7.23 metres — a remarkably flat arch. "
            "The innovative open-spandrel design employed two smaller arches in the spandrels to reduce weight "
            "and allow floodwaters to flow through, a concept not used in European bridge engineering until "
            "the 14th century. The bridge has survived at least eight major floods, ten wars, and multiple earthquakes."
        ),
    },
    {
        "building": "general",
        "dynasty": "various",
        "language": "en",
        "source": "chinese_architecture_principles",
        "text": (
            "Chinese architecture (中国建筑) is characterized by several key principles: "
            "1) Bilateral symmetry — buildings are arranged symmetrically along a central axis. "
            "2) Enclosed spaces — courtyards (四合院, sìhéyuàn) surround the central buildings. "
            "3) Hierarchical arrangement — the importance of a building is signified by its size and position. "
            "4) The dougong (斗拱) bracketing system — interlocking wooden brackets that distribute the weight "
            "of the roof to the columns without the use of nails, representing extraordinary engineering. "
            "5) Upturned eaves — the curved roofline (飞檐, fēiyán) symbolizes the flight of birds and "
            "elegance of nature. 6) Color symbolism — yellow for emperor, red for good fortune, green for youth."
        ),
    },
    {
        "building": "Hakka Tulou",
        "dynasty": "Ming/Qing Dynasty",
        "language": "en",
        "source": "folk_architecture_guide",
        "text": (
            "The Fujian Tulou (福建土楼) are rural cluster buildings of the Hakka and other peoples in "
            "Fujian Province, China. Built between the 12th and 20th centuries during the Ming and Qing dynasties, "
            "these massive earthen structures are typically circular or square and can house up to 800 people. "
            "The thick rammed-earth walls (up to 6 metres thick) provide thermal insulation and defense. "
            "Each tulou contains wells, mills, and other facilities, functioning as a self-sufficient community. "
            "In 2008, 46 Fujian Tulou were inscribed on the UNESCO World Heritage List."
        ),
    },
]


async def initialize_knowledge_base(vector_store: VectorStore) -> None:
    """Seed the vector store with curated architecture knowledge."""
    processor = DocumentProcessor()
    all_docs: list[Document] = []

    for entry in SEED_DOCUMENTS:
        docs = processor.process_text(
            text=entry["text"],
            source=entry["source"],
            building=entry["building"],
            dynasty=entry["dynasty"],
            language=entry["language"],
        )
        all_docs.extend(docs)

    logger.info(f"Seeding vector store with {len(all_docs)} document chunks …")
    count = await vector_store.upsert(all_docs)
    logger.info(f"Knowledge base initialized: {count} chunks stored")


if __name__ == "__main__":
    async def main():
        vs = VectorStore()
        await vs.initialize()
        await initialize_knowledge_base(vs)

    asyncio.run(main())
