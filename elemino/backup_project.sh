#!/data/data/com.termux/files/usr/bin/bash
set -e
PROJECT_DIR="$(pwd)"
BACKUP_DIR="$PROJECT_DIR/backups"
STAMP="$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/project-backup-$STAMP.tar.gz" app
echo "Backup created: $BACKUP_DIR/project-backup-$STAMP.tar.gz"
