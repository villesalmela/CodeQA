# Code QA
## Status
The app is ready for evaluation and can be tested at https://codeqa.online

[Status history](../../wiki/StatusHistory) is available on wiki.

## Use Case
This application will allow users to save their Python functions in a code library. The functions are searchable and browsable, publicly available for other users.
The application supports users in documentation and quality control of their functions.

## Features
### Registration
- Users can create new accounts using their email as username

### Saving new functions
- Users can save new functions to the library
- Application will do following checks and provide feedback
    - Linting using pylint
    - Type checking using pyright
    - Security checking using bandit
    - Automated documentation using OpenAI API
    - Automated generation of unit tests using OpenAI API
    - Automated execution of unit tests using AWS Lambda
    - Automated keyword classification using OpenAI API

### Browsing and searching the library
- Users can search and view functions saved by other people
- Users can rate functions and sort by average rating
    - Users cannot rate their own functions

### Library management
- Administrators can delete any saved functions
- Users can delete their own saved functions

### User management
- Administrators can:
    - Enable/Disable users
    - Lock/Unlock users (temporary 5 min suspension)
    - Promote/Demote users
    - Revoke user's active sessions
    - Delete users

## Database Schema
Database schema is [detailed in wiki](../../wiki/Schema). However here is a short summary.

### Users
Each row represents one user.  
Contains username, hashed password, and various status flags.

### Auth_events
Each row represents one authentication event.  
Contains reference to user, event type and action result, along with other details.

### Account_events
Each row represents one account event.  
Contains reference to user, event type and action result, along with other details. 

### Functions
Each row represents one function in the library.  
Contains reference to user, function data and metadata.

### Sessions
Each row represents one session.  
Contains reference to user, session id, creation time and session serialized session data.

### Ratings
Each row represents one rating.
Contains references to both user and function, and of course the rating.

## Security Considerations
During the application design process, most relevant common weaknesses were identified. They, and related mitigations are [listed on wiki](../../wiki/Security)

## Testing
Application is packaged into docker container using Github Action, and uploaded to AWS ECR by the pipeline.
AWS AppRunner is serving the app, which is available at https://codeqa.online

To create an account, you need to use your university email address.
A verification code is sent to your email, and it's required during first login.

Test accounts are available:

Normal user:
- username: testuser@villesalmela.fi
- password: password

Administrator:
- username: testadmin@villesalmela.fi
- password: password

Please don't delete or disable the last admin account, since recovering from that needs direct access to the production database.

Here's a test function you could try:
```python
def celsius_to_fahrenheit(celsius):
    fahrenheit = (9/5) * celsius + 32
    return fahrenheit
```

And a flawed function to test all static checkers:
```python
def factorial(n: int) -> int:
    if not isinstance(n, int):
        raise TypeError("Input must be an integer.")
    if n < 0:
        raise ValueError("Input must be a non-negative integer.")
    if n == 0:
        return "1"
    else:
        exec("print('test')")
        return n * factorial(n-1)
```

Feel free to try the process with these ones, or come up with something else.

### Local Testing
Local testing is not quite viable for this app, as it relies heavily on public cloud services, that you need to configure separately. If you really want to, [wiki has instructions](../../wiki/LocalTesting)
