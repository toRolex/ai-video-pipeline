interface Props {
  src: string;
  kind: "video" | "audio";
}

export default function MediaPlayer({ src, kind }: Props) {
  if (!src) {
    return <div className="text-gray-400 text-sm py-4">无媒体文件</div>;
  }
  if (kind === "video") {
    return (
      <video controls className="w-full rounded-lg max-h-96">
        <source src={src} />
        您的浏览器不支持视频播放
      </video>
    );
  }
  return (
    <audio controls className="w-full">
      <source src={src} />
      您的浏览器不支持音频播放
    </audio>
  );
}
