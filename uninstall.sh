#!/usr/bin/env bash

set -e

###############################################################################
# Uninstall NablaPoker (Service Only)
###############################################################################

# Define paths
APP_NAME="nablapoker"
SYSTEMD_USER_DIR="${HOME}/.config/systemd/user"
SERVICE_FILE="${SYSTEMD_USER_DIR}/${APP_NAME}.service"

# Stop and disable the systemd service (if it exists)
if [ -f "${SERVICE_FILE}" ]; then
    echo "Stopping and disabling the systemd service..."
    systemctl --user stop ${APP_NAME} || echo "Service was not running."
    systemctl --user disable ${APP_NAME} || echo "Service was not enabled."
    echo "Deleting the service file..."
    rm -f "${SERVICE_FILE}"
    echo "Reloading user-level systemd daemon..."
    systemctl --user daemon-reload
else
    echo "No systemd service file found for ${APP_NAME}. Skipping."
fi

# Final confirmation
echo "Uninstallation complete! Systemd service for ${APP_NAME} has been removed."
echo "Source files and virtual environment remain intact. To fully remove, delete the project directory manually."
