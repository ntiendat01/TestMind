# Spec 00 — Cấu trúc repository

Monorepo. Mỗi file ≤ 500 dòng (luật cứng, xem `AGENT.md`); cây dưới đây được thiết kế để file nhỏ, mỗi file một trách nhiệm.

## Cây thư mục

```
testmind-ai/
├── AGENT.md                      # luật cho agent
├── README.md                     # giới thiệu, quickstart, demo, bảng benchmark (số thật)
├── Makefile                      # check, test, lint, eval-dev, eval-test, reindex, bench, gen-api
├── docker-compose.yml            # web, api, postgres(pgvector)
├── .env.example
├── .gitignore
├── .github/workflows/
│   ├── ci.yml                    # lint + type + test + file-length + smoke eval
│   └── release.yml               # (tuỳ chọn) build image
│
├── apps/
│   ├── api/                      # FastAPI
│   │   ├── pyproject.toml        # uv, ruff, mypy, pytest config
│   │   ├── Dockerfile            # multi-stage: build tm-core wheel -> runtime
│   │   ├── alembic.ini
│   │   ├── migrations/versions/  # Alembic, không sửa migration đã áp dụng
│   │   ├── app/
│   │   │   ├── main.py           # tạo app, mount router, middleware
│   │   │   ├── settings.py       # pydantic-settings, đọc env
│   │   │   ├── deps.py           # dependency injection (db session, clients)
│   │   │   ├── core/
│   │   │   │   ├── interfaces.py # Protocol: Chunker, LexicalIndex, Retriever, Reranker, LLMClient, Embedder
│   │   │   │   ├── errors.py     # lỗi miền + mã lỗi API
│   │   │   │   ├── logging.py
│   │   │   │   └── ids.py        # sinh chunk_id, hash
│   │   │   ├── schemas/          # Pydantic (vào/ra API + schema trao đổi với tm_core)
│   │   │   │   ├── documents.py
│   │   │   │   ├── query.py
│   │   │   │   ├── trace.py
│   │   │   │   ├── eval.py
│   │   │   │   └── parsed.py     # ParsedDocument, Block, ChunkDoc
│   │   │   ├── db/
│   │   │   │   ├── models.py     # SQLAlchemy (tách file nếu > 300 dòng)
│   │   │   │   ├── session.py
│   │   │   │   └── repositories/ # documents.py, chunks.py, trace.py, queries.py, eval_runs.py
│   │   │   ├── routers/          # mỏng: validate -> service
│   │   │   │   ├── documents.py
│   │   │   │   ├── jobs.py
│   │   │   │   ├── query.py      # SSE
│   │   │   │   ├── trace.py
│   │   │   │   ├── requirements.py
│   │   │   │   ├── eval.py
│   │   │   │   └── health.py
│   │   │   ├── services/
│   │   │   │   ├── ingestion/    # pipeline.py, versioning.py, extract_requirements.py,
│   │   │   │   │                 # extract_testcases.py, column_mapping.py, jobs.py
│   │   │   │   ├── retrieval/    # analyze.py, dense.py, lexical.py, fusion.py,
│   │   │   │   │                 # rerank.py, context.py, sufficiency.py, pipeline.py
│   │   │   │   ├── generation/   # prompt.py, answer.py, citation_check.py, stream.py
│   │   │   │   ├── trace/        # candidates.py, judge.py, coverage.py, matrix.py, export.py
│   │   │   │   └── eval/         # runner.py, metrics.py, judge.py, report.py
│   │   │   ├── parsers/          # bản Python tham chiếu
│   │   │   │   ├── docx.py, xlsx.py, csv.py, md.py, pdf.py
│   │   │   ├── chunking/         # structure_aware.py, fixed.py (baseline), tokens.py
│   │   │   ├── lexical/          # python_ref.py (BM25 tham chiếu), tm_core_adapter.py
│   │   │   └── clients/          # llm.py, embedder.py, reranker.py (kèm fake trong tests)
│   │   └── tests/
│   │       ├── unit/             # theo cấu trúc app/
│   │       ├── integration/      # cần Postgres (testcontainers/compose)
│   │       ├── fakes/            # fake LLM/embedder
│   │       └── fixtures/         # docx/xlsx/md nhỏ cho test
│   │
│   └── web/                      # Next.js (xem spec 06)
│       ├── package.json, tsconfig.json, next.config.ts, tailwind.config.ts
│       ├── Dockerfile
│       ├── app/(app)/{documents,chat,trace,eval,history}/page.tsx
│       ├── app/layout.tsx
│       ├── components/{documents,chat,trace,eval,ui}/
│       ├── hooks/
│       ├── lib/{api,sse,i18n}/
│       └── tests/{unit,e2e}/
│
├── crates/
│   └── tm-core/                  # Rust (xem spec 07)
│       ├── Cargo.toml
│       ├── pyproject.toml        # maturin
│       ├── src/
│       │   ├── lib.rs            # đăng ký module PyO3, chỉ re-export
│       │   ├── error.rs          # TmCoreError
│       │   ├── types.rs          # Block, Loc, ChunkDoc (serde)
│       │   ├── parse/            # mod.rs, xlsx.rs, csv.rs, md.rs, (docx.rs: hoãn)
│       │   ├── chunk/            # mod.rs, structure.rs, tokens.rs
│       │   ├── lexical/          # mod.rs, index.rs, tokenizer.rs, filters.rs
│       │   ├── fusion.rs
│       │   └── metrics.rs
│       ├── tests/                # integration test Rust + fixtures/
│       ├── benches/              # criterion
│       └── python/tests/         # pytest kiểm tra binding
│
├── config/                       # cấu hình thí nghiệm (versioned)
│   ├── chunking.yaml
│   ├── retrieval.yaml            # top-N, RRF k, rerank on/off, tau
│   ├── prompts/                  # answer.vi.md, judge_trace.md, ... (có prompt_version)
│   └── exp/                      # baseline.yaml, hybrid.yaml, hybrid_rerank.yaml
│
├── eval/
│   ├── datasets/<domain>/
│   │   ├── corpus/               # BRD, testcase.xlsx, bugs.csv (giả lập/công khai)
│   │   ├── dev.jsonl
│   │   ├── test.jsonl            # KHÓA
│   │   ├── adversarial.jsonl
│   │   ├── trace_gt.jsonl
│   │   ├── bug_gt.jsonl
│   │   └── README.md             # nguồn, giấy phép, cách tạo, giới hạn
│   ├── cli.py                    # entrypoint `make eval-*`
│   └── reports/                  # báo cáo mỗi run (md + json)
│
├── bench/
│   ├── python_vs_rust/           # parse, index, search, chunk
│   ├── data/                     # dữ liệu benchmark sinh theo script (không commit file lớn)
│   └── results/                  # kết quả thật kèm môi trường
│
├── scripts/
│   ├── check_file_length.py      # fail nếu file > 500 dòng (miễn lockfile + AUTO-GENERATED)
│   ├── gen_api_client.sh         # OpenAPI -> TS client (header AUTO-GENERATED)
│   ├── seed_demo.py              # nạp dataset mẫu
│   └── reindex.py                # dựng lại tantivy từ Postgres
│
└── docs/
    ├── architecture.md
    ├── roadmap.md
    ├── specs/                    # 00 .. 07
    ├── adr/                      # 0001-*.md: mỗi quyết định/dependency mới một file
    └── images/                   # sơ đồ xuất ra (nếu cần)
```

## Quy ước

| Chủ đề | Quy ước |
|---|---|
| Phụ thuộc đi một chiều | `routers → services → (db/repositories, clients, lexical, parsers, tm_core)`; `services/*` không import vòng tròn |
| Tách file | Chạm ~400 dòng thì tách module; hàm < 50 dòng, file < 300 dòng là mục tiêu |
| Tên file/test | Test phản chiếu cấu trúc nguồn: `app/services/retrieval/fusion.py` ↔ `tests/unit/services/retrieval/test_fusion.py` |
| Interface | Chỉ khai báo ở `core/interfaces.py`; cài đặt Python (`lexical/python_ref.py`) và Rust (`tm_core_adapter.py`) đều tuân thủ |
| Cấu hình | Tham số thí nghiệm nằm ở `config/`, không hard-code trong service; mỗi eval run lưu snapshot |
| Dữ liệu | `eval/datasets/*/corpus` chỉ chứa dữ liệu giả lập/công khai; file lớn dùng script sinh, không commit |
| Sinh tự động | File sinh (OpenAPI client) có header `AUTO-GENERATED`, không sửa tay |
| Chủ sở hữu thay đổi | Đổi `schemas/parsed.py` ⇔ đổi `crates/tm-core/src/types.rs` + golden test + spec 07 trong cùng commit |

## Thứ tự dựng cây (khớp roadmap)

- **M0:** tạo toàn bộ khung thư mục, `Makefile`, Compose, CI, `check_file_length.py`, health check; thư mục chưa dùng chỉ có `.gitkeep`.
- **M1:** `parsers/`, `chunking/`, `services/ingestion`, `services/retrieval` (dense), `services/generation`, `routers`, `apps/web` (documents/chat).
- **M2:** `eval/`, `services/eval`, `config/exp/baseline.yaml`.
- **M3:** `lexical/`, `services/retrieval/{fusion,rerank}`, `crates/tm-core`, `bench/`.
- **M4:** `services/trace`, `routers/trace.py`, `apps/web/trace`.
- **M5:** hoàn thiện CI, E2E, logging, deploy, README.

## Acceptance

- Sau M0: `tree` của repo khớp cây trên (cho phép thư mục `.gitkeep` rỗng); `make check` xanh.
- Không file nào do agent viết vượt 500 dòng (script kiểm tra xác nhận).
