import { useState, useEffect, useMemo, useCallback } from "react";
import type { MetricsOverview, TopicStat, VideoMetric, IncrementData } from "../types";
import MetricsCards from "../components/MetricsCards";
import TrendChart from "../components/TrendChart";
import TopicGrid from "../components/TopicGrid";
import VideoTable from "../components/VideoTable";

function fmt(v: unknown, fallback: number): number {
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}

function daysAgo(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().slice(0, 10);
}

function formatNum(v: number): string {
  if (v >= 10000) return (v / 10000).toFixed(1) + "万";
  return v.toLocaleString();
}

const DAYS_OPTIONS = [
  { value: 1, label: "1天" },
  { value: 7, label: "7天" },
  { value: 30, label: "30天" },
];

const MODE_OPTIONS = [
  { value: "cumulative" as const, label: "累计模式" },
  { value: "increment" as const, label: "增量模式" },
];

const INCR_CARDS = [
  { key: "plays_delta" as const, label: "播放增量", color: "text-blue-600" },
  { key: "likes_delta" as const, label: "点赞增量", color: "text-pink-600" },
  { key: "followers_delta" as const, label: "涨粉增量", color: "text-green-600" },
  { key: "shares_delta" as const, label: "分享增量", color: "text-orange-600" },
  { key: "comments_delta" as const, label: "评论增量", color: "text-purple-600" },
];

function DeltaCards({ data }: { data: IncrementData | null }) {
  if (!data) return null;

  return (
    <div className="grid grid-cols-5 gap-4">
      {INCR_CARDS.map((it) => {
        const val = data.summary[it.key];
        const prefix = val >= 0 ? "+" : "";
        return (
          <div
            key={it.key}
            className="rounded-xl border border-gray-200 p-5 bg-white"
          >
            <div className="text-sm text-gray-500 mb-1">{it.label}</div>
            <div className={`text-2xl font-bold ${it.key === "plays_delta" || it.key === "likes_delta" ? it.color : it.color}`}>
              {prefix}{formatNum(Math.abs(val))}
            </div>
            <div className="text-xs text-gray-400 mt-1">
              {data.summary.new_videos} 新增 · {data.summary.updated_videos} 更新 · {data.summary.disappeared_videos} 消失
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default function AnalyticsStaticPage() {
  const [allDaily, setAllDaily] = useState<MetricsOverview["daily"]>([]);
  const [topics, setTopics] = useState<TopicStat[]>([]);
  const [allVideos, setAllVideos] = useState<VideoMetric[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Increment mode
  const [mode, setMode] = useState<"cumulative" | "increment">("cumulative");
  const [incrementData, setIncrementData] = useState<IncrementData | null>(null);
  const [incrementError, setIncrementError] = useState<string | null>(null);
  const [incrementLoading, setIncrementLoading] = useState(false);

  // Days filter
  const [days, setDays] = useState(7);

  // Local filter / sort
  const [sortBy, setSortBy] = useState("plays_desc");
  const [search, setSearch] = useState("");
  const [platform, setPlatform] = useState("");

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [ov, tp, vl] = await Promise.all([
        fetch("overview.json").then((r) => {
          if (!r.ok) throw new Error(`overview.json: ${r.status}`);
          return r.json() as Promise<MetricsOverview>;
        }),
        fetch("topics.json").then((r) => {
          if (!r.ok) throw new Error(`topics.json: ${r.status}`);
          return r.json() as Promise<TopicStat[]>;
        }),
        fetch("videos.json").then((r) => {
          if (!r.ok) throw new Error(`videos.json: ${r.status}`);
          return r.json() as Promise<VideoMetric[]>;
        }),
      ]);
      setAllDaily(ov.daily);
      setTopics(tp);
      setAllVideos(vl);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadIncrement = useCallback(async () => {
    setIncrementLoading(true);
    setIncrementError(null);
    try {
      const r = await fetch("increment.json");
      if (!r.ok) throw new Error(`increment.json: ${r.status}`);
      setIncrementData(await r.json() as IncrementData);
    } catch (e) {
      setIncrementError((e as Error).message);
      setIncrementData(null);
    } finally {
      setIncrementLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    if (mode === "increment") {
      loadIncrement();
    }
  }, [mode, loadIncrement]);

  // Compute filtered overview from selected days
  const filteredOverview = useMemo((): MetricsOverview | null => {
    if (allDaily.length === 0) return null;
    const cutoff = daysAgo(days);
    const filtered = allDaily.filter((d) => d.publish_date >= cutoff);
    const totalPlays = filtered.reduce((s, d) => s + fmt(d.plays, 0), 0);
    const totalLikes = filtered.reduce((s, d) => s + fmt(d.likes, 0), 0);
    const totalFollowers = filtered.reduce((s, d) => s + fmt(d.followers, 0), 0);
    const avgCompletion =
      filtered.length > 0
        ? filtered.reduce((s, d) => s + fmt(d.avg_completion, 0), 0) / filtered.length
        : 0;
    const videoCount = filtered.reduce((s, d) => s + d.plays > 0 ? 1 : 0, 0);
    return {
      total_plays: totalPlays,
      total_likes: totalLikes,
      total_followers: totalFollowers,
      avg_completion: avgCompletion,
      video_count: videoCount,
      daily: filtered,
    };
  }, [allDaily, days]);

  // Filter videos by date range
  const videosInRange = useMemo(() => {
    const cutoff = daysAgo(days);
    return allVideos.filter((v) => v.publish_date >= cutoff);
  }, [allVideos, days]);

  // Client-side sort + search + platform filter
  const filteredVideos = useMemo(() => {
    let list = videosInRange;

    if (platform) {
      list = list.filter((v) => v.platform === platform);
    }
    if (search) {
      const q = search.toLowerCase();
      list = list.filter((v) => v.title.toLowerCase().includes(q));
    }

    const sorted = [...list];
    switch (sortBy) {
      case "plays_desc":
        sorted.sort((a, b) => fmt(b.plays, 0) - fmt(a.plays, 0));
        break;
      case "plays_asc":
        sorted.sort((a, b) => fmt(a.plays, 0) - fmt(b.plays, 0));
        break;
      case "date_desc":
        sorted.sort((a, b) => (b.publish_date || "").localeCompare(a.publish_date || ""));
        break;
      case "date_asc":
        sorted.sort((a, b) => (a.publish_date || "").localeCompare(b.publish_date || ""));
        break;
      case "completion_desc":
        sorted.sort((a, b) => fmt(b.completion_rate, 0) - fmt(a.completion_rate, 0));
        break;
      case "likes_desc":
        sorted.sort((a, b) => fmt(b.likes, 0) - fmt(a.likes, 0));
        break;
      case "followers_desc":
        sorted.sort((a, b) => fmt(b.followers_gained, 0) - fmt(a.followers_gained, 0));
        break;
    }
    return sorted;
  }, [videosInRange, sortBy, search, platform]);

  // ── Error state ───────────────────────────────────
  if (error) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-12 text-center">
        <p className="text-red-500 mb-2">数据加载失败</p>
        <p className="text-sm text-gray-500">{error}</p>
        <button
          onClick={loadData}
          className="mt-4 px-4 py-2 rounded-lg bg-blue-500 text-white text-sm hover:bg-blue-600"
        >
          重试
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 space-y-6">
      {/* Top bar */}
      <div className="flex items-center gap-3 flex-wrap">
        <h1 className="text-lg font-semibold text-gray-800 mr-auto">
          内容运营数据追踪
        </h1>
        {loading && mode === "cumulative" && (
          <span className="text-sm text-gray-400">数据加载中…</span>
        )}
        {incrementLoading && mode === "increment" && (
          <span className="text-sm text-gray-400">增量数据加载中…</span>
        )}

        {/* Mode switch */}
        <div className="flex items-center gap-1">
          {MODE_OPTIONS.map((m) => (
            <button
              key={m.value}
              onClick={() => setMode(m.value)}
              className={`px-3 py-1 text-sm rounded-lg border transition-colors ${
                mode === m.value
                  ? "bg-blue-50 border-blue-300 text-blue-700"
                  : "border-gray-200 text-gray-600 hover:bg-gray-50"
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>

        {/* Days filter (cumulative mode only) */}
        {mode === "cumulative" && (
          <div className="flex items-center gap-1">
            {DAYS_OPTIONS.map((d) => (
              <button
                key={d.value}
                onClick={() => setDays(d.value)}
                className={`px-3 py-1 text-sm rounded-lg border transition-colors ${
                  days === d.value
                    ? "bg-blue-50 border-blue-300 text-blue-700"
                    : "border-gray-200 text-gray-600 hover:bg-gray-50"
                }`}
              >
                {d.label}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* ── Increment mode ────────────────────────── */}
      {mode === "increment" && (
        <>
          {incrementError ? (
            <div className="rounded-xl border border-yellow-200 bg-yellow-50 p-6 text-center">
              <p className="text-yellow-700 font-medium mb-1">增量数据不可用</p>
              <p className="text-sm text-yellow-600">
                请先通过导出脚本生成增量数据：<br />
                <code className="text-xs bg-yellow-100 px-2 py-0.5 rounded">
                  uv run python tools/export_metrics_json.py --save-snapshot DATE
                </code>
              </p>
            </div>
          ) : incrementLoading ? (
            <div className="grid grid-cols-5 gap-4">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="rounded-xl border border-gray-200 p-5 animate-pulse">
                  <div className="h-4 bg-gray-200 rounded w-16 mb-3" />
                  <div className="h-8 bg-gray-200 rounded w-24" />
                </div>
              ))}
            </div>
          ) : (
            <>
              <DeltaCards data={incrementData} />

              {/* Snapshot date info */}
              {incrementData && (
                <div className="text-xs text-gray-400 text-right">
                  对比周期：{incrementData.previous_snapshot} → {incrementData.snapshot_date}
                </div>
              )}
            </>
          )}
        </>
      )}

      {/* ── Cumulative mode (existing) ────────────── */}
      {mode === "cumulative" && (
        <>
          <MetricsCards data={filteredOverview} loading={loading} />
          <TrendChart data={filteredOverview} />
          <div>
            <div className="text-sm text-gray-500 mb-2">热门话题 Top10</div>
            <TopicGrid topics={topics} loading={loading} />
          </div>
          <VideoTable
            videos={filteredVideos}
            total={filteredVideos.length}
            loading={loading}
            sortBy={sortBy}
            onSortChange={setSortBy}
            onSearchChange={setSearch}
            onPlatformChange={setPlatform}
            onAssetClick={function () {}}
          />
        </>
      )}
    </div>
  );
}
