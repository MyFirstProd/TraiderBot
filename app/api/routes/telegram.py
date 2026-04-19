from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.dependencies import get_services, get_session
from app.core.security import validate_telegram_init_data
from app.repositories.analytics import AnalyticsRepository
from app.repositories.trading import TradingRepository
from app.schemas.common import MessageResponse
from app.schemas.dashboard import DashboardChartsResponse, MiniAppDashboardResponse, TimeValuePoint
from app.services.config_service import ConfigService

router = APIRouter()


@router.post("/miniapp/validate", response_model=dict)
async def validate_mini_app(authorization: str = Header(..., alias="X-Telegram-Init-Data")) -> dict:
    settings = get_settings()
    token = settings.TELEGRAM_BOT_TOKEN.get_secret_value()
    if not token:
        raise HTTPException(status_code=503, detail="Токен Telegram-бота не настроен")
    return validate_telegram_init_data(authorization, token, settings.TELEGRAM_INITDATA_TTL_SECONDS)


@router.get("/commands", response_model=dict)
async def list_commands() -> dict:
    return {
        "commands": [
            {"command": "/start", "description": "Старт и кнопки управления"},
            {"command": "/status", "description": "Текущий статус и риск"},
            {"command": "/positions", "description": "Открытые позиции"},
            {"command": "/trades", "description": "История сделок"},
            {"command": "/signals", "description": "Последние сигналы"},
            {"command": "/miniapp", "description": "Открыть дашборд"},
            {"command": "/enable", "description": "Включить торговлю"},
            {"command": "/disable", "description": "Отключить торговлю"},
        ],
        "mini_app_url": get_settings().TELEGRAM_MINI_APP_URL,
    }


@router.get("/dashboard", response_model=MiniAppDashboardResponse)
async def dashboard(
    session: AsyncSession = Depends(get_session),
    services=Depends(get_services),
) -> MiniAppDashboardResponse:
    trading_repo = TradingRepository(session)
    analytics_repo = AnalyticsRepository(session)
    config_service = ConfigService(session)
    await config_service.ensure_defaults()

    runtime = services.runtime
    snapshots = await trading_repo.list_latest_snapshots_by_symbol()
    signals = await trading_repo.list_signals(limit=18)
    positions = await trading_repo.list_open_positions()
    trades = await trading_repo.list_trades(limit=24)
    news = await analytics_repo.list_news(limit=18)
    whales = await analytics_repo.list_whales(limit=18)
    strategies = await config_service.list_configs()
    chart_payload = await _build_charts(
        trading_repo=trading_repo,
        analytics_repo=analytics_repo,
        symbols=runtime.settings.TRADING_SYMBOLS,
        trades=trades,
    )

    return MiniAppDashboardResponse(
        server_time=datetime.now(UTC),
        app_name=get_settings().APP_NAME,
        paper_trading=runtime.settings.PAPER_TRADING,
        trading_enabled=runtime.trading_enabled,
        equity=runtime.equity,
        risk={
            "trading_enabled": runtime.trading_enabled,
            "paper_trading": runtime.settings.PAPER_TRADING,
            "circuit_breaker_open": runtime.risk.circuit_breaker_open,
            "daily_realized_pnl": runtime.risk.daily_realized_pnl,
            "daily_loss_limit_pct": runtime.risk.max_daily_loss_pct,
            "consecutive_losses": runtime.risk.consecutive_losses,
            "open_positions": len(runtime.paper.positions),
            "max_concurrent_positions": runtime.risk.max_concurrent_positions,
        },
        model=services.ml.status(),
        snapshots=snapshots,
        signals=signals,
        positions=positions,
        trades=trades,
        news=news,
        whales=whales,
        strategies=strategies,
        charts=chart_payload,
    )


@router.get("/miniapp", response_class=HTMLResponse)
async def mini_app(token: str = Query(default="")) -> HTMLResponse:  # noqa: C901
    html = f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>TraiderBot Mini App</title>
  <style>
    :root {{
      --bg: #f4efe6;
      --card: rgba(255,252,247,.96);
      --ink: #182028;
      --muted: #60707b;
      --line: #e3d8c9;
      --accent: #0b7285;
      --accent-soft: #dff4f8;
      --warn: #f08c6c;
      --ok: #2f9e44;
      --danger: #c92a2a;
    }}
    *{{box-sizing:border-box;margin:0;padding:0;}}
    body{{font-family:"Segoe UI",Tahoma,sans-serif;font-size:13px;color:var(--ink);
         background:linear-gradient(160deg,#faf7f2,#efe8dd);min-height:100vh;}}
    .wrap{{max-width:1400px;margin:0 auto;padding:14px;}}
    .hero{{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:14px;flex-wrap:wrap;}}
    .hero h1{{font-size:26px;font-weight:800;}}
    .toolbar{{display:flex;gap:8px;align-items:center;flex-wrap:wrap;}}
    .btn{{border:0;border-radius:10px;padding:8px 14px;cursor:pointer;font-weight:700;font-size:13px;color:#fff;background:var(--accent);}}
    .btn.warn{{background:var(--accent2);}}
    .btn:disabled{{opacity:.4;cursor:default;}}
    .sync{{color:var(--muted);font-size:12px;}}
    .card{{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:14px;box-shadow:0 8px 24px rgba(24,32,40,.06);}}
    .card h2{{font-size:15px;margin-bottom:10px;}}
    .grid{{display:grid;gap:12px;}}
    .kpi-grid{{grid-template-columns:repeat(auto-fit,minmax(145px,1fr));}}
    .two-grid{{grid-template-columns:repeat(auto-fit,minmax(300px,1fr));}}
    .kpi-val{{font-size:22px;font-weight:800;margin-top:5px;}}
    .lbl{{color:var(--muted);font-size:11px;}}
    .section{{margin-top:12px;}}
    table{{width:100%;border-collapse:collapse;font-size:12px;}}
    th,td{{text-align:left;padding:6px 5px;border-bottom:1px solid #f0e8df;vertical-align:top;}}
    th{{color:var(--muted);font-weight:700;font-size:11px;}}
    .badge{{display:inline-block;padding:2px 7px;border-radius:999px;background:var(--asoft);color:var(--accent);font-size:11px;font-weight:700;}}
    .badge.d{{background:#fdecea;color:var(--danger);}}
    .badge.ok{{background:#ebfbee;color:var(--ok);}}
    .badge.w{{background:#fff4e6;color:var(--accent2);}}
    .badge.p{{background:#f3f0ff;color:var(--purple);}}
    .ok{{color:var(--ok);font-weight:700;}}
    .warn{{color:var(--accent2);font-weight:700;}}
    .danger{{color:var(--danger);font-weight:700;}}
    .mono{{font-family:Consolas,monospace;}}
    .empty{{color:var(--muted);padding:6px 0;font-size:12px;}}
    .tabs{{display:flex;gap:6px;}}
    .tab{{border:1px solid var(--line);border-radius:8px;padding:5px 12px;cursor:pointer;font-size:12px;font-weight:700;background:transparent;color:var(--muted);}}
    .tab.active{{background:var(--accent);color:#fff;border-color:var(--accent);}}
    canvas{{display:block;width:100%;}}
    #notice{{margin-bottom:12px;padding:10px 14px;border-radius:12px;background:#fff8e1;border:1px solid #ffe58f;font-size:12px;color:#7c5c00;}}
    .clegend{{display:flex;gap:10px;flex-wrap:wrap;font-size:11px;margin-bottom:4px;align-items:center;}}
    .clegend i{{display:inline-block;border-radius:2px;margin-right:3px;}}
      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="hero">
          <div>
            <h1>TraiderBot Dashboard</h1>
            <p>Рынок, киты, новости, сигналы, торговая статистика и обучение модели в одном месте. Если Mini App открыта из Telegram, дашборд сразу готов к работе.</p>
          </div>
          <div class="toolbar">
            <button onclick="loadDashboard()">Обновить</button>
            <button id="trainBtn" class="alt" onclick="trainModel()">Обучить модель</button>
            <span id="sync" class="muted small">Загрузка…</span>
          </div>
        </div>

        <div id="notice" class="card small" style="display:none; margin-bottom:16px;"></div>

        <div id="kpis" class="grid kpi-grid"></div>

        <div class="section grid three-grid">
          <div class="card">
            <h2>Курсы</h2>
            <div id="marketCards"></div>
          </div>
          <div class="card">
            <h2>График цен</h2>
            <div class="chart-wrap"><canvas id="priceChart" width="600" height="220"></canvas></div>
          </div>
          <div class="card">
            <h2>Сигналы и score</h2>
            <div class="chart-wrap"><canvas id="signalChart" width="600" height="220"></canvas></div>
          </div>
        </div>

        <div class="section grid three-grid">
          <div class="card">
            <h2>Киты</h2>
            <div class="chart-wrap"><canvas id="whaleChart" width="600" height="220"></canvas></div>
            <div id="whaleTable"></div>
          </div>
          <div class="card">
            <h2>Новости</h2>
            <div class="chart-wrap"><canvas id="newsChart" width="600" height="220"></canvas></div>
            <div id="newsTable"></div>
          </div>
          <div class="card">
            <h2>Обучение модели</h2>
            <div class="chart-wrap"><canvas id="modelChart" width="600" height="220"></canvas></div>
            <div id="modelInfo"></div>
          </div>
        </div>

        <div class="section grid two-grid">
          <div class="card">
            <h2>Стратегии и расчёты риска</h2>
            <div id="strategyTable"></div>
          </div>
          <div class="card">
            <h2>Сделки и PnL</h2>
            <div class="chart-wrap"><canvas id="tradeChart" width="600" height="220"></canvas></div>
            <div id="tradeTable"></div>
          </div>
        </div>

        <div class="section grid two-grid">
          <div class="card">
            <h2>Расчёты по символам</h2>
            <div id="calcTable"></div>
          </div>
          <div class="card">
            <h2>Контур риска</h2>
            <div id="riskTable"></div>
          </div>
        </div>

        <div class="section grid two-grid">
          <div class="card">
            <h2>Последние сигналы</h2>
            <div id="signalTable"></div>
          </div>
          <div class="card">
            <h2>Открытые позиции</h2>
            <div id="positionTable"></div>
          </div>
        </div>
      </div>

      <script src="https://telegram.org/js/telegram-web-app.js"></script>
      <script>
        const tg = window.Telegram?.WebApp;
        if (tg) {{
          tg.ready();
          tg.expand();
        }}

        const miniAppToken = {token!r};
        const canTrain = Boolean(miniAppToken);
        const trainBtn = document.getElementById("trainBtn");
        trainBtn.disabled = !canTrain;
        const notice = document.getElementById("notice");
        if (!canTrain) {{
          notice.style.display = "block";
          notice.textContent = "Mini App открыта в режиме просмотра. Для обучения модели откройте её из Telegram-кнопки.";
        }}

        function esc(value) {{
          return String(value ?? "").replace(/[&<>"]/g, (ch) => ({{
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
          }}[ch]));
        }}

        function fmtTime(value) {{
          return new Date(value).toLocaleString("ru-RU");
        }}

        function yesNo(value) {{
          return value ? "да" : "нет";
        }}

        function requestHeaders() {{
          const headers = {{ "Content-Type": "application/json" }};
          if (miniAppToken) headers["X-MiniApp-Token"] = miniAppToken;
          return headers;
        }}

        function renderTable(columns, rows) {{
          if (!rows.length) return '<div class="empty">Пока нет данных</div>';
          const head = columns.map((col) => `<th>${{esc(col.label)}}</th>`).join("");
          const body = rows.map((row) => {{
            const cells = columns.map((col) => `<td>${{col.render(row)}}</td>`).join("");
            return `<tr>${{cells}}</tr>`;
          }}).join("");
          return `<table><thead><tr>${{head}}</tr></thead><tbody>${{body}}</tbody></table>`;
        }}

        function drawLineChart(canvasId, datasets, options = {{}}) {{
          const canvas = document.getElementById(canvasId);
          const ctx = canvas.getContext("2d");
          const width = canvas.width;
          const height = canvas.height;
          ctx.clearRect(0, 0, width, height);

          const allValues = datasets.flatMap((set) => set.values.map((item) => item.value));
          if (!allValues.length) {{
            ctx.fillStyle = "#60707b";
            ctx.font = "14px Segoe UI";
            ctx.fillText("Нет данных для графика", 20, 40);
            return;
          }}

          const min = Math.min(...allValues);
          const max = Math.max(...allValues);
          const range = max - min || 1;
          const padding = 28;

          ctx.strokeStyle = "#d7cec0";
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(padding, height - padding);
          ctx.lineTo(width - padding, height - padding);
          ctx.moveTo(padding, padding / 2);
          ctx.lineTo(padding, height - padding);
          ctx.stroke();

          datasets.forEach((set) => {{
            if (!set.values.length) return;
            ctx.strokeStyle = set.color;
            ctx.lineWidth = 2.4;
            ctx.beginPath();
            set.values.forEach((point, index) => {{
              const x = padding + ((width - padding * 2) * index) / Math.max(set.values.length - 1, 1);
              const y = height - padding - ((point.value - min) / range) * (height - padding * 1.8);
              if (index === 0) ctx.moveTo(x, y);
              else ctx.lineTo(x, y);
            }});
            ctx.stroke();
          }});

          ctx.fillStyle = "#60707b";
          ctx.font = "12px Segoe UI";
          ctx.fillText(`${{options.minLabel || min.toFixed(2)}}`, 4, height - padding + 4);
          ctx.fillText(`${{options.maxLabel || max.toFixed(2)}}`, 4, 16);

          let legendX = padding;
          datasets.forEach((set) => {{
            ctx.fillStyle = set.color;
            ctx.fillRect(legendX, 8, 12, 12);
            ctx.fillStyle = "#24313a";
            ctx.fillText(set.label, legendX + 16, 18);
            legendX += Math.max(90, set.label.length * 8 + 28);
          }});
        }}

        async function loadDashboard() {{
          document.getElementById("sync").textContent = "Обновление…";
          const response = await fetch("/api/v1/telegram/dashboard");
          const data = await response.json();
          renderDashboard(data);
          document.getElementById("sync").textContent = `Обновлено: ${{new Date().toLocaleTimeString("ru-RU")}}`;
        }}

        async function trainModel() {{
          if (!canTrain) return;
          document.getElementById("sync").textContent = "Идет обучение…";
          const response = await fetch("/api/v1/admin/model/train", {{
            method: "POST",
            headers: requestHeaders(),
          }});
          const data = await response.json();
          alert(`Обучение: ${{data.trained ? "успешно" : "не выполнено"}}${{data.samples ? `, выборка ${{data.samples}}` : ""}}`);
          await loadDashboard();
        }}

        function renderDashboard(data) {{
          document.getElementById("kpis").innerHTML = [
            ["Капитал", data.equity.toFixed(2)],
            ["Торговля", yesNo(data.trading_enabled)],
            ["Paper trading", yesNo(data.paper_trading)],
            ["Позиций", data.risk.open_positions],
            ["Дневной PnL", data.risk.daily_realized_pnl.toFixed(2)],
            ["Модель", data.model.trained ? "обучена" : "не обучена"],
          ].map(([label, value]) => (
            `<div class="card"><div class="muted small">${{esc(label)}}</div><div class="kpi-value">${{esc(value)}}</div></div>`
          )).join("");

          document.getElementById("marketCards").innerHTML = renderTable(
            [
              {{ label: "Символ", render: (row) => `<span class="mono">${{esc(row.symbol)}}</span>` }},
              {{ label: "Цена", render: (row) => Number(row.price).toFixed(4) }},
              {{ label: "Spread", render: (row) => (((row.ask - row.bid) / row.price) * 10000).toFixed(2) + " bps" }},
              {{ label: "Лента", render: (row) => Number(row.trade_imbalance).toFixed(3) }},
              {{ label: "Стакан", render: (row) => Number(row.orderbook_imbalance).toFixed(3) }},
              {{ label: "Источник", render: (row) => row.is_synthetic ? '<span class="badge danger">synthetic</span>' : '<span class="badge">Bybit</span>' }},
            ],
            data.snapshots
          );

          document.getElementById("strategyTable").innerHTML = renderTable(
            [
              {{ label: "Символ", render: (row) => esc(row.symbol) }},
              {{ label: "MA", render: (row) => `${{esc(row.ma_type)}} ${{row.ema_fast}}/${{row.ema_slow}}` }},
              {{ label: "RSI", render: (row) => row.rsi_period }},
              {{ label: "Риск", render: (row) => `${{(row.risk_pct * 100).toFixed(2)}}%` }},
              {{ label: "Порог модели", render: (row) => Number(row.min_model_score).toFixed(2) }},
              {{ label: "Max spread", render: (row) => `${{Number(row.max_spread_bps).toFixed(1)}} bps` }},
              {{ label: "Включена", render: (row) => yesNo(row.is_enabled) }},
            ],
            data.strategies
          );

          const signalMap = Object.fromEntries(data.signals.map((row) => [row.symbol, row]));
          const strategyMap = Object.fromEntries(data.strategies.map((row) => [row.symbol, row]));

          document.getElementById("calcTable").innerHTML = renderTable(
            [
              {{ label: "Символ", render: (row) => `<span class="mono">${{esc(row.symbol)}}</span>` }},
              {{ label: "Spread", render: (row) => `${{row.spreadBps.toFixed(2)}} bps` }},
              {{ label: "Волатильность", render: (row) => `${{row.volatilityBps.toFixed(2)}} bps` }},
              {{ label: "RSI", render: (row) => row.rsi == null ? "n/a" : Number(row.rsi).toFixed(2) }},
              {{ label: "EMA gap", render: (row) => row.emaGap == null ? "n/a" : `${{Number(row.emaGap).toFixed(4)}}%` }},
              {{ label: "Model score", render: (row) => Number(row.modelScore).toFixed(3) }},
              {{ label: "Signal score", render: (row) => Number(row.signalScore).toFixed(3) }},
              {{ label: "Лимит spread", render: (row) => `${{Number(row.maxSpread).toFixed(1)}} bps` }},
              {{ label: "Риск", render: (row) => `${{Number(row.riskPct * 100).toFixed(2)}}%` }},
            ],
            data.snapshots.map((snapshot) => {{
              const signal = signalMap[snapshot.symbol] || {{}};
              const strategy = strategyMap[snapshot.symbol] || {{}};
              const indicators = signal.indicators_snapshot || {{}};
              const spreadBps = snapshot.price ? ((snapshot.ask - snapshot.bid) / snapshot.price) * 10000 : 0;
              const emaFast = indicators.ema9;
              const emaSlow = indicators.ema21;
              return {{
                symbol: snapshot.symbol,
                spreadBps,
                volatilityBps: snapshot.volatility_bps,
                rsi: indicators.rsi14,
                emaGap: emaFast && emaSlow ? ((emaFast - emaSlow) / emaSlow) * 100 : null,
                modelScore: signal.rationale?.model_score ?? 0,
                signalScore: signal.score ?? 0,
                maxSpread: strategy.max_spread_bps ?? 0,
                riskPct: strategy.risk_pct ?? 0,
              }};
            }})
          );

          document.getElementById("riskTable").innerHTML = renderTable(
            [
              {{ label: "Параметр", render: (row) => esc(row.name) }},
              {{ label: "Значение", render: (row) => esc(row.value) }},
            ],
            [
              {{ name: "Торговля включена", value: yesNo(data.risk.trading_enabled) }},
              {{ name: "Paper trading", value: yesNo(data.risk.paper_trading) }},
              {{ name: "Circuit breaker", value: yesNo(data.risk.circuit_breaker_open) }},
              {{ name: "Дневной PnL", value: Number(data.risk.daily_realized_pnl).toFixed(2) }},
              {{ name: "Лимит дневного убытка", value: `${{Number(data.risk.daily_loss_limit_pct * 100).toFixed(2)}}%` }},
              {{ name: "Серия убытков", value: String(data.risk.consecutive_losses) }},
              {{ name: "Открытых позиций", value: String(data.risk.open_positions) }},
              {{ name: "Максимум позиций", value: String(data.risk.max_concurrent_positions) }},
            ]
          );

          document.getElementById("signalTable").innerHTML = renderTable(
            [
              {{ label: "Время", render: (row) => fmtTime(row.observed_at) }},
              {{ label: "Символ", render: (row) => esc(row.symbol) }},
              {{ label: "Направление", render: (row) => row.direction === "long" ? "лонг" : row.direction === "short" ? "шорт" : "нейтрально" }},
              {{ label: "Score", render: (row) => Number(row.score).toFixed(3) }},
              {{ label: "Торговать", render: (row) => yesNo(row.should_trade) }},
              {{ label: "Причина", render: (row) => esc(row.rationale.reason || JSON.stringify(row.rationale)) }},
            ],
            data.signals
          );

          document.getElementById("positionTable").innerHTML = renderTable(
            [
              {{ label: "Символ", render: (row) => esc(row.symbol) }},
              {{ label: "Сторона", render: (row) => row.side === "long" ? "лонг" : "шорт" }},
              {{ label: "Qty", render: (row) => Number(row.quantity).toFixed(4) }},
              {{ label: "Вход", render: (row) => Number(row.entry_price).toFixed(4) }},
              {{ label: "SL / TP", render: (row) => `${{Number(row.stop_price).toFixed(4)}} / ${{Number(row.take_price).toFixed(4)}}` }},
            ],
            data.positions
          );

          document.getElementById("tradeTable").innerHTML = renderTable(
            [
              {{ label: "Закрыта", render: (row) => fmtTime(row.closed_at) }},
              {{ label: "Символ", render: (row) => esc(row.symbol) }},
              {{ label: "Сторона", render: (row) => row.side === "long" ? "лонг" : "шорт" }},
              {{ label: "PnL", render: (row) => `<span class="${{row.pnl >= 0 ? "ok" : "warn"}}">${{Number(row.pnl).toFixed(4)}}</span>` }},
              {{ label: "Причина", render: (row) => esc(row.reason) }},
            ],
            data.trades
          );

          document.getElementById("newsTable").innerHTML = renderTable(
            [
              {{ label: "Время", render: (row) => fmtTime(row.published_at) }},
              {{ label: "Заголовок", render: (row) => `<strong>${{esc(row.title)}}</strong><div class="muted small">${{esc(row.summary)}}</div>` }},
              {{ label: "Язык", render: (row) => esc(row.language) }},
              {{ label: "Sentiment", render: (row) => Number(row.sentiment).toFixed(2) }},
            ],
            data.news
          );

          document.getElementById("whaleTable").innerHTML = renderTable(
            [
              {{ label: "Время", render: (row) => fmtTime(row.timestamp) }},
              {{ label: "Актив", render: (row) => esc(row.asset) }},
              {{ label: "USD", render: (row) => Number(row.usd_value).toFixed(2) }},
              {{ label: "Маршрут", render: (row) => `${{esc(row.from_type)}} → ${{esc(row.to_type)}}` }},
              {{ label: "Score", render: (row) => Number(row.significance_score).toFixed(2) }},
            ],
            data.whales
          );

          document.getElementById("modelInfo").innerHTML = `
            <div class="small muted">Тип модели</div>
            <div><strong>${{esc(data.model.model_type)}}</strong></div>
            <div class="small muted" style="margin-top:8px;">Файл</div>
            <div class="mono">${{esc(data.model.path)}}</div>
            <div class="small muted" style="margin-top:8px;">Размер</div>
            <div>${{Number(data.model.size_bytes).toLocaleString("ru-RU")}} байт</div>
            <div class="small muted" style="margin-top:8px;">Обновлена</div>
            <div>${{data.model.updated_at ? fmtTime(data.model.updated_at) : "нет данных"}}</div>
          `;

          drawLineChart("priceChart", Object.entries(data.charts.market_price).map(([symbol, values], idx) => ({{
            label: symbol,
            color: ["#0b7285", "#f08c6c", "#7b2cbf"][idx % 3],
            values,
          }})));
          drawLineChart("signalChart", Object.entries(data.charts.signal_score).map(([symbol, values], idx) => ({{
            label: symbol,
            color: ["#2b8a3e", "#c2255c", "#1c7ed6"][idx % 3],
            values,
          }})), {{ minLabel: "-1.00", maxLabel: "1.00" }});
          drawLineChart("whaleChart", Object.entries(data.charts.whale_usd).map(([asset, values], idx) => ({{
            label: asset,
            color: ["#f08c00", "#2f9e44", "#1971c2"][idx % 3],
            values,
          }})));
          drawLineChart("newsChart", [
            {{ label: "Новости", color: "#7048e8", values: data.charts.news_sentiment }},
          ]);
          drawLineChart("tradeChart", [
            {{ label: "PnL", color: "#0ca678", values: data.charts.trade_pnl }},
          ]);
          drawLineChart("modelChart", [
            {{ label: "Сэмплы", color: "#c92a2a", values: data.charts.model_training }},
          ]);
        }}

        loadDashboard().catch((error) => {{
          document.getElementById("sync").textContent = `Ошибка: ${{error.message}}`;
        }});
      </script>
    </body>
    </html>
    """
    return HTMLResponse(html)


@router.post("/simulate/{command}", response_model=MessageResponse)
async def simulate_command(command: str, services=Depends(get_services)) -> MessageResponse:
    runtime = services.runtime
    if command == "status":
        return MessageResponse(message=f"Капитал={runtime.equity:.2f}, позиций={len(runtime.paper.positions)}")
    if command == "enable":
        runtime.trading_enabled = True
        return MessageResponse(message="Торговля включена")
    if command == "disable":
        runtime.trading_enabled = False
        return MessageResponse(message="Торговля отключена")
    if command == "risk":
        return MessageResponse(message=f"Дневной PnL={runtime.risk.daily_realized_pnl:.2f}")
    if command == "miniapp":
        return MessageResponse(message="Mini App готова к открытию")
    return MessageResponse(message=f"Команда {command} обработана")


async def _build_charts(
    trading_repo: TradingRepository,
    analytics_repo: AnalyticsRepository,
    symbols: list[str],
    trades,
) -> DashboardChartsResponse:
    market_price: dict[str, list[TimeValuePoint]] = {}
    signal_score: dict[str, list[TimeValuePoint]] = {}
    whale_usd: dict[str, list[TimeValuePoint]] = defaultdict(list)

    for symbol in symbols:
        snapshots = list(reversed(await trading_repo.list_recent_snapshots_for_symbol(symbol, limit=30)))
        market_price[symbol] = [
            TimeValuePoint(timestamp=item.observed_at, value=item.price, label=symbol)
            for item in snapshots
        ]

    signals = list(reversed(await trading_repo.list_signals(limit=120)))
    per_symbol_signals: dict[str, list[TimeValuePoint]] = defaultdict(list)
    for item in signals:
        if len(per_symbol_signals[item.symbol]) >= 20:
            continue
        per_symbol_signals[item.symbol].append(
            TimeValuePoint(timestamp=item.observed_at, value=item.score, label=item.direction)
        )
    signal_score = dict(per_symbol_signals)

    whales = list(reversed(await analytics_repo.list_whales(limit=60)))
    for item in whales:
        whale_usd[item.asset].append(
            TimeValuePoint(timestamp=item.timestamp, value=item.usd_value, label=item.to_type)
        )

    news = list(reversed(await analytics_repo.list_news(limit=24)))
    news_sentiment = [
        TimeValuePoint(
            timestamp=item.published_at,
            value=item.sentiment + item.relevance * 0.2,
            label=item.title[:60],
        )
        for item in news
    ]

    running = 0.0
    trade_pnl = []
    for item in reversed(trades):
        running += item.pnl
        trade_pnl.append(TimeValuePoint(timestamp=item.closed_at, value=running, label=item.symbol))

    training_logs = []
    audit_logs = list(reversed(await analytics_repo.list_audit_logs(limit=80)))
    for item in audit_logs:
        if item.action != "model_trained":
            continue
        training_logs.append(
            TimeValuePoint(
                timestamp=item.created_at,
                value=float(item.details.get("samples", 0)),
                label=str(item.details.get("model_type", "model")),
                meta=item.details,
            )
        )

    return DashboardChartsResponse(
        market_price=market_price,
        signal_score=signal_score,
        whale_usd=dict(whale_usd),
        news_sentiment=news_sentiment,
        trade_pnl=trade_pnl,
        model_training=training_logs,
    )
