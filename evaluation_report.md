# TXST Unofficial Guide - Evaluation Report

**Generated:** 2026-06-09 18:06 UTC

| # | Question | Retrieval | Response accuracy |
|---|----------|-----------|-------------------|
| 1 | What do students say about Prof. Smith for CS 1428... | PASS | SKIP (no API key) |
| 2 | Is Prof. Jones a good choice for CS 1428?... | PASS | SKIP (no API key) |
| 3 | Which on-campus housing is near Alkek Library?... | PASS | SKIP (no API key) |
| 4 | Which dining hall has the widest hours on main cam... | PASS | SKIP (no API key) |
| 5 | Who is the best professor for MATH 2471 at TXST?... | PASS | SKIP (no API key) |

## Detailed Results

### Q1: professor_smith

**Question:** What do students say about Prof. Smith for CS 1428?
**Expected:** Clear lectures, extra credit on labs, math-heavy exams, 4.5/5 rating.
**Retrieval:** PASS
**Accuracy:** SKIP (no API key)

**Retrieved chunks:**
- `rmp_cs1428_smith.txt` (dist=0.3163): Prof. Smith teaches CS 1428 (Fundamentals of Computer Science) at Texas State. Students praise his clear lectures and ge...
- `rmp_cs1428_jones.txt` (dist=0.4677): Prof. Jones also teaches CS 1428 at TXST. Reviews warn about frequent pop quizzes and strict attendance policies. Gradin...
- `rmp_cs1428_garcia.txt` (dist=0.5104): Prof. Garcia teaches CS 1428 in the fall. Students say she moves fast but posts detailed lecture slides on Canvas. Offic...
- `reddit_academics_cs_advising.txt` (dist=0.5849): The CS advising office is in Comal Building 307. Bring your degree audit PDF to drop/add week — walk-in slots go fast in...

### Q2: professor_jones

**Question:** Is Prof. Jones a good choice for CS 1428?
**Expected:** No — pop quizzes, strict attendance, harsh grading, 2/10 rating.
**Retrieval:** PASS
**Accuracy:** SKIP (no API key)

**Retrieved chunks:**
- `rmp_cs1428_jones.txt` (dist=0.3433): Prof. Jones also teaches CS 1428 at TXST. Reviews warn about frequent pop quizzes and strict attendance policies. Gradin...
- `rmp_cs1428_smith.txt` (dist=0.4387): Prof. Smith teaches CS 1428 (Fundamentals of Computer Science) at Texas State. Students praise his clear lectures and ge...
- `reddit_academics_cs_advising.txt` (dist=0.5601): The CS advising office is in Comal Building 307. Bring your degree audit PDF to drop/add week — walk-in slots go fast in...
- `rmp_cs1428_garcia.txt` (dist=0.5805): Prof. Garcia teaches CS 1428 in the fall. Students say she moves fast but posts detailed lecture slides on Canvas. Offic...

### Q3: housing_library

**Question:** Which on-campus housing is near Alkek Library?
**Expected:** San Jacinto Hall, near Alkek Library and LBJ Student Center.
**Retrieval:** PASS
**Accuracy:** SKIP (no API key)

**Retrieved chunks:**
- `reddit_campus_alkek_library.txt` (dist=0.3714): Alkek Library floor 4 is the go-to quiet study zone at Texas State. Group study rooms on floor 2 must be booked through ...
- `reddit_housing_san_jacinto.txt` (dist=0.4749): San Jacinto Hall sits near Alkek Library and the LBJ Student Center. Apply through the TXST housing portal early — fall ...
- `reddit_housing_chautauqua.txt` (dist=0.5389): Chautauqua Hall is closer to the Roy F. Mitte building (engineering/CS). Good pick if you have early morning classes on ...
- `reddit_housing_bobcat_village.txt` (dist=0.6122): Bobcat Village is popular on-campus housing at TXST. Pros: furnished units and a pool. Cons: pricey compared to off-camp...

### Q4: dining_hours

**Question:** Which dining hall has the widest hours on main campus?
**Expected:** Jones Dining Hall (JDH) has the widest hours on main campus.
**Retrieval:** PASS
**Accuracy:** SKIP (no API key)

**Retrieved chunks:**
- `reddit_dining_jones_hall.txt` (dist=0.3486): Jones Dining Hall (JDH) accepts meal swipes and has the widest hours on main campus. The breakfast bar is solid; dinner ...
- `reddit_housing_chautauqua.txt` (dist=0.4282): Chautauqua Hall is closer to the Roy F. Mitte building (engineering/CS). Good pick if you have early morning classes on ...
- `reddit_dining_harris_hall.txt` (dist=0.6356): Harris Dining Hall near the stadium is quieter at lunch. Vegetarian options improved after the 2024 menu refresh accordi...
- `reddit_campus_alkek_library.txt` (dist=0.6393): Alkek Library floor 4 is the go-to quiet study zone at Texas State. Group study rooms on floor 2 must be booked through ...

### Q5: out_of_scope

**Question:** Who is the best professor for MATH 2471 at TXST?
**Expected:** System should refuse — no MATH 2471 documents in corpus.
**Retrieval:** PASS
**Accuracy:** SKIP (no API key)

**Retrieved chunks:**
- `rmp_cs1428_smith.txt` (dist=0.5127): Prof. Smith teaches CS 1428 (Fundamentals of Computer Science) at Texas State. Students praise his clear lectures and ge...
- `rmp_cs1428_jones.txt` (dist=0.5595): Prof. Jones also teaches CS 1428 at TXST. Reviews warn about frequent pop quizzes and strict attendance policies. Gradin...
- `rmp_cs1428_garcia.txt` (dist=0.5839): Prof. Garcia teaches CS 1428 in the fall. Students say she moves fast but posts detailed lecture slides on Canvas. Offic...
- `reddit_campus_alkek_library.txt` (dist=0.6900): Alkek Library floor 4 is the go-to quiet study zone at Texas State. Group study rooms on floor 2 must be booked through ...

## Failure Case

**Question:** Who is the best professor for MATH 2471 at TXST?

**Pipeline stage:** Retrieval + Generation

**What happened:** Retrieval returns CS 1428 professor chunks (semantic similarity to 'professor' queries) even though MATH 2471 is not in the corpus. Without strict grounding, the LLM might hallucinate a math professor name.

**Mitigation:** System prompt requires refusal when context lacks the answer. Programmatic source list shows retrieved docs are CS-related, not MATH 2471.

## Summary

All retrieval checks passed. Run with GEMINI_API_KEY for generation scores.