"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { PageBanner } from "@/components/ui/page-banner";
import { listDocuments } from "@/lib/api/client";
import { vi } from "@/lib/i18n/vi";
import { DocumentList } from "./document-list";
import { UploadForm } from "./upload-form";
import styles from "./documents.module.css";

export function DocumentDesk() {
  const documents = useQuery({
    queryKey: ["documents"],
    queryFn: listDocuments,
    refetchInterval: (query) => query.state.data?.some(({ status }) => status !== "ready" && status !== "failed")
      ? 1500 : false,
  });
  const [search, setSearch] = useState("");

  return (
    <>
      <PageBanner title={vi.documentsTitle} description={vi.documentsLead} variant="documents" />
      <div className={styles.library}>
        <UploadForm />
        <DocumentList
          rows={documents.data ?? []} search={search} setSearch={setSearch}
          loading={documents.isPending} failed={documents.isError}
          retry={() => { void documents.refetch(); }}
        />
      </div>
    </>
  );
}
