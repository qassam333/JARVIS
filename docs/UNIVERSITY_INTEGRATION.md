# University Integration Documentation

> **Purpose**: Automatically fetch assignments from university LMS (Moodle) and import as JARVIS tasks.

---

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│              UNIVERSITY SCRAPER SYSTEM                       │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              JARVIS Core                            │   │
│  │   • Decision Engine                                 │   │
│  │   • Task Management                                 │   │
│  │   • User Interface                                  │   │
│  └─────────────────────────┬───────────────────────────┘   │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           University Skills                          │   │
│  │   ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │   │
│  │   │   Sync      │  │  Converter  │  │  Credential│  │   │
│  │   │  Manager    │  │             │  │  Manager   │  │   │
│  │   └─────────────┘  └─────────────┘  └────────────┘  │   │
│  └─────────────────────────┬───────────────────────────┘   │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Scraper Adapters                           │   │
│  │   ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │   │
│  │   │   Base      │  │  Moodle     │  │  (Future)  │  │   │
│  │   │  Interface  │  │  Adapter    │  │  Adapters  │  │   │
│  │   └─────────────┘  └─────────────┘  └────────────┘  │   │
│  └─────────────────────────┬───────────────────────────┘   │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 External LMS                         │   │
│  │   ┌─────────────┐  ┌─────────────┐                   │   │
│  │   │   Moodle   │  │  (Canvas)  │  (Blackboard)     │   │
│  │   │  Instance  │  │             │                   │   │
│  │   └─────────────┘  └─────────────┘                   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
jarvis/skills/university/
├── __init__.py       # Module exports
├── base.py           # Abstract scraper interface
├── moodle.py         # Moodle-specific implementation
├── models.py         # Course, Assignment models
├── sync.py           # Sync orchestrator
├── converter.py      # Convert LMS data → JARVIS tasks
└── credentials.py     # Credential management (encrypted)
```

---

## Architecture: Strategy Pattern

### Why Strategy Pattern?

```python
# The ABSTRACT interface that ALL scrapers must implement
class UniversityScraper(ABC):
    """Interface for university LMS scrapers"""
    
    @abstractmethod
    def authenticate(self, credentials: Credentials) -> Session:
        """Login and return authenticated session"""
        pass
    
    @abstractmethod
    def get_courses(self, session: Session) -> List[Course]:
        """Fetch enrolled courses"""
        pass
    
    @abstractmethod
    def get_assignments(self, session: Session, course: Course) -> List[Assignment]:
        """Fetch assignments for a specific course"""
        pass
    
    @abstractmethod
    def get_quizzes(self, session: Session, course: Course) -> List[Assignment]:
        """Fetch quizzes for a specific course"""
        pass
    
    @abstractmethod
    def get_events(self, session: Session) -> List[Assignment]:
        """Fetch calendar events (lectures, etc.)"""
        pass
    
    @abstractmethod
    def logout(self, session: Session):
        """Securely terminate session"""
        pass
```

### Benefits

| Benefit | Explanation |
|---------|-------------|
| **Testability** | Mock adapter for testing without real LMS |
| **Extensibility** | Add Canvas/Blackboard by implementing interface |
| **Maintainability** | Changes to one adapter don't affect others |
| **Separation** | Core logic separated from LMS-specific code |

---

## Data Models

### LMS Models

```python
@dataclass
class Course:
    """University course from LMS"""
    lms_id: str              # LMS's internal ID
    name: str                # e.g., "Introduction to Computer Science"
    code: str | None         # e.g., "CS101"
    semester: str | None      # e.g., "Fall 2024"
    instructor: str | None
    url: str | None          # Link to course page

@dataclass
class Assignment:
    """Assignment, quiz, or event from LMS"""
    lms_id: str              # LMS's internal ID
    course_id: str           # Reference to Course
    title: str               # e.g., "Quiz 1: Variables"
    type: AssignmentType     # assignment, quiz, exam, lecture
    description: str | None
    due_date: datetime | None
    url: str | None          # Link to assignment page
    status: str = "pending"  # pending, submitted, graded
    raw_data: dict = field(default_factory=dict)  # Original data
```

### Assignment Types

```python
from enum import Enum

class AssignmentType(Enum):
    ASSIGNMENT = "assignment"  # Regular homework
    QUIZ = "quiz"            # Timed quiz
    EXAM = "exam"             # Exam/test
    LECTURE = "lecture"       # Scheduled lecture/event
    PROJECT = "project"        # Long-term project
    READING = "reading"       # Reading assignment
```

---

## Credential Management

### Purpose

Securely store and retrieve university login credentials.

### Credential Storage

```python
@dataclass
class StoredCredentials:
    """Credentials stored in JARVIS database"""
    id: str
    service: str              # "moodle", "canvas", etc.
    username: str | None
    encrypted_password: bytes  # Fernet encrypted
    base_url: str              # LMS URL
    created_at: datetime
    last_sync: datetime | None
```

### Secure Workflow

```
┌─────────────────────────────────────────────────────────────┐
│              CREDENTIAL SECURITY FLOW                        │
│                                                              │
│  1. First Setup:                                            │
│     User: "jarvis university setup --moodle https://lms..." │
│     │                                                      │
│     ▼                                                      │
│     Prompt for username/password                            │
│     │                                                      │
│     ▼                                                      │
│     Encrypt password with Fernet                            │
│     │                                                      │
│     ▼                                                      │
│     Store encrypted blob + username + URL in SQLite         │
│                                                              │
│  2. Each Sync:                                              │
│     Read encrypted blob from DB                             │
│     │                                                      │
│     ▼                                                      │
│     Decrypt with master key                                │
│     │                                                      │
│     ▼                                                      │
│     Login to LMS                                           │
│     │                                                      │
│     ▼                                                      │
│     Perform sync                                            │
│     │                                                      │
│     ▼                                                      │
│     Logout (invalidate session)                            │
│     │                                                      │
│     ▼                                                      │
│     Password never stored in plaintext                     │
└─────────────────────────────────────────────────────────────┘
```

### Credential Manager

```python
class CredentialManager:
    """Manage encrypted university credentials"""
    
    def __init__(self, encryption: Encryption, db: Database):
        self.encryption = encryption
        self.db = db
    
    def save_credentials(self, service: str, url: str, 
                        username: str, password: str) -> str:
        """Save new credentials (encrypted)"""
        encrypted_password = self.encryption.encrypt(password)
        
        with self.db.get_session() as session:
            creds = StoredCredentials(
                id=str(uuid.uuid4()),
                service=service,
                username=username,
                encrypted_password=encrypted_password,
                base_url=url
            )
            session.add(creds)
            session.commit()
            return creds.id
    
    def get_credentials(self, service: str) -> tuple[str, str]:
        """Get decrypted username and password"""
        with self.db.get_session() as session:
            creds = session.query(StoredCredentials).filter(
                StoredCredentials.service == service
            ).first()
            
            if not creds:
                raise CredentialsNotFound(f"No credentials for {service}")
            
            password = self.encryption.decrypt(creds.encrypted_password)
            return creds.username, password
```

---

## Moodle Scraper Implementation

### Overview

The Moodle adapter implements the `UniversityScraper` interface for Moodle instances.

### Key Features

| Feature | Implementation |
|---------|----------------|
| **Rate Limiting** | 1 request per 2 seconds |
| **Session Management** | Token-based authentication |
| **Error Handling** | Graceful failures, retry logic |
| **Data Extraction** | BeautifulSoup4 for HTML parsing |
| **API Fallback** | Try Moodle Web Services if available |

### Authentication

```python
class MoodleScraper(UniversityScraper):
    
    def authenticate(self, credentials: StoredCredentials) -> MoodleSession:
        """Login to Moodle and return session"""
        
        # Try Web Services API first (preferred)
        if self._supports_web_services(credentials.base_url):
            return self._authenticate_api(credentials)
        
        # Fallback to web scraping
        return self._authenticate_web(credentials)
    
    def _authenticate_api(self, credentials: StoredCredentials) -> MoodleSession:
        """Moodle Web Services API authentication"""
        username, password = self._decrypt_credentials(credentials)
        
        response = httpx.post(
            f"{credentials.base_url}/login/token.php",
            params={
                "service": "moodle_mobile_app",  # or custom service
                "username": username,
                "password": password
            }
        )
        
        data = response.json()
        if "token" in data:
            return MoodleSession(
                token=data["token"],
                base_url=credentials.base_url
            )
        
        raise AuthenticationError("Failed to get API token")
```

### Fetching Courses

```python
def get_courses(self, session: MoodleSession) -> List[Course]:
    """Fetch enrolled courses from Moodle"""
    
    response = httpx.get(
        f"{session.base_url}/webservice/rest/server.php",
        params={
            "wstoken": session.token,
            "moodlewsrestformat": "json",
            "wsfunction": "core_enrol_get_users_courses",
            "userid": "self"  # Current user
        }
    )
    
    courses = []
    for item in response.json():
        courses.append(Course(
            lms_id=str(item["id"]),
            name=item["fullname"],
            code=item.get("shortname"),
            url=f"{session.base_url}/course/view.php?id={item['id']}"
        ))
    
    return courses
```

### Fetching Assignments

```python
def get_assignments(self, session: MoodleSession, course: Course) -> List[Assignment]:
    """Fetch assignments for a course"""
    
    response = httpx.get(
        f"{session.base_url}/webservice/rest/server.php",
        params={
            "wstoken": session.token,
            "moodlewsrestformat": "json",
            "wsfunction": "mod_assign_get_assignments",
            "courseids[0]": course.lms_id
        }
    )
    
    assignments = []
    data = response.json()
    
    for course_data in data.get("courses", []):
        for assign in course_data.get("assignments", []):
            assignments.append(Assignment(
                lms_id=str(assign["id"]),
                course_id=course.lms_id,
                title=assign["name"],
                type=AssignmentType.ASSIGNMENT,
                description=assign.get("intro"),
                due_date=self._parse_timestamp(assign.get("duedate")),
                url=f"{session.base_url}/mod/assign/view.php?id={assign['cmid']}",
                raw_data=assign
            ))
    
    return assignments
```

### Rate Limiting

```python
import time
from functools import wraps

def rate_limit(seconds: float = 2.0):
    """Decorator to enforce rate limiting"""
    last_call = {}
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Use function name as key
            key = func.__name__
            now = time.time()
            
            if key in last_call:
                elapsed = now - last_call[key]
                if elapsed < seconds:
                    time.sleep(seconds - elapsed)
            
            last_call[key] = time.time()
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

class MoodleScraper:
    
    @rate_limit(2.0)
    def _make_request(self, url: str, **kwargs):
        """Make rate-limited request"""
        return httpx.get(url, **kwargs)
```

---

## Sync Orchestrator

### Purpose

Coordinates the entire sync process:
1. Authenticate
2. Fetch data
3. Deduplicate
4. Convert to tasks
5. Store in database
6. Notify user
7. Clean up

### Sync Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    SYNC WORKFLOW                             │
│                                                              │
│  1. START SYNC                                               │
│     │                                                       │
│     ▼                                                       │
│  2. Get credentials (decrypt)                               │
│     │                                                       │
│     ▼                                                       │
│  3. Login to LMS                                            │
│     │                                                       │
│     ▼                                                       │
│  4. Fetch courses                                            │
│     │                                                       │
│     ▼                                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  FOR EACH COURSE:                                    │   │
│  │    • Rate limit (2 sec)                             │   │
│  │    • Fetch assignments                              │   │
│  │    • Fetch quizzes                                  │   │
│  │    • Store in temp list                             │   │
│  └─────────────────────────────────────────────────────┘   │
│     │                                                       │
│     ▼                                                       │
│  5. Logout (secure)                                         │
│     │                                                       │
│     ▼                                                       │
│  6. Deduplicate (by LMS ID)                                 │
│     │                                                       │
│     ▼                                                       │
│  7. Convert to JARVIS tasks                                 │
│     │                                                       │
│     ▼                                                       │
│  8. Store in database (update existing)                      │
│     │                                                       │
│     ▼                                                       │
│  9. Log sync result                                          │
│     │                                                       │
│     ▼                                                       │
│  10. NOTIFY USER                                            │
│                                                              │
│  11. END                                                     │
└─────────────────────────────────────────────────────────────┘
```

### Sync Manager Implementation

```python
class SyncManager:
    """Orchestrates university data sync"""
    
    def __init__(self, scraper: UniversityScraper, 
                 credential_manager: CredentialManager,
                 converter: AssignmentConverter,
                 db: Database):
        self.scraper = scraper
        self.credential_manager = credential_manager
        self.converter = converter
        self.db = db
    
    def sync(self, service: str = "moodle") -> SyncResult:
        """Execute full sync"""
        result = SyncResult()
        
        try:
            # 1. Get credentials
            creds = self.credential_manager.get(service)
            session = self.scraper.authenticate(creds)
            result.authenticated = True
            
            # 2. Fetch courses
            courses = self.scraper.get_courses(session)
            result.courses_fetched = len(courses)
            self._store_courses(courses)
            
            # 3. Fetch all assignments
            all_assignments = []
            for course in courses:
                assignments = self.scraper.get_assignments(session, course)
                quizzes = self.scraper.get_quizzes(session, course)
                events = self.scraper.get_events(session)
                
                all_assignments.extend(assignments + quizzes + events)
                result.items_fetched += len(all_assignments)
            
            # 4. Logout
            self.scraper.logout(session)
            
            # 5. Deduplicate
            new_assignments = self._deduplicate(all_assignments)
            result.new_items = len(new_assignments)
            
            # 6. Convert and store
            tasks_created = self._import_assignments(new_assignments)
            result.tasks_created = len(tasks_created)
            
            result.success = True
            
        except Exception as e:
            result.success = False
            result.error = str(e)
        
        return result
```

### Deduplication Logic

```python
def _deduplicate(self, new_assignments: List[Assignment]) -> List[Assignment]:
    """Remove assignments already in database"""
    
    with self.db.get_session() as session:
        existing_ids = {
            ua.lms_id for ua in 
            session.query(UniversityAssignment).all()
        }
    
    return [
        a for a in new_assignments 
        if a.lms_id not in existing_ids
    ]
```

---

## Converter: LMS → JARVIS

### Purpose

Transform LMS assignments into JARVIS tasks.

### Conversion Rules

| LMS Type | JARVIS Priority | JARVIS Energy | Notes |
|----------|-----------------|---------------|-------|
| exam | 5 (highest) | 8 | Requires high focus |
| quiz | 4 | 6 | Timed, moderate energy |
| assignment | 3 | 5 | Standard |
| project | 3 | 5 | May have soft deadline |
| lecture | 2 | 3 | Low energy |
| reading | 1 | 2 | Can do when low energy |

### Converter Implementation

```python
class AssignmentConverter:
    """Convert LMS assignments to JARVIS tasks"""
    
    def convert(self, assignment: Assignment) -> Task:
        """Convert single assignment to task"""
        
        return Task(
            id=str(uuid.uuid4()),
            title=f"[{assignment.course_name}] {assignment.title}",
            description=assignment.description,
            deadline=assignment.due_date,
            priority=self._map_priority(assignment.type),
            energy_level=self._map_energy(assignment.type),
            status="pending",
            source="moodle"
        )
    
    def _map_priority(self, assignment_type: AssignmentType) -> int:
        """Map LMS type to JARVIS priority (1-5)"""
        mapping = {
            AssignmentType.EXAM: 5,
            AssignmentType.QUIZ: 4,
            AssignmentType.ASSIGNMENT: 3,
            AssignmentType.PROJECT: 3,
            AssignmentType.LECTURE: 2,
            AssignmentType.READING: 1,
        }
        return mapping.get(assignment_type, 3)
    
    def _map_energy(self, assignment_type: AssignmentType) -> int:
        """Map LMS type to required energy (1-10)"""
        mapping = {
            AssignmentType.EXAM: 8,
            AssignmentType.QUIZ: 6,
            AssignmentType.ASSIGNMENT: 5,
            AssignmentType.PROJECT: 5,
            AssignmentType.LECTURE: 3,
            AssignmentType.READING: 2,
        }
        return mapping.get(assignment_type, 5)
```

---

## CLI Commands

```bash
# Setup university connection
jarvis university setup --moodle https://lms.youruni.edu
# Prompts for username/password

# Manual sync
jarvis university sync

# View imported assignments
jarvis university tasks
jarvis university tasks --type quiz
jarvis university tasks --course "Computer Science"

# View courses
jarvis university courses

# Toggle auto-sync
jarvis university auto-sync on
jarvis university auto-sync off

# Check sync status
jarvis university status
```

---

## Scheduled Sync

### Background Task

```python
import sched
import time

class UniversitySyncScheduler:
    """Schedule periodic university syncs"""
    
    def __init__(self, sync_manager: SyncManager):
        self.sync_manager = sync_manager
        self.scheduler = sched.scheduler(time.time, time.sleep)
    
    def start_daily(self, hour: int = 6, minute: int = 0):
        """Schedule daily sync at specified time"""
        
        def run_sync():
            self.sync_manager.sync()
            # Schedule next day
            self.start_daily(hour, minute)
        
        # Calculate next run time
        now = datetime.now()
        next_run = now.replace(hour=hour, minute=minute, second=0)
        if next_run <= now:
            next_run += timedelta(days=1)
        
        self.scheduler.enterabs(
            next_run.timestamp(), 
            1, 
            run_sync
        )
        self.scheduler.run()
```

---

## Error Handling

### Error Types

| Error | Handling |
|-------|----------|
| Authentication failed | Prompt to re-enter credentials |
| Network error | Retry 3 times, then fail gracefully |
| LMS unavailable | Log error, continue with cached data |
| Rate limited | Wait and retry |
| Parse error | Log raw data, skip item |

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def fetch_with_retry(url: str, **kwargs) -> httpx.Response:
    """Fetch with exponential backoff retry"""
    return httpx.get(url, timeout=30, **kwargs)
```

---

## Privacy Considerations

| Concern | Solution |
|---------|----------|
| Credential storage | Fernet encrypted |
| Data minimization | Only fetch deadlines/types, no grades |
| Session security | Tokens expire after 24h |
| Rate limiting | Respect LMS servers |
| No grades | Explicitly excluded |
| Secure logout | Session invalidation |
| Error messages | Don't expose sensitive data |

---

<div align="center">

**Your university data stays private.**

</div>
