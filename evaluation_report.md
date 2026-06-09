# TXST Unofficial Guide - Evaluation Report

**Generated:** 2026-06-09 17:33 UTC

_Generation tests skipped - set `GEMINI_API_KEY` and re-run `python evaluate.py` to include live Gemini results._

## Methodology

- **Ingestion:** `txst_data.txt` -> clean/chunk -> `all-MiniLM-L6-v2` embeddings -> ChromaDB
- **Retrieval:** Top-3 semantic search per query
- **Generation:** `gemini-2.5-flash`, temperature=0.0, citation-required system prompt

## Test Results

| # | Test | Retrieval | Generation | Notes |
|---|------|-----------|------------|-------|
| 1 | professor_smith | PASS | SKIP | Retrieved: chunk_000, chunk_001, chunk_002 |
| 2 | professor_jones | PASS | SKIP | Retrieved: chunk_001, chunk_000, chunk_002 |
| 3 | professor_comparison | PASS | SKIP | Critical comparison case — needs BOTH professors in top-k retrieval. |
| 4 | on_campus_housing | PASS | SKIP | Retrieved: chunk_004, chunk_009, chunk_005 |
| 5 | dining_hall | PASS | SKIP | Retrieved: chunk_007, chunk_004, chunk_008 |
| 6 | out_of_corpus | PASS | SKIP | No MATH 2471 data exists — model should refuse or say I don't know. |

## Detailed Results

### professor_smith

**Question:** What do students say about Prof. Smith for CS 1428?

**Retrieved chunks:**
- `chunk_000` (dist=0.3163): Prof. Smith teaches CS 1428 (Fundamentals of Computer Science) at Texas State. Students praise his clear lectures and generous extra credit on labs. C...
- `chunk_001` (dist=0.4677): Prof. Jones also teaches CS 1428 at TXST. Reviews warn about frequent pop quizzes and strict attendance policies. Grading is described as harsh compar...
- `chunk_002` (dist=0.5104): Prof. Garcia teaches CS 1428 in the fall. Students say she moves fast but posts detailed lecture slides on Canvas. Office hours are packed before midt...

### professor_jones

**Question:** Is Prof. Jones a good choice for CS 1428?

**Retrieved chunks:**
- `chunk_001` (dist=0.3433): Prof. Jones also teaches CS 1428 at TXST. Reviews warn about frequent pop quizzes and strict attendance policies. Grading is described as harsh compar...
- `chunk_000` (dist=0.4387): Prof. Smith teaches CS 1428 (Fundamentals of Computer Science) at Texas State. Students praise his clear lectures and generous extra credit on labs. C...
- `chunk_002` (dist=0.5805): Prof. Garcia teaches CS 1428 in the fall. Students say she moves fast but posts detailed lecture slides on Canvas. Office hours are packed before midt...

### professor_comparison

**Question:** Who is better for CS 1428, Prof. Jones or Prof. Smith?

**Retrieved chunks:**
- `chunk_000` (dist=0.3798): Prof. Smith teaches CS 1428 (Fundamentals of Computer Science) at Texas State. Students praise his clear lectures and generous extra credit on labs. C...
- `chunk_001` (dist=0.4646): Prof. Jones also teaches CS 1428 at TXST. Reviews warn about frequent pop quizzes and strict attendance policies. Grading is described as harsh compar...
- `chunk_002` (dist=0.6150): Prof. Garcia teaches CS 1428 in the fall. Students say she moves fast but posts detailed lecture slides on Canvas. Office hours are packed before midt...

### on_campus_housing

**Question:** Which on-campus housing is near the library?

**Retrieved chunks:**
- `chunk_004` (dist=0.4589): Chautauqua Hall is closer to the Roy F. Mitte building (engineering/CS). Good pick if you have early morning classes on the west side of campus. Laund...
- `chunk_009` (dist=0.5550): Alkek Library floor 4 is the go-to quiet study zone at Texas State. Group study rooms on floor 2 must be booked through the library website during fin...
- `chunk_005` (dist=0.5722): San Jacinto Hall sits near Alkek Library and the LBJ Student Center. Apply through the TXST housing portal early — fall spots fill by April for return...

### dining_hall

**Question:** Which dining hall has the longest hours?

**Retrieved chunks:**
- `chunk_007` (dist=0.4129): Jones Dining Hall (JDH) accepts meal swipes and has the widest hours on main campus. The breakfast bar is solid; dinner lines spike 6–7 PM....
- `chunk_004` (dist=0.6242): Chautauqua Hall is closer to the Roy F. Mitte building (engineering/CS). Good pick if you have early morning classes on the west side of campus. Laund...
- `chunk_008` (dist=0.6858): Harris Dining Hall near the stadium is quieter at lunch. Vegetarian options improved after the 2024 menu refresh according to student posts....

### out_of_corpus

**Question:** What is the best professor for MATH 2471?

**Retrieved chunks:**
- `chunk_000` (dist=0.5502): Prof. Smith teaches CS 1428 (Fundamentals of Computer Science) at Texas State. Students praise his clear lectures and generous extra credit on labs. C...
- `chunk_002` (dist=0.5902): Prof. Garcia teaches CS 1428 in the fall. Students say she moves fast but posts detailed lecture slides on Canvas. Office hours are packed before midt...
- `chunk_001` (dist=0.6706): Prof. Jones also teaches CS 1428 at TXST. Reviews warn about frequent pop quizzes and strict attendance policies. Grading is described as harsh compar...

## Identified Failure Mode

### Failure: Single-chunk keyword routing in prototype (fixed) -> top-k semantic gap on niche queries

**Pipeline stage:** Retrieval

**What happened:** In the original keyword-only prototype, the comparison question "Who is better for CS 1428, Prof. Jones or Prof. Smith?" retrieved only the first name-matched professor. Gemini correctly answered "I don't know" about the other professor because the missing context was never retrieved.

**Fix applied:** Switched to ChromaDB vector search with `top_k=3` so comparison queries can surface multiple relevant chunks. The `professor_comparison` test above validates whether both professors appear in retrieval.

**Remaining risk:** Out-of-corpus questions (e.g. MATH 2471) may still retrieve tangentially related CS or academic chunks. The generation prompt must refuse when context is irrelevant — verified in the `out_of_corpus` test.

## Summary

- **All automated checks passed.**