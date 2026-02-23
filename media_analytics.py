#!/usr/bin/env python3
"""BlackRoad Media Analytics - Media content performance analytics and reporting"""

import sqlite3
import uuid
import json
import math
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Tuple
from datetime import datetime, timezone, timedelta
from enum import Enum


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ContentType(str, Enum):
    VIDEO = "video"
    IMAGE = "image"
    ARTICLE = "article"
    PODCAST = "podcast"


@dataclass
class ContentItem:
    id: str
    title: str
    type: str
    platform: str
    url: str
    published_at: str
    created_at: str = field(default_factory=_now)
    tags: str = "[]"

    @property
    def tags_list(self) -> list:
        return json.loads(self.tags or "[]")

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class MetricSnapshot:
    id: str
    item_id: str
    captured_at: str
    views: int = 0
    likes: int = 0
    shares: int = 0
    comments: int = 0
    watch_time_sec: int = 0
    revenue_usd: float = 0.0

    @property
    def engagement_rate(self) -> float:
        if self.views == 0:
            return 0.0
        engaged = self.likes + self.shares + self.comments
        return round(engaged / self.views, 4)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Benchmark:
    id: str
    content_type: str
    metric: str
    p50: float
    p75: float
    p90: float
    sample_size: int
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return asdict(self)


class MediaAnalytics:
    """Media content performance analytics and reporting engine."""

    def __init__(self, db_path: str = "media_analytics.db"):
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS content_items (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    type TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    url TEXT NOT NULL,
                    published_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    tags TEXT DEFAULT '[]'
                );

                CREATE TABLE IF NOT EXISTS metric_snapshots (
                    id TEXT PRIMARY KEY,
                    item_id TEXT NOT NULL,
                    captured_at TEXT NOT NULL,
                    views INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    shares INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    watch_time_sec INTEGER DEFAULT 0,
                    revenue_usd REAL DEFAULT 0.0,
                    FOREIGN KEY (item_id) REFERENCES content_items(id)
                );

                CREATE TABLE IF NOT EXISTS benchmarks (
                    id TEXT PRIMARY KEY,
                    content_type TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    p50 REAL NOT NULL,
                    p75 REAL NOT NULL,
                    p90 REAL NOT NULL,
                    sample_size INTEGER NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(content_type, metric)
                );

                CREATE INDEX IF NOT EXISTS idx_snapshots_item
                    ON metric_snapshots(item_id);
                CREATE INDEX IF NOT EXISTS idx_snapshots_captured
                    ON metric_snapshots(captured_at DESC);
                CREATE INDEX IF NOT EXISTS idx_items_type
                    ON content_items(type);
                CREATE INDEX IF NOT EXISTS idx_items_platform
                    ON content_items(platform);
            """)

    def register_content(self, title: str, content_type: str,
                         platform: str, url: str,
                         published_at: Optional[str] = None,
                         tags: Optional[List[str]] = None) -> ContentItem:
        """Register a new content item for tracking."""
        item_id = str(uuid.uuid4())
        now = _now()
        item = ContentItem(
            id=item_id,
            title=title,
            type=content_type,
            platform=platform,
            url=url,
            published_at=published_at or now,
            created_at=now,
            tags=json.dumps(tags or []),
        )
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO content_items
                (id, title, type, platform, url, published_at, created_at, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (item.id, item.title, item.type, item.platform,
                  item.url, item.published_at, item.created_at, item.tags))
        return item

    def get_content(self, item_id: str) -> Optional[ContentItem]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM content_items WHERE id=?", (item_id,)).fetchone()
        return ContentItem(**dict(row)) if row else None

    def record_metrics(self, item_id: str, views: int = 0, likes: int = 0,
                       shares: int = 0, comments: int = 0,
                       watch_time_sec: int = 0, revenue_usd: float = 0.0) -> MetricSnapshot:
        """Record a metrics snapshot for a content item."""
        if not self.get_content(item_id):
            raise ValueError(f"Content {item_id} not found")
        snap = MetricSnapshot(
            id=str(uuid.uuid4()),
            item_id=item_id,
            captured_at=_now(),
            views=views,
            likes=likes,
            shares=shares,
            comments=comments,
            watch_time_sec=watch_time_sec,
            revenue_usd=revenue_usd,
        )
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO metric_snapshots
                (id, item_id, captured_at, views, likes, shares, comments,
                 watch_time_sec, revenue_usd)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (snap.id, snap.item_id, snap.captured_at, snap.views,
                  snap.likes, snap.shares, snap.comments,
                  snap.watch_time_sec, snap.revenue_usd))
        return snap

    def get_latest_metrics(self, item_id: str) -> Optional[MetricSnapshot]:
        """Get the most recent metrics snapshot for an item."""
        with self._connect() as conn:
            row = conn.execute("""
                SELECT * FROM metric_snapshots WHERE item_id=?
                ORDER BY captured_at DESC LIMIT 1
            """, (item_id,)).fetchone()
        return MetricSnapshot(**dict(row)) if row else None

    def get_metrics_history(self, item_id: str,
                            limit: int = 30) -> List[MetricSnapshot]:
        """Get metrics history for an item."""
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT * FROM metric_snapshots WHERE item_id=?
                ORDER BY captured_at DESC LIMIT ?
            """, (item_id, limit)).fetchall()
        return [MetricSnapshot(**dict(r)) for r in rows]

    def trend_analysis(self, item_id: str, window_days: int = 30) -> dict:
        """Analyze trends for a content item over a time window."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=window_days)).isoformat()
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT * FROM metric_snapshots
                WHERE item_id=? AND captured_at >= ?
                ORDER BY captured_at ASC
            """, (item_id, cutoff)).fetchall()

        if not rows:
            return {"item_id": item_id, "window_days": window_days, "snapshots": 0}

        snapshots = [MetricSnapshot(**dict(r)) for r in rows]
        views_list = [s.views for s in snapshots]
        likes_list = [s.likes for s in snapshots]
        revenue_list = [s.revenue_usd for s in snapshots]

        def _pct_change(vals: list) -> float:
            if len(vals) < 2 or vals[0] == 0:
                return 0.0
            return round((vals[-1] - vals[0]) / vals[0] * 100, 2)

        def _avg(vals: list) -> float:
            return round(sum(vals) / len(vals), 2) if vals else 0.0

        def _max(vals: list) -> float:
            return max(vals) if vals else 0.0

        return {
            "item_id": item_id,
            "window_days": window_days,
            "snapshots": len(snapshots),
            "views": {
                "total": sum(views_list),
                "avg": _avg(views_list),
                "peak": _max(views_list),
                "change_pct": _pct_change(views_list),
            },
            "likes": {
                "total": sum(likes_list),
                "avg": _avg(likes_list),
                "change_pct": _pct_change(likes_list),
            },
            "revenue": {
                "total": round(sum(revenue_list), 2),
                "avg": _avg(revenue_list),
                "change_pct": _pct_change(revenue_list),
            },
            "avg_engagement_rate": round(
                sum(s.engagement_rate for s in snapshots) / len(snapshots), 4
            ),
        }

    def top_performers(self, metric: str = "views", n: int = 10,
                       content_type: Optional[str] = None) -> List[dict]:
        """Get top N performing content items by a metric."""
        valid_metrics = {"views", "likes", "shares", "comments", "watch_time_sec", "revenue_usd"}
        if metric not in valid_metrics:
            raise ValueError(f"Invalid metric '{metric}'. Valid: {valid_metrics}")

        query = f"""
            SELECT ci.id, ci.title, ci.type, ci.platform,
                   SUM(ms.{metric}) as total_metric,
                   COUNT(ms.id) as snapshot_count,
                   MAX(ms.captured_at) as last_updated
            FROM content_items ci
            LEFT JOIN metric_snapshots ms ON ci.id = ms.item_id
            {"WHERE ci.type = ?" if content_type else ""}
            GROUP BY ci.id
            ORDER BY total_metric DESC
            LIMIT ?
        """
        params = (content_type, n) if content_type else (n,)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        return [
            {
                "item_id": r["id"],
                "title": r["title"],
                "type": r["type"],
                "platform": r["platform"],
                f"total_{metric}": r["total_metric"] or 0,
                "snapshot_count": r["snapshot_count"],
            }
            for r in rows
        ]

    def platform_comparison(self, metric: str = "views") -> List[dict]:
        """Compare performance across platforms for a metric."""
        valid_metrics = {"views", "likes", "shares", "comments", "watch_time_sec", "revenue_usd"}
        if metric not in valid_metrics:
            raise ValueError(f"Invalid metric '{metric}'")

        with self._connect() as conn:
            rows = conn.execute(f"""
                SELECT ci.platform,
                       COUNT(DISTINCT ci.id) as item_count,
                       SUM(ms.{metric}) as total,
                       AVG(ms.{metric}) as avg_val
                FROM content_items ci
                LEFT JOIN metric_snapshots ms ON ci.id = ms.item_id
                GROUP BY ci.platform
                ORDER BY total DESC
            """).fetchall()

        return [
            {
                "platform": r["platform"],
                "item_count": r["item_count"],
                f"total_{metric}": round(r["total"] or 0, 2),
                f"avg_{metric}": round(r["avg_val"] or 0, 2),
            }
            for r in rows
        ]

    def revenue_attribution(self, item_id: str) -> dict:
        """Get revenue breakdown for a content item."""
        item = self.get_content(item_id)
        if not item:
            return {"error": "Content not found"}

        with self._connect() as conn:
            rows = conn.execute("""
                SELECT revenue_usd, views, captured_at
                FROM metric_snapshots WHERE item_id=?
                ORDER BY captured_at ASC
            """, (item_id,)).fetchall()

        if not rows:
            return {"item_id": item_id, "total_revenue": 0.0, "snapshots": 0}

        revenues = [r["revenue_usd"] for r in rows]
        total_views = sum(r["views"] for r in rows)
        total_rev = sum(revenues)
        rpm = (total_rev / total_views * 1000) if total_views > 0 else 0.0

        return {
            "item_id": item_id,
            "title": item.title,
            "platform": item.platform,
            "total_revenue_usd": round(total_rev, 2),
            "rpm_usd": round(rpm, 4),
            "total_views": total_views,
            "snapshot_count": len(rows),
            "avg_revenue_per_snapshot": round(total_rev / len(rows), 4),
        }

    def _percentiles(self, values: List[float]) -> Tuple[float, float, float]:
        """Calculate p50, p75, p90 from a list of values."""
        if not values:
            return 0.0, 0.0, 0.0
        s = sorted(values)
        n = len(s)
        p50 = s[int(n * 0.5)]
        p75 = s[int(n * 0.75)]
        p90 = s[min(int(n * 0.9), n - 1)]
        return float(p50), float(p75), float(p90)

    def benchmark_update(self, content_type: str, metric: str) -> Benchmark:
        """Recalculate benchmark percentiles for a content type and metric."""
        valid_metrics = {"views", "likes", "shares", "comments", "watch_time_sec", "revenue_usd"}
        if metric not in valid_metrics:
            raise ValueError(f"Invalid metric '{metric}'")

        with self._connect() as conn:
            rows = conn.execute(f"""
                SELECT ms.{metric} as val
                FROM metric_snapshots ms
                JOIN content_items ci ON ms.item_id = ci.id
                WHERE ci.type = ?
            """, (content_type,)).fetchall()

        values = [r["val"] for r in rows if r["val"] is not None]
        p50, p75, p90 = self._percentiles(values)

        bm = Benchmark(
            id=str(uuid.uuid4()),
            content_type=content_type,
            metric=metric,
            p50=p50,
            p75=p75,
            p90=p90,
            sample_size=len(values),
        )

        with self._connect() as conn:
            conn.execute("""
                INSERT INTO benchmarks (id, content_type, metric, p50, p75, p90, sample_size, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(content_type, metric) DO UPDATE SET
                    p50=excluded.p50, p75=excluded.p75, p90=excluded.p90,
                    sample_size=excluded.sample_size, updated_at=excluded.updated_at
            """, (bm.id, bm.content_type, bm.metric, bm.p50, bm.p75, bm.p90,
                  bm.sample_size, bm.updated_at))
        return bm

    def get_benchmark(self, content_type: str, metric: str) -> Optional[Benchmark]:
        with self._connect() as conn:
            row = conn.execute("""
                SELECT * FROM benchmarks WHERE content_type=? AND metric=?
            """, (content_type, metric)).fetchone()
        return Benchmark(**dict(row)) if row else None

    def weekly_report(self) -> dict:
        """Generate a weekly performance report."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        with self._connect() as conn:
            total_items = conn.execute("SELECT COUNT(*) FROM content_items").fetchone()[0]
            new_items = conn.execute(
                "SELECT COUNT(*) FROM content_items WHERE published_at >= ?", (cutoff,)
            ).fetchone()[0]
            total_views = conn.execute(
                "SELECT SUM(views) FROM metric_snapshots WHERE captured_at >= ?", (cutoff,)
            ).fetchone()[0] or 0
            total_revenue = conn.execute(
                "SELECT SUM(revenue_usd) FROM metric_snapshots WHERE captured_at >= ?", (cutoff,)
            ).fetchone()[0] or 0.0
            top_by_views = conn.execute("""
                SELECT ci.title, ci.platform, SUM(ms.views) as total_views
                FROM content_items ci
                JOIN metric_snapshots ms ON ci.id = ms.item_id
                WHERE ms.captured_at >= ?
                GROUP BY ci.id
                ORDER BY total_views DESC
                LIMIT 5
            """, (cutoff,)).fetchall()
            by_type = conn.execute("""
                SELECT ci.type, COUNT(DISTINCT ci.id) as items, SUM(ms.views) as views
                FROM content_items ci
                LEFT JOIN metric_snapshots ms ON ci.id = ms.item_id
                WHERE ms.captured_at >= ?
                GROUP BY ci.type
            """, (cutoff,)).fetchall()

        return {
            "week_ending": _now(),
            "total_content_items": total_items,
            "new_items_this_week": new_items,
            "total_views_this_week": total_views,
            "total_revenue_this_week": round(total_revenue, 2),
            "top_performers": [
                {"title": r["title"], "platform": r["platform"], "views": r["total_views"]}
                for r in top_by_views
            ],
            "by_content_type": [
                {"type": r["type"], "items": r["items"], "views": r["views"] or 0}
                for r in by_type
            ],
        }

    def list_content(self, content_type: Optional[str] = None,
                     platform: Optional[str] = None,
                     limit: int = 50) -> List[ContentItem]:
        conditions = []
        params = []
        if content_type:
            conditions.append("type=?")
            params.append(content_type)
        if platform:
            conditions.append("platform=?")
            params.append(platform)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM content_items {where} ORDER BY published_at DESC LIMIT ?",
                params
            ).fetchall()
        return [ContentItem(**dict(r)) for r in rows]

    def get_platform_list(self) -> List[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT DISTINCT platform FROM content_items ORDER BY platform"
            ).fetchall()
        return [r["platform"] for r in rows]

    def get_overall_stats(self) -> dict:
        with self._connect() as conn:
            total_items = conn.execute("SELECT COUNT(*) FROM content_items").fetchone()[0]
            total_snapshots = conn.execute("SELECT COUNT(*) FROM metric_snapshots").fetchone()[0]
            total_views = conn.execute("SELECT SUM(views) FROM metric_snapshots").fetchone()[0] or 0
            total_revenue = conn.execute(
                "SELECT SUM(revenue_usd) FROM metric_snapshots"
            ).fetchone()[0] or 0.0
        return {
            "total_content_items": total_items,
            "total_snapshots": total_snapshots,
            "total_views": total_views,
            "total_revenue_usd": round(total_revenue, 2),
        }


def create_analytics(db_path: str = "media_analytics.db") -> MediaAnalytics:
    return MediaAnalytics(db_path=db_path)


if __name__ == "__main__":
    analytics = create_analytics()
    print("BlackRoad Media Analytics")
    print("=" * 40)

    items = []
    for i, (title, ctype, platform) in enumerate([
        ("How to Deploy with Railway", "video", "youtube"),
        ("BlackRoad OS Deep Dive", "article", "medium"),
        ("AI Agents Explained", "podcast", "spotify"),
        ("Dashboard UI Preview", "image", "instagram"),
    ]):
        pub = (datetime.now(timezone.utc) - timedelta(days=i * 10)).isoformat()
        item = analytics.register_content(title, ctype, platform, f"https://{platform}.com/{i}", pub)
        items.append(item)
        for j in range(5):
            analytics.record_metrics(
                item.id,
                views=1000 * (i + 1) + j * 200,
                likes=50 * (i + 1) + j * 10,
                shares=20 * (i + 1) + j * 5,
                comments=10 * (i + 1) + j * 3,
                revenue_usd=round((i + 1) * 5.0 + j * 0.5, 2),
            )

    top = analytics.top_performers("views", n=3)
    print(f"\nTop 3 by views: {[t['title'] for t in top]}")

    comp = analytics.platform_comparison("views")
    print(f"Platform comparison: {[c['platform'] for c in comp]}")

    trend = analytics.trend_analysis(items[0].id)
    print(f"Trend (views change): {trend['views']['change_pct']}%")

    rev = analytics.revenue_attribution(items[0].id)
    print(f"Revenue: ${rev['total_revenue_usd']}")

    bm = analytics.benchmark_update("video", "views")
    print(f"Video views benchmark - p50: {bm.p50}, p75: {bm.p75}")

    report = analytics.weekly_report()
    print(f"Weekly report: {report['total_views_this_week']} views, ${report['total_revenue_this_week']} revenue")
