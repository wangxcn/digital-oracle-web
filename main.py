"""
Digital Oracle Web API
独立 Web 服务，封装 digital-oracle 的分析能力
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import sys
import os

# 添加 digital-oracle 路径
skill_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'skills', 'digital-oracle')
sys.path.insert(0, skill_path)

app = FastAPI(title="Digital Oracle API", description="基于市场数据的预测分析")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求模型
class AnalyzeRequest(BaseModel):
    question: str
    detail_level: Optional[str] = "normal"  # simple, normal, detailed

# 响应模型
class AnalyzeResponse(BaseModel):
    question: str
    analysis: str
    signals: dict
    confidence: str


def analyze_war_risk(question: str) -> dict:
    """分析战争风险相关问题"""
    from digital_oracle import (
        PolymarketProvider, PolymarketEventQuery,
        USTreasuryProvider,
        FearGreedProvider,
        CoinGeckoProvider, CoinGeckoPriceQuery,
        gather,
    )
    
    pm = PolymarketProvider()
    treasury = USTreasuryProvider()
    fear_greed = FearGreedProvider()
    coingecko = CoinGeckoProvider()
    
    # 并行获取数据
    result = gather({
        'pm_war': lambda: pm.list_events(PolymarketEventQuery(slug_contains='war', limit=10)),
        'pm_russia': lambda: pm.list_events(PolymarketEventQuery(slug_contains='russia', limit=10)),
        'pm_ukraine': lambda: pm.list_events(PolymarketEventQuery(slug_contains='ukraine', limit=10)),
        'pm_ceasefire': lambda: pm.list_events(PolymarketEventQuery(slug_contains='ceasefire', limit=10)),
        'pm_taiwan': lambda: pm.list_events(PolymarketEventQuery(slug_contains='taiwan', limit=10)),
        'pm_china': lambda: pm.list_events(PolymarketEventQuery(slug_contains='china', limit=10)),
        'pm_nuclear': lambda: pm.list_events(PolymarketEventQuery(slug_contains='nuclear', limit=10)),
        'fear_greed': lambda: fear_greed.get_index(),
        'yield_curve': lambda: treasury.latest_yield_curve(),
        'crypto': lambda: coingecko.get_prices(CoinGeckoPriceQuery(coin_ids=('bitcoin', 'ethereum'))),
    })
    
    return result


def analyze_recession(question: str) -> dict:
    """分析经济衰退相关问题"""
    from digital_oracle import (
        USTreasuryProvider,
        FearGreedProvider,
        CoinGeckoProvider, CoinGeckoPriceQuery,
        CMEFedWatchProvider,
        gather,
    )
    
    treasury = USTreasuryProvider()
    fear_greed = FearGreedProvider()
    coingecko = CoinGeckoProvider()
    fedwatch = CMEFedWatchProvider()
    
    result = gather({
        'yield_curve': lambda: treasury.latest_yield_curve(),
        'fear_greed': lambda: fear_greed.get_index(),
        'crypto': lambda: coingecko.get_prices(CoinGeckoPriceQuery(coin_ids=('bitcoin', 'ethereum'))),
        'fedwatch': lambda: fedwatch.get_probabilities(),
    })
    
    return result


def analyze_asset(question: str) -> dict:
    """分析资产相关问题（黄金、股票等）"""
    from digital_oracle import (
        YahooPriceProvider, PriceHistoryQuery,
        FearGreedProvider,
        CoinGeckoProvider, CoinGeckoPriceQuery,
        USTreasuryProvider,
        gather,
    )
    
    yahoo = YahooPriceProvider()
    fear_greed = FearGreedProvider()
    coingecko = CoinGeckoProvider()
    treasury = USTreasuryProvider()
    
    result = gather({
        'gold': lambda: yahoo.get_history(PriceHistoryQuery(symbol='GC=F', limit=30)),
        'silver': lambda: yahoo.get_history(PriceHistoryQuery(symbol='SI=F', limit=30)),
        'spy': lambda: yahoo.get_history(PriceHistoryQuery(symbol='SPY', limit=30)),
        'oil': lambda: yahoo.get_history(PriceHistoryQuery(symbol='CL=F', limit=30)),
        'fear_greed': lambda: fear_greed.get_index(),
        'crypto': lambda: coingecko.get_prices(CoinGeckoPriceQuery(coin_ids=('bitcoin', 'ethereum'))),
        'yield_curve': lambda: treasury.latest_yield_curve(),
    })
    
    return result


def analyze_crypto(question: str) -> dict:
    """分析加密货币相关问题"""
    from digital_oracle import (
        CoinGeckoProvider, CoinGeckoPriceQuery, CoinGeckoMarketQuery,
        DeribitProvider, DeribitFuturesCurveQuery,
        FearGreedProvider,
        gather,
    )
    
    coingecko = CoinGeckoProvider()
    deribit = DeribitProvider()
    fear_greed = FearGreedProvider()
    
    result = gather({
        'crypto_prices': lambda: coingecko.get_prices(CoinGeckoPriceQuery(coin_ids=('bitcoin', 'ethereum', 'solana'))),
        'crypto_market': lambda: coingecko.get_market(CoinGeckoMarketQuery()),
        'btc_futures': lambda: deribit.get_futures_term_structure(DeribitFuturesCurveQuery(currency='BTC')),
        'eth_futures': lambda: deribit.get_futures_term_structure(DeribitFuturesCurveQuery(currency='ETH')),
        'fear_greed': lambda: fear_greed.get_index(),
    })
    
    return result


def format_analysis(question: str, signals: dict) -> str:
    """格式化分析结果"""
    lines = []
    lines.append(f"## 📊 分析报告\n")
    lines.append(f"**问题**: {question}\n")
    
    # Fear & Greed
    fg = signals.get('fear_greed')
    if fg:
        lines.append(f"### 🎯 Fear & Greed Index")
        lines.append(f"- **分数**: {fg.score} ({fg.label})")
        if hasattr(fg, 'interpretation') and fg.interpretation:
            lines.append(f"- **解读**: {fg.interpretation}")
        lines.append("")
    
    # Yield Curve
    yc = signals.get('yield_curve')
    if yc:
        lines.append(f"### 📈 美债收益率曲线")
        if hasattr(yc, 'rates') and yc.rates:
            for r in yc.rates[:5]:
                lines.append(f"- {r.maturity}: {r.rate:.2f}%")
        lines.append("")
    
    # Polymarket Events
    for key in ['pm_war', 'pm_russia', 'pm_ukraine', 'pm_ceasefire', 'pm_taiwan', 'pm_china', 'pm_nuclear']:
        events = signals.get(key, [])
        if events:
            label = key.replace('pm_', '').replace('_', ' ').title()
            lines.append(f"### 🎲 Polymarket: {label}")
            for e in events[:5]:
                if hasattr(e, 'title') and hasattr(e, 'probability') and e.probability:
                    lines.append(f"- {e.title}: **{e.probability:.1%}**")
                elif hasattr(e, 'title'):
                    lines.append(f"- {e.title}")
            lines.append("")
    
    # Crypto
    crypto = signals.get('crypto') or signals.get('crypto_prices')
    if crypto:
        lines.append(f"### ₿ 加密货币")
        for p in crypto[:5]:
            if hasattr(p, 'symbol') and hasattr(p, 'price'):
                lines.append(f"- {p.symbol}: ${p.price:,.2f}")
        lines.append("")
    
    # Gold/Silver
    gold = signals.get('gold')
    if gold and hasattr(gold, 'latest'):
        lines.append(f"### 🥇 黄金")
        lines.append(f"- 最新价格: ${gold.latest.close:,.2f}")
        lines.append("")
    
    silver = signals.get('silver')
    if silver and hasattr(silver, 'latest'):
        lines.append(f"### 🥈 白银")
        lines.append(f"- 最新价格: ${silver.latest.close:,.2f}")
        lines.append("")
    
    # SPY
    spy = signals.get('spy')
    if spy and hasattr(spy, 'latest'):
        lines.append(f"### 📊 S&P 500")
        lines.append(f"- 最新价格: ${spy.latest.close:,.2f}")
        lines.append("")
    
    # Oil
    oil = signals.get('oil')
    if oil and hasattr(oil, 'latest'):
        lines.append(f"### 🛢️ 原油")
        lines.append(f"- 最新价格: ${oil.latest.close:,.2f}")
        lines.append("")
    
    # FedWatch
    fw = signals.get('fedwatch')
    if fw:
        lines.append(f"### 🏦 美联储利率预期")
        if hasattr(fw, 'probabilities'):
            for p in fw.probabilities[:5]:
                if hasattr(p, 'rate') and hasattr(p, 'probability'):
                    lines.append(f"- {p.rate:.2f}%: {p.probability:.1%}")
        lines.append("")
    
    return "\n".join(lines)


def detect_question_type(question: str) -> str:
    """检测问题类型"""
    q = question.lower()
    
    war_keywords = ['ww3', 'war', '战争', '冲突', 'russia', 'ukraine', '俄罗斯', '乌克兰', 
                    'taiwan', '台湾', 'china', '中国', 'nuclear', '核', 'ceasefire', '停火',
                    'invasion', '入侵', 'regime', '政权']
    recession_keywords = ['recession', '衰退', 'economy', '经济', 'gdp', 'crisis', '危机',
                          '失业', 'unemployment', '利率', 'rate', 'fed', '美联储']
    crypto_keywords = ['crypto', '加密', 'bitcoin', 'btc', 'eth', 'ethereum', '比特币', '以太坊']
    asset_keywords = ['gold', '黄金', 'silver', '白银', 'oil', '原油', 'stock', '股票', 
                      'spy', '指数', 'price', '价格', '买', 'sell', '卖', '投资']
    
    if any(k in q for k in war_keywords):
        return 'war'
    if any(k in q for k in recession_keywords):
        return 'recession'
    if any(k in q for k in crypto_keywords):
        return 'crypto'
    if any(k in q for k in asset_keywords):
        return 'asset'
    
    return 'general'


@app.get("/", response_class=HTMLResponse)
async def root():
    """返回前端页面"""
    html_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    """分析预测问题"""
    try:
        question_type = detect_question_type(request.question)
        
        if question_type == 'war':
            signals = analyze_war_risk(request.question)
        elif question_type == 'recession':
            signals = analyze_recession(request.question)
        elif question_type == 'crypto':
            signals = analyze_crypto(request.question)
        elif question_type == 'asset':
            signals = analyze_asset(request.question)
        else:
            # 默认获取综合数据
            signals = analyze_asset(request.question)
        
        analysis = format_analysis(request.question, signals)
        
        # 简化 signals 用于 JSON 响应
        simple_signals = {}
        for k, v in signals.items():
            if v is not None:
                if hasattr(v, '__dict__'):
                    simple_signals[k] = str(v)[:200]
                elif isinstance(v, list):
                    simple_signals[k] = f"{len(v)} items"
                else:
                    simple_signals[k] = str(v)[:200]
        
        return AnalyzeResponse(
            question=request.question,
            analysis=analysis,
            signals=simple_signals,
            confidence="基于市场数据的多信号交叉验证"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health():
    """健康检查"""
    return {"status": "ok", "service": "digital-oracle-web"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
