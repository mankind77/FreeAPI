"""
Seed script: populate the database with initial categories and real free APIs.
Run once: python seed.py
"""

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session, init_db
from models import Category, ApiEntry

SEED_CATEGORIES = [
    {"name": "天气地理", "slug": "weather-geo", "icon": "cloud-sun", "description": "天气预报、空气质量、地理编码、地图服务", "sort_order": 1},
    {"name": "新闻媒体", "slug": "news-media", "icon": "newspaper", "description": "新闻资讯、媒体内容、舆情数据", "sort_order": 2},
    {"name": "人工智能", "slug": "ai-ml", "icon": "brain", "description": "大语言模型、图像识别、语音合成、NLP", "sort_order": 3},
    {"name": "金融数据", "slug": "finance", "icon": "chart-line", "description": "股票行情、汇率转换、加密货币、经济数据", "sort_order": 4},
    {"name": "社交平台", "slug": "social", "icon": "users", "description": "社交媒体、即时通讯、内容分享", "sort_order": 5},
    {"name": "开发工具", "slug": "dev-tools", "icon": "code", "description": "代码托管、持续集成、API 测试、监控、趣味数据", "sort_order": 6},
]

SEED_APIS = [
    # ===== 天气地理 (10 APIs) =====
    {"category_slug": "weather-geo", "name": "OpenWeatherMap", "provider": "OpenWeather Ltd",
     "url": "https://openweathermap.org/api", "description": "全球天气数据 API，提供当前天气、5天/3小时预报、历史天气、紫外线指数、空气污染等。免费套餐每天 1000 次调用，支持全球 20 万+ 城市。",
     "tags": "天气,免费,REST,JSON", "is_free": True, "auth_type": "api_key",
     "request_example": 'GET https://api.openweathermap.org/data/2.5/weather?q=Beijing&appid=YOUR_API_KEY&lang=zh_cn'},
    {"category_slug": "weather-geo", "name": "和风天气", "provider": "和风互联科技",
     "url": "https://dev.qweather.com/", "description": "中国天气数据最全的 API。提供实时天气、7/15/30天预报、分钟级降水、空气质量、灾害预警、太阳辐射等。免费版每天 1000 次，国内城市覆盖极好，中文文档完善。",
     "tags": "天气,中国,免费,REST,空气质量", "is_free": True, "auth_type": "api_key",
     "request_example": 'GET https://devapi.qweather.com/v7/weather/now?location=101010100&key=YOUR_KEY'},
    {"category_slug": "weather-geo", "name": "Open-Meteo", "provider": "Open-Meteo",
     "url": "https://open-meteo.com/", "description": "完全免费、无需 API Key 的天气 API。提供全球天气预报、历史天气、海洋数据、空气质量等。基于 NWP 模型，分辨率可达 1km，完全开源。",
     "tags": "天气,免费,无认证,开源,全球", "is_free": True, "auth_type": "no_auth",
     "request_example": 'GET https://api.open-meteo.com/v1/forecast?latitude=39.9042&longitude=116.4074&current_weather=true'},
    {"category_slug": "weather-geo", "name": "WeatherAPI.com", "provider": "WeatherAPI.com",
     "url": "https://www.weatherapi.com/", "description": "轻量级全球天气 API，提供实时天气、预报、历史、天文、时区、IP 定位等。免费版每月 100 万次，支持 JSON/XML，响应速度极快。",
     "tags": "天气,全球,免费,实时,高配额", "is_free": True, "auth_type": "api_key",
     "request_example": 'GET https://api.weatherapi.com/v1/current.json?key=YOUR_KEY&q=Beijing&lang=zh'},
    {"category_slug": "weather-geo", "name": "OpenAQ", "provider": "OpenAQ",
     "url": "https://docs.openaq.org/", "description": "全球空气质量开放数据 API。提供 PM2.5、PM10、NO2、SO2 等污染物实时和历史数据，覆盖 100+ 国家。完全免费开源，无需 API Key。",
     "tags": "空气质量,全球,免费,无认证,开源", "is_free": True, "auth_type": "no_auth",
     "request_example": 'GET https://api.openaq.org/v2/latest?city=Beijing'},
    {"category_slug": "weather-geo", "name": "Nominatim", "provider": "OpenStreetMap Foundation",
     "url": "https://nominatim.org/release-docs/latest/api/Overview/", "description": "免费地理编码 API，地址与经纬度互相转换。基于 OpenStreetMap 数据，全球覆盖，无认证即可使用（有频率限制 1 req/s）。",
     "tags": "地理编码,地图,免费,无认证,全球", "is_free": True, "auth_type": "no_auth",
     "request_example": 'GET https://nominatim.openstreetmap.org/search?q=Beijing&format=json&limit=5'},
    {"category_slug": "weather-geo", "name": "高德地图 Web API", "provider": "高德软件",
     "url": "https://lbs.amap.com/api/webservice/summary/", "description": "国内最好用的地图 API。地理编码、逆地理编码、路径规划、IP 定位、静态地图、行政区划查询等。个人开发者每日免费 5000 次，覆盖率全国。",
     "tags": "地图,中国,地理编码,路径规划,免费", "is_free": True, "auth_type": "api_key",
     "request_example": 'GET https://restapi.amap.com/v3/geocode/geo?key=YOUR_KEY&address=北京市朝阳区'},
    {"category_slug": "weather-geo", "name": "USGS Earthquake API", "provider": "USGS",
     "url": "https://earthquake.usgs.gov/fdsnws/event/1/", "description": "美国地质调查局地震数据 API。提供全球实时地震监测数据，包含震级、位置、深度、时间等。完全免费无认证，适合科学研究和数据可视化。",
     "tags": "地震,地理,免费,无认证,科学,全球", "is_free": True, "auth_type": "no_auth",
     "request_example": 'GET https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2024-01-01&minmagnitude=5'},
    {"category_slug": "weather-geo", "name": "AQICN", "provider": "AQICN.org",
     "url": "https://aqicn.org/api/", "description": "全球空气质量指数 API。提供中国、美国、欧洲等区域 AQI、PM2.5、PM10、臭氧等数据。免费版有频率限制，支持 100+ 国家 10000+ 站点。",
     "tags": "空气质量,全球,免费,中国,健康", "is_free": True, "auth_type": "api_key",
     "request_example": 'GET https://api.waqi.info/feed/Beijing/?token=YOUR_TOKEN'},
    {"category_slug": "weather-geo", "name": "Mapbox", "provider": "Mapbox Inc.",
     "url": "https://docs.mapbox.com/api/", "description": "高性能地图 API，提供矢量瓦片、地理编码、路线规划、等时圈等。免费版每月 50000 次地图加载，适合高质量 Web/移动端地图应用。",
     "tags": "地图,矢量瓦片,免费,全球,路径规划", "is_free": True, "auth_type": "api_key",
     "request_example": 'GET https://api.mapbox.com/geocoding/v5/mapbox.places/Beijing.json?access_token=YOUR_TOKEN'},

    # ===== 新闻媒体 (10 APIs) =====
    {"category_slug": "news-media", "name": "NewsAPI", "provider": "NewsAPI.org",
     "url": "https://newsapi.org/", "description": "全球新闻聚合 API，覆盖 80,000+ 新闻源。支持按关键词、来源、国家、语言、日期范围搜索。免费版每天 100 次，适合原型开发。",
     "tags": "新闻,全球,搜索,REST,英文", "is_free": True, "auth_type": "api_key",
     "request_example": 'GET https://newsapi.org/v2/everything?q=china&apiKey=YOUR_KEY&language=zh'},
    {"category_slug": "news-media", "name": "GNews API", "provider": "GNews",
     "url": "https://gnews.io/", "description": "简洁的 Google 新闻 API。支持按关键词、国家、语言、来源筛选，中文支持良好。免费版每天 100 次，返回 JSON 格式，适合新闻聚合器。",
     "tags": "新闻,Google,搜索,REST,中文", "is_free": True, "auth_type": "api_key",
     "request_example": 'GET https://gnews.io/api/v4/search?q=科技&lang=zh&country=cn&token=YOUR_TOKEN'},
    {"category_slug": "news-media", "name": "The Guardian API", "provider": "The Guardian",
     "url": "https://open-platform.theguardian.com/", "description": "英国卫报开放平台 API。可搜索和获取卫报自 1999 年以来的全部文章、标签、分类等。免费注册即用，适合新闻分析和内容聚合。",
     "tags": "新闻,英国,英文,免费,内容,开放数据", "is_free": True, "auth_type": "api_key",
     "request_example": 'GET https://content.guardianapis.com/search?q=technology&api-key=YOUR_KEY'},
    {"category_slug": "news-media", "name": "今日热榜 API", "provider": "今日热榜",
     "url": "https://api-hot.imsyy.top/", "description": "中文互联网热榜聚合 API，汇集微博热搜、知乎热榜、百度热搜、抖音热点、36氪、B站等主流平台榜单。非官方，免费使用。",
     "tags": "热榜,中国,微博,知乎,百度,免费", "is_free": True, "auth_type": "no_auth",
     "request_example": 'GET https://api-hot.imsyy.top/weibo?cache=true'},
    {"category_slug": "news-media", "name": "Hacker News API", "provider": "Y Combinator",
     "url": "https://github.com/HackerNews/API", "description": "Hacker News 官方 API，获取热门科技新闻、Show HN、Ask HN 等内容。完全免费无认证，实时数据，Firebase 实时数据库驱动。",
     "tags": "科技,新闻,英文,免费,无认证", "is_free": True, "auth_type": "no_auth",
     "request_example": 'GET https://hacker-news.firebaseio.com/v0/topstories.json'},
    {"category_slug": "news-media", "name": "Spaceflight News API", "provider": "Spaceflight News",
     "url": "https://spaceflightnewsapi.net/", "description": "航天新闻 API，提供最新火箭发射、太空探索、航天任务等新闻文章和博客。完全免费无认证，适合科技爱好者和新闻聚合。",
     "tags": "航天,科技,新闻,英文,免费,无认证", "is_free": True, "auth_type": "no_auth",
     "request_example": 'GET https://api.spaceflightnewsapi.net/v4/articles/?limit=10'},
    {"category_slug": "news-media", "name": "澎湃热榜 API", "provider": "澎湃新闻（非官方）",
     "url": "https://github.com/justjavac/weibo-trending-hot-search", "description": "澎湃新闻、微博热搜、知乎热榜等中文平台热点数据聚合。社区维护的非官方接口，数据延迟约 5-10 分钟，适合舆情监控和学习项目。",
     "tags": "热榜,中国,微博,知乎,澎湃,免费", "is_free": True, "auth_type": "no_auth",
     "request_example": 'GET https://tenapi.cn/v2/weibohot'},
    {"category_slug": "news-media", "name": "Reddit API", "provider": "Reddit Inc.",
     "url": "https://www.reddit.com/dev/api/", "description": "Reddit 内容 API，获取热门帖子、子版块信息、评论、用户数据等。免费无需审核即可使用（有频率限制），适合内容聚合和舆情分析。",
     "tags": "Reddit,社交,新闻,免费,英文,全球", "is_free": True, "auth_type": "oauth",
     "request_example": 'GET https://www.reddit.com/r/news/hot.json?limit=10'},
    {"category_slug": "news-media", "name": "Currents API", "provider": "Currents API",
     "url": "https://currentsapi.services/", "description": "新闻聚合 API，提供全球最新新闻、历史新闻搜索、多语言支持。免费版每小时 600 次请求，支持关键词、语言、类别筛选。",
     "tags": "新闻,全球,搜索,多语言,免费", "is_free": True, "auth_type": "api_key",
     "request_example": 'GET https://api.currentsapi.services/v1/latest-news?apiKey=YOUR_KEY&language=zh'},
    {"category_slug": "news-media", "name": "NPR API", "provider": "NPR",
     "url": "https://www.npr.org/api/", "description": "美国国家公共广播电台 API。提供 NPR 文章、节目、音频片段、站台信息等。适合音频内容聚合和新闻应用开发。",
     "tags": "新闻,音频,英文,免费,广播", "is_free": True, "auth_type": "api_key",
     "request_example": 'GET https://api.npr.org/query?apiKey=YOUR_KEY&query=technology&output=JSON'},

    # ===== 人工智能 (12 APIs) =====
    {"category_slug": "ai-ml", "name": "OpenAI API", "provider": "OpenAI",
     "url": "https://platform.openai.com/docs/api-reference", "description": "GPT-4o、GPT-4o-mini 等大语言模型 API。提供对话补全、嵌入向量、图像生成、语音转文字、文字转语音。新用户有免费额度。",
     "tags": "大语言模型,ChatGPT,AI,GPT,付费有免费额度", "is_free": True, "auth_type": "api_key",
     "request_example": 'POST https://api.openai.com/v1/chat/completions\nBody: {"model":"gpt-4o-mini","messages":[{"role":"user","content":"Hello"}]}'},
    {"category_slug": "ai-ml", "name": "Google Gemini API", "provider": "Google",
     "url": "https://ai.google.dev/gemini-api/docs", "description": "Google Gemini 大语言模型 API。支持文本、图像、音频、视频多模态理解。免费版每分钟 15 次请求，中文能力优秀。",
     "tags": "大语言模型,AI,Google,多模态,免费", "is_free": True, "auth_type": "api_key",
     "request_example": 'POST https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=YOUR_KEY'},
    {"category_slug": "ai-ml", "name": "Hugging Face Inference API", "provider": "Hugging Face",
     "url": "https://huggingface.co/docs/api-inference/", "description": "业界最大模型库的免费推理 API。文本生成、图像分类、目标检测、翻译、摘要、语音识别等数千个模型，开源社区驱动。",
     "tags": "大语言模型,AI,开源,推理,免费", "is_free": True, "auth_type": "api_key",
     "request_example": 'POST https://api-inference.huggingface.co/models/gpt2\nHeaders: Authorization: Bearer YOUR_TOKEN'},
    {"category_slug": "ai-ml", "name": "Cloudflare Workers AI", "provider": "Cloudflare",
     "url": "https://developers.cloudflare.com/workers-ai/", "description": "Cloudflare 的 AI 推理平台，提供 Llama、Mistral、Stable Diffusion 等开源模型。每天 10,000 次免费调用，无需信用卡。",
     "tags": "大语言模型,AI,免费,推理,Llama,图像生成", "is_free": True, "auth_type": "api_key",
     "request_example": 'POST https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/@cf/meta/llama-3-8b-instruct'},
    {"category_slug": "ai-ml", "name": "DeepSeek API", "provider": "DeepSeek",
     "url": "https://platform.deepseek.com/api-docs/", "description": "国产顶级大模型 API，提供 DeepSeek-V3、DeepSeek-R1。价格极低（约为 GPT-4 的 1/50），中文理解能力极强，新用户赠送免费额度。",
     "tags": "大语言模型,AI,国产,DeepSeek,中文,付费有免费额度", "is_free": True, "auth_type": "api_key",
     "request_example": 'POST https://api.deepseek.com/chat/completions\nBody: {"model":"deepseek-chat","messages":[{"role":"user","content":"你好"}]}'},
    {"category_slug": "ai-ml", "name": "Groq API", "provider": "Groq Inc.",
     "url": "https://console.groq.com/docs/api-reference", "description": "超高速大模型推理 API，提供 Llama、Mixtral、Gemma 等开源模型。免费版每分钟 30 次请求，推理速度全球领先（LPU 芯片加速）。",
     "tags": "大语言模型,AI,免费,高速,Llama", "is_free": True, "auth_type": "api_key",
     "request_example": 'POST https://api.groq.com/openai/v1/chat/completions\nBody: {"model":"llama-3.3-70b","messages":[{"role":"user","content":"Hello"}]}'},
    {"category_slug": "ai-ml", "name": "智谱 AI (GLM) API", "provider": "智谱华章",
     "url": "https://open.bigmodel.cn/dev/api", "description": "智谱 GLM-4 系列大模型 API。对话补全、文生图、知识库、代码解释器。新用户赠送大量免费 tokens，中文效果优秀。",
     "tags": "大语言模型,AI,国产,GLM,中文,免费额度", "is_free": True, "auth_type": "api_key",
     "request_example": 'POST https://open.bigmodel.cn/api/paas/v4/chat/completions\nHeaders: Authorization: Bearer YOUR_TOKEN'},
    {"category_slug": "ai-ml", "name": "Mistral AI API", "provider": "Mistral AI",
     "url": "https://docs.mistral.ai/api/", "description": "法国 AI 公司 Mistral 的大模型 API。提供 Mistral Large、Small、Nemo 等模型。免费套餐有限但推理效果好，支持多语言。",
     "tags": "大语言模型,AI,Mistral,欧洲,免费额度", "is_free": True, "auth_type": "api_key",
     "request_example": 'POST https://api.mistral.ai/v1/chat/completions\nBody: {"model":"mistral-small","messages":[{"role":"user","content":"Hello"}]}'},
    {"category_slug": "ai-ml", "name": "Replicate", "provider": "Replicate Inc.",
     "url": "https://replicate.com/docs", "description": "模型云托管 API 平台。可运行 Stable Diffusion、Llama、Whisper、ESRGAN 等数千个社区模型。按使用量付费，有免费试用额度。",
     "tags": "AI,模型平台,图像,语音,推理", "is_free": True, "auth_type": "api_key",
     "request_example": 'POST https://api.replicate.com/v1/predictions\nBody: {"version":"model-id","input":{"prompt":"a cat"}}'},
    {"category_slug": "ai-ml", "name": "ElevenLabs API", "provider": "ElevenLabs",
     "url": "https://elevenlabs.io/docs/api-reference", "description": "顶级文字转语音 (TTS) API。提供超逼真 AI 语音合成，支持 29 种语言、多种音色、语音克隆。免费版每月 10,000 字符。",
     "tags": "TTS,语音合成,AI,多语言,免费", "is_free": True, "auth_type": "api_key",
     "request_example": 'POST https://api.elevenlabs.io/v1/text-to-speech/VOICE_ID\nBody: {"text":"Hello world","model_id":"eleven_multilingual_v2"}'},
    {"category_slug": "ai-ml", "name": "AssemblyAI", "provider": "AssemblyAI",
     "url": "https://www.assemblyai.com/docs/", "description": "语音转文字 API，提供实时/异步语音识别、说话人分割、情感分析、章节摘要等。免费版每月 100 小时，准确率极高。",
     "tags": "语音识别,STT,AI,转录,免费", "is_free": True, "auth_type": "api_key",
     "request_example": 'POST https://api.assemblyai.com/v2/transcript\nBody: {"audio_url":"https://example.com/audio.mp3"}'},
    {"category_slug": "ai-ml", "name": "Cohere API", "provider": "Cohere",
     "url": "https://docs.cohere.com/reference/about", "description": "Cohere 企业级 AI API。提供文本生成、语义搜索、嵌入向量、重排序、多语言分类等。免费版每月 1000 次，嵌入质量业界领先。",
     "tags": "大语言模型,AI,嵌入,搜索,免费", "is_free": True, "auth_type": "api_key",
     "request_example": 'POST https://api.cohere.ai/v1/generate\nBody: {"model":"command","prompt":"Hello world"}'},

    # ===== 金融数据 (10 APIs) =====
    {"category_slug": "finance", "name": "Alpha Vantage", "provider": "Alpha Vantage Inc.",
     "url": "https://www.alphavantage.co/", "description": "免费股票、外汇、加密货币数据 API。提供实时行情、50+ 技术指标、公司基本面、经济指标等。免费版每天 25 次请求。",
     "tags": "股票,外汇,加密货币,技术指标,免费,REST", "is_free": True, "auth_type": "api_key",
     "request_example": 'GET https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&apikey=YOUR_KEY'},
    {"category_slug": "finance", "name": "ExchangeRate-API", "provider": "ExchangeRate-API",
     "url": "https://www.exchangerate-api.com/", "description": "汇率转换 API，支持 161 种法定货币。免费版每月 1500 次，每日自动更新汇率。数据来源于各国央行，准确可靠。",
     "tags": "汇率,货币,金融,免费,REST", "is_free": True, "auth_type": "api_key",
     "request_example": 'GET https://v6.exchangerate-api.com/v6/YOUR_KEY/latest/CNY'},
    {"category_slug": "finance", "name": "CoinGecko API", "provider": "CoinGecko",
     "url": "https://www.coingecko.com/api/documentation", "description": "加密货币数据 API，价格、市值、交易量、历史数据等。完全免费无需认证（有频率限制），覆盖 10,000+ 币种、500+ 交易所。",
     "tags": "加密货币,区块链,免费,无认证,金融", "is_free": True, "auth_type": "no_auth",
     "request_example": 'GET https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=cny'},
    {"category_slug": "finance", "name": "Tushare", "provider": "Tushare",
     "url": "https://tushare.pro/", "description": "中国最好的开源金融数据接口。A 股行情、财务数据、指数、基金、期货、债券、宏观经济等。免费注册积分可满足日常需求。",
     "tags": "A股,中国,金融,开源,股票,期货", "is_free": True, "auth_type": "api_key",
     "request_example": 'import tushare as ts\npro = ts.pro_api("YOUR_TOKEN")\ndf = pro.daily(ts_code="000001.SZ")'},
    {"category_slug": "finance", "name": "Yahoo Finance API", "provider": "Yahoo（非官方）",
     "url": "https://github.com/ranaroussi/yfinance", "description": "Yahoo Finance 的 Python 库，股票历史行情、基本面、分红、财报、期权链等。无需 API Key，适合数据分析和量化研究。",
     "tags": "股票,免费,Python,数据分析,全球", "is_free": True, "auth_type": "no_auth",
     "request_example": 'import yfinance as yf\nmsft = yf.Ticker("MSFT")\nhist = msft.history(period="1mo")'},
    {"category_slug": "finance", "name": "Finnhub", "provider": "Finnhub",
     "url": "https://finnhub.io/docs/api", "description": "实时股票数据 API。提供实时报价、蜡烛图、公司新闻、内幕交易、SEC 文件、财报日历等。免费版每分钟 60 次，覆盖美股和全球市场。",
     "tags": "股票,实时,新闻,美股,免费", "is_free": True, "auth_type": "api_key",
     "request_example": 'GET https://finnhub.io/api/v1/quote?symbol=AAPL&token=YOUR_TOKEN'},
    {"category_slug": "finance", "name": "Twelve Data", "provider": "Twelve Data",
     "url": "https://twelvedata.com/docs", "description": "高质量金融数据 API。提供实时/历史股票、外汇、加密货币、技术指标、ETF、指数等。免费版每天 800 次，WebSocket 实时推送。",
     "tags": "股票,实时,外汇,WebSocket,免费", "is_free": True, "auth_type": "api_key",
     "request_example": 'GET https://api.twelvedata.com/time_series?symbol=AAPL&interval=1day&apikey=YOUR_KEY'},
    {"category_slug": "finance", "name": "FRED API", "provider": "Federal Reserve Bank",
     "url": "https://fred.stlouisfed.org/docs/api/fred/", "description": "美联储经济数据库 API。提供 80 万+ 经济时间序列：GDP、CPI、就业、利率、贸易等宏观数据。免费注册，适合经济学研究和数据分析。",
     "tags": "宏观经济,GDP,美联储,免费,数据", "is_free": True, "auth_type": "api_key",
     "request_example": 'GET https://api.stlouisfed.org/fred/series/observations?series_id=GDP&api_key=YOUR_KEY&file_type=json'},
    {"category_slug": "finance", "name": "Binance API", "provider": "Binance",
     "url": "https://binance-docs.github.io/apidocs/", "description": "全球最大加密货币交易所 API。实时行情、K线数据、深度、交易、账户管理等。完全免费，REST + WebSocket，覆盖 1500+ 交易对。",
     "tags": "加密货币,交易所,实时,WebSocket,免费", "is_free": True, "auth_type": "api_key",
     "request_example": 'GET https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT'},
    {"category_slug": "finance", "name": "CoinDesk API", "provider": "CoinDesk",
     "url": "https://www.coindesk.com/coindesk-api", "description": "CoinDesk 比特币价格指数 API。提供 BTC、ETH 等加密货币的实时价格、历史数据。完全免费无认证，数据被广泛引用。",
     "tags": "比特币,加密货币,价格,免费,无认证", "is_free": True, "auth_type": "no_auth",
     "request_example": 'GET https://api.coindesk.com/v1/bpi/currentprice/CNY.json'},

    # ===== 社交平台 (10 APIs) =====
    {"category_slug": "social", "name": "Telegram Bot API", "provider": "Telegram",
     "url": "https://core.telegram.org/bots/api", "description": "Telegram 官方机器人 API。创建聊天机器人、发送消息、内联查询、管理群组、支付等。完全免费无限制，是消息类应用开发的首选。",
     "tags": "Telegram,聊天,机器人,免费,实时", "is_free": True, "auth_type": "api_key",
     "request_example": 'POST https://api.telegram.org/bot{TOKEN}/sendMessage\nBody: {"chat_id":"@channel","text":"Hello"}'},
    {"category_slug": "social", "name": "Discord API", "provider": "Discord Inc.",
     "url": "https://discord.com/developers/docs/intro", "description": "Discord 官方 API。创建 Bot、管理服务器、发送消息、语音频道、Slash 命令等。完全免费，社区活跃，WebSocket 实时通信。",
     "tags": "Discord,聊天,机器人,免费,游戏", "is_free": True, "auth_type": "api_key",
     "request_example": 'POST https://discord.com/api/v10/channels/{CHANNEL_ID}/messages\nHeaders: Authorization: Bot YOUR_TOKEN'},
    {"category_slug": "social", "name": "微博开放平台", "provider": "新浪微博",
     "url": "https://open.weibo.com/wiki/API", "description": "新浪微博官方 API。获取微博内容、用户信息、评论、话题、粉丝服务等。需应用审核通过，适合社交媒体分析和内容管理。",
     "tags": "微博,中国,社交,内容,中文", "is_free": True, "auth_type": "oauth",
     "request_example": 'GET https://api.weibo.com/2/statuses/public_timeline.json?access_token=YOUR_TOKEN'},
    {"category_slug": "social", "name": "企业微信 API", "provider": "腾讯",
     "url": "https://developer.work.weixin.qq.com/document/", "description": "企业微信官方 API。消息推送、通讯录管理、应用开发、客户联系、日程、会议等。免费注册即用，适合企业内部工具和客户运营。",
     "tags": "企业微信,中国,消息,办公,免费", "is_free": True, "auth_type": "api_key",
     "request_example": 'POST https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=TOKEN'},
    {"category_slug": "social", "name": "Slack API", "provider": "Slack",
     "url": "https://api.slack.com/", "description": "Slack 开放 API。发送消息、创建频道、管理用户、接收事件、交互式组件等。免费版无限制，WebSocket 实时模式，是团队协作工具开发首选。",
     "tags": "Slack,协作,消息,免费,WebSocket", "is_free": True, "auth_type": "api_key",
     "request_example": 'POST https://slack.com/api/chat.postMessage\nBody: {"channel":"#general","text":"Hello"}'},
    {"category_slug": "social", "name": "LINE Messaging API", "provider": "LINE Corporation",
     "url": "https://developers.line.biz/en/docs/messaging-api/", "description": "LINE 消息 API。发送文本、图片、视频、按钮模板等富消息。免费版每月 500 条推送，日本/台湾/泰国用户基础庞大。",
     "tags": "LINE,消息,聊天,亚洲,免费", "is_free": True, "auth_type": "api_key",
     "request_example": 'POST https://api.line.me/v2/bot/message/push\nBody: {"to":"USER_ID","messages":[{"type":"text","text":"Hello"}]}'},
    {"category_slug": "social", "name": "Mastodon API", "provider": "Mastodon gGmbH",
     "url": "https://docs.joinmastodon.org/api/", "description": "去中心化社交网络 Mastodon 开放 API。发帖、时间线、通知、搜索、关注等。任何实例均可调用，无审核流程，完全开放。",
     "tags": "社交,去中心化,开源,免费,联邦宇宙", "is_free": True, "auth_type": "oauth",
     "request_example": 'GET https://mastodon.social/api/v1/timelines/public'},
    {"category_slug": "social", "name": "Twitch API", "provider": "Twitch Interactive",
     "url": "https://dev.twitch.tv/docs/api/", "description": "Twitch 直播平台 API。获取直播流、频道信息、游戏数据、用户信息、订阅数据等。免费注册应用即可使用，适合游戏和直播社区开发。",
     "tags": "Twitch,直播,游戏,免费,社区", "is_free": True, "auth_type": "oauth",
     "request_example": 'GET https://api.twitch.tv/helix/streams?game_id=12345\nHeaders: Client-ID: YOUR_CLIENT_ID'},
    {"category_slug": "social", "name": "WhatsApp Cloud API", "provider": "Meta",
     "url": "https://developers.facebook.com/docs/whatsapp/cloud-api", "description": "WhatsApp Business 云 API。发送模板消息、文本、媒体、互动按钮等。Meta 提供免费测试额度（1000 次/月），适合客服和营销场景。",
     "tags": "WhatsApp,消息,商务,免费额度,Meta", "is_free": True, "auth_type": "api_key",
     "request_example": 'POST https://graph.facebook.com/v18.0/{PHONE-ID}/messages\nBody: {"to":"PHONE","type":"text","text":{"body":"Hello"}}'},
    {"category_slug": "social", "name": "微信公众号 API", "provider": "腾讯",
     "url": "https://developers.weixin.qq.com/doc/offiaccount/Getting_Started/Overview.html", "description": "微信公众号开发接口。自定义菜单、消息管理、用户管理、素材管理、模板消息、客服消息等。个人号即可申请，适合内容分发。",
     "tags": "微信,公众号,中国,消息,免费", "is_free": True, "auth_type": "api_key",
     "request_example": 'POST https://api.weixin.qq.com/cgi-bin/message/template/send?access_token=TOKEN'},

    # ===== 开发工具 (10 APIs) =====
    {"category_slug": "dev-tools", "name": "GitHub REST API", "provider": "GitHub Inc.",
     "url": "https://docs.github.com/en/rest", "description": "GitHub 官方 REST API。管理仓库、Issues、PR、Actions、用户、组织等。免费版每分钟 60 次（认证后 5000 次），开发工具链核心。",
     "tags": "GitHub,代码,CI,开源,REST", "is_free": True, "auth_type": "api_key",
     "request_example": 'GET https://api.github.com/repos/facebook/react\nHeaders: Authorization: Bearer YOUR_TOKEN'},
    {"category_slug": "dev-tools", "name": "JSONPlaceholder", "provider": "Typicode",
     "url": "https://jsonplaceholder.typicode.com/", "description": "免费的在线 REST API 测试 Mock 服务。提供 Posts、Comments、Users、Todos、Photos 等假数据，支持完整 CRUD。开发调试必备。",
     "tags": "测试,Mock,开发,REST,JSON,免费,无认证", "is_free": True, "auth_type": "no_auth",
     "request_example": 'GET https://jsonplaceholder.typicode.com/posts/1'},
    {"category_slug": "dev-tools", "name": "IP-API", "provider": "IP-API.com",
     "url": "https://ip-api.com/", "description": "IP 地址信息查询 API。国家、城市、ISP、经纬度、时区等。免费版每分钟 45 次，无需 API Key，支持批量查询和 JSON/XML 格式。",
     "tags": "IP,网络,免费,无认证,开发", "is_free": True, "auth_type": "no_auth",
     "request_example": 'GET http://ip-api.com/json/8.8.8.8?lang=zh-CN'},
    {"category_slug": "dev-tools", "name": "httpbin.org", "provider": "Kenneth Reitz",
     "url": "https://httpbin.org/", "description": "HTTP 请求和响应测试服务。测试 GET/POST/PUT/DELETE、Cookie、Header、状态码、重定向、流式、图片等。完全免费开源，HTTP 调试瑞士军刀。",
     "tags": "HTTP,测试,开发,免费,开源,调试", "is_free": True, "auth_type": "no_auth",
     "request_example": 'POST https://httpbin.org/post\nBody: {"test":"data"}'},
    {"category_slug": "dev-tools", "name": "Sentry API", "provider": "Sentry (Functional Software)",
     "url": "https://docs.sentry.io/api/", "description": "错误监控和性能追踪平台 API。管理项目、查询错误、获取事件详情、性能数据、发布管理。免费版 5000 events/月，适合个人和小团队。",
     "tags": "监控,错误,性能,开发,免费", "is_free": True, "auth_type": "api_key",
     "request_example": 'GET https://sentry.io/api/0/projects/\nHeaders: Authorization: Bearer YOUR_TOKEN'},
    {"category_slug": "dev-tools", "name": "Have I Been Pwned API", "provider": "Troy Hunt",
     "url": "https://haveibeenpwned.com/API/v3", "description": "数据泄露查询 API。检查邮箱/手机是否出现在已知数据泄露事件中。支持域名搜索、密码泄露检查。免费版有频率限制，安全开发必备。",
     "tags": "安全,数据泄露,免费,隐私,检查", "is_free": True, "auth_type": "api_key",
     "request_example": 'GET https://haveibeenpwned.com/api/v3/breachedaccount/test@example.com\nHeaders: hibp-api-key: YOUR_KEY'},
    {"category_slug": "dev-tools", "name": "NASA API", "provider": "NASA",
     "url": "https://api.nasa.gov/", "description": "NASA 开放数据 API。每日天文图 (APOD)、火星探测器照片、近地天体数据、地球影像、卫星图集等。完全免费，科学可视化项目首选。",
     "tags": "NASA,太空,天文,图片,免费,科学", "is_free": True, "auth_type": "api_key",
     "request_example": 'GET https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY'},
    {"category_slug": "dev-tools", "name": "PokeAPI", "provider": "PokeAPI",
     "url": "https://pokeapi.co/", "description": "宝可梦数据 API。800+ 宝可梦的详细信息：名称、属性、能力值、进化链、招式等。完全免费无认证，RESTful，是练习 API 调用的经典项目。",
     "tags": "宝可梦,游戏,数据,免费,无认证,REST", "is_free": True, "auth_type": "no_auth",
     "request_example": 'GET https://pokeapi.co/api/v2/pokemon/pikachu'},
    {"category_slug": "dev-tools", "name": "REST Countries", "provider": "Community",
     "url": "https://restcountries.com/", "description": "全球国家信息 API。获取国家名称、国旗、首都、人口、语言、货币、时区、区域等。完全免费无认证，适合地理信息类应用。",
     "tags": "国家,地理,数据,免费,无认证,REST", "is_free": True, "auth_type": "no_auth",
     "request_example": 'GET https://restcountries.com/v3.1/name/china'},
    {"category_slug": "dev-tools", "name": "CountAPI", "provider": "Community",
     "url": "https://countapi.xyz/", "description": "免费计数 API。创建、获取、增加命名空间化的计数值，支持设置上限、重置等功能。完全免费无认证，适合网页访问统计等轻量场景。",
     "tags": "计数,统计,免费,无认证,简单", "is_free": True, "auth_type": "no_auth",
     "request_example": 'GET https://api.countapi.xyz/hit/mysite.com/visits'},
]


async def seed():
    """Main seed function."""
    await init_db()

    async with async_session() as session:
        # Seed categories
        existing = (await session.execute(select(Category))).scalars().all()
        if existing:
            print(f"Database already has {len(existing)} categories. Skipping seed.")
            await session.close()
            return

        print("Seeding categories...")
        slug_to_id = {}
        for cat_data in SEED_CATEGORIES:
            cat = Category(**cat_data)
            session.add(cat)
            slug_to_id[cat_data["slug"]] = cat
        await session.flush()

        # Remap slug to id
        slug_to_id_map = {c.slug: c.id for c in slug_to_id.values()}

        print("Seeding APIs...")
        now = datetime.now(timezone.utc)
        for api_data in SEED_APIS:
            slug = api_data.pop("category_slug")
            api_data["category_id"] = slug_to_id_map[slug]
            api_data["created_at"] = now
            api_data["updated_at"] = now
            session.add(ApiEntry(**api_data))

        await session.commit()
        print(f"Done! Seeded {len(SEED_CATEGORIES)} categories and {len(SEED_APIS)} APIs.")


if __name__ == "__main__":
    asyncio.run(seed())
