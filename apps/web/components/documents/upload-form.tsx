"use client";

import Link from "next/link";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, type DragEvent, type FormEvent } from "react";

import { Icon } from "@/components/ui/icon";
import { readJob, uploadDocument } from "@/lib/api/client";
import { requestFeedback } from "@/lib/api/feedback";
import { vi } from "@/lib/i18n/vi";
import styles from "./documents.module.css";

const extensions = [".docx", ".xlsx", ".md", ".txt", ".csv"];

type Feedback = { tone: "success" | "error" | "neutral"; text: string };

export function UploadForm() {
  const queryClient = useQueryClient();
  const [docType, setDocType] = useState("brd");
  const [module, setModule] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const upload = useMutation({
    mutationFn: async (chosen: File) => {
      const created = await uploadDocument(chosen, docType, module);
      return readJob(created.job_id);
    },
    onSuccess: (job) => {
      if (job.status === "failed") setFeedback({ tone: "error", text: vi.uploadFailed });
      else {
        setFile(null);
        setFeedback(job.status === "ready"
          ? { tone: "success", text: vi.uploadReady }
          : { tone: "neutral", text: vi.uploadWorking });
      }
    },
    onError: (error) => setFeedback({ tone: "error", text: requestFeedback(error, vi.uploadFailed) }),
    onSettled: () => queryClient.invalidateQueries({ queryKey: ["documents"] }),
  });

  function choose(files: FileList | null) {
    if (!files?.length || upload.isPending) return;
    const chosen = files[0];
    setFile(null);
    if (files.length !== 1) setFeedback({ tone: "error", text: vi.fileTooMany });
    else if (!extensions.some((extension) => chosen.name.toLowerCase().endsWith(extension))) {
      setFeedback({ tone: "error", text: vi.fileUnsupported });
    } else {
      setFile(chosen);
      setFeedback(null);
    }
  }

  function drop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    setDragging(false);
    choose(event.dataTransfer.files);
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file || upload.isPending) return;
    setFeedback(null);
    upload.mutate(file);
  }

  return (
    <form className={`panel ${styles.uploadForm}`} aria-labelledby="upload-title" onSubmit={submit}>
      <h2 className="panel-title" id="upload-title">{vi.uploadTitle}</h2>
      <label className={styles.dropzone} data-dragging={dragging} data-disabled={upload.isPending}
        onDragOver={(event) => { event.preventDefault(); if (!upload.isPending) setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={drop}>
        <input
          type="file" aria-label={vi.chooseFile} aria-describedby="upload-format"
          className="sr-only" accept={extensions.join(",")} disabled={upload.isPending}
          onChange={(event) => {
            choose(event.currentTarget.files);
            event.currentTarget.value = "";
          }} />
        <span className={styles.uploadIcon}><Icon name={file ? "document" : "upload"} size={24} /></span>
        <strong className="wrap">{file?.name ?? vi.dropHint}</strong>
        <span id="upload-format">{vi.supportedFormats}</span>
      </label>
      {feedback?.tone === "error" && (
        <p className="feedback" role="alert" data-tone="error">{feedback.text}</p>
      )}
      <label className="field">
        {vi.docType}
        <select className="control" value={docType} disabled={upload.isPending}
          onChange={(event) => setDocType(event.target.value)}>
          {Object.entries(vi.docTypes).map(([type, label]) => <option key={type} value={type}>{label}</option>)}
        </select>
      </label>
      <label className="field">
        {vi.module}
        <input className="control" value={module} placeholder={vi.modulePlaceholder}
          disabled={upload.isPending} maxLength={200} onChange={(event) => setModule(event.target.value)} />
      </label>
      <button type="submit" className="button primary" disabled={!file || upload.isPending}>
        <Icon name="upload" size={17} /> {upload.isPending ? vi.uploading : vi.upload}
      </button>
      {upload.isPending && <div className="sr-only" role="status">{vi.uploading}</div>}
      {feedback && feedback.tone !== "error" && (
        <div className="feedback" data-tone={feedback.tone}>
          <p role="status">{feedback.text}</p>
          {feedback.tone === "success" && <Link href="/chat" className="text-link">{vi.goToChat}</Link>}
        </div>
      )}
    </form>
  );
}
