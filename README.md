# RoomLoop Assignment

## Setup and Run

### 1. Clone the repository

```bash
git clone https://github.com/ianuj4231/ianuj4231_roomloop_assignment.git
cd ianuj4231_roomloop_assignment
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

**And for macOS / Linux:**

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

Have also included a simulate_concurrency.py file that spawn  2 threads/2 users  hit same create booking or create recurring endpoint at same time. this is when 2 people try to book same time range at same time. below screenshot terminal outputs are a proof of properly handling concurrency scenario (high no of conflicting writes along with trying to book overlapping time-ranges).   

<img width="1920" height="1080" alt="Screenshot (545)" src="https://github.com/user-attachments/assets/f916ac40-b016-4dfe-9fce-31e793bb6314" />


## (optional to visualize tables and data) sqlite:

Database Inspection

The project uses SQLite, and the database file is included as:

the file   `roomloop.db` currently contains a room. 

[

{
1	Aurora	8	Europe/Berlin
}

]


can be visualized using : A SQLite GUI such as DB Browser for SQLite can optionally be used to inspect the database tables and test data. link - https://sqlitebrowser.org/dl/ 




<img width="1334" height="675" alt="image" src="https://github.com/user-attachments/assets/5d88be44-ab1f-41d6-a02f-59909e16c0b3" />




