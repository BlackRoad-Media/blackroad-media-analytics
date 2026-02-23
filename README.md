# BlackRoad Media Analytics

Media content performance analytics and reporting.

[![CI](https://github.com/BlackRoad-Media/blackroad-media-analytics/actions/workflows/ci.yml/badge.svg)](https://github.com/BlackRoad-Media/blackroad-media-analytics/actions/workflows/ci.yml)

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

## License
Proprietary - (c) BlackRoad OS, Inc.
