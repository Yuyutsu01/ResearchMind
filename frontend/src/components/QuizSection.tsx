import React, { useState } from "react";
import { Award, CheckCircle, XCircle } from "lucide-react";

interface QuizQuestion {
  question: string;
  options: string[];
  correct_index: number;
}

interface QuizSectionProps {
  quiz: QuizQuestion[];
  onComplete: (scorePercentage: number) => void;
}

export default function QuizSection({ quiz, onComplete }: QuizSectionProps) {
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, number>>({});
  const [submitted, setSubmitted] = useState(false);
  const [score, setScore] = useState(0);

  const handleSelectOption = (qIdx: number, oIdx: number) => {
    if (submitted) return;
    setSelectedAnswers((prev) => ({ ...prev, [qIdx]: oIdx }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (submitted || Object.keys(selectedAnswers).length < quiz.length) return;

    let correctCount = 0;
    quiz.forEach((q, idx) => {
      if (selectedAnswers[idx] === q.correct_index) {
        correctCount += 1;
      }
    });

    const finalScore = (correctCount / quiz.length) * 100;
    setScore(finalScore);
    setSubmitted(true);
    onComplete(finalScore);
  };

  if (!quiz || quiz.length === 0) {
    return null;
  }

  return (
    <div className="glass-panel p-6 flex flex-col gap-4">
      <div className="flex items-center gap-2 border-b border-white/10 pb-2">
        <Award className="w-5 h-5 text-amber-400" />
        <h3 className="font-header text-sm font-bold uppercase tracking-wider text-slate-300">
          Researcher Learning Gain Quiz
        </h3>
      </div>
      <p className="text-xs text-slate-400">
        Assess your understanding of the extracted core concepts to calculate the User Learning Gain metric.
      </p>

      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        {quiz.map((q, qIdx) => (
          <div key={qIdx} className="flex flex-col gap-3">
            <h4 className="text-sm font-medium text-slate-200">
              Q{qIdx + 1}: {q.question}
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {q.options.map((opt, oIdx) => {
                const isSelected = selectedAnswers[qIdx] === oIdx;
                const isCorrect = q.correct_index === oIdx;
                
                let optionStyle = "border-white/5 bg-white/5 text-slate-300 hover:bg-white/10";
                let StatusIcon = null;

                if (isSelected) {
                  optionStyle = "border-primary/50 bg-primary/20 text-white";
                }

                if (submitted) {
                  if (isCorrect) {
                    optionStyle = "border-emerald-500/50 bg-emerald-500/10 text-emerald-200";
                    StatusIcon = <CheckCircle className="w-4 h-4 text-emerald-400" />;
                  } else if (isSelected) {
                    optionStyle = "border-rose-500/50 bg-rose-500/10 text-rose-200";
                    StatusIcon = <XCircle className="w-4 h-4 text-rose-400" />;
                  } else {
                    optionStyle = "border-white/5 opacity-50 bg-transparent text-slate-500";
                  }
                }

                return (
                  <button
                    key={oIdx}
                    type="button"
                    disabled={submitted}
                    onClick={() => handleSelectOption(qIdx, oIdx)}
                    className={`flex items-center justify-between p-3 rounded-lg border text-left text-xs transition-all ${optionStyle}`}
                  >
                    <span>{opt}</span>
                    {StatusIcon}
                  </button>
                );
              })}
            </div>
          </div>
        ))}

        {!submitted ? (
          <button
            type="submit"
            disabled={Object.keys(selectedAnswers).length < quiz.length}
            className="btn btn-primary self-end disabled:opacity-50"
          >
            Submit Quiz
          </button>
        ) : (
          <div className="glass-panel bg-white/5 p-4 flex flex-col md:flex-row justify-between items-center rounded-lg">
            <span className="text-sm font-medium text-slate-300">
              Quiz Completed! Your Score:{" "}
              <strong className="text-amber-400 text-lg">{score.toFixed(0)}%</strong>
            </span>
            <span className="text-xs text-slate-400">
              User Learning Gain metric logged in database telemetry logs.
            </span>
          </div>
        )}
      </form>
    </div>
  );
}
