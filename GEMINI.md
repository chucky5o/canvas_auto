# Gemini Canvas Automation Log

## Project Goal
Automate the management of Canvas courses (INF-102 Spring 2026), specifically optimizing assignment timelines, ensuring content clarity (Learning Objectives), and enforcing access control dates to pace student progress.

## Current Status (Feb 15, 2026)
- **Tooling:** Created `CanvasClient` CLI tool in `main.py` with API Token support.
- **Access:** Verified instructor access to 3 courses: `W091` (25688), `W094` (25691), `W099` (25697).
- **Automation:** Successfully automated all updates using the provided API Token.

## Completed Actions

### 1. Standardization Across All Courses
The following actions were applied identically to **INF-102-W091**, **INF-102-W094**, and **INF-102-W099**:

*   **Module Renamed:** "Module 7" renamed to **"Module 6 - Reflective assignment"**.
*   **Content Published:** Module 4 and all associated assignments published.
*   **Descriptions Updated:**
    *   *Networking Basics:* Added Learning Objectives.
    *   *MSFT Word:* Standardized "Learning Objectives" header.

### 2. Assignment Timeline & Access Control
All assignments in Modules 4, 5, and 6 have been rescheduled with a weekly cadence (Sundays) and access control dates (Unlock 2 weeks prior, Lock on following Wednesday).

| Assignment | Due Date (Sun) | Unlock Date (Avail From) | Lock Date (Until) |
| :--- | :--- | :--- | :--- |
| **MSFT Word** | Mar 08, 2026 | Feb 23, 2026 | Mar 11, 2026 |
| **Networking Basics** | Mar 22, 2026 | Mar 09, 2026 | Mar 25, 2026 |
| **Programming 1** | Apr 05, 2026 | Mar 23, 2026 | Apr 08, 2026 |
| **Programming 2** | Apr 19, 2026 | Apr 06, 2026 | Apr 22, 2026 |
| **Quiz 2** | Apr 26, 2026 | Apr 20, 2026 | Apr 29, 2026 |
| **Reflection** | May 03, 2026 | Apr 27, 2026 | May 06, 2026 |

## Next Semester Planning
A comprehensive review and proposal for the 14-week / 1-credit structure has been generated in `NEXT_SEMESTER_PROPOSAL.md`.
