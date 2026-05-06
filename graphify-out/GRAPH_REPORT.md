# Graph Report - D:\Projects\Trading\trading_bot  (2026-05-06)

## Corpus Check
- 55 files · ~167,491 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 423 nodes · 1008 edges · 32 communities detected
- Extraction: 50% EXTRACTED · 50% INFERRED · 0% AMBIGUOUS · INFERRED: 499 edges (avg confidence: 0.59)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]

## God Nodes (most connected - your core abstractions)
1. `DataStorage` - 81 edges
2. `RiskManager` - 77 edges
3. `DataFetcher` - 70 edges
4. `Broker` - 61 edges
5. `BacktestEngine` - 51 edges
6. `PairsTradingStrategy` - 48 edges
7. `OrderManager` - 46 edges
8. `TradingBot` - 32 edges
9. `DataValidator` - 25 edges
10. `BaseStrategy` - 16 edges

## Surprising Connections (you probably didn't know these)
- `DataStorage` --uses--> `Calculate stop loss price based on ATR or fixed percentage.         For long: st`  [INFERRED]
  old version\data\storage.py → risk\manager.py
- `DataStorage` --uses--> `Calculate take profit price based on risk-reward ratio.`  [INFERRED]
  old version\data\storage.py → risk\manager.py
- `DataStorage` --uses--> `Get current risk metrics for monitoring.`  [INFERRED]
  old version\data\storage.py → risk\manager.py
- `BotRuntime` --uses--> `DataStorage`  [INFERRED]
  old version\design_python_desktop.py → old version\data\storage.py
- `BotRuntime` --uses--> `Broker`  [INFERRED]
  old version\design_python_desktop.py → old version\execution\broker.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.07
Nodes (42): BaseStrategy, Broker, OrderManager, BacktestEngine, example_backtest(), example_execution(), example_risk_management(), example_strategy() (+34 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (31): get_design_component_info(), init_design_system(), list_design_components(), Design System Integration with Trading Bot This module ensures the design system, Initialize the design system for the trading bot., Get information about a specific design component.          Args:         compon, List all available design components.          Returns:         List of componen, Verify that the design system is properly set up.          Returns:         True (+23 more)

### Community 2 - "Community 2"
Cohesion: 0.09
Nodes (14): Process a trading signal., Update unrealized P&L for open positions., Close a position and record the trade., Close all open positions., Calculate current equity including unrealized P&L., Run a backtest for a given strategy on historical data.         Returns a dictio, Reset backtest state., Calculate stop loss price based on ATR or fixed percentage.         For long: st (+6 more)

### Community 3 - "Community 3"
Cohesion: 0.12
Nodes (24): BaseModel, main(), TradingBot, BotStatusResponse, StartRequest, TradeResponse, ConnectionManager, get_analytics() (+16 more)

### Community 4 - "Community 4"
Cohesion: 0.1
Nodes (18): log_error(), log_performance(), log_signal(), log_trade(), MonitoringSystem, Log a trade execution., Log a trading signal., Log performance metrics. (+10 more)

### Community 5 - "Community 5"
Cohesion: 0.11
Nodes (9): Check if weekly loss limit has been breached.         Returns True if trading sh, Check if monthly loss limit has been breached.         Returns True if trading s, Check if maximum drawdown has been breached.         Returns True if trading sho, Get the peak equity from storage., Check if we have exceeded maximum number of positions or position size limits., Determine if we can open a new position based on all risk checks., Calculate position size based on risk per trade and stop loss distance., Check if daily loss limit has been breached.         Returns True if trading sho (+1 more)

### Community 6 - "Community 6"
Cohesion: 0.11
Nodes (8): BotRuntime, Get current bot status., Start the trading bot in a separate thread., Stop the trading bot., example_data_operations(), Demonstrate data fetching and storage., DataFetcher, Run the bot in backtest mode.

### Community 7 - "Community 7"
Cohesion: 0.09
Nodes (15): api_bot_status(), api_components(), api_design_spec(), health(), logs(), positions(), Web Frontend Server for Trading Bot Serves the design UI components and provides, Get trading bot status (+7 more)

### Community 8 - "Community 8"
Cohesion: 0.13
Nodes (11): ABC, BaseStrategy, calculate_position_size(), generate_signals(), Validate that a signal contains all required information., Set strategy parameters., Get current strategy parameters., Calculate hedge ratio using linear regression.         price1 = hedge_ratio * pr (+3 more)

### Community 9 - "Community 9"
Cohesion: 0.19
Nodes (14): Calculate and return backtest results., calculate_max_drawdown(), calculate_profit_factor(), calculate_sharpe(), ensure_dir(), format_currency(), format_percent(), get_date() (+6 more)

### Community 10 - "Community 10"
Cohesion: 0.26
Nodes (14): main(), MainWindow, _render_page(), route_action(), route_analytics(), route_configuration(), route_dashboard(), route_favicon() (+6 more)

### Community 11 - "Community 11"
Cohesion: 0.21
Nodes (12): analytics(), api_bot_status(), api_design_spec(), configuration(), dashboard(), _get_live_bot_snapshot(), index(), logs() (+4 more)

### Community 12 - "Community 12"
Cohesion: 0.4
Nodes (0): 

### Community 13 - "Community 13"
Cohesion: 0.5
Nodes (2): App(), useWebSocket()

### Community 14 - "Community 14"
Cohesion: 0.67
Nodes (0): 

### Community 15 - "Community 15"
Cohesion: 1.0
Nodes (0): 

### Community 16 - "Community 16"
Cohesion: 1.0
Nodes (0): 

### Community 17 - "Community 17"
Cohesion: 1.0
Nodes (0): 

### Community 18 - "Community 18"
Cohesion: 1.0
Nodes (0): 

### Community 19 - "Community 19"
Cohesion: 1.0
Nodes (0): 

### Community 20 - "Community 20"
Cohesion: 1.0
Nodes (0): 

### Community 21 - "Community 21"
Cohesion: 1.0
Nodes (0): 

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (0): 

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (0): 

### Community 24 - "Community 24"
Cohesion: 1.0
Nodes (0): 

### Community 25 - "Community 25"
Cohesion: 1.0
Nodes (1): Generate trading signals from market data.         Should return DataFrame with

### Community 26 - "Community 26"
Cohesion: 1.0
Nodes (1): Calculate position size for a given signal.

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (0): 

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (0): 

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (0): 

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (0): 

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **39 isolated node(s):** `Log a trade execution.`, `Log a trading signal.`, `Log performance metrics.`, `Send an alert (could be email, Telegram, etc.).`, `Get recent performance metrics.` (+34 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 15`** (2 nodes): `reportWebVitals.js`, `reportWebVitals()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 16`** (2 nodes): `Analytics()`, `Analytics.jsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 17`** (2 nodes): `ControlPanel()`, `ControlPanel.jsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 18`** (2 nodes): `History.jsx`, `History()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (2 nodes): `NotificationsDropdown.jsx`, `NotificationsDropdown()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (2 nodes): `OrderBook.jsx`, `OrderBook()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (2 nodes): `Profile.jsx`, `Profile()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (2 nodes): `SettingsModal.jsx`, `SettingsModal()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (2 nodes): `Tooltip.jsx`, `Tooltip()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (1 nodes): `config.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (1 nodes): `Generate trading signals from market data.         Should return DataFrame with`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (1 nodes): `Calculate position size for a given signal.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (1 nodes): `postcss.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (1 nodes): `vite.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (1 nodes): `App.test.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (1 nodes): `index.jsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (1 nodes): `setupTests.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DataStorage` connect `Community 5` to `Community 0`, `Community 2`, `Community 3`, `Community 4`, `Community 6`, `Community 9`, `Community 10`, `Community 11`?**
  _High betweenness centrality (0.130) - this node is a cross-community bridge._
- **Why does `RiskManager` connect `Community 0` to `Community 2`, `Community 3`, `Community 4`, `Community 5`, `Community 6`, `Community 8`, `Community 9`, `Community 10`, `Community 11`?**
  _High betweenness centrality (0.113) - this node is a cross-community bridge._
- **Why does `TradingBot` connect `Community 3` to `Community 0`, `Community 4`, `Community 5`, `Community 6`, `Community 10`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Are the 67 inferred relationships involving `DataStorage` (e.g. with `TradingBot` and `Initialize the trading bot.`) actually correct?**
  _`DataStorage` has 67 INFERRED edges - model-reasoned connections that need verification._
- **Are the 60 inferred relationships involving `RiskManager` (e.g. with `TradingBot` and `Initialize the trading bot.`) actually correct?**
  _`RiskManager` has 60 INFERRED edges - model-reasoned connections that need verification._
- **Are the 56 inferred relationships involving `DataFetcher` (e.g. with `TradingBot` and `Initialize the trading bot.`) actually correct?**
  _`DataFetcher` has 56 INFERRED edges - model-reasoned connections that need verification._
- **Are the 45 inferred relationships involving `Broker` (e.g. with `TradingBot` and `Initialize the trading bot.`) actually correct?**
  _`Broker` has 45 INFERRED edges - model-reasoned connections that need verification._