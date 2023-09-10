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
    - (Optinal) Automated keyword classification using OpenAI API
- Users are given possibility to refine their code before saving, based on feedback
- Users can classify their functions using keywords

### Browsing and searching the library
- Users can search and view functions saved by other people
- Users can rate functions and sort by rating

### Library management
- Administrators can manage users and saved functions
- Users can remove their own saved functions
