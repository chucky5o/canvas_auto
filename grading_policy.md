# Grading Policy for 1-Credit Course

## General Philosophy
- **Flexibility:** This is a 1-credit course. Do not be overly strict.
- **Focus:** Look for understanding of core concepts rather than perfection in execution.
- **Effort:** If the student is "completely off," this must be noted and graded accordingly.

## Rules
1.  **Late Policy:** 
    -   Assignments submitted after the `due_at` date carry a **10% penalty**. 
    -   **No exceptions.**
    -   Calculation: `Final Grade = Raw Grade * 0.90` (or `Max Score - 10%`).

## Instructions for AI Grader
-   Check the `submitted_at` timestamp against `due_at`.
-   If `submitted_at` > `due_at`, explicitly mention "Late Penalty Applied (-10%)".
-   Evaluate content based on the specific assignment instructions (Learning Objectives).
