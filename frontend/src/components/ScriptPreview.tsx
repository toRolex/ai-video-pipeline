import type { ScriptCheckResult } from "../types";

interface Props {
  script: string;
  checks: ScriptCheckResult | null;
  onApprove: () => void;
  onReject: () => void;
  onRegenerate: () => void;
}

export default function ScriptPreview({
  script,
  checks,
  onApprove,
  onReject,
  onRegenerate,
}: Props) {
  return (
    <div>
      <h3 className="font-semibold text-sm mb-3">口播脚本</h3>
      <div className="bg-gray-50 border rounded-lg p-4 mb-4 text-sm leading-relaxed min-h-[80px]">
        {script || "暂无脚本"}
      </div>
      {checks && (
        <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs mb-4">
          <span className={checks.passed ? "text-green-600" : "text-red-600"}>
            字数: {checks.length} {checks.length >= 150 && checks.length <= 200 ? "\u2713" : "\u2717"}
          </span>
          <span
            className={checks.brand_name_count >= 1 ? "text-green-600" : "text-red-600"}
          >
            品牌"滋元堂": {checks.brand_name_count}次
          </span>
          <span
            className={checks.product_name_count >= 1 ? "text-green-600" : "text-red-600"}
          >
            品名: {checks.product_name_count}次
          </span>
          <span className={checks.has_safety_warning ? "text-green-600" : "text-red-600"}>
            充分烹熟: {checks.has_safety_warning ? "\u2713" : "\u2717"}
          </span>
          <span className={!checks.has_emoji ? "text-green-600" : "text-red-600"}>
            禁emoji: {!checks.has_emoji ? "\u2713" : "\u2717"}
          </span>
          {checks.forbidden_terms.length > 0 && (
            <span className="text-red-600">禁词: {checks.forbidden_terms.join(", ")}</span>
          )}
        </div>
      )}
      <div className="flex gap-2">
        <button
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 transition-colors"
          onClick={onApprove}
        >
          {"\u2713"} 通过
        </button>
        <button
          className="bg-red-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-red-700 transition-colors"
          onClick={onReject}
        >
          {"\u2717"} 打回
        </button>
        <button
          className="border px-4 py-2 rounded-lg text-sm hover:bg-gray-50 transition-colors"
          onClick={onRegenerate}
        >
          {"\U0001F504"} 重生成
        </button>
      </div>
    </div>
  );
}
