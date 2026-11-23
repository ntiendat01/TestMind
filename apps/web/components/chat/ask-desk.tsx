"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";

import { PageBanner } from "@/components/ui/page-banner";
import { askQuestion } from "@/lib/api/client";
import { orderEvidence } from "@/lib/api/citations";
import { requestFeedback } from "@/lib/api/feedback";
import { vi } from "@/lib/i18n/vi";
import { AnswerPanel, type AnswerState } from "./answer-panel";
import { QuestionForm } from "./question-form";
import { SourcePanel } from "./source-panel";

import styles from "./chat.module.css";

export function AskDesk() {
  const [question, setQuestion] = useState("");
  const [docType, setDocType] = useState("");
  const [module, setModule] = useState("");
  const [answer, setAnswer] = useState<AnswerState>({ kind: "idle" });
  const [selectedId, setSelectedId] = useState("");
  const [canReturn, setCanReturn] = useState(false);
  const request = useRef<AbortController | null>(null);
  const input = useRef<HTMLTextAreaElement>(null);
  const panel = useRef<HTMLElement>(null);
  const previousCitation = useRef<HTMLButtonElement | null>(null);

  useEffect(() => () => {
    request.current?.abort();
    request.current = null;
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const query = question.trim();
    if (!query || request.current) return;
    const controller = new AbortController();
    request.current = controller;
    setAnswer({ kind: "pending" });
    setSelectedId("");
    previousCitation.current = null;
    setCanReturn(false);
    try {
      const result = await askQuestion(query, { docType, module }, controller.signal);
      if (request.current !== controller) return;
      const sources = orderEvidence(result.hits, result.final.claims);
      setAnswer({ kind: "ready", query, result, sources });
      setSelectedId(sources[0]?.hit.chunk_id ?? "");
    } catch (error) {
      if (request.current === controller) {
        setAnswer({ kind: "error", message: requestFeedback(error, vi.queryError) });
      }
    } finally {
      if (request.current === controller) request.current = null;
    }
  }

  function cancel() {
    const controller = request.current;
    if (!controller) return;
    request.current = null;
    controller.abort();
    setAnswer({ kind: "cancelled" });
    input.current?.focus();
  }

  function openCitation(id: string, trigger: HTMLButtonElement) {
    setSelectedId(id);
    previousCitation.current = trigger;
    setCanReturn(true);
    panel.current?.focus({ preventScroll: true });
    panel.current?.scrollIntoView({ block: "nearest" });
  }

  const sources = answer.kind === "ready" ? answer.sources : [];

  return (
    <>
      <PageBanner title={vi.chatTitle} description={vi.chatLead} variant="chat" />
      <div className={styles.workbench}>
        <div className={styles.mainColumn}>
          <QuestionForm
            question={question} setQuestion={setQuestion}
            docType={docType} setDocType={setDocType} module={module} setModule={setModule}
            input={input} onSubmit={submit} onCancel={cancel}
            pending={answer.kind === "pending"} showExamples={answer.kind === "idle"}
          />
          <AnswerPanel state={answer} selectedId={selectedId} onCitation={openCitation} />
        </div>
        <SourcePanel
          panel={panel} sources={sources} selectedId={selectedId} onSelect={setSelectedId}
          onReturn={canReturn ? () => previousCitation.current?.focus() : undefined}
          noResults={answer.kind === "ready" && sources.length === 0}
        />
      </div>
    </>
  );
}
