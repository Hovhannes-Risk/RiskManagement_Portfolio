Project C — Automated PDF Reporting

Two scheduled PDF reports built directly with matplotlib + PdfPages. Designed to run unattended on a Windows Task Scheduler cron — no daemon, no web server, no infrastructure overhead.

Why scheduled PDFs

The dashboard in Project A answers "what's happening right now?" — operator-driven, interactive, one user at a time. The PDFs answer a different question: what happened over the last day / week, signed and filed for the record?

PDFs are the right format because

- Versioned artefact — each run is a frozen, time-stamped file. Useful for audit and for week-over-week comparison without re-running the pipeline.
- No client dependency — opens anywhere, no Streamlit / Python install needed on the recipient side.
- Email-attachable — daily report goes to the risk desk inbox; weekly to management. Same file, different distribution.

The two reports

| Report | Cadence | Audience | Sections |

| Daily Risk Report | Daily | Risk desk | KPI strip · top-risk players · bot suspects · sport-level breakdown |
| Weekly Executive Summary | Weekly | Management | Week-over-week trend · loss concentration · top markets · prioritised recommendations |

The daily is operational — it answers what changed since yesterday and who needs reviewing? The weekly is strategic — where is the book bleeding and what should we do about it?

Design choice — manual axis placement

Layout uses explicit fig.add_axes([x, y, w, h]) placement with 0–1 figure-relative coordinates, not matplotlib's grid system.

Why: week-over-week PDF diffs are only meaningful if the cards, headers, and tables sit at the same pixel positions every run. The grid system reflows when content lengths change; manual axes do not. The cost is more layout code; the benefit is deterministic visual diffs across periods.

Files


Project_C_Automated_Reports
├── README.md              This file
├── daily_report.py        Daily Risk Report generator
├── weekly_report.py       Weekly Executive Summary generator
└── sample_output          Example PDFs from real runs


Run locally

bash
pip install -r requirements.txt
python daily_report.py
python weekly_report.py


Both scripts write a date-stamped PDF into sample_output. Inputs are the anonymized analysis files produced by Project B; no raw wallet identifiers are read at any point.

Scheduling

Designed for Windows Task Scheduler. Example daily trigger


Program   C:\Python310\python.exe
Arguments C:\path\to\Project_C_Automated_Reports\daily_report.py
Trigger   Daily at 07:00


No long-running process, no port to expose, no service to monitor. The scheduler is the orchestrator.

Known limitations

- No email delivery in the script itself. Generation and distribution are separated — the script writes the PDF, an external scheduler / mail job picks it up. Production deployment would add SMTP, but keeping it out of the report script avoids tying generation to mail-server availability.
- Static thresholds. Risk-band cutoffs are inherited from Project B; if those are recalibrated the reports inherit the new bands automatically, but the report itself has no calibration logic.
- Single-language output. PDFs render in English. Multi-language output would require a font fallback layer for non-Latin scripts.

Cross-references

- Inputs produced by Project_B_ML_Anomaly_Detection/ (master_analysis.xlsx, risk scores)
- Same anonymization rule as Projects A and B — see Documentation/methodology.md §7
- The dashboard's PDF export button (Project A) uses the same template family as daily_report.py

Stack

Python 3.10+ · matplotlib (PdfPages) · pandas · numpy · openpyxl
