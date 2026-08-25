# RoomLoop Assignment

## Setup and Run

### 1. Clone the repository

```bash
git clone https://github.com/ianuj4231/roomloop_assignment.git
cd roomloop_assignment
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

**Windows PowerShell:**

```powershell
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Start the FastAPI server

```bash
uvicorn app:app --reload
```

The API will run at:

```text
http://127.0.0.1:8000
```

### 6. Open the API documentation

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

The Swagger UI provides the available API endpoints and allows them to be executed directly.

## API Testing

A Postman collection containing the API endpoints, example request inputs, and tested examples is included in the repository:

```text
api_endpoint_tests_with_examples.postman_collection.json
```

Import this file into Postman after starting the FastAPI server to run the API requests locally.
