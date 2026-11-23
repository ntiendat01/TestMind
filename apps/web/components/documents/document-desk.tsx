"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import { listDocuments, readJob, uploadDocument } from "@/lib/api/client";
import { vi, type DocType } from "@/lib/i18n/vi";

const types = Object.keys(vi.docTypes) as DocType[];

export function DocumentDesk() {
  const queryClient = useQueryClient();
  const documents = useQuery({ queryKey: ["documents"], queryFn: listDocuments });
  const [docType, setDocType] = useState<DocType>("brd");
  const [moduleName, setModuleName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState("");

  const upload = useMutation({
    mutationFn: async () => {
      if (!file) {
        throw new Error(vi.chooseFile);
      }
      const created = await uploadDocument(file, docType, moduleName);
      return readJob(created.job_id);
    },
    onSuccess: async (job) => {
      setMessage(job.error ?? "");
      setFile(null);
      await queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
    onError: (error: Error) => setMessage(error.message),
  });

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    setMessage("");
    upload.mutate();
  }

  return (
    <div className="grid gap-8">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">{vi.documentsTitle}</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-stone-600">{vi.documentsLead}</p>
      </header>
      <form onSubmit={onSubmit} className="grid gap-4 rounded-lg border border-stone-200 bg-white p-4 sm:grid-cols-2">
        <label className="grid gap-1 text-sm">
          {vi.docType}
          <select
            className="rounded border border-stone-300 px-2 py-2"
            value={docType}
            onChange={(event) => setDocType(event.target.value as DocType)}
          >
            {types.map((type) => (
              <option key={type} value={type}>
                {vi.docTypes[type]}
              </option>
            ))}
          </select>
        </label>
        <label className="grid gap-1 text-sm">
          {vi.module}
          <input
            className="rounded border border-stone-300 px-2 py-2"
            value={moduleName}
            placeholder={vi.modulePlaceholder}
            onChange={(event) => setModuleName(event.target.value)}
          />
        </label>
        <label className="grid gap-1 text-sm sm:col-span-2">
          {vi.chooseFile}
          <input
            className="rounded border border-dashed border-stone-300 px-2 py-6 text-stone-600"
            type="file"
            accept=".md,.txt,text/markdown,text/plain"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
          <span className="text-xs text-stone-500">{file ? file.name : vi.dropHint}</span>
        </label>
        <button
          className="rounded bg-stone-900 px-3 py-2 text-sm text-white disabled:opacity-50 sm:col-span-2 sm:w-fit"
          type="submit"
          disabled={upload.isPending || !file}
        >
          {upload.isPending ? vi.uploading : vi.upload}
        </button>
        {message ? <p className="text-sm text-red-700 sm:col-span-2">{message}</p> : null}
      </form>
      {documents.isLoading ? <p className="text-sm text-stone-500">…</p> : null}
      {documents.data && documents.data.length === 0 ? (
        <p className="text-sm text-stone-600">{vi.emptyDocuments}</p>
      ) : null}
      {documents.data && documents.data.length > 0 ? (
        <div className="overflow-x-auto rounded-lg border border-stone-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-stone-200 text-stone-500">
              <tr>
                <th className="px-3 py-2 font-medium">{vi.name}</th>
                <th className="px-3 py-2 font-medium">{vi.docType}</th>
                <th className="px-3 py-2 font-medium">{vi.status}</th>
                <th className="px-3 py-2 font-medium">{vi.chunks}</th>
              </tr>
            </thead>
            <tbody>
              {documents.data.map((row) => (
                <tr key={row.version_id} className="border-b border-stone-100 last:border-0">
                  <td className="px-3 py-2">{row.name}</td>
                  <td className="px-3 py-2">{vi.docTypes[row.doc_type as DocType] ?? row.doc_type}</td>
                  <td className="px-3 py-2">
                    {row.status === "ready" ? vi.statusReady : row.status === "failed" ? vi.statusFailed : vi.statusWorking}
                    {row.error ? <span className="mt-1 block text-red-700">{row.error}</span> : null}
                  </td>
                  <td className="px-3 py-2">{row.chunk_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
      {documents.error instanceof Error ? <p className="text-sm text-red-700">{documents.error.message}</p> : null}
    </div>
  );
}
