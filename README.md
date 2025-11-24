# FastAPI-for-fun

# The Knowledge Agora

**The Knowledge Agora** is a collaborative micro-blogging platform where users can share thoughts, ideas, and knowledge on any topic. Built with **FastAPI** and **SQLite**, it focuses on simplicity, performance, and clean architecture.

## 🚀 Features

*   **Create & Share**: Write notes anonymously or with a nickname.
*   **Discover**: Browse notes, filter by topic or author, and search content.
*   **Engage**: Upvote the most interesting notes.
*   **Curate**: Pin important notes to highlight them.
*   **Manage**: Securely delete notes (Admin only).
*   **Documentation**: Interactive API documentation via Swagger UI.

## 🛠️ Tech Stack

*   **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
*   **Database**: [SQLite](https://www.sqlite.org/index.html) (Native implementation, no ORM)
*   **Validation**: [Pydantic](https://docs.pydantic.dev/)
*   **Server**: [Uvicorn](https://www.uvicorn.org/)
*   **Testing**: [Pytest](https://docs.pytest.org/)

## 📦 Installation

1.  **Clone the repository** (or download the source code).

2.  **Install dependencies**:
    ```bash
    pip install fastapi uvicorn pydantic pytest httpx
    ```

3.  **Initialize the database**:
    Populate the database with sample data to get started quickly.
    ```bash
    python data_sample/init_data.py
    ```

## 🏃‍♂️ Running the Application

### Option 1: Local Development
Start the development server:
```bash
uvicorn app.main:app --reload
```

### Option 2: Using Docker 🐳

1.  **Build the image**:
    ```bash
    docker build -t knowledge-agora .
    ```

2.  **Run the container**:
    ```bash
    docker run -d -p 8000:8000 --name agora-app knowledge-agora
    ```

The API will be available at **http://127.0.0.1:8000**.

## 📖 API Documentation

Once the server is running, visit **http://127.0.0.1:8000/docs** to access the interactive Swagger UI. You can test all endpoints directly from your browser.

### Key Endpoints

*   `GET /notes`: List all notes (supports filtering).
*   `POST /notes`: Create a new note.
*   `GET /notes/top`: View top-voted notes.
*   `POST /notes/{id}/vote`: Upvote a note.
*   `POST /notes/{id}/pin`: Pin a note.
*   `DELETE /notes/{id}`: Delete a note (**Requires API Key**).

## 🔐 Authentication

The `DELETE` endpoint is protected by an API Key.
*   **Header Name**: `X-API-Key`
*   **Default Key**: `admin-secret`

## 🧪 Running Tests

This project follows **Test-Driven Development (TDD)** principles. To run the test suite:

```bash
python -m pytest
```

## 📂 Project Structure

For a detailed explanation of the architecture and database schema, please refer to [ARCHITECTURE.md](ARCHITECTURE.md).

```
.
├── app/
│   ├── core/               # Config, DB, Security
│   ├── models/             # Pydantic models
│   ├── routers/            # API endpoints
│   └── main.py             # App entry point
├── tests/                  # Test suite
└── data_sample/            # Sample data script
```

## 📄 License

This project is licensed under the MIT License.
