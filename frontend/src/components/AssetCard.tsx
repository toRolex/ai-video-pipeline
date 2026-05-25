import type { AssetFile } from "../types";

interface Props {
  asset: AssetFile;
  onDelete: (name: string) => void;
}

export default function AssetCard({ asset, onDelete }: Props) {
  const seconds = asset.duration_seconds || 0;
  const min = Math.floor(seconds / 60);
  const sec = String(Math.floor(seconds % 60)).padStart(2, "0");

  return (
    <div
      className={`w-44 border rounded-lg overflow-hidden flex-shrink-0 ${
        asset.in_use ? "border-green-500 bg-green-50" : "border-gray-200"
      }`}
    >
      <div className="h-24 bg-gray-100 flex items-center justify-center text-2xl">{/* 视频图标 */}</div>
      <div className="p-2 text-xs">
        <div className="font-medium truncate" title={asset.name}>{asset.name}</div>
        {seconds > 0 && <div className="text-gray-500">{min}:{sec}</div>}
        {asset.in_use && <div className="text-green-600 mt-0.5">&#10003; 使用中</div>}
        <button
          className="text-red-500 hover:underline mt-1"
          onClick={(e) => {
            e.stopPropagation();
            onDelete(asset.name);
          }}
        >
          删除
        </button>
      </div>
    </div>
  );
}
