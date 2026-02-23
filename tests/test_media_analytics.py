import pytest
from datetime import datetime, timezone, timedelta
from media_analytics import (
    MediaAnalytics, ContentItem, MetricSnapshot, Benchmark,
    ContentType, create_analytics,
)


@pytest.fixture
def analytics(tmp_path):
    return MediaAnalytics(db_path=str(tmp_path / "test_analytics.db"))


@pytest.fixture
def analytics_with_data(analytics):
    items = []
    for i, (title, ctype, platform) in enumerate([
        ("Video One", "video", "youtube"),
        ("Article One", "article", "medium"),
        ("Podcast One", "podcast", "spotify"),
        ("Image One", "image", "instagram"),
    ]):
        pub = (datetime.now(timezone.utc) - timedelta(days=i * 5)).isoformat()
        item = analytics.register_content(title, ctype, platform,
                                           f"https://{platform}.com/{i}", pub)
        items.append(item)
        for j in range(3):
            analytics.record_metrics(
                item.id,
                views=500 * (i + 1) + j * 100,
                likes=25 * (i + 1) + j * 5,
                shares=10 * (i + 1) + j * 2,
                comments=5 * (i + 1) + j,
                revenue_usd=round((i + 1) * 2.5 + j * 0.25, 2),
            )
    return analytics, items


class TestContentRegistration:
    def test_register_content(self, analytics):
        item = analytics.register_content(
            "Test Video", "video", "youtube", "https://youtube.com/test"
        )
        assert item.id is not None
        assert item.title == "Test Video"
        assert item.type == "video"

    def test_get_content(self, analytics):
        item = analytics.register_content("Test", "article", "medium", "https://medium.com/test")
        fetched = analytics.get_content(item.id)
        assert fetched is not None
        assert fetched.id == item.id

    def test_get_nonexistent_content(self, analytics):
        assert analytics.get_content("nonexistent") is None

    def test_list_content_by_type(self, analytics_with_data):
        a, items = analytics_with_data
        videos = a.list_content(content_type="video")
        assert all(v.type == "video" for v in videos)

    def test_list_content_by_platform(self, analytics_with_data):
        a, items = analytics_with_data
        yt = a.list_content(platform="youtube")
        assert all(v.platform == "youtube" for v in yt)


class TestMetricRecording:
    def test_record_metrics(self, analytics):
        item = analytics.register_content("Test", "video", "youtube", "https://youtube.com/1")
        snap = analytics.record_metrics(item.id, views=1000, likes=50, shares=20)
        assert snap.id is not None
        assert snap.views == 1000
        assert snap.likes == 50

    def test_record_metrics_nonexistent(self, analytics):
        with pytest.raises(ValueError):
            analytics.record_metrics("nonexistent", views=100)

    def test_get_latest_metrics(self, analytics_with_data):
        a, items = analytics_with_data
        snap = a.get_latest_metrics(items[0].id)
        assert snap is not None
        assert snap.views > 0

    def test_engagement_rate(self, analytics):
        item = analytics.register_content("Test", "video", "youtube", "https://youtube.com/2")
        snap = analytics.record_metrics(item.id, views=1000, likes=50, shares=30, comments=20)
        assert snap.engagement_rate == pytest.approx(0.1, abs=0.001)


class TestAnalytics:
    def test_trend_analysis(self, analytics_with_data):
        a, items = analytics_with_data
        trend = a.trend_analysis(items[0].id, window_days=30)
        assert "views" in trend
        assert "snapshots" in trend
        assert trend["snapshots"] > 0

    def test_top_performers(self, analytics_with_data):
        a, items = analytics_with_data
        top = a.top_performers("views", n=3)
        assert len(top) <= 3
        assert "title" in top[0]

    def test_top_performers_invalid_metric(self, analytics_with_data):
        a, items = analytics_with_data
        with pytest.raises(ValueError):
            a.top_performers("invalid_metric")

    def test_platform_comparison(self, analytics_with_data):
        a, items = analytics_with_data
        comp = a.platform_comparison("views")
        assert len(comp) > 0
        assert "platform" in comp[0]

    def test_revenue_attribution(self, analytics_with_data):
        a, items = analytics_with_data
        rev = a.revenue_attribution(items[0].id)
        assert "total_revenue_usd" in rev
        assert rev["total_revenue_usd"] > 0

    def test_benchmark_update(self, analytics_with_data):
        a, items = analytics_with_data
        bm = a.benchmark_update("video", "views")
        assert bm.p50 >= 0
        assert bm.p75 >= bm.p50
        assert bm.p90 >= bm.p75

    def test_get_benchmark(self, analytics_with_data):
        a, items = analytics_with_data
        a.benchmark_update("video", "views")
        bm = a.get_benchmark("video", "views")
        assert bm is not None

    def test_weekly_report(self, analytics_with_data):
        a, items = analytics_with_data
        report = a.weekly_report()
        assert "total_views_this_week" in report
        assert "top_performers" in report

    def test_overall_stats(self, analytics_with_data):
        a, items = analytics_with_data
        stats = a.get_overall_stats()
        assert stats["total_content_items"] == 4
        assert stats["total_snapshots"] == 12

    def test_get_platform_list(self, analytics_with_data):
        a, items = analytics_with_data
        platforms = a.get_platform_list()
        assert "youtube" in platforms
        assert "medium" in platforms

    def test_create_analytics_factory(self, tmp_path):
        a = create_analytics(str(tmp_path / "factory.db"))
        assert a is not None
