import type { Phase } from "../types";

const colorMap: Record<string, string> = {
  queued: "bg-gray-100 text-gray-700",
  script_generating: "bg-blue-100 text-blue-700",
  tts_generating: "bg-blue-100 text-blue-700",
  subtitle_generating: "bg-blue-100 text-blue-700",
  asset_retrieving: "bg-blue-100 text-blue-700",
  video_rendering: "bg-blue-100 text-blue-700",
  schedule_writing: "bg-blue-100 text-blue-700",
  script_review: "bg-yellow-100 text-yellow-700",
  asset_review: "bg-yellow-100 text-yellow-700",
  final_review: "bg-yellow-100 text-yellow-700",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
  cancelled: "bg-gray-200 text-gray-500",
  paused: "bg-orange-100 text-orange-700",
};

const labelMap: Record<string, string> = {
  queued: "排队中",
  script_generating: "生成脚本",
  script_review: "待审核",
  tts_generating: "配音中",
  subtitle_generating: "字幕中",
  asset_retrieving: "取素材",
  asset_review: "素材审核",
  video_rendering: "视频合成",
  final_review: "最终审核",
  schedule_writing: "写排期",
  completed: "已完成",
  failed: "失败",
  cancelled: "已取消",
  paused: "已暂停",
};

export default function StatusBadge({ phase }: { phase: Phase }) {
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
        colorMap[phase] || "bg-gray-100 text-gray-700"
      }`}
    >
      {labelMap[phase] || phase}
    </span>
  );
}
