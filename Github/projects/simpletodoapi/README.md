# SimpleTodoAPI

## Project Introduction
SimpleTodoAPI is a small production-ready Python FastAPI Todo REST API built from zero. It uses SQLite and SQLAlchemy for the database and implements Todo CRUD operations, validation, error handling, automated tests, and more.

## Features
- User registration and authentication
- Todo CRUD operations
- Validation and error handling
- Automated tests

## Installation
1. Clone the repository:
   bash
   git clone https://github.com/yourusername/simpletodoapi.git

2. Navigate to the project directory:
   bash
   cd simpletodoapi

3. Install dependencies:
   bash
   pip install -r requirements.txt

## Configuration
Create a `.env` file in the root directory with the following content:
env
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:///site.db

## Usage
1. Run the application:
   bash
   uvicorn main:app --reload

2. Access the API at `http://127.0.0.1:8000`

## Examples
### Create a Todo
bash
curl -X POST "http://127.0.0.1:8000/todos" -H "Content-Type: application/json" -d '{"user_id": 1, "data": "testdata"}'

### Get a Todo
bash
curl -X GET "http://127.0.0.1:8000/todos/1"

### Update a Todo
bash
curl -X PUT "http://127.0.0.1:8000/todos/1" -H "Content-Type: application/json" -d '{"user_id": 1, "data": "updateddata"}'

### Delete a Todo
bash
curl -X DELETE "http://127.0.0.1:8000/todos/1"