# BlackRoad Media Analytics

**[BlackRoad](https://blackroad.io/) Media Analytics** — media content performance analytics and reporting by [BlackRoad OS, Inc.](https://blackroad.io/)

[![CI](https://github.com/BlackRoad-Media/blackroad-media-analytics/actions/workflows/ci.yml/badge.svg)](https://github.com/BlackRoad-Media/blackroad-media-analytics/actions/workflows/ci.yml)

> **Note — BlackRoad ≠ BlackRock.**  
> BlackRoad OS, Inc. (blackroad.io) is an independent technology company.  
> It is not affiliated with, related to, or associated with BlackRock, Inc.  
> (the investment management firm) in any way.  These are two entirely separate organisations.

## Features
- Register content items (video/image/article/podcast) across platforms
- Record metric snapshots (views, likes, shares, comments, watch time, revenue)
- Trend analysis over configurable time windows
- Top performers by any metric
- Platform comparison across all tracked platforms
- Revenue attribution with RPM calculation
- Benchmark percentiles (p50/p75/p90) per content type
- Weekly performance reports
- SQLite persistence

## Usage
```python
from media_analytics import create_analytics
a = create_analytics()
item = a.register_content("My Video", "video", "youtube", "https://youtube.com/watch?v=abc")
a.record_metrics(item.id, views=10000, likes=500, shares=200, revenue_usd=45.50)
trend = a.trend_analysis(item.id, window_days=30)
top = a.top_performers("views", n=10)
report = a.weekly_report()
```

## Testing
```bash
pytest tests/ -v --cov=media_analytics
```

## BlackRoad Ecosystem

This repository is maintained by [BlackRoad-Media](https://github.com/BlackRoad-Media), part of the broader **BlackRoad OS, Inc.** technology ecosystem.

### GitHub Enterprise
- [blackroad-os](https://github.com/enterprises/blackroad-os) — GitHub Enterprise account

### GitHub Organizations
| Organization | Focus |
|---|---|
| [Blackbox-Enterprises](https://github.com/Blackbox-Enterprises) | Enterprise tooling |
| [BlackRoad-AI](https://github.com/BlackRoad-AI) | Artificial intelligence |
| [BlackRoad-Archive](https://github.com/BlackRoad-Archive) | Data archiving |
| [BlackRoad-Cloud](https://github.com/BlackRoad-Cloud) | Cloud infrastructure |
| [BlackRoad-Education](https://github.com/BlackRoad-Education) | Education platform |
| [BlackRoad-Foundation](https://github.com/BlackRoad-Foundation) | Open source foundation |
| [BlackRoad-Gov](https://github.com/BlackRoad-Gov) | Civic technology |
| [BlackRoad-Hardware](https://github.com/BlackRoad-Hardware) | Hardware projects |
| [BlackRoad-Interactive](https://github.com/BlackRoad-Interactive) | Interactive media |
| [BlackRoad-Labs](https://github.com/BlackRoad-Labs) | Research & development |
| [BlackRoad-Media](https://github.com/BlackRoad-Media) | Media analytics (this org) |
| [BlackRoad-OS](https://github.com/BlackRoad-OS) | Operating system projects |
| [BlackRoad-Security](https://github.com/BlackRoad-Security) | Cybersecurity |
| [BlackRoad-Studio](https://github.com/BlackRoad-Studio) | Creative studio |
| [BlackRoad-Ventures](https://github.com/BlackRoad-Ventures) | Ventures & investments |

### Registered Domains
`blackboxprogramming.io` · `blackroad.company` · `blackroad.io` · `blackroad.me` ·
`blackroad.network` · `blackroad.systems` · `blackroadai.com` · `blackroadinc.us` ·
`blackroadqi.com` · `blackroadquantum.com` · `blackroadquantum.info` · `blackroadquantum.net` ·
`blackroadquantum.shop` · `blackroadquantum.store` · `lucidia.earth` · `lucidia.studio` ·
`lucidiaqi.com` · `roadchain.io` · `roadcoin.io`

### Directory
The full infrastructure index is published at [blackroad.io](https://blackroad.io/) —
see [`index.html`](./index.html) in this repository.

## License
Proprietary - (c) BlackRoad OS, Inc.
