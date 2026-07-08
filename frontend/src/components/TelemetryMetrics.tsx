import React from "react";
import { Award, Zap, HelpCircle, AlertTriangle, ShieldCheck } from "lucide-react";

interface TelemetryProps {
  metrics: {
    task_completion_rate: number;
    autonomy_score: number;
    answer_grounding_score: number;
    hallucination_rate: number;
    cost_usd: number;
  };
  budget: {
    tokens_remaining: number;
    dollars_remaining: number;
  };
}

export default function TelemetryMetrics({ metrics, budget }: TelemetryProps) {
  // Format percentage helper
  const pct = (val: number) => `${Math.round(val * 100)}%`;

  return (
    <div className="glass-panel p-6 flex flex-col gap-6 w-full">
      <div className="border-b border-white/10 pb-2">
        <h3 className="font-header text-sm font-bold uppercase tracking-wider text-slate-400">
          Telemetry Dashboard
        </h3>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Metric 1: Task Completion Rate */}
        <div className="glass-panel bg-white/5 p-4 flex flex-col gap-2 relative overflow-hidden group">
          <div className="flex justify-between items-center text-slate-400">
            <span className="text-xs font-medium">Completion Rate (TCR)</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <span className="text-2xl font-bold font-header text-emerald-400">
            {pct(metrics.task_completion_rate)}
          </span>
          <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
            <div
              className="bg-emerald-400 h-full transition-all duration-500"
              style={{ width: `${metrics.task_completion_rate * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Metric 2: Autonomy Score */}
        <div className="glass-panel bg-white/5 p-4 flex flex-col gap-2 relative overflow-hidden group">
          <div className="flex justify-between items-center text-slate-400">
            <span className="text-xs font-medium">Autonomy Score</span>
            <Zap className="w-4 h-4 text-blue-400" />
          </div>
          <span className="text-2xl font-bold font-header text-blue-400">
            {pct(metrics.autonomy_score)}
          </span>
          <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
            <div
              className="bg-blue-400 h-full transition-all duration-500"
              style={{ width: `${metrics.autonomy_score * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Metric 3: Answer Grounding Score */}
        <div className="glass-panel bg-white/5 p-4 flex flex-col gap-2 relative overflow-hidden group">
          <div className="flex justify-between items-center text-slate-400">
            <span className="text-xs font-medium">Answer Grounding</span>
            <Award className="w-4 h-4 text-sky-400" />
          </div>
          <span className="text-2xl font-bold font-header text-sky-400">
            {pct(metrics.answer_grounding_score)}
          </span>
          <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
            <div
              className="bg-sky-400 h-full transition-all duration-500"
              style={{ width: `${metrics.answer_grounding_score * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Metric 4: Hallucination Rate */}
        <div className="glass-panel bg-white/5 p-4 flex flex-col gap-2 relative overflow-hidden group">
          <div className="flex justify-between items-center text-slate-400">
            <span className="text-xs font-medium">Hallucination Rate</span>
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          </div>
          <span className="text-2xl font-bold font-header text-rose-400">
            {pct(metrics.hallucination_rate)}
          </span>
          <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
            <div
              className="bg-rose-400 h-full transition-all duration-500"
              style={{ width: `${metrics.hallucination_rate * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Metric 5: Cost per Session */}
        <div className="glass-panel bg-white/5 p-4 flex flex-col gap-2 relative overflow-hidden group">
          <div className="flex justify-between items-center text-slate-400">
            <span className="text-xs font-medium">Session Cost</span>
            <span className="text-xs font-bold text-amber-400">USD</span>
          </div>
          <span className="text-2xl font-bold font-header text-amber-400">
            ${metrics.cost_usd.toFixed(3)}
          </span>
          <div className="flex justify-between text-[10px] text-slate-400">
            <span>Remaining: ${budget.dollars_remaining.toFixed(2)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
