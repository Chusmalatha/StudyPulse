import React, { useState, useEffect, useCallback } from 'react';
import {
  HelpCircle,
  Plus,
  Loader2,
  CheckCircle2,
  XCircle,
  ArrowRight,
  Sparkles,
  BookOpen,
  Award,
  Clock,
  RotateCcw,
  FileText,
  AlertCircle,
  Brain,
  ChevronRight,
  Target,
} from 'lucide-react';
import assessmentService from '../../services/api/assessmentService';
import FormattedMarkdown from '../common/FormattedMarkdown';

const AssessmentsSection = ({ projectId, targetConceptId = null, targetConceptName = null }) => {
  const [assessments, setAssessments] = useState([]);
  const [activeAssessment, setActiveAssessment] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [mcqSelection, setMcqSelection] = useState('');
  const [openEndedAnswer, setOpenEndedAnswer] = useState('');
  const [currentResult, setCurrentResult] = useState(null);
  const [isLoadingList, setIsLoadingList] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const autoCreatedConceptRef = React.useRef(null);

  // Create new adaptive assessment (optional concept targeting)
  const handleCreateAssessment = async (questionCount = 5, conceptId = null) => {
    setIsGenerating(true);
    setError(null);
    try {
      const targetCid = conceptId || targetConceptId || targetConceptName;
      const newAss = await assessmentService.createAssessment(projectId, questionCount, targetCid);
      setActiveAssessment(newAss);
      setCurrentQuestionIndex(0);
      setCurrentResult(null);
      setMcqSelection('');
      setOpenEndedAnswer('');
      const data = await assessmentService.getAssessments(projectId);
      setAssessments(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate practice assessment.');
    } finally {
      setIsGenerating(false);
    }
  };

  // Load past assessments list or trigger auto-creation for concept (ONCE)
  const loadAssessments = useCallback(async () => {
    setIsLoadingList(true);
    setError(null);
    try {
      const data = await assessmentService.getAssessments(projectId);
      setAssessments(data);

      const targetConcept = targetConceptId || targetConceptName;
      if (targetConcept && autoCreatedConceptRef.current !== targetConcept) {
        autoCreatedConceptRef.current = targetConcept;

        // Check if an in-progress assessment already exists for this concept
        const existingInProgress = data.find(
          (a) => a.status === 'IN_PROGRESS' && a.title.toLowerCase().includes(targetConcept.toLowerCase())
        );

        if (existingInProgress) {
          setActiveAssessment(existingInProgress);
          setCurrentQuestionIndex(existingInProgress.current_question_index || 0);
        } else {
          // Auto create concept-specific quiz ONCE
          setIsGenerating(true);
          try {
            const newAss = await assessmentService.createAssessment(projectId, 5, targetConcept);
            setActiveAssessment(newAss);
            setCurrentQuestionIndex(0);
            setCurrentResult(null);
            setMcqSelection('');
            setOpenEndedAnswer('');
            const updated = await assessmentService.getAssessments(projectId);
            setAssessments(updated);
          } catch (createErr) {
            setError(createErr.response?.data?.detail || 'Failed to generate practice assessment.');
          } finally {
            setIsGenerating(false);
          }
        }
      } else if (!targetConcept) {
        // Open active IN_PROGRESS assessment if present
        const inProgress = data.find((a) => a.status === 'IN_PROGRESS');
        if (inProgress && !activeAssessment) {
          setActiveAssessment(inProgress);
          setCurrentQuestionIndex(inProgress.current_question_index || 0);
        }
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load assessments.');
    } finally {
      setIsLoadingList(false);
    }
  }, [projectId, targetConceptId, targetConceptName]);

  useEffect(() => {
    loadAssessments();
  }, [loadAssessments]);

  // Submit Answer for current question
  const handleSubmitAnswer = async (e) => {
    e?.preventDefault();
    if (!activeAssessment) return;
    const questions = activeAssessment.questions || [];
    const currentQ = questions[currentQuestionIndex];
    if (!currentQ) return;

    const answerText = currentQ.question_type === 'MCQ' ? mcqSelection : openEndedAnswer.trim();
    if (!answerText || isSubmitting) return;

    setIsSubmitting(true);
    setError(null);
    try {
      const res = await assessmentService.submitAnswer(
        projectId,
        activeAssessment.id,
        currentQ.id,
        answerText
      );
      setCurrentResult(res);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit answer.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Move to next question or complete assessment
  const handleNextQuestion = async () => {
    if (!activeAssessment) return;
    const questions = activeAssessment.questions || [];
    const nextIdx = currentQuestionIndex + 1;

    setCurrentResult(null);
    setMcqSelection('');
    setOpenEndedAnswer('');

    if (nextIdx < questions.length) {
      setCurrentQuestionIndex(nextIdx);
    } else {
      // Complete Assessment
      try {
        const completed = await assessmentService.completeAssessment(projectId, activeAssessment.id);
        setActiveAssessment(completed);
        loadAssessments();
      } catch (err) {
        alert(err.response?.data?.detail || 'Failed to complete assessment.');
      }
    }
  };

  const questions = activeAssessment?.questions || [];
  const currentQ = questions[currentQuestionIndex];
  const isCompleted = activeAssessment?.status === 'COMPLETED';

  return (
    <div className="space-y-6">
      {/* Top Banner & Header */}
      <div className="bg-gradient-to-r from-amber-500 via-amber-600 to-indigo-600 rounded-2xl p-6 text-white shadow-md flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-amber-100 text-xs font-semibold uppercase tracking-wider">
            <Sparkles size={16} />
            <span>Adaptive Assessment Engine</span>
          </div>
          <h2 className="text-xl font-bold">Concept-Aware Practice & Evaluation</h2>
          <p className="text-xs text-amber-100/90 leading-relaxed max-w-xl">
            Generates grounded MCQs and open-ended questions targeting your weak concepts, recent errors, and study history.
          </p>
        </div>

        <button
          onClick={() => handleCreateAssessment(5)}
          disabled={isGenerating}
          className="bg-white hover:bg-amber-50 text-amber-900 px-5 py-3 rounded-xl font-bold text-xs shadow-sm transition-all disabled:opacity-50 flex items-center gap-2 shrink-0 cursor-pointer"
        >
          {isGenerating ? (
            <>
              <Loader2 size={16} className="animate-spin text-amber-600" />
              <span>Generating Quiz...</span>
            </>
          ) : (
            <>
              <Plus size={16} />
              <span>New Practice Quiz</span>
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 text-red-700 rounded-xl text-xs flex items-center justify-between border border-red-100 shadow-2xs">
          <div className="flex items-center gap-2">
            <AlertCircle size={16} className="shrink-0 text-red-500" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="font-bold hover:underline cursor-pointer">
            Dismiss
          </button>
        </div>
      )}

      {/* Main Layout: Sidebar List & Quiz Interface */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Past Assessments Sidebar */}
        <div className="lg:col-span-1 bg-white rounded-xl border border-gray-200 p-4 shadow-sm space-y-3">
          <div className="flex items-center justify-between border-b border-gray-100 pb-3">
            <h3 className="text-xs font-bold text-gray-900 uppercase tracking-wider flex items-center gap-1.5">
              <Award size={14} className="text-amber-500" />
              Quiz History
            </h3>
            <span className="bg-gray-100 text-gray-600 text-[10px] font-bold px-2 py-0.5 rounded-full">
              {assessments.length}
            </span>
          </div>

          <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
            {isLoadingList ? (
              <div className="flex items-center justify-center py-10 text-gray-400 gap-2 text-xs">
                <Loader2 size={16} className="animate-spin text-amber-500" />
                <span>Loading...</span>
              </div>
            ) : assessments.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <HelpCircle size={24} className="mx-auto mb-1 opacity-40 text-amber-500" />
                <p className="text-xs font-medium text-gray-600">No quizzes yet</p>
                <p className="text-[10px] text-gray-400 mt-0.5">Click 'New Practice Quiz' above.</p>
              </div>
            ) : (
              assessments.map((ass) => (
                <button
                  key={ass.id}
                  onClick={() => {
                    setActiveAssessment(ass);
                    setCurrentQuestionIndex(ass.current_question_index || 0);
                    setCurrentResult(null);
                    setError(null);
                  }}
                  className={`w-full text-left p-3 rounded-xl border transition-all cursor-pointer ${
                    activeAssessment?.id === ass.id
                      ? 'bg-amber-50/60 border-amber-300 shadow-2xs ring-1 ring-amber-500/20'
                      : 'border-gray-100 hover:bg-gray-50 text-gray-700'
                  }`}
                >
                  <div className="flex items-center justify-between gap-1 mb-1">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        ass.status === 'COMPLETED'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-amber-100 text-amber-800'
                      }`}
                    >
                      {ass.status === 'COMPLETED' ? 'Completed' : 'In Progress'}
                    </span>
                    {ass.score_mcq !== null && ass.score_mcq !== undefined && (
                      <span className="text-xs font-bold text-emerald-600">{ass.score_mcq}%</span>
                    )}
                  </div>
                  <p className="text-xs font-bold text-gray-900 truncate">{ass.title}</p>
                  <p className="text-[10px] text-gray-400 mt-1 flex items-center gap-1">
                    <Clock size={10} />
                    {new Date(ass.created_at).toLocaleDateString()} • {ass.question_count} Qs
                  </p>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Quiz Workspace Panel */}
        <div className="lg:col-span-3 bg-white rounded-xl border border-gray-200 p-6 shadow-sm min-h-[500px] flex flex-col justify-between">
          {!activeAssessment ? (
            <div className="my-auto text-center py-16 space-y-4 max-w-md mx-auto">
              <div className="w-16 h-16 bg-amber-50 text-amber-600 rounded-2xl flex items-center justify-center mx-auto shadow-xs">
                <Brain size={32} />
              </div>
              <div>
                <h3 className="text-base font-bold text-gray-900">Start an Adaptive Practice Quiz</h3>
                <p className="text-xs text-gray-500 mt-1">
                  Select a past quiz from the sidebar or click "New Practice Quiz" to generate adaptive questions from your materials.
                </p>
              </div>
            </div>
          ) : isCompleted ? (
            /* Completed Screen */
            <div className="my-auto text-center py-12 space-y-6 max-w-lg mx-auto">
              <div className="w-16 h-16 bg-emerald-50 text-emerald-600 rounded-2xl flex items-center justify-center mx-auto shadow-xs border border-emerald-100">
                <CheckCircle2 size={36} />
              </div>
              <div className="space-y-2">
                <h3 className="text-xl font-bold text-gray-900">Assessment Completed!</h3>
                <p className="text-xs text-gray-500">
                  Great job completing your adaptive practice session. Your responses have been saved to refine your study model.
                </p>
              </div>

              {activeAssessment.score_mcq !== null && activeAssessment.score_mcq !== undefined && (
                <div className="bg-emerald-50/70 border border-emerald-200 rounded-2xl p-5 inline-block">
                  <p className="text-xs font-semibold text-emerald-800 uppercase tracking-wider">MCQ Accuracy Score</p>
                  <p className="text-3xl font-extrabold text-emerald-600 mt-1">{activeAssessment.score_mcq}%</p>
                </div>
              )}

              <div className="pt-4 flex justify-center gap-3">
                <button
                  onClick={() => handleCreateAssessment(5)}
                  className="bg-amber-500 hover:bg-amber-600 text-white px-5 py-2.5 rounded-xl text-xs font-bold transition-all shadow-xs flex items-center gap-2 cursor-pointer"
                >
                  <RotateCcw size={14} />
                  Take Another Quiz
                </button>
              </div>
            </div>
          ) : (
            /* Question Screen */
            <div className="space-y-6">
              {/* Progress & Header */}
              <div className="flex items-center justify-between border-b border-gray-100 pb-4">
                <div className="flex items-center gap-2">
                  <span className="bg-amber-100 text-amber-900 text-xs font-bold px-3 py-1 rounded-full">
                    Question {currentQuestionIndex + 1} of {questions.length}
                  </span>
                  <span className="bg-gray-100 text-gray-700 text-xs font-semibold px-2.5 py-0.5 rounded-full">
                    {currentQ?.question_type}
                  </span>
                  <span className="bg-purple-50 text-purple-700 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-purple-100">
                    Difficulty: {currentQ?.difficulty}
                  </span>
                </div>

                <span className="text-xs text-gray-400 font-medium">
                  {currentQ?.concept_names?.[0] || 'Target Concept'}
                </span>
              </div>

              {/* Question Text & Citations */}
              <div className="space-y-3">
                <h3 className="text-base font-bold text-gray-900 leading-snug">{currentQ?.question_text}</h3>

                {currentQ?.source_references && currentQ.source_references.length > 0 && (
                  <div className="flex items-center gap-2 text-[11px] text-gray-500">
                    <BookOpen size={12} className="text-amber-500" />
                    <span>Grounded Source:</span>
                    <span className="font-semibold text-gray-700">{currentQ.source_references[0].filename}</span>
                    <span>•</span>
                    <span className="bg-amber-50 text-amber-800 font-bold px-1.5 py-0.2 rounded text-[10px]">
                      Page {currentQ.source_references[0].page_number}
                    </span>
                  </div>
                )}
              </div>

              {/* Question Answer Inputs */}
              {!currentResult ? (
                <form onSubmit={handleSubmitAnswer} className="space-y-5 pt-2">
                  {currentQ?.question_type === 'MCQ' && currentQ.options ? (
                    <div className="grid grid-cols-1 gap-3">
                      {Object.entries(currentQ.options).map(([key, optText]) => (
                        <label
                          key={key}
                          onClick={() => setMcqSelection(key)}
                          className={`flex items-start gap-3 p-4 rounded-xl border text-xs cursor-pointer transition-all ${
                            mcqSelection === key
                              ? 'bg-amber-50/80 border-amber-400 shadow-2xs ring-1 ring-amber-500/20 text-gray-900 font-semibold'
                              : 'bg-white border-gray-200 hover:bg-gray-50 text-gray-700'
                          }`}
                        >
                          <span
                            className={`w-6 h-6 rounded-lg flex items-center justify-center font-bold text-xs shrink-0 ${
                              mcqSelection === key ? 'bg-amber-500 text-white' : 'bg-gray-100 text-gray-600'
                            }`}
                          >
                            {key}
                          </span>
                          <span className="mt-0.5 leading-relaxed">{optText}</span>
                        </label>
                      ))}
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <textarea
                        rows={5}
                        value={openEndedAnswer}
                        onChange={(e) => setOpenEndedAnswer(e.target.value)}
                        placeholder="Explain your answer in detail using your own words..."
                        className="w-full text-xs border border-gray-300 rounded-xl p-4 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent leading-relaxed"
                      />
                      <p className="text-[11px] text-gray-400">
                        Qualitative evaluation checks conceptual understanding against project material.
                      </p>
                    </div>
                  )}

                  <div className="flex justify-end pt-2">
                    <button
                      type="submit"
                      disabled={
                        isSubmitting ||
                        (currentQ?.question_type === 'MCQ' ? !mcqSelection : !openEndedAnswer.trim())
                      }
                      className="bg-amber-500 hover:bg-amber-600 text-white px-6 py-3 rounded-xl text-xs font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-xs flex items-center gap-2 cursor-pointer"
                    >
                      {isSubmitting ? (
                        <>
                          <Loader2 size={16} className="animate-spin" />
                          <span>Evaluating...</span>
                        </>
                      ) : (
                        <>
                          <span>Submit Answer</span>
                          <ArrowRight size={14} />
                        </>
                      )}
                    </button>
                  </div>
                </form>
              ) : (
                /* Question Result Feedback View */
                <div className="space-y-5 pt-2 border-t border-gray-100">
                  {currentQ?.question_type === 'MCQ' ? (
                    /* MCQ Feedback */
                    <div
                      className={`p-4 rounded-xl border text-xs space-y-2 ${
                        currentResult.is_correct
                          ? 'bg-emerald-50 border-emerald-200 text-emerald-950'
                          : 'bg-red-50 border-red-200 text-red-950'
                      }`}
                    >
                      <div className="flex items-center gap-2 font-bold text-sm">
                        {currentResult.is_correct ? (
                          <>
                            <CheckCircle2 size={18} className="text-emerald-600" />
                            <span>Correct!</span>
                          </>
                        ) : (
                          <>
                            <XCircle size={18} className="text-red-600" />
                            <span>Incorrect — Correct Answer is ({currentResult.correct_answer})</span>
                          </>
                        )}
                      </div>
                      <FormattedMarkdown content={currentResult.explanation} />
                    </div>
                  ) : (
                    /* Open-Ended Qualitative Feedback */
                    <div className="bg-gray-50 border border-gray-200 rounded-2xl p-5 space-y-4 text-xs">
                      <div className="flex items-center justify-between border-b border-gray-200 pb-3">
                        <h4 className="font-bold text-gray-900 flex items-center gap-2">
                          <Sparkles size={16} className="text-amber-500" />
                          Qualitative Evaluation Breakdown
                        </h4>
                        <span className="bg-amber-100 text-amber-900 font-bold px-2.5 py-0.5 rounded-full text-[10px]">
                          Understanding: {currentResult.evaluation?.understanding?.status || 'GOOD'}
                        </span>
                      </div>

                      {/* Strengths & Missing Concepts Grid */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* What You Understood */}
                        <div className="bg-emerald-50/70 border border-emerald-200/80 rounded-xl p-3.5 space-y-2">
                          <p className="font-bold text-emerald-900 flex items-center gap-1.5 text-xs">
                            <CheckCircle2 size={14} className="text-emerald-600" />
                            What You Understood
                          </p>
                          <ul className="space-y-1 text-emerald-950 text-[11px] list-disc list-inside">
                            {currentResult.evaluation?.strengths?.map((strItem, idx) => (
                              <li key={idx}>{strItem}</li>
                            ))}
                          </ul>
                        </div>

                        {/* Missing Concepts */}
                        <div className="bg-amber-50/70 border border-amber-200/80 rounded-xl p-3.5 space-y-2">
                          <p className="font-bold text-amber-900 flex items-center gap-1.5 text-xs">
                            <AlertCircle size={14} className="text-amber-600" />
                            Missing Key Concepts
                          </p>
                          {currentResult.evaluation?.missing_concepts &&
                          currentResult.evaluation.missing_concepts.length > 0 ? (
                            <ul className="space-y-1 text-amber-950 text-[11px] list-disc list-inside">
                              {currentResult.evaluation.missing_concepts.map((mItem, idx) => (
                                <li key={idx} className="capitalize">
                                  {mItem}
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <p className="text-[11px] text-amber-800">All primary key concepts were present.</p>
                          )}
                        </div>
                      </div>

                      {/* Reasoning & Suggestion */}
                      <div className="bg-white border border-gray-200 rounded-xl p-4 space-y-2">
                        <p className="font-bold text-gray-900">Feedback & Suggestion</p>
                        <FormattedMarkdown content={currentResult.evaluation?.reasoning_feedback} />
                        <p className="text-indigo-900 font-semibold bg-indigo-50 p-2.5 rounded-lg border border-indigo-100 mt-2">
                          💡 {currentResult.evaluation?.suggestion}
                        </p>
                      </div>
                    </div>
                  )}

                  <div className="flex justify-end pt-2">
                    <button
                      onClick={handleNextQuestion}
                      className="bg-amber-500 hover:bg-amber-600 text-white px-6 py-3 rounded-xl text-xs font-bold transition-all shadow-xs flex items-center gap-2 cursor-pointer"
                    >
                      <span>
                        {currentQuestionIndex + 1 < questions.length ? 'Next Question' : 'Complete Quiz'}
                      </span>
                      <ChevronRight size={16} />
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AssessmentsSection;
