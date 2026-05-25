import { PIPELINE_STEPS } from "../types";
import type { Phase } from "../types";

interface Props {
  currentPhase: Phase;
  completedPhases: Phase[];
  onStepClick: (key: string) => void;
  activeStepKey: string;
}

export default function PipelineSidebar({
  currentPhase,
  completedPhases,
  onStepClick,
  activeStepKey,
}: Props) {
  const currentIdx = PIPELINE_STEPS.findIndex((s) => s.phase === currentPhase);

  return (
    <div className="w-52 bg-gray-50 border-r p-3 flex-shrink-0 overflow-y-auto">
      <div className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
        流水线步骤
      </div>
      {PIPELINE_STEPS.map((step, i) => {
        const done = completedPhases.includes(step.phase) || i < currentIdx;
        const active = step.key === activeStepKey;
        const isReview = step.isReview;

        return (
          <button
            key={step.key}
            onClick={() => onStepClick(step.key)}
            className={`flex items-center gap-2 w-full text-left px-2 py-2 rounded-md mb-1 text-xs transition-colors ${
              active
                ? isReview
                  ? "bg-yellow-100 text-yellow-800 font-semibold"
                  : "bg-blue-100 text-blue-800 font-semibold"
                : done
                ? "hover:bg-gray-100 text-gray-600"
                : "text-gray-400 cursor-default"
            }`}
          >
            <span
              className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] flex-shrink-0 ${
                done
                  ? "bg-blue-600 text-white"
                  : active
                  ? isReview
                    ? "bg-yellow-500 text-white"
                    : "bg-blue-600 text-white"
                  : "border border-gray-300 text-gray-400"
              }`}
            >
              {done ? "\u2713" : active ? "!" : i + 1}
            </span>
            {step.label}
          </button>
        );
      })}
    </div>
  );
}
