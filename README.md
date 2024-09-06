![Proprietary](https://img.shields.io/badge/License-Proprietary-red)
# Sylhet Engineering College Undergraduate Result Portal (SEC UGRP)

## Getting Started

These instructions will guide you through setting up the project on your local machine for development and testing purposes.

### Prerequisites

- Python 3.8.x
- PostgreSQL or other supported database systems

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/rnium/sec_ugrp
   cd sec_ugrp
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**

   Create a `.env` file in the `base_dir/config` folder with the following keys:

   ```ini
   SECRET_KEY=<your_django_secret_key>
   SG_API_KEY=<your_sendgrid_api_key>
   SG_FROM_EMAIL=<your_sendgrid_from_email>
   ```

   #### Generating a Django Secret Key

   You can generate a Django secret key using one of the following methods:

   - Use Django's `get_random_secret_key()`:
     ```python
     from django.core.management.utils import get_random_secret_key
     print(get_random_secret_key())
     ```

   - Use an online generator like [Djecrety](https://djecrety.ir/).
   - Use the command line to generate a random string:
     ```bash
     python -c 'import secrets; print(secrets.token_urlsafe(50))'
     ```

5. **Create `local_settings.py` for overriding default settings:**

   In `base_dir/config` folder, create a file named `local_settings.py` and add any setting overrides. For example:

   ```python
   # local_settings.py

   DEBUG = True
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'your_db_name',
           'USER': 'your_db_user',
           'PASSWORD': 'your_db_password',
           'HOST': 'localhost',
           'PORT': '5432',
       }
   }
   ```

6. **Apply migrations to set up the database:**

   Run the following command to migrate the database schema:

   ```bash
   python manage.py migrate
   ```

   If you have backup data available in JSON or XML format, you can load it using Django's `loaddata` command:

   ```bash
   python manage.py loaddata <fixture_name>
   ```

7. **Run the development server:**

   Start the development server to verify the installation:

   ```bash
   python manage.py runserver
   ```

   Your application should now be running at `http://127.0.0.1:8000/`.

## Additional Information

- **Environment Variables:** Ensure all required environment variables are correctly set in your `.env` file.
- **Email:** The project uses SendGrid for sending emails. Ensure you have valid API keys and a verified sending email address.

