# User Management API

This is a serverless functions project provides a user management API using AWS Lambda and DynamoDB. The API includes endpoints for creating, retrieving, updating, and deleting users. The project is set up using the Serverless Framework.


### Installation

1. Clone the repository:

   ```
   git clone https://github.com/Yash114Bansal/Serverless-UserAPI
   cd user-management-api
   ```

2. Install dependencies:

   ```
   npm install
   ```

3. Deploy the service:

   ```
   serverless deploy
   ```

### Environment Variables

Ensure the following environment variables are set:

- `USERS_TABLE`: DynamoDB table name for users.
- `MANAGERS_TABLE`: DynamoDB table name for managers.

These are configured in the `serverless.yml` file.

## API Endpoints

### 1. Create User

**Endpoint:** `/create_user`  
**Method:** `POST`
**Hosted URL:** `https://z1leghcpid.execute-api.us-east-1.amazonaws.com/dev/create_user`

**Request Body:**

```json
{
  "full_name": "John Doe",
  "mob_num": "+911234567890",
  "pan_num": "AABCP1234C",
  "manager_id": "manager-id" // Optional
}
```

**Response:**

- Success: `201 Created`

  ```json
  {
    "message": "User created successfully"
  }
  ```

- Error: `400 Bad Request`

  ```json
  {
    "error": "<Error Message>"
  }
  ```

### 2. Get Users

**Endpoint:** `/get_users`  
**Method:** `POST`
**Hosted URL:** `https://z1leghcpid.execute-api.us-east-1.amazonaws.com/dev/get_users`
**Request Body (Optional):**

```json
{
  "user_id": "user-uuid",
  "mob_num": "1234567890",
  "manager_id": "manager-id"
}
```

**Response:**

- Success: `200 OK`

  ```json
  [
    {
      "user_id": "user-uuid",
      "manager_id": "manager-id",
      "full_name": "John Doe",
      "mob_num": "1234567890",
      "pan_num": "AABCP1234C",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "is_active": true
    }
  ]
  ```

### 3. Delete User

**Endpoint:** `/delete_user`  
**Method:** `POST`
**Hosted URL:** `https://z1leghcpid.execute-api.us-east-1.amazonaws.com/dev/delete_user`

**Request Body:**

```json
{
  "user_id": "user-uuid"
}
```

or

```json
{
  "mob_num": "1234567890"
}
```

**Response:**

- Success: `200 OK`

  ```json
  {
    "message": "User Deleted Successfully"
  }
  ```

- Error: `404 Not Found`

  ```json
  {
    "error": "No User Exist With Given user_id/phone"
  }
  ```

### 4. Update User

**Endpoint:** `/update_user`  
**Method:** `POST`
**Hosted URL:**  `https://z1leghcpid.execute-api.us-east-1.amazonaws.com/dev/update_user`

**Request Body:**

```json
{
  "user_ids": ["user-uuid"],
  "update_data": {
    "full_name": "Jane Doe",
    "mob_num": "0987654321",
    "pan_num": "BBDCP1234C"
  }
}
```

or

```json
{
  "user_ids": ["user-uuid1", "user-uuid2"],
  "update_data": {
    "manager_id" : "2"
  }
}
```

**Response:**

- Success: `200 OK`

  ```json
  {
    "message": "Users updated successfully"
  }
  ```

- Error: `400 Bad Request`

  ```json
  {
    "error": "Invalid manager_id"
  }
  ```

  or

  ```json
  {
      "errors": [
          "<Error Message 1>",
          "<Error Message 2>"
      ]
  }
  ```

## Database Schema

### Users Table

- `user_id`: String (Primary Key)
- `full_name`: String
- `mob_num`: String
- `pan_num`: String
- `manager_id`: String
- `created_at`: String
- `updated_at`: String
- `is_active`: Boolean

### Managers Table

- `manager_id`: String (Primary Key)
- `name`: String (Manager's name)
- `department`: String (Manager's Department)

### Test Data for Managers Table

```json
[
  {
    "manager_id": "1",
    "name": "Alice",
    "department" : "HR"
  },
  {
    "manager_id": "2",
    "name": "Bob",
    "department" : "CS"
  }
]
```
