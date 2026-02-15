import argparse
import requests
import browser_cookie3
import sys
import json
import re
import os
import pickle
import time
from urllib.parse import urlparse
from datetime import datetime, timezone
from pathlib import Path

# Try importing pypdf for text extraction
try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

# Configuration Paths
CONFIG_DIR = Path.home() / ".canvas_tool"
SESSION_FILE = CONFIG_DIR / "session.pkl"
CACHE_FILE = CONFIG_DIR / "cache.json"
CONTEXT_FILE = CONFIG_DIR / "context.json"

# Ensure config directory exists
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

class ConfigManager:
    def __init__(self):
        self.context = self._load_json(CONTEXT_FILE)
        self.cache = self._load_json(CACHE_FILE)

    def _load_json(self, path):
        if path.exists():
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_context(self, data):
        self.context.update(data)
        with open(CONTEXT_FILE, 'w') as f:
            json.dump(self.context, f, indent=4)

    def save_cache(self, key, data):
        self.cache[key] = data
        with open(CACHE_FILE, 'w') as f:
            json.dump(self.cache, f, indent=4)

    def get_context(self, key):
        return self.context.get(key)

    def get_cache(self, key):
        return self.cache.get(key)

class CanvasClient:
    def __init__(self, domain=None, browser="chrome", api_token=None, force_login=False):
        self.config = ConfigManager()
        
        # Load domain from context if not provided
        if not domain:
            domain = self.config.get_context("domain")
        
        if not domain:
            # Fallback default or error
            domain = "canvas.bergen.edu" # Default based on user history

        self.domain = domain
        self.base_url = f"https://{domain}"
        self.session = requests.Session()
        
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

        if api_token:
            self.session.headers.update({"Authorization": f"Bearer {api_token}"})
            print("Using API Token.")
        else:
            if not force_login and self._load_session():
                print("Restored session from cache.")
            else:
                print("Initializing new session...")
                self.session.headers.update({
                    "Referer": self.base_url,
                    "Origin": self.base_url
                })
                self._load_cookies(browser)
                self._extract_csrf_from_html()
                self._save_session()
                
        # Update context with valid domain
        self.config.save_context({"domain": self.domain})

    def _save_session(self):
        with open(SESSION_FILE, 'wb') as f:
            pickle.dump(self.session.cookies, f)

    def _load_session(self):
        if SESSION_FILE.exists():
            try:
                with open(SESSION_FILE, 'rb') as f:
                    cookies = pickle.load(f)
                    self.session.cookies.update(cookies)
                return True
            except:
                return False
        return False

    def _load_cookies(self, browser):
        print(f"Extracting cookies from {browser} for {self.domain}...")
        try:
            cj = getattr(browser_cookie3, browser)(domain_name=self.domain)
            if not cj:
                raise ValueError("No cookies found.")
            self.session.cookies.update(cj)
        except Exception as e:
            print(f"[!] Error extracting cookies: {e}")
            sys.exit(1)

    def _extract_csrf_from_html(self):
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            match = re.search(r'<meta name="_csrf_token" content="(.*?)"', response.text)
            if match:
                self.session.headers.update({"X-CSRF-Token": match.group(1)})
                return
            
            # Fixed regex for CSRF token extraction
            match = re.search(r'["\']_csrf_token["\']\s*:\s*["\'](.*?)["\']', response.text)
            if match:
                self.session.headers.update({"X-CSRF-Token": match.group(1)})
                return

            for cookie in self.session.cookies:
                if cookie.name == '_csrf_token':
                    self.session.headers.update({"X-CSRF-Token": cookie.value})
                    break
        except Exception as e:
            print(f"Warning: CSRF token extraction failed: {e}")

    def _get(self, endpoint, params=None):
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"API Request failed: {e}")
            if hasattr(e, 'response') and e.response.status_code == 401:
                print("Session expired. Try running with --force-login")
                # Invalidate session
                if SESSION_FILE.exists():
                    os.remove(SESSION_FILE)
            sys.exit(1)

    def _put(self, endpoint, data=None):
        url = f"{self.base_url}{endpoint}"
        self.session.headers.update({"Content-Type": "application/json"})
        try:
            response = self.session.put(url, json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Update failed: {e}")
            sys.exit(1)

    # --- Smart Resolution ---
    def resolve_course(self, identifier):
        if not identifier:
            # Try context
            ctx_id = self.config.get_context("course_id")
            if ctx_id:
                return ctx_id
            print("Error: No course specified and no context found. Use --set-context or --course-id.")
            sys.exit(1)

        # Check if it's an ID (digits)
        if identifier.isdigit():
            return identifier
        
        # Try to resolve name from cache
        courses = self.config.get_cache("courses")
        if courses:
            for c in courses:
                if identifier.lower() in c['name'].lower() or identifier.lower() in c['code'].lower():
                    return str(c['id'])
        
        # If not in cache, fetch and update cache
        print(f"Searching for course '{identifier}'...")
        self.list_courses(print_output=False) # Updates cache
        return self.resolve_course(identifier) # Retry

    def resolve_assignment(self, course_id, identifier):
        if identifier.isdigit():
            return identifier
        
        # Try cache
        cache_key = f"assignments_{course_id}"
        assignments = self.config.get_cache(cache_key)
        if assignments:
            for a in assignments:
                if identifier.lower() in a['name'].lower():
                    return str(a['id'])
        
        print(f"Searching for assignment '{identifier}'...")
        self.list_assignments(course_id, print_output=False)
        return self.resolve_assignment(course_id, identifier) # Retry

    # --- Actions ---

    def list_courses(self, print_output=True):
        courses = self._get("/api/v1/courses", params={"per_page": 100, "include[]": ["term", "teachers"]})
        
        # Cache simple list
        cache_data = []
        for c in courses:
            if 'name' in c:
                cache_data.append({
                    "id": c['id'],
                    "name": c.get('name', 'N/A'),
                    "code": c.get('course_code', 'N/A')
                })
        self.config.save_cache("courses", cache_data)

        if print_output:
            print(f"\nFound {len(cache_data)} courses:")
            print("-" * 100)
            print(f"{'ID':<10} | {'Code':<25} | {'Name'}")
            print("-" * 100)
            for c in cache_data:
                print(f"{c['id']:<10} | {c['code']:<25} | {c['name']}")
            print("-" * 100)

    def list_assignments(self, course_id, print_output=True):
        assignments = self._get(f"/api/v1/courses/{course_id}/assignments", params={"per_page": 100})
        
        # Cache
        cache_data = []
        for a in assignments:
            cache_data.append({
                "id": a['id'],
                "name": a['name'],
                "due_at": a.get('due_at')
            })
        self.config.save_cache(f"assignments_{course_id}", cache_data)

        if print_output:
            print(f"\nFound {len(cache_data)} assignments:")
            print("-" * 100)
            print(f"{'ID':<10} | {'Name':<50} | {'Due Date'}")
            print("-" * 100)
            for a in cache_data:
                print(f"{a['id']:<10} | {a['name']:<50} | {a['due_at']}")
            print("-" * 100)
        return assignments

    def get_submission(self, course_id, assignment_id, user_id):
        return self._get(f"/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}")

    def list_ungraded_submissions(self, course_id, assignment_id):
        print(f"Fetching ungraded submissions for assignment {assignment_id}...")
        submissions = self._get(f"/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions", 
                              params={"per_page": 100, "include[]": ["user", "submission_history"]})
        
        ungraded = []
        for sub in submissions:
            if sub.get('workflow_state') == 'submitted':
                ungraded.append(sub)
        return ungraded

    def get_assignment_details(self, course_id, assignment_id):
        return self._get(f"/api/v1/courses/{course_id}/assignments/{assignment_id}")

    def download_file(self, url, filename):
        if url.startswith("/"):
            url = f"{self.base_url}{url}"
        with self.session.get(url, stream=True) as r:
            r.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return filename

    # --- Grading Helper ---
    def analyze_submission(self, submission, assignment):
        """
        Analyzes a submission for late penalty, format issues (screenshots), and extracts content.
        """
        result = {
            "user_id": submission.get('user_id'),
            "late": False,
            "late_penalty": 0,
            "format_warning": None,
            "content": "",
            "files": []
        }

        # Check Late Policy
        submitted_at = submission.get('submitted_at')
        due_at = assignment.get('due_at')
        
        if submitted_at and due_at:
            s_dt = datetime.strptime(submitted_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            d_dt = datetime.strptime(due_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            
            if s_dt > d_dt:
                result["late"] = True
                result["late_penalty"] = 0.10 # 10%
                print(f"  [!] LATE SUBMISSION: {s_dt} > {d_dt}")

        # Extract Content & Check Format
        if submission.get('body'):
            result["content"] += f"\n[Text Body]:\n{submission['body']}\n"
        
        if submission.get('attachments'):
            image_exts = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.heic']
            has_images = False
            
            for att in submission['attachments']:
                fname = att['display_name']
                furl = att['url']
                ext = os.path.splitext(fname)[1].lower()
                
                result["files"].append({"name": fname, "url": furl})
                
                # Check for images
                if ext in image_exts:
                    has_images = True
                    result["content"] += f"\n[IMAGE FILE DETECTED]: {fname} (Visual Check Required)\n"

                # If PDF and pypdf available, extract text
                elif fname.lower().endswith('.pdf') and PYPDF_AVAILABLE:
                    try:
                        print(f"  Downloading {fname} for analysis...")
                        local_path = f"temp_{fname}"
                        self.download_file(furl, local_path)
                        
                        reader = PdfReader(local_path)
                        text = ""
                        for page in reader.pages:
                            text += page.extract_text() + "\n"
                        
                        result["content"] += f"\n[PDF Content - {fname}]:\n{text}\n"
                        os.remove(local_path)
                    except Exception as e:
                        print(f"  [!] Failed to read PDF {fname}: {e}")
            
            if has_images:
                result["format_warning"] = "⚠️ SCREENSHOTS DETECTED: Student submitted images instead of a document."

        return result

    def grade_submission(self, course_id, assignment_id, user_id, grade, comment=None):
        data = {"submission": {"posted_grade": grade}}
        if comment:
            data["comment"] = {"text_comment": comment}
        return self._put(f"/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}", data)

def main():
    parser = argparse.ArgumentParser(description="Canvas Assistant CLI")
    parser.add_argument("--action", choices=[
        "list-courses", "list-assignments", "set-context", 
        "grade-queue", "grade-submission", "get-assignment"
    ], default="list-courses")
    
    # Context & Auth
    parser.add_argument("--domain", help="Canvas domain (e.g. canvas.bergen.edu)")
    parser.add_argument("--force-login", action="store_true", help="Force new login (ignore cache)")
    parser.add_argument("--browser", default="chrome", help="Browser to use for cookies")
    
    # Identifiers (Names or IDs)
    parser.add_argument("--course", help="Course Name or ID")
    parser.add_argument("--assignment", help="Assignment Name or ID")
    parser.add_argument("--student", help="Student ID")
    
    # Grading
    parser.add_argument("--grade", help="Grade to submit")
    parser.add_argument("--comment", help="Comment to submit")

    args = parser.parse_args()

    client = CanvasClient(domain=args.domain, browser=args.browser, force_login=args.force_login)

    # Resolve Course
    course_id = None
    if args.course:
        course_id = client.resolve_course(args.course)
        # Auto-update context if explicitly set
        if args.action == "set-context":
            client.config.save_context({"course_id": course_id})
            print(f"Context set to Course ID: {course_id}")
            return
    else:
        # Use context if available
        course_id = client.config.get_context("course_id")

    # Actions
    if args.action == "list-courses":
        client.list_courses()

    elif args.action == "list-assignments":
        if not course_id:
            print("Error: No course context. Use --course or set-context.")
            sys.exit(1)
        client.list_assignments(course_id)

    elif args.action == "grade-queue":
        if not course_id:
            print("Error: No course context.")
            sys.exit(1)
        
        assignment_id = client.resolve_assignment(course_id, args.assignment)
        if not assignment_id:
            print("Error: Assignment not specified.")
            sys.exit(1)

        assignment = client.get_assignment_details(course_id, assignment_id)
        print(f"\nProcessing Queue for: {assignment['name']}")
        print(f"Due Date: {assignment.get('due_at')}")
        
        ungraded = client.list_ungraded_submissions(course_id, assignment_id)
        print(f"Found {len(ungraded)} ungraded submissions.\n")

        for sub in ungraded:
            user_id = sub['user_id']
            print(f"--- Student {user_id} ---")
            
            analysis = client.analyze_submission(sub, assignment)
            
            print(f"Late: {analysis['late']} (Penalty: {analysis['late_penalty']*100}%)")
            print(f"Content Preview: {analysis['content'][:200]}...")
            
            # Here we could output a prompt for an LLM
            print("\n[To Grade, run]:")
            print(f"python main.py --action grade-submission --course {course_id} --assignment {assignment_id} --student {user_id} --grade <SCORE> --comment \"<FEEDBACK>\"")
            print("-" * 50)

    elif args.action == "grade-submission":
        if not course_id or not args.assignment or not args.student or not args.grade:
            print("Error: Missing arguments for grading.")
            sys.exit(1)
            
        assignment_id = client.resolve_assignment(course_id, args.assignment)
        client.grade_submission(course_id, assignment_id, args.student, args.grade, args.comment)
        print("Graded successfully.")

if __name__ == "__main__":
    main()