# NablaPoker

### 1. Clone the Repository

### 2. Set Up a Virtual Environment

It’s recommended to use a Python virtual environment to isolate dependencies.
On Linux/MacOS:

    python3 -m venv venv
    source venv/bin/activate

On Windows:

    python -m venv venv
    venv\Scripts\activate

### 3. Install Dependencies

With the virtual environment activated, install the required dependencies:

    pip install -r requirements.txt

### 4. Configuration

The app requires configuration files for secrets and other environment-specific settings.

Create the Instance Folder:

    mkdir instance

Create config.py in the instance Folder: Example configuration:

    SECRET_KEY = 'your-secret-key'
    DEBUG = True

The app will automatically use this file for instance-specific configurations.

### 5. Launch the App

Run the application with the following command:

    python run.py

### 6. Deployment

For production:

Use Gunicorn to run the app:

    gunicorn -w 4 -b 0.0.0.0:5187 app:app

Optionally, configure Nginx to act as a reverse proxy for the app.
