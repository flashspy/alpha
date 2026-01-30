#!/usr/bin/env bash

#
# Alpha Daemon Installation Script
#
# This script installs Alpha as a systemd service for 24/7 background operation.
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/alpha"
SERVICE_FILE="alpha.service"
SERVICE_DIR="/etc/systemd/system"
ALPHA_USER="alpha"
PID_DIR="/var/run/alpha"
ENV_FILE="/etc/alpha/environment"

# Functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

check_systemd() {
    if ! command -v systemctl &> /dev/null; then
        print_error "systemd is not available on this system"
        exit 1
    fi
}

check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi

    python_version=$(python3 --version | awk '{print $2}')
    print_info "Python version: $python_version"
}

create_user() {
    if id "$ALPHA_USER" &>/dev/null; then
        print_warn "User '$ALPHA_USER' already exists"
    else
        print_info "Creating system user: $ALPHA_USER"
        useradd -r -s /bin/false -d "$INSTALL_DIR" -c "Alpha AI Assistant" "$ALPHA_USER"
    fi
}

setup_directories() {
    print_info "Setting up directories..."

    # Create install directory if it doesn't exist
    if [[ ! -d "$INSTALL_DIR" ]]; then
        print_error "Alpha installation not found at $INSTALL_DIR"
        print_info "Please install Alpha first, or modify INSTALL_DIR in this script"
        exit 1
    fi

    # Create PID directory
    mkdir -p "$PID_DIR"
    chown "$ALPHA_USER:$ALPHA_USER" "$PID_DIR"
    chmod 755 "$PID_DIR"

    # Create environment config directory
    mkdir -p /etc/alpha
    chmod 755 /etc/alpha

    # Create logs directory
    mkdir -p "$INSTALL_DIR/logs"
    chown "$ALPHA_USER:$ALPHA_USER" "$INSTALL_DIR/logs"
    chmod 755 "$INSTALL_DIR/logs"

    # Set ownership of installation directory
    chown -R "$ALPHA_USER:$ALPHA_USER" "$INSTALL_DIR"

    print_info "Directories configured"
}

install_service() {
    print_info "Installing systemd service..."

    # Copy service file
    if [[ ! -f "systemd/$SERVICE_FILE" ]]; then
        print_error "Service file not found: systemd/$SERVICE_FILE"
        print_info "Please run this script from the Alpha project root directory"
        exit 1
    fi

    cp "systemd/$SERVICE_FILE" "$SERVICE_DIR/"
    chmod 644 "$SERVICE_DIR/$SERVICE_FILE"

    # Reload systemd
    systemctl daemon-reload

    print_info "Service installed: $SERVICE_FILE"
}

setup_environment() {
    print_info "Setting up environment configuration..."

    if [[ ! -f "$ENV_FILE" ]]; then
        cat > "$ENV_FILE" << 'EOF'
# Alpha Environment Configuration
#
# Add your API keys and environment variables here.
# This file is loaded by the systemd service.

# AI Provider API Keys (add your keys)
# DEEPSEEK_API_KEY=your-key-here
# ANTHROPIC_API_KEY=your-key-here
# OPENAI_API_KEY=your-key-here

# Logging
LOG_LEVEL=INFO

# Optional: Custom configuration file
# ALPHA_CONFIG=/opt/alpha/config.yaml
EOF

        chmod 640 "$ENV_FILE"
        chown root:$ALPHA_USER "$ENV_FILE"
        print_info "Environment file created: $ENV_FILE"
        print_warn "Please edit $ENV_FILE and add your API keys"
    else
        print_warn "Environment file already exists: $ENV_FILE"
    fi
}

enable_service() {
    print_info "Enabling Alpha service..."
    systemctl enable alpha.service
    print_info "Service enabled (will start on boot)"
}

show_usage() {
    echo ""
    echo "Alpha Daemon Installation Complete!"
    echo ""
    echo "Next steps:"
    echo "  1. Edit environment file: sudo nano $ENV_FILE"
    echo "  2. Add your API keys to the environment file"
    echo "  3. Start the service: sudo systemctl start alpha"
    echo ""
    echo "Common commands:"
    echo "  Start:    sudo systemctl start alpha"
    echo "  Stop:     sudo systemctl stop alpha"
    echo "  Restart:  sudo systemctl restart alpha"
    echo "  Status:   sudo systemctl status alpha"
    echo "  Logs:     sudo journalctl -u alpha -f"
    echo ""
}

main() {
    echo "========================================"
    echo "Alpha Daemon Installation"
    echo "========================================"
    echo ""

    check_root
    check_systemd
    check_python
    create_user
    setup_directories
    install_service
    setup_environment
    enable_service

    show_usage
}

# Run main function
main
