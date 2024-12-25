# NablaPoker

## Overview

NablaPoker is an open-source poker platform currently under development.

## Features

- **Game Platform**: Create and join poker games
- **Replayer**: Replay previous hands
- **Statistics**: Display the user and opponents statistics

## Prerequisites

Before you begin, ensure you have met the following requirements:

- **Python 3**: The project is built using Python 3.
- **pip**: Python package installer for managing project dependencies.
- **Systemd**: For managing the application as a service (optional).

## Installation

To set up NablaPoker, follow these steps:

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Andres-Briones/NablaPoker.git
   cd NablaPoker
   ```

2. **Make the Script Executable**
   ```bash
   chmod +x install.sh
   ```

3. **Run the Installation Script**
   ```bash
   ./install.sh
   ```

   The `install.sh` script will:

   - Check for Python 3 and `venv` availability.
   - Create a Python virtual environment and install dependencies from `requirements.txt`.
   - Generate a run script (`run-nablapoker.sh`) for launching the application.
   - Optionally set up a user-level systemd service if the user agrees and systemd is available.

## Running the Application

After installation, you can start the application in one of the following ways:

### Option 1: Using the Run Script

Execute the generated run script to start the app:

```bash
./run-nablapoker.sh
```

### Option 2: Using Systemd (Optional)

If you set up the systemd service during installation, use the following commands:

1. Start the service:
   ```bash
   systemctl --user start nablapoker
   ```

2. Check the service status:
   ```bash
   systemctl --user status nablapoker
   ```

3. View logs (if `journald` is used):
   ```bash
   journalctl --user -u nablapoker
   ```

4. Enable the service to start automatically upon login:
   ```bash
   systemctl --user enable nablapoker
   ```

## Uninstallation

To uninstall NablaPoker and clean up the system, use the `uninstall.sh` script:

1. **Make the Uninstall Script Executable**
   ```bash
   chmod +x uninstall.sh
   ```

2. **Run the Uninstall Script**
   ```bash
   ./uninstall.sh
   ```

   The `uninstall.sh` script will:

   - Stop and disable the systemd service (if it exists).
   - Remove the systemd service file.

3. **Confirmation**
   The application has been unregistered as a service. The virtual environment and source files remain intact for potential reinstallation or manual management.

   If you wish to completely remove the application, delete the project directory manually:

   ```bash
   rm -rf /path/to/nablapoker
   ```

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a new branch.
3. Make your changes.
4. Submit a pull request.

## License

This project is licensed under the GPL-3.0 License. See the [LICENSE](https://github.com/Andres-Briones/NablaPoker/blob/main/LICENSE) file for more details.

---

If you encounter any issues during installation or have questions, feel free to open an issue or contact the maintainer.
