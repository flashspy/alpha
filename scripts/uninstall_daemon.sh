#!/usr/bin/env bash

#
# Alpha Daemon Uninstallation Script
#
# This script removes Alpha systemd service.
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SERVICE_FILE="alpha.service"
SERVICE_DIR="/etc/systemd/system"
ALPHA_USER="alpha"
PID_DIR="/var/run/alpha"

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

stop_service() {
    print_info "Stopping Alpha service..."
    if systemctl is-active --quiet alpha; then
        systemctl stop alpha
        print_info "Service stopped"
    else
        print_warn "Service is not running"
    fi
}

disable_service() {
    print_info "Disabling Alpha service..."
    if systemctl is-enabled --quiet alpha 2>/dev/null; then
        systemctl disable alpha
        print_info "Service disabled"
    else
        print_warn "Service is not enabled"
    fi
}

remove_service() {
    print_info "Removing service file..."
    if [[ -f "$SERVICE_DIR/$SERVICE_FILE" ]]; then
        rm "$SERVICE_DIR/$SERVICE_FILE"
        systemctl daemon-reload
        print_info "Service file removed"
    else
        print_warn "Service file not found"
    fi
}

cleanup_pid() {
    print_info "Cleaning up PID directory..."
    if [[ -d "$PID_DIR" ]]; then
        rm -rf "$PID_DIR"
        print_info "PID directory removed"
    fi
}

main() {
    echo "========================================"
    echo "Alpha Daemon Uninstallation"
    echo "========================================"
    echo ""

    check_root
    stop_service
    disable_service
    remove_service
    cleanup_pid

    echo ""
    print_info "Alpha daemon uninstalled successfully"
    echo ""
    print_warn "Note: Alpha installation directory and user account were not removed"
    print_info "To remove completely, run:"
    echo "  sudo userdel $ALPHA_USER"
    echo "  sudo rm -rf /opt/alpha"
    echo "  sudo rm -rf /etc/alpha"
    echo ""
}

# Run main function
main
