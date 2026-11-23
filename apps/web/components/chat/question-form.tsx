import type { FormEvent, RefObject } from "react";

import { Icon } from "@/components/ui/icon";
import { vi } from "@/lib/i18n/vi";
import styles from "./chat.module.css";

type Props = {
  question: string;
  setQuestion: (question: string) => void;
  docType: string;
  setDocType: (type: string) => void;
  module: string;
  setModule: (module: string) => void;
  input: RefObject<HTMLTextAreaElement | null>;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onCancel: () => void;
  pending: boolean;
  showExamples: boolean;
};

export function QuestionForm(props: Props) {
  return (
    <form className={`panel ${styles.composer}`} onSubmit={props.onSubmit}>
      <label className="field">
        <span className="panel-title">{vi.question}</span>
        <textarea
          className={`control ${styles.question}`}
          ref={props.input}
          name="question"
          value={props.question}
          onChange={(event) => props.setQuestion(event.target.value)}
          placeholder={vi.questionPlaceholder}
          required
          maxLength={2000}
          rows={3}
        />
      </label>
      <div className={styles.formBar}>
        <label className="field">
          {vi.docType}
          <select className="control" value={props.docType} onChange={(event) => props.setDocType(event.target.value)}>
            <option value="">{vi.filterAll}</option>
            {Object.entries(vi.docTypes).map(([type, label]) => <option key={type} value={type}>{label}</option>)}
          </select>
        </label>
        <label className="field">
          {vi.module}
          <input className="control" value={props.module} onChange={(event) => props.setModule(event.target.value)}
            placeholder={vi.filterModule} maxLength={200} />
        </label>
        <div className={styles.submit}>
          {props.pending ? (
            <button type="button" className="button secondary" key="cancel" onClick={(event) => {
              event.preventDefault();
              props.onCancel();
            }}>
              <Icon name="close" size={16} /> {vi.stop}
            </button>
          ) : (
            <button type="submit" className="button primary" key="submit" disabled={!props.question.trim()}>
              {vi.ask} <Icon name="arrow" size={18} />
            </button>
          )}
        </div>
      </div>
      {props.showExamples && (
        <div className={styles.examples}>
          <span>{vi.exampleQuestions}</span>
          <div>
            {vi.examples.map((example) => (
              <button type="button" key={example} onClick={() => {
                props.setQuestion(example);
                props.input.current?.focus();
              }}>{example}</button>
            ))}
          </div>
        </div>
      )}
    </form>
  );
}
