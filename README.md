# Plant Epigenomics Weekly Digest

A bilingual literature workspace for plant epigenomics, fruit development and multi-omics, emphasizing Capsicum and Solanaceae.

**Website:** https://qliugithub.github.io/plant-epigenomics-weekly-digest/

## Reading workspace / 文献工作台

- Switch **中文 / English** at the top right. Every archived paper has the same complete six-part commentary in both languages; language, tags and filters have shareable URLs.
- Combine the tag bar with species, process, regulation, method, evidence type, article type and reading-priority filters. Tags describe the actual study, not proposed pepper applications.
- Four bilingual research guides: H3K27me3 and ripening, fruit TF networks, the 22-tissue atlas, and metabolism. These are research guides, not systematic reviews.
- Open independent paper pages to read sources, commentary versions, registered publication relations and correction/retraction records.
- Save papers, mark to-read/read and add personal notes. **Notes stay in this browser**, may be visible to other users of the device, and do not synchronize or enter this public repository. Export/import JSON backups to move them. Import keeps the newer record per paper without deleting others. Export remains available if browser storage fails.
- Export one paper or filtered results as RIS / BibTeX. Missing authors are never invented. Unmatched bibliography is marked unverified; confirm before citing.
- The left sidebar uses an AI-generated decorative pepper image, not a scientific specimen photograph.

## Data and versions

Authoritative files live in `data/`:

| File | Purpose |
| --- | --- |
| `papers.json` | Current paper records, both languages, classifications, source and bibliographic check |
| `issues.json` | Issue summaries and references to specific paper revision numbers |
| `revisions.json` | Append-only commentary snapshots; historical issues keep their referenced content |
| `candidates.json` | All retained retrieved candidates, selection state and search coverage |
| `topics.json` | Bilingual research guides and topic matching rules |

Run `python scripts/build_site.py` after editing canonical content. It records changed paper content as a new revision, renders `dist/*.json` and creates stable `dist/papers/paper-…/` URLs. Do not edit generated catalog or paper HTML directly. Keep existing issue revision references unchanged when revising a current paper. Git history also retains all committed data changes.

The initial four issues (2026-08-14 through 2026-09-04) contain 13 imported historical papers. Chinese source text is retained; the English commentary mirrors it. **Imported scientific claims have not all been independently verified.**

## Retrieval and checks

`python scripts/refresh_resources.py` runs without a model key:

- Europe PMC searches in three lanes: Capsicum/Solanaceae, plant epigenomics, and methods/resources. A 28-day publication **or first-indexing** window helps recover late-indexed records. Each lane paginates up to 500 results; truncation and failures are marked incomplete rather than silently called complete.
- The candidate pool retains retrieved records, including unselected records and records without abstracts. Candidate inclusion is not a recommendation.
- Crossref DOI/title checks use a conservative title-match threshold. Registered authors, dates, DOI relations and publication updates are recorded, with original dates retained and differences shown. Checks refresh at most weekly; failures never erase a previous successful match.
- A bibliographic match **does not verify full-text scientific conclusions**. Missing records do not establish that a paper is invalid. Crossref relations and update notices are not exhaustive.

Source documentation: [Europe PMC](https://europepmc.org/RestfulWebService), [Crossref API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/), [Crossref relation/update filters](https://www.crossref.org/documentation/retrieve-metadata/rest-api/rest-api-filters/).

## Weekly generation and deployment

- The weekly workflow runs Friday **01:00 UTC / 09:00 Singapore**. GitHub can delay scheduled runs. Check the Actions run history for actual results.
- It refreshes candidates, deduplicates by title/DOI and balances candidates across three lanes (up to 36 unique abstracts). The model may select 0–5 worthwhile papers, preserving preprint uncertainty and separating findings from research proposals.
- Every selected paper must have six substantive sections in **both languages**, an English/Chinese issue summary and valid controlled classifications. Missing English or incomplete analysis causes failure before changing the archive.
- Analysis uses abstracts, not an assumed full-text review. Retrieval coverage is limited to indexed sources; no qualifying papers is distinct from failed retrieval.
- Same-date issues are preserved. Candidate checks may refresh, but duplicate dates do not regenerate a historical issue.
- Both workflows build and publish GitHub Pages and commit refreshed canonical data. Website publication uses no model key. A weekly generation needs repository secret `OPENAI_API_KEY`; optional repository variable `OPENAI_MODEL` defaults to `gpt-4.1-mini`. Never place secrets in site code or data.
- Manual weekly runs check API access before generation. API charges are separate from a ChatGPT subscription.
- Configure Pages source as **GitHub Actions**. Both workflows share a concurrency group so scheduled generation and publication do not overwrite each other.
- This repository updates the public GitHub Pages site; the earlier private Sites snapshot and the separate ChatGPT scheduled conversation are not synchronized by this workflow.

## Validation

```sh
python tests/test_pipeline.py
node tests/test_ui.cjs
python scripts/build_site.py
node --check dist/app.js
```

Tests use mocked network/model responses and a DOM harness. They cover bilingual completeness, combined tags, topic routing, browser-only notes, backup validation, citation escaping, mismatched metadata, failed search coverage and immutable revisions. They make no paid API calls. Serve `dist/` with any static HTTP server for local preview.
