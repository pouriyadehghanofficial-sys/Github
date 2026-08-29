# API Documentation

## Endpoints
### User Service
- **POST /users**: Create a new user
- **GET /users/{username}**: Get a user by username
- **PUT /users/{username}**: Update a user
- **DELETE /users/{username}**: Delete a user

### Data Service
- **POST /todos**: Create a new todo
- **GET /todos/{user_id}**: Get todos by user ID
- **PUT /todos/{user_id}**: Update a todo
- **DELETE /todos/{user_id}**: Delete a todo

## Classes
### User
- **Attributes**: id, username, password

### Data
- **Attributes**: id, user_id, content

## Methods
### User Service
- **create_user(user_data)**: Create a new user
- **get_user(username)**: Get a user by username
- **update_user(username, updated_data)**: Update a user
- **delete_user(username)**: Delete a user

### Data Service
- **create_data(data)**: Create a new todo
- **get_data(user_id)**: Get todos by user ID
- **update_data(user_id, updated_data)**: Update a todo
- **delete_data(user_id)**: Delete a todo

## Parameters
- **user_data**: A dictionary containing user information
- **data**: A dictionary containing todo information

## Responses
- **200 OK**: Successful request
- **400 Bad Request**: Invalid request
- **404 Not Found**: Resource not found