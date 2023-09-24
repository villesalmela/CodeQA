# Quality Code Lib
## Objective
This application will allow users to save their Python functions in a code library. The functions are searchable and browsable, publicly available for other users.
The application supports users in documentation and quality control of their functions.

## Features
### Registration
- Users can create new accounts using their email as username

### Saving new functions
- Users can save new functions to the library
- Application will do following checks and provide feedback
    - Linting using pylint
    - Type checking using mypy
    - Security checking using bandit
    - (Optional) Automated documentation using OpenAI API
    - (Optional) Automated generation of unit tests using OpenAI API
    - (Optional) Automated execution of unit tests using AWS Lambda
    - (Optional) Automated keyword classification using OpenAI API
- Users are given possibility to refine their code before saving, based on feedback
- Users can classify their functions using keywords

### Browsing and searching the library
- Users can search and view functions saved by other people
- Users can rate functions and sort by rating

### Library management
- Administrators can manage users and saved functions
- Users can remove their own saved functions

## Status
### Operational functionalities
- Users can create new accounts using their email as username
- Users can save new functions to the library
    - Linting with pylint
    - Automated documentation using OpenAI API
    - Automated generation of unit tests using OpenAI API
    - Automated execution of unit tests using AWS Lambda
    - Automated keyword classification using OpenAI API
- Users can browse (not search) functions saved by other people

### TODO
- Type checking using mypy
- Security checking using bandit
- Search and rating functionality
- User and library management functionality
- Improve user interface and visuals

## Testing
Application is packaged into docker container using Github Action, and uploaded to AWS ECR by the pipeline.
AWS AppRunner is serving the app, which is available at https://codeqa.online

To create an account, you need to use your university email address.

Test account is available:
- username: testuser@villesalmela.fi
- password: password