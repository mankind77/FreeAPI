"""
Ollama AI Q&A service.
Queries local Ollama (Qwen3.5 0.8b) with SQLite FTS5 search.
"""

import re
import httpx
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from models import ApiEntry

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen3.5:0.8b"
REQUEST_TIMEOUT = 120
MAX_SEARCH_RESULTS = 12


async def search_apis(db: AsyncSession, query: str) -> list[ApiEntry]:
    """Hybrid search: FTS5 for ASCII, keyword extraction for Chinese."""
    if not query.strip():
        return []

    cleaned = re.sub(r'[？?！!，,。.、\s]+', ' ', query).strip()
    if len(cleaned) < 2:
        return []

    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', cleaned))

    if has_chinese:
        # Chinese concept mapping: expand domain terms to English tag equivalents
        CONCEPT_MAP = {
            "计算机": ["计算机", "编程", "开发", "代码", "GitHub", "Python", "开源"],
            "科研": ["科学", "研究", "数据分析", "人工智能", "AI", "机器学习", "science", "research"],
            "编程": ["编程", "开发", "代码", "Python", "GitHub", "开源"],
            "金融": ["股票", "外汇", "加密货币", "比特币", "finance", "trading", "行情"],
            "天气": ["weather", "气候", "预报", "降水", "空气质量", "cloud"],
            "新闻": ["news", "媒体", "热榜", "热搜", "文章"],
            "人工智能": ["AI", "GPT", "LLM", "大模型", "机器学习", "图像", "语音"],
            "语音": ["speech", "TTS", "STT", "语音合成", "语音识别"],
        }
        extra_keywords = []
        for concept, mappings in CONCEPT_MAP.items():
            if concept in cleaned:
                extra_keywords.extend(mappings)

        words = list(extra_keywords)
        chinese_only = re.sub(r'[^\u4e00-\u9fff]', '', cleaned)
        if len(chinese_only) >= 2:
            words.append(chinese_only)
            for i in range(len(chinese_only) - 1):
                words.append(chinese_only[i:i+2])
        chinese_parts = re.findall(r'[\u4e00-\u9fff]{2,}', cleaned)
        for part in chinese_parts:
            if part not in words:
                words.append(part)
        english_parts = re.findall(r'[a-zA-Z]{2,}', cleaned)
        words.extend(english_parts)
        STOP = {"的","了","在","是","有","我","不","人","都","一","一个","什么","怎么","如何","哪些","哪","吗","呢","吧","啊","和","与","或","可以","这个","那个","这些","那些","它","他","她",
                "适合","给我","帮我","获取","使用","有没有","有什么","推荐","哪些","怎么"}
        keywords = list(dict.fromkeys([w for w in words if len(w) >= 2 and w.lower() not in STOP]))

        if not keywords:
            single_chars = list(set(chinese_only)) if len(chinese_only) >= 1 else []
            keywords = [c for c in single_chars if c not in STOP]

    if not has_chinese:
        # English / ASCII: use FTS5 full-text search with BM25 ranking
        fts_sql = text("""
            SELECT rowid, rank FROM api_fts
            WHERE api_fts MATCH :query
            ORDER BY rank
            LIMIT :limit
        """)
        result = await db.execute(fts_sql, {"query": cleaned, "limit": MAX_SEARCH_RESULTS})
        ranked = [(r[0], r[1]) for r in result.fetchall()]

        if not ranked:
            return []

        ids = [r[0] for r in ranked]
        stmt = (select(ApiEntry)
                .where(ApiEntry.id.in_(ids), ApiEntry.status == "active")
                .options(selectinload(ApiEntry.category)))
        result = await db.execute(stmt)
        entries = {e.id: e for e in result.scalars().all()}
        return [entries[eid] for eid in ids if eid in entries]

    # Chinese keyword search
    conditions = []
    for kw in keywords[:10]:
        pattern = f"%{kw}%"
        conditions.append(ApiEntry.name.ilike(pattern))
        conditions.append(ApiEntry.provider.ilike(pattern))
        conditions.append(ApiEntry.description.ilike(pattern))
        conditions.append(ApiEntry.tags.ilike(pattern))

    if not conditions:
        return []

    from sqlalchemy import or_
    stmt = (select(ApiEntry).where(ApiEntry.status == "active", or_(*conditions))
            .options(selectinload(ApiEntry.category)).limit(MAX_SEARCH_RESULTS))
    result = await db.execute(stmt)
    entries = result.scalars().all()

    # Score by keyword match count + category boosting
    # Map concept keywords to preferred category slugs
    CATEGORY_BOOST = {}
    for kw in keywords:
        if kw in {"编程", "开发", "代码", "GitHub", "Python", "开源"}:
            CATEGORY_BOOST["dev-tools"] = 10
            CATEGORY_BOOST["ai-ml"] = 5
        if kw in {"科学", "研究", "science", "research"}:
            CATEGORY_BOOST["weather-geo"] = 3  # earthquake, climate data etc

    def match_score(e):
        s = 0
        cat_slug = e.category.slug if e.category else ""
        if cat_slug in CATEGORY_BOOST:
            s += CATEGORY_BOOST[cat_slug]
        text = f"{e.name} {e.provider} {e.description}"
        for kw in keywords:
            if kw.lower() in text.lower():
                s += 1
            if any(kw.lower() in (t or "").lower() for t in (e.tag_list() or [])):
                s += 3  # Tag matches are strongest signal
        return -s

    entries = sorted(entries, key=match_score)
    return entries


def extract_final_answer(thinking: str) -> str:
    """Extract the final recommendation portion from thinking text."""
    if not thinking:
        return ""

    # Look for clear answer markers
    markers = [
        "Final Answer:", "最终回答：", "最终答案：", "最终推荐：",
        "答案：", "推荐：", "结论：", "总结：",
        "Final Recommendation:", "Conclusion:",
    ]
    for marker in markers:
        idx = thinking.find(marker)
        if idx >= 0:
            after = thinking[idx + len(marker):].strip()
            if len(after) > 20:
                return after[:2000]

    # Look for structured API list (numbered APIs)
    api_list_match = re.search(r'(?:以下|推荐|最终|Therefore).*?(?:API|api|推荐)如下[：:]', thinking)
    if api_list_match:
        after = thinking[api_list_match.end():].strip()
        if len(after) > 20:
            return after[:2000]

    # Extract numbered API recommendations
    numbered = re.findall(r'^\d+\.\s+\*\*[^*]+\*\*[^\n]+', thinking, re.MULTILINE)
    if numbered and len(numbered) >= 2:
        return "\n".join(numbered[:5])

    # Last resort: take last 30% as likely conclusion
    lines = thinking.split("\n")
    if len(lines) > 20:
        conclusion_start = int(len(lines) * 0.7)
        tail = "\n".join(lines[conclusion_start:])
        # Filter noise lines
        clean = [l for l in tail.split("\n") if not l.strip().startswith('*Wait') and not l.strip().startswith('*Self') and len(l.strip()) > 10]
        if clean:
            return "\n".join(clean[:15])

    return ""


def truncate_repetition(text: str) -> str:
    """Detect and truncate repetitive patterns in Qwen thinking output."""
    lines = text.split("\n")
    if len(lines) < 10:
        return text
    # Find first line that repeats 3+ times
    seen = {}
    cutoff = len(lines)
    for i, line in enumerate(lines):
        stripped = line.strip()
        if len(stripped) < 5:
            continue
        if stripped in seen:
            seen[stripped] += 1
            if seen[stripped] >= 3:
                cutoff = min(cutoff, i)
        else:
            seen[stripped] = 1
    if cutoff < len(lines) * 0.6:
        return "\n".join(lines[:cutoff]) + "\n... (truncated repeated content)"
    return text


async def query_ollama(context: str, user_query: str) -> dict:
    """Query Ollama with DB context and return thinking + answer."""
    system_prompt = (
        "You have a database of free APIs below. Answer the user's question using ONLY these APIs.\n"
        "IMPORTANT: Think ONCE, then give your final answer. Do NOT repeat yourself.\n"
        "Limit thinking to 3 steps max. Then output Final Answer in Chinese.\n\n"
        f"{context}"
    )
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(OLLAMA_URL, json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query},
                ],
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 1024},
            })
            response.raise_for_status()
            data = response.json()
            msg = data.get("message", {})
            thinking = msg.get("thinking", "")
            content = msg.get("content", "")
            # Truncate repetitive thinking
            if thinking:
                thinking = truncate_repetition(thinking[:3000])
            # Extract final answer from thinking (look for "Final Answer", "推荐", "结论" etc)
            final_answer = extract_final_answer(thinking) if thinking else ""
            # If extraction failed, use raw thinking as fallback
            answer = final_answer or content.strip() or thinking
            return {"thinking": thinking, "answer": answer}
    except httpx.ConnectError:
        return {"thinking": "", "answer": "[error] Cannot connect to Ollama"}
    except httpx.TimeoutException:
        return {"thinking": "", "answer": "[error] Ollama timed out"}
    except Exception as e:
        return {"thinking": "", "answer": f"[error] {str(e)}"}


async def search_and_answer(db: AsyncSession, query: str) -> dict:
    entries = await search_apis(db, query)

    if not entries:
        context = "(No matching APIs found in the FreeAPI Directory.)"
        llm = await query_ollama(context, query)
        return {
            "thinking": llm["thinking"],
            "answer": "No matching APIs found. Try different keywords.",
            "sources": [],
        }

    # Build answers from search results (clean, structured)
    lines = []
    for i, e in enumerate(entries[:5], 1):
        cat = e.category.name if e.category else "N/A"
        free = "Free" if e.is_free else "Paid"
        lines.append(f"{i}. {e.name} ({cat})\n   Provider: {e.provider} | Auth: {e.auth_type} | {free}\n   {e.description[:150]}")
    structured_answer = "\n\n".join(lines)

    # Get Ollama thinking for transparency
    context_lines = []
    for e in entries:
        context_lines.append(f"- {e.name} ({e.category.name if e.category else 'N/A'}): {e.description[:150]}")
    context = "\n".join(context_lines)
    llm = await query_ollama(context, query)

    sources = [{"id": e.id, "name": e.name, "provider": e.provider, "url": e.url,
                "category": e.category.name if e.category else "N/A", "tags": e.tag_list()}
               for e in entries]

    return {
        "thinking": llm["thinking"],
        "answer": structured_answer,
        "sources": sources,
    }
