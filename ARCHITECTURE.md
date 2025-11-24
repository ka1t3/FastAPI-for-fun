# The Knowledge Agora - Architecture & Design Documentation

## 1. Project Overview
"The Knowledge Agora" is a collaborative micro-blogging platform built with **FastAPI**. It allows users to create, read, update, and delete notes, as well as vote on them and pin important ones. The project emphasizes simplicity, performance, and clean code practices.

## 2. Database Schema
The application uses **SQLite** as its relational database management system. It consists of a single table named `notes`.

### Table: `notes`

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Unique identifier for each note. |
| `topic` | `TEXT` | `NOT NULL` | The subject or title of the note. |
| `content` | `TEXT` | `NOT NULL` | The main body text of the note. |
| `author` | `TEXT` | `DEFAULT 'Anonymous'` | The nickname of the creator. |
| `created_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | Timestamp of creation (UTC). |
| `votes` | `INTEGER` | `DEFAULT 0` | Counter for upvotes. |
| `pinned` | `BOOLEAN` | `DEFAULT 0` | Flag to mark important notes (0=False, 1=True). |

## 3. System Architecture
The project follows a **Modular Monolithic** architecture, structured to separate concerns while keeping the codebase simple and navigable.

### Directory Structure
```
.
├── app/
│   ├── core/               # Core functionality (Config, DB, Security)
│   │   ├── database.py     # Database connection & initialization
│   │   ├── security.py     # Authentication logic
│   │   └── limiter.py      # Rate limiting configuration
│   ├── models/             # Pydantic data models
│   │   └── models.py       # Schema definitions
│   ├── routers/            # API endpoints
│   │   └── notes.py        # Business logic for notes
│   └── main.py             # Application entry point
├── tests/                  # Test suite (TDD)
│   ├── conftest.py         # Test fixtures & setup
│   ├── test_notes.py       # CRUD & Voting tests
│   ├── test_auth.py        # Authentication tests
│   └── test_pin_note.py    # Pinning feature tests
└── data_sample/
    └── init_data.py        # Script to populate sample data
```

### Key Components

#### A. Entry Point (`app/main.py`)
*   **Role:** Initializes the FastAPI application, configures middleware (CORS, TrustedHost), sets up rate limiting, and includes routers.
*   **Design Choice:** Centralizes configuration and bootstrapping.

#### B. Core Module (`app/core/`)
*   **Database (`database.py`):** Manages the raw SQLite connection using native `sqlite3`.
*   **Security (`security.py`):** Handles API Key validation using environment variables.
*   **Limiter (`limiter.py`):** Configures the `slowapi` rate limiter.

#### C. Data Validation (`app/models/`)
*   **Role:** Defines Pydantic models with strict typing and validation (e.g., `max_length`).
*   **Design Choice:** Ensures data integrity and prevents DoS attacks via massive payloads.

#### D. Routing (`app/routers/`)
*   **Role:** Handles HTTP requests and business logic.
*   **Design Choice:** Modular routing allows the application to scale easily.

#### E. Security & Performance
*   **Authentication:** API Key required for sensitive operations (DELETE).
*   **Rate Limiting:** Implemented via `slowapi` to prevent abuse (e.g., 10 requests/minute for creating notes).

## 4. Design Decisions & Philosophy

### 1. Native SQL vs. ORM
We chose **Native SQL** to demonstrate a lightweight, high-performance approach. While ORMs are great for complex relationships, they add abstraction layers. Writing raw SQL for a single table is straightforward, explicit, and efficient.

### 2. Test-Driven Development (TDD)
The project was built using TDD.
*   **Benefit:** Every feature (Pinning, Auth, CRUD) has a corresponding test that verifies its behavior.
*   **Reliability:** Refactoring (like translating French to English) was done with confidence because the test suite immediately highlighted any regressions.
*   **Isolation:** Tests use an **in-memory SQLite database**, ensuring they run instantly and never corrupt the actual data.

### 3. Dependency Injection
FastAPI's dependency injection system is used extensively (for DB connections and Auth).
*   **Benefit:** It makes components loosely coupled and easily testable. For example, we can easily swap the real database for a mock or in-memory one during testing without changing the business logic code.

## 5. Key Concepts & Code Examples (For Beginners)

This section explains the core concepts used in this project with real examples from our codebase.

### A. Dependency Injection (`Depends`)
**Concept:** Instead of creating resources (like database connections) inside every function, we "inject" them. This makes code cleaner and easier to test.

**Example (`app/routers/notes.py`):**
```python
# We ask FastAPI to "inject" the database connection (conn)
def create_note(note: NoteCreate, conn=Depends(get_db)):
    cursor = conn.cursor()
    # ... use cursor ...
```
*   **Why?** We don't need to write `conn = sqlite3.connect(...)` in every single function. FastAPI handles opening and closing it for us.

### B. Pydantic Models (Data Validation)
**Concept:** We define "shapes" for our data. If the data doesn't fit the shape, the app rejects it automatically.

**Example (`app/models/models.py`):**
```python
class NoteCreate(BaseModel):
    # "topic" MUST be a string, and MUST be between 1 and 100 characters
    topic: str = Field(..., min_length=1, max_length=100)
```
*   **Why?** If a user tries to send a 10,000-character topic, Pydantic stops them instantly. We don't need to write `if len(topic) > 100:` checks manually.

### C. Middleware
**Concept:** Code that runs *before* every request and *after* every response. It's like a security guard checking everyone who enters the building.

**Example (`app/main.py`):**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Only allow this website to talk to us
    # ...
)
```
*   **Why?** It protects the entire application globally. We don't need to add security checks to every single router function.

### D. Rate Limiting (Decorators)
**Concept:** We use a "decorator" (the `@` symbol) to wrap our functions with extra logic, like counting how many times a user has called it.

**Example (`app/routers/notes.py`):**
```python
@limiter.limit("10/minute") # <--- The Decorator
def create_note(...):
    # ...
```
*   **Why?** It prevents spam. If a user calls this function 11 times in a minute, the 11th call is blocked before it even runs the code.

### E. Test-Driven Development (TDD)
**Concept:** We write the test *before* or *alongside* the code. If the test passes, we know the code works.

**Example (`tests/test_auth.py`):**
```python
def test_delete_note_no_auth(client):
    # 1. Try to delete without a key
    response = client.delete(f"/notes/{note_id}")
    # 2. Expect a 403 Forbidden error
    assert response.status_code == 403
```
*   **Why?** It gives us confidence. When we change code later, we run the tests. If they still pass, we didn't break anything!