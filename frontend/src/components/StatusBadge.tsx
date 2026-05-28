import type { Phase } from "../types";

const colorMap: Record<string, string> = {
  queued: "bg-gray-100 text-gray-700",
  script_generating: "bg-[#e3f2fd] text-[#0969da]",
  tts_generating: "bg-[#e3f2fd] text-[#0969da]",
  subtitle_generating: "bg-[#e3f2fd] text-[#0969da]",
  asset_retrieving: "bg-[#e3f2fd] text-[#0969da]",
  video_rendering: "bg-[#e3f2fd] text-[#0969da]",
  schedule_writing: "bg-[#e3f2fd] text-[#0969da]",
  script_review: "bg-[#fff3cd] text-[#997404]",
  asset_review: "bg-[#fff3cd] text-[#997404]",
  final_review: "bg-[#fff3cd] text-[#997404]",
  completed: "bg-[#e6f4ea] text-[#1a7f37]",
  failed: "bg-[#ffe0e0] text-[#d1242f]",
  cancelled: "bg-gray-200 text-gray-500",
  paused: "bg-[#fff3e0] text-[#e65100]",
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
