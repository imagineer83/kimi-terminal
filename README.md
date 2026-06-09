# Kimi Terminal

Bloomberg-style terminal for Mainland China (A-share) and Hong Kong stock market data, powered by `plugin-kimi-datasource`.

## Features

- Real-time watchlist dashboard with auto refresh
- Individual stock quote with price trend and technical indicators
- Financial statements and financial index analysis
- A-share announcements
- Intelligent stock screener

## Install

```bash
git clone <repo>
cd kimi-terminal
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run

```bash
kmt
```

## Shortcuts

| Key | Action |
|---|---|
| `F1` / `d` | Dashboard |
| `F2` / `:` | Command bar |
| `Enter` | Open selected stock detail |
| `a` | Add to watchlist |
| `d` | Remove from watchlist / go back |
| `q` | Quit |

## Commands

- `:EQ 600519.SH` — Open quote screen
- `:FA 0700.HK` — Open financials
- `:ANN 000001.SZ` — Open announcements
- `:SCR 人工智能 PE小于30` — Run screener
- `:ADD 0700.HK` — Add to watchlist
- `:DEL 0700.HK` — Remove from watchlist

## Test

```bash
make test
```
