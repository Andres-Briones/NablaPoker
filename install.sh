#!/usr/bin/env bash

set -e

###############################################################################
# 1. Identify the script directory as the app directory
###############################################################################
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$SCRIPT_DIR"

###############################################################################
# 2. Define your app name and key paths
###############################################################################
APP_NAME="nablapoker"

# Virtual env and run script in the same directory
VENV_DIR="${APP_DIR}/venv"
RUN_SCRIPT="${APP_DIR}/run-${APP_NAME}.sh"

# Location of user-level systemd service file
SYSTEMD_USER_DIR="${HOME}/.config/systemd/user"
SERVICE_FILE="${SYSTEMD_USER_DIR}/${APP_NAME}.service"

###############################################################################
# 3. Ensure the user-level systemd directory exists
###############################################################################
mkdir -p "${SYSTEMD_USER_DIR}"

###############################################################################
# 4. Check Python 3 & venv availability
###############################################################################
if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: Python 3 not found on this system. Please install Python 3 first."
    exit 1
fi

# Check if the venv module is available by testing the --help command
if ! python3 -m venv --help >/dev/null 2>&1; then
    echo "Error: python3-venv (the venv module) is not installed or not available."
    echo "       Please install it on your system. For example, on Debian/Ubuntu:"
    echo "           sudo apt-get install python3-venv"
    echo "       Then re-run this script."
    exit 1
fi

PYTHON="$(command -v python3)"

###############################################################################
# 5. Create or update the Python virtual environment
###############################################################################
echo "Creating/Updating Python venv in: ${VENV_DIR}"
if [ ! -d "$VENV_DIR" ]; then
    "$PYTHON" -m venv "${VENV_DIR}"
fi

# Make sure pip is available in the venv
if [ ! -x "${VENV_DIR}/bin/pip" ]; then
    echo "Pip is missing in the virtual environment. Trying to install via ensurepip..."
    "$PYTHON" -m ensurepip --upgrade || {
        echo "Failed to install pip in the virtual environment."
        exit 1
    }
fi

# Upgrade pip and install dependencies (if requirements.txt is present)
"${VENV_DIR}/bin/pip" install --upgrade pip
if [ -f "${APP_DIR}/requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    "${VENV_DIR}/bin/pip" install -r "${APP_DIR}/requirements.txt"
else
    echo "No requirements.txt found. Skipping pip install."
fi

###############################################################################
# 6. Create a run script that re-checks requirements before each launch
###############################################################################
echo "Creating run script at: ${RUN_SCRIPT}"
cat <<EOF > "${RUN_SCRIPT}"
#!/usr/bin/env bash
# 
# Activates the virtual env and runs the app.
# It also re-installs requirements if requirements.txt is present.

cd "${APP_DIR}"
source "${VENV_DIR}/bin/activate"

# Double-check that 'pip' is in the path
if ! command -v pip &>/dev/null; then
    echo "Error: 'pip' not found in the activated virtual environment."
    exit 1
fi

# Reinstall dependencies if requirements.txt is updated
if [ -f requirements.txt ]; then
    echo "Upgrading/installing requirements before launch..."
    pip install --upgrade -r requirements.txt
fi

# Finally, run the app (assuming run.py is your entry point)
exec python run.py
EOF

chmod +x "${RUN_SCRIPT}"

###############################################################################
# 7. Create a user-level systemd unit file (not enabled by default)
###############################################################################
echo "Creating user-level systemd service at: ${SERVICE_FILE}"

cat <<EOF > "${SERVICE_FILE}"
[Unit]
Description=NablaPoker (User-level) Service
After=network.target

[Service]
WorkingDirectory=${APP_DIR}
ExecStart=${RUN_SCRIPT}
Restart=always
# Type=simple is default

[Install]
WantedBy=default.target
EOF

###############################################################################
# 8. Reload systemd (user), but DO NOT enable or start automatically
###############################################################################
echo "Reloading user-level systemd daemon..."
systemctl --user daemon-reload

###############################################################################
# 9. Print final instructions
###############################################################################
echo "--------------------------------------------------------------"
echo " Installation complete!"
echo " - App Directory:   ${APP_DIR}"
echo " - Virtual Env:     ${VENV_DIR}"
echo " - Run Script:      ${RUN_SCRIPT}"
echo " - Service File:    ${SERVICE_FILE}"
echo "--------------------------------------------------------------"
echo " You can start your user-level service with:"
echo "   systemctl --user start ${APP_NAME}"
echo
echo " Check status with:"
echo "   systemctl --user status ${APP_NAME}"
echo
echo " View logs with (if journald is used):"
echo "   journalctl --user -u ${APP_NAME}"
echo
echo " To have the service start automatically upon login, run:"
echo "   systemctl --user enable ${APP_NAME}"
echo
echo " If you want the service to keep running after you log out,"
echo " consider enabling lingering (requires sudo):"
echo "   sudo loginctl enable-linger \$USER"
echo "--------------------------------------------------------------"
