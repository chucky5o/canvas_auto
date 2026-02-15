# Canvas Assistant CLI

A smart command-line tool for managing Canvas courses, automating grading workflows, and handling student submissions.

## Features

-   **Session Caching:** fast startup by remembering your login.
-   **Context Awareness:** "Set it and forget it" course selection.
-   **Smart Resolution:** Use course and assignment *names* instead of obscure IDs.
-   **Auto-Grader Helper:**
    -   Detects late submissions (10% penalty flag).
    -   Extracts text from PDF submissions for AI analysis.
    -   Queues ungraded work for review.

## Installation

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### 1. Initial Setup (Login)
Run any command to initialize your session. The tool will extract cookies from your browser (Chrome by default).
```bash
python main.py --action list-courses --browser chrome
```

### 2. Set Context
Select a course to work in. You can use part of the name!
```bash
python main.py --action set-context --course "INF-102"
```
*Now you don't need to specify `--course` for subsequent commands.*

### 3. Smart Grading Queue
Fetch all ungraded submissions for an assignment. The tool will check for late penalties and extract PDF text.
```bash
python main.py --action grade-queue --assignment "Networking Basics"
```

### 4. Grade a Submission
Submit a grade and comment.
```bash
python main.py --action grade-submission --assignment "Networking Basics" --student 12345 --grade 85 --comment "Good job, but late penalty applied."
```

## Configuration
Data is stored in `~/.canvas_tool/`.
-   `session.pkl`: Your login session.
-   `context.json`: Current course setting.
-   `cache.json`: Mappings of names to IDs.