# Alpha Systemd Service Installation and Management

## Service Configuration

The `alpha.service` systemd service file provides:

- **Automatic startup** on system boot
- **Auto-restart on failure** (up to 3 times per minute)
- **Graceful shutdown** handling
- **Configuration reload** without restart (SIGHUP)
- **Resource limits** for stability
- **Security hardening** (NoNewPrivileges, PrivateTmp)

## Installation

### 1. Prerequisites

- Linux system with systemd
- Python 3.8 or higher
- Alpha installed at `/opt/alpha` (or modify service file)

### 2. Create Alpha User (Recommended)

```bash
sudo useradd -r -s /bin/false alpha
sudo chown -R alpha:alpha /opt/alpha
```

### 3. Install Service File

```bash
# Copy service file
sudo cp systemd/alpha.service /etc/systemd/system/

# Reload systemd to recognize new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable alpha.service
```

## Usage

### Start Service

```bash
sudo systemctl start alpha
```

### Stop Service

```bash
sudo systemctl stop alpha
```

### Restart Service

```bash
sudo systemctl restart alpha
```

### Reload Configuration (Without Restart)

```bash
sudo systemctl reload alpha
```

### Check Status

```bash
sudo systemctl status alpha
```

### View Logs

```bash
# View recent logs
sudo journalctl -u alpha -n 50

# Follow logs in real-time
sudo journalctl -u alpha -f

# View logs from specific date
sudo journalctl -u alpha --since "2026-01-01"
```

### Enable/Disable Auto-Start

```bash
# Enable auto-start on boot
sudo systemctl enable alpha

# Disable auto-start
sudo systemctl disable alpha
```

## Configuration

### Environment Variables

To set environment variables for the service, edit the service file or create an environment file:

```bash
# Create environment file
sudo mkdir -p /etc/alpha
sudo nano /etc/alpha/environment

# Add your variables
DEEPSEEK_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here
LOG_LEVEL=INFO

# Update service file to use environment file
# Add under [Service]:
# EnvironmentFile=/etc/alpha/environment
```

### Custom Installation Directory

If Alpha is not installed at `/opt/alpha`, modify the service file:

1. Edit `/etc/systemd/system/alpha.service`
2. Change `WorkingDirectory` and paths to match your installation
3. Reload systemd: `sudo systemctl daemon-reload`

## Monitoring

### Health Checks

```bash
# Check if service is active
systemctl is-active alpha

# Check if service is enabled
systemctl is-enabled alpha

# Get service PID
systemctl show -p MainPID alpha
```

### Resource Usage

```bash
# View resource usage
systemctl status alpha

# Detailed resource metrics
systemd-cgtop alpha.service
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs for errors
sudo journalctl -u alpha -n 100

# Verify Python environment
/opt/alpha/venv/bin/python -m alpha.main --help

# Check permissions
ls -la /opt/alpha
```

### Service Crashes

```bash
# Check crash logs
sudo journalctl -u alpha -p err

# Verify restart count
systemctl show -p NRestarts alpha

# Check resource limits
systemctl show -p LimitNOFILE alpha
```

### Configuration Reload Fails

```bash
# Check if SIGHUP handler is working
sudo journalctl -u alpha | grep SIGHUP

# Try manual reload
sudo kill -HUP $(systemctl show -p MainPID alpha | cut -d= -f2)
```

## Security

### Running as Non-Root User

The service is configured to run as the `alpha` user for security. Ensure:

1. Alpha user exists: `id alpha`
2. Proper ownership: `sudo chown -R alpha:alpha /opt/alpha`
3. Required permissions: `chmod +x /opt/alpha/venv/bin/python`

### API Key Security

- Store API keys in `/etc/alpha/environment` with restricted permissions
- Set ownership: `sudo chown root:alpha /etc/alpha/environment`
- Set permissions: `sudo chmod 640 /etc/alpha/environment`

## Uninstallation

```bash
# Stop and disable service
sudo systemctl stop alpha
sudo systemctl disable alpha

# Remove service file
sudo rm /etc/systemd/system/alpha.service

# Reload systemd
sudo systemctl daemon-reload
```

## Advanced Configuration

### Custom Restart Policy

Edit service file to adjust restart behavior:

```ini
Restart=on-failure           # When to restart (on-failure, always, on-abnormal)
RestartSec=10s               # Delay before restart
StartLimitInterval=60s       # Time window for restart attempts
StartLimitBurst=3            # Max restart attempts in interval
```

### Resource Limits

Adjust resource limits in service file:

```ini
LimitNOFILE=65536           # Max open files
LimitNPROC=4096             # Max processes
MemoryLimit=2G              # Max memory usage (optional)
CPUQuota=80%                # CPU usage limit (optional)
```

### Logging Configuration

Configure logging behavior:

```ini
StandardOutput=journal      # Output to systemd journal
StandardError=journal       # Errors to systemd journal
SyslogIdentifier=alpha      # Identifier in logs
```

## See Also

- [Systemd Documentation](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [Alpha Documentation](../docs/)
- [Troubleshooting Guide](../docs/TROUBLESHOOTING.md)
