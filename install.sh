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

###############################################################################
# 3. Check Python 3 & venv availability
###############################################################################
if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: Python 3 not found on this system. Please install Python 3 first."
    exit 1
fi

if ! python3 -m venv --help >/dev/null 2>&1; then
    echo "Error: python3-venv (the venv module) is not installed or not available."
    echo "       Please install it on your system. For example, on Debian/Ubuntu:"
    echo "           sudo apt-get install python3-venv"
    echo "       Then re-run this script."
    exit 1
fi

PYTHON="$(command -v python3)"

###############################################################################
# 4. Create or update the Python virtual environment
###############################################################################
echo "Creating/Updating Python venv in: ${VENV_DIR}"
if [ ! -d "$VENV_DIR" ]; then
    "$PYTHON" -m venv "$VENV_DIR"
fi

# Upgrade pip and install dependencies
"${VENV_DIR}/bin/pip" install --upgrade pip
if [ -f "${APP_DIR}/requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    "${VENV_DIR}/bin/pip" install -r "${APP_DIR}/requirements.txt"
else
    echo "No requirements.txt found. Skipping pip install."
fi

###############################################################################
# 5. Create a run script that re-checks requirements before each launch
###############################################################################
echo "Creating run script at: ${RUN_SCRIPT}"
cat <<EOF > "$RUN_SCRIPT"
#!/usr/bin/env bash
source "$VENV_DIR/bin/activate"
exec python "${APP_DIR}/run.py"
EOF
chmod +x "$RUN_SCRIPT"

###############################################################################
# 6. Ask user about systemd service setup
###############################################################################
read -p "Do you want to create a systemd service for NablaPoker? (y/n): " CREATE_SERVICE
if [[ "$CREATE_SERVICE" =~ ^[Yy]$ ]]; then
    if ! command -v systemctl >/dev/null 2>&1; then
        echo "Error: systemd is not available on this system. Skipping service setup."
    else
        SYSTEMD_USER_DIR="${HOME}/.config/systemd/user"
        SERVICE_FILE="${SYSTEMD_USER_DIR}/${APP_NAME}.service"
        mkdir -p "$SYSTEMD_USER_DIR"

        echo "Creating systemd service at: ${SERVICE_FILE}"
        cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=NablaPoker Service
After=network.target

[Service]
WorkingDirectory=$APP_DIR
ExecStart=$RUN_SCRIPT
Restart=always

[Install]
WantedBy=default.target
EOF

        echo "Reloading systemd daemon..."
        systemctl --user daemon-reload
        echo "Systemd service created. Use the following commands to manage it:"
        echo "  systemctl --user start ${APP_NAME}"
        echo "  systemctl --user enable ${APP_NAME}"
        SERVICE_CREATED=true
    fi
else
    echo "Skipping systemd service setup. You can use ${RUN_SCRIPT} to run the app."
    SERVICE_CREATED=false
fi

###############################################################################
# 7. Print final instructions
###############################################################################
echo "--------------------------------------------------------------"
echo " Installation complete!"
echo " - App Directory:   ${APP_DIR}"
echo " - Virtual Env:     ${VENV_DIR}"
echo " - Run Script:      ${RUN_SCRIPT}"
echo "--------------------------------------------------------------"
if [ "$SERVICE_CREATED" = true ]; then
    echo " Systemd service was successfully created. Use 'systemctl --user start ${APP_NAME}' to start it."
else
    echo " Use './run-${APP_NAME}.sh' to start the application."
    echo " To create a user-level systemd service later, rerun this script."
fi
echo "--------------------------------------------------------------"
