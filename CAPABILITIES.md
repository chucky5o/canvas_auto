# Canvas Scraper Capabilities & Documentation

## Overview
This tool leverages your local browser's session cookies to authenticate with the Canvas Learning Management System (LMS). This allows it to act on your behalf with the same permissions you have in the web interface (Student, Teacher, TA, or Admin).

## Current Features
- **Authentication**: Automatically extracts session cookies from Chrome, Firefox, Safari, Brave, or Edge.
- **Course Listing**: Retrieves all courses where the user is enrolled (`--list-courses`).
- **Content Fetching**: Can download the HTML content of any specific Canvas URL.

## Potential Capabilities (Instructor Access)
Since the script operates with your user session, it can perform any action available in the Canvas web UI. By utilizing the [Canvas REST API](https://canvas.instructure.com/doc/api/), the script can be extended to automate the following:

### Course Management
- **Announcements**: Post, edit, or delete course announcements.
- **Assignments**: Create new assignments, update due dates, and modify settings (points, submission types).
- **Modules**: Publish/unpublish modules and items.
- **Pages**: Create and edit wiki pages.

### Grading & Student Interaction
- **SpeedGrader**: Retrieve student submissions and post grades/comments.
- **Quizzes**: Moderate quizzes and view statistics.
- **Discussions**: Reply to discussion threads automatically.
- **Inbox**: Send messages to students or course sections.

### Analytics & Reporting
- **Student Activity**: Download access logs and participation reports.
- **Assignment Stats**: Export grade distributions and submission times.

## "Optimized" Script Usage
The script has been updated to support modular actions.

### List All Courses
View all courses you have access to:
```bash
python main.py --list-courses
```

### Future Usage (Examples)
*Note: These commands demonstrate how the script can be extended.*

**List Assignments for a Course:**
```bash
python main.py --action list-assignments --course-id 25697
```

**Post an Announcement:**
```bash
python main.py --action post-announcement --course-id 25697 --title "Exam Reminder" --message "Don't forget the midterm is tomorrow!"
```
