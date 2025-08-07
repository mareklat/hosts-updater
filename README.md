# Hosts Updater

A utility to update the system hosts file with domains from Nginx Proxy Manager.

## Installation

1. Build the binary:
   ```bash
   ./build.sh
   ```

2. The executable will be created in `dist/hosts_updater`

## Configuration

Copy `config.ini` to the same directory as the executable. Example configuration:

```ini
[nginx-proxy-manager]
api_url = https://your-npm-instance.com
ip_address = 192.168.1.100

[hosts]
section_header = # BEGIN nginx-proxy-manager domains
section_footer = # END nginx-proxy-manager domains
file_path = /etc/hosts  # Path to hosts file
```

## Usage

Run the executable and provide credentials when prompted:

```bash
./dist/hosts_updater
```

The application will prompt you for:
- NPM username (entered interactively)
- NPM password (entered securely without echo)

## Requirements

- Python 3.7+
- PyInstaller (for building)
- requests library

## Notes

- The application needs root privileges to modify `/etc/hosts`
- Credentials are entered interactively for security
- The hosts file path is configurable in `config.ini`
