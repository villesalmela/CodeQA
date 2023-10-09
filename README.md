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

## Database Schema
### Users
| name              | type    | default                                 | constraints     | references | description                             |
|-------------------|---------|-----------------------------------------|-----------------|------------|-----------------------------------------|
| user_id           | UUID    | gen_random_uuid()                       | PRIMARY KEY     |            | unique identifier for all users         |
| username          | TEXT    |                                         | UNIQUE NOT NULL |            | username in plain text                  |
| password          | TEXT    |                                         | NOT NULL        |            | hashed password                         |
| verification_code | TEXT    |                                         | NOT NULL        |            | hashed verification code                |
| admin             | BOOLEAN | FALSE                                   |                 |            | flag is true if user is administrator   |
| verified          | BOOLEAN | FALSE                                   |                 |            | flag is true if user has verified email |
| disabled          | BOOLEAN | FALSE                                   |                 |            | flag is true if user is disabled        |
| created           | INT     | EXTRACT(EPOCH  FROM  CURRENT_TIMESTAMP) |                 |            | timestamp of creation, in unix format   |
| locked            | INT     |                                         |                 |            | timestamp of locking, in unix format    |

### Auth_events
| name       | type    | default                               | constraints | references     | description                                                     |
|------------|---------|---------------------------------------|-------------|----------------|-----------------------------------------------------------------|
| event_id   | SERIAL  |                                       | PRIMARY KEY |                | unique id for each event                                        |
| user_id    | UUID    |                                       |             | users(user_id) | user related to this event                                      |
| event_time | INT     | EXTRACT(EPOCH FROM CURRENT_TIMESTAMP) |             |                | timestamp of action, in unix format                             |
| event_type | TEXT    |                                       | NOT NULL    |                | either 'login' or 'verification'                                |
| success    | BOOLEAN |                                       | NOT NULL    |                | flag is true if authentication was successful                   |
| remote_ip  | TEXT    |                                       | NOT NULL    |                | remote IP address from which the authentication originated from |
| reason     | TEXT    |                                       |             |                | description of why action failed                                |

### Account_events
| name       | type    | default                               | constraints | references     | description                                             |
|------------|---------|---------------------------------------|-------------|----------------|---------------------------------------------------------|
| event_id   | SERIAL  |                                       | PRIMARY KEY |                | unique id for each event                                |
| user_id    | UUID    |                                       |             | users(user_id) | user related to this event                              |
| event_time | INT     | EXTRACT(EPOCH FROM CURRENT_TIMESTAMP) |             |                | timestamp of action, in unix format                     |
| event_type | TEXT    |                                       | NOT NULL    |                | always 'create'                                         |
| success    | BOOLEAN |                                       | NOT NULL    |                | flag is true if action was successful                   |
| remote_ip  | TEXT    |                                       | NOT NULL    |                | remote IP address from which the action originated from |
| reason     | TEXT    |                                       |             |                | description of why action failed                        |

### Functions
| name        | type   | default | constraints | references     | description                        |
|-------------|--------|---------|-------------|----------------|------------------------------------|
| function_id | SERIAL |         | PRIMARY KEY |                | unique id for each function        |
| user_id     | UUID   |         | NOT NULL    | users(user_id) | user who created to this function  |
| name        | TEXT   |         | NOT NULL    |                | name of the function               |
| code        | TEXT   |         | NOT NULL    |                | source code of the function        |
| tests       | TEXT   |         | NOT NULL    |                | source code of the unit tests      |
| usecase     | TEXT   |         | NOT NULL    |                | description of function's use case |
| keywords    | TEXT   |         | NOT NULL    |                | comma separated list of keywords   |

### Sessions
| name       | type  | default                               | constraints | references     | description                              |
|------------|-------|---------------------------------------|-------------|----------------|------------------------------------------|
| session_id | UUID  | gen_random_uuid()                     | PRIMARY KEY |                | unique id for each session               |
| user_id    | UUID  |                                       | NOT NULL    | users(user_id) | user who is associated with this session |
| created    | INT   | EXTRACT(EPOCH FROM CURRENT_TIMESTAMP) |             |                | timestamp of creation, in unix format    |
| data       | BYTEA |                                       |             |                | session data, LZMA compressed JSON       |

## Security Considerations
| Weakness                                                                                     | Mitigation                                                                               | Status |
|----------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|--------|
| CWE-613: Insufficient Session Expiration                                                     | Ensure sessions have expiration time                                                     | Done   |
| CWE-613: Insufficient Session Expiration                                                     | Ensure sessions are invalidated on logout                                                | Done   |
| CWE-307: Improper Restriction of Excessive Authentication Attempts                           | Lock out account after certain number of failed authentication attempts                  | Todo   |
| CWE-307: Improper Restriction of Excessive Authentication Attempts                           | Reject remote IP after certain number of failed authentication attempts                  | Todo   |
| CWE-384: Session Fixation                                                                    | Generate a new random session_id on server-side for every new session                    | Done   |
| CWE-79: Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting') | Use Flask’s template rendering, which escapes HTML and Javascript. Quote all attributes. | Todo   |
| CWE-79: Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting') | Setup Content Security Policy (CSP)                                                      | Done   |
| CWE-352: Cross-Site Request Forgery (CSRF)                                                   | Use CSRF-tokens in POST requests.                                                        | Done   |
| CWE-352: Cross-Site Request Forgery (CSRF)                                                   | Do not use GET requests for triggering any changes.                                      | Done   |
| CWE-89: Improper Neutralization of Special Elements used in an SQL Command ('SQL Injection') | Use parameterization to separate data and code.                                          | Done   |
| CWE-798: Use of Hard-coded Credentials                                                       | Read all secrets from environment variables.                                             | Done   |
| CWE-1021: Improper Restriction of Rendered UI Layers or Frames                               | Use X-Frame-Options header to disallow rendering the app in a frame                      | Done   |
| CWE-614: Sensitive Cookie in HTTPS Session Without 'Secure' Attribute                        | Set the secure attribute to cookies                                                      | Done   |
| CWE-757: Selection of Less-Secure Algorithm During Negotiation ('Algorithm Downgrade')       | Set HTTP Strict Transport Security (HSTS) headers                                        | Done   |
| CWE-778: Insufficient Logging                                                                | Identify security critical events and needed details and log them                        | Todo   |
| CWE-308: Use of Single-factor Authentication                                                 | Use multi-factor authentication                                                          | Todo   |
| CWE-759: Use of a One-Way Hash without a Salt                                                | Use salt when hashing passwords                                                          | Done   |
| CWE-760: Use of a One-Way Hash with a Predictable Salt                                       | Use unpredictable salt                                                                   | Done   |
| CWE-602: Client-Side Enforcement of Server-Side Security                                     | Double-check client side validations on server side.                                     | Done   |
| CWE-829: Inclusion of Functionality from Untrusted Control Sphere                            | Run untrusted code in a sandbox environment                                              | Done   |
| CWE-829: Inclusion of Functionality from Untrusted Control Sphere                            | Force capability restrictions on untrusted code                                          | Done   |
| CWE-250: Execution with Unnecessary Privileges                                               | Execute untrusted code with minimum privileges                                           | Done   |
| CWE-400: Uncontrolled Resource Consumption                                                   | Force resource usage limits on untrusted code                                            | Done   |

## Status 1
### Operational functionalities
- Users can create new accounts using their email as username
    - Access to the email is verified with verification code
- Users can save new functions to the library
    - Linting with pylint
    - Automated documentation using OpenAI API
    - Automated generation of unit tests using OpenAI API
    - Automated execution of unit tests using AWS Lambda
    - Automated keyword classification using OpenAI API
- Users can browse functions saved by other people

## Status 2
### New operational functionalities (since status 1)
- Admins can:
    - list all users
    - disable and enable users
    - suspend and unsuspend users
    - revoke user's all sessions
    - promote users to admin
    - demote admins to user
    - delete users (along with all their data)
- Users can delete their own functions from the library
- Admins can delete any functions from the library
- Added navigation bar
- Added indicator that displays currently logged in user

### New back-end features (since status 1)
- Changed to using server-side session
    - Logout now permanently invalidates session
    - Server can invalidate sessions without client cooperation
    - Client can no longer read its session data, just a session ID
- Increased security by controlling headers with Flask-Talisman
    - Content Security Policy (CSP)
    - HTTP Strict Transport Security (HSTS)
    - Refuse to send cookies over HTTP
    - Deny Javascript access to cookies
    - Disallow rendering page in a frame
    - Disable MIME type sniffing
    - Disallow sending cookie on cross-site requests (SameSite=Strict)
- Configured and instructed usage of Development Containers extension for VSCode

### New documentation (since status 1)
- Started listing security considerations on README
- Added description of database schema on README

### TODO
- Add more static checkers (mypy, bandit)
- Implement search and rating functionality
- Improve user interface
- Address security considerations

## Testing
Application is packaged into docker container using Github Action, and uploaded to AWS ECR by the pipeline.
AWS AppRunner is serving the app, which is available at https://codeqa.online

To create an account, you need to use your university email address.

Test accounts are available:

Normal user:
- username: testuser@villesalmela.fi
- password: password

Administrator:
- username: testadmin@villesalmela.fi
- password: password

Please don't delete or disable admin account, you currently can't make more of them without direct DB access.

Couple of test functions were saved to the library using these inputs:
```python
def celsius_to_fahrenheit(celsius):
    fahrenheit = (9/5) * celsius + 32
    return fahrenheit
```

```python
def factorial(n):
    if not isinstance(n, int):
        raise TypeError("Input must be an integer.")
    if n < 0:
        raise ValueError("Input must be a non-negative integer.")
    if n == 0:
        return 1
    else:
        return n * factorial(n-1)
```

Feel free to try the process with these ones, or come up with something else.

### Local Testing
While you can run the web app and database locally, some components don't currently have local options.
1. Install [Docker Engine](https://docs.docker.com/engine/install/)
1. Install [Visual Studio Code](https://code.visualstudio.com)
1. Install [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
1. Setup a PostgreSQL server
    - *ENV: DB_HOST, DB_PORT, DB_PASSWORD, DB_USER, DB_NAME*
1. Create a new [AWS VPC](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-getting-started.html), which will be used to isolate the lambda function
    - Give it one subnet, and no access to other networks
1. Create a new [AWS Lambda](https://docs.aws.amazon.com/lambda/latest/dg/getting-started.html) function
    - *ENV: PYTEST_REGION*
    - Attach the lambda function to the newly created VPC
    - Modify the automatically created [execution role](https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html), which the lambda function will assume
        - Set the role to have one policy, [AWSDenyALL](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/AWSDenyAll.html). \
        This will limit any damage that can occur if malicious user manages to escape isolation. 
    - Upload the [code for the lambda function](aws/lambda/lambda_function.py)
    - Create a [resource based policy](https://docs.aws.amazon.com/lambda/latest/dg/access-control-resource-based.html) that allows invoking this lambda function
    - Create a user, and assign it the policy you just created
        - [Setup an access key](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html)
        - *ENV: PYTEST_KEY_ID, PYTEST_KEY_SECRET*
1. Setup [OpenAI API](https://platform.openai.com/docs/introduction) key
    - *ENV: OPENAI_API_KEY*
1. Setup [Mailjet](https://www.mailjet.com) account
    - *ENV: MJ_APIKEY_PUBLIC, MJ_APIKEY_SECRET*
    - [create a template for transactional email](https://documentation.mailjet.com/hc/en-us/articles/360042952713-Mailjet-s-Email-Editor-for-Transactional-Emails)
        - *ENV: MJ_TEMPLATE_ID*
    - the template must:
        - accept one variable: "VERIFICATION_CODE"
        - include default subject and sender
1. Clone this project to your workstation
1. Change directory to project root
1. Copy the template for environment variables from [this template](.devcontainer/devcontainer.env.example)
    - Paste the template values in a new file, located in `.devcontainer/devcontainer.env`
    - Place secret values in the newly created file
1. In VS Code, press F1
1. Enter command `>dev containers: open folder in container`
    - Select the project root folder
    - This will build and start the image
1. Change to `app` directory
1. Run `gunicorn -c gunicorn_config.py qcl:app`
    - This will make the app available at http://localhost:8000
