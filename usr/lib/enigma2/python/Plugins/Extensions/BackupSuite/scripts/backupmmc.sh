#!/bin/sh

###############################################################################
#                    BACKUP SUITE LAUNCHER - BACKUP ON MMC                    #
#                https://github.com/persianpros/BackupSuite-PLi               #
#                                                                             #
#     FULL BACKUP UTILITY FOR ENIGMA2/OPENVISION, SUPPORTS VARIOUS MODELS     #
#                   MAKES A FULL BACKUP READY FOR FLASHING.                   #
#               SUPPORT FORUM: https://forums.openpli.org/                    #
#                                                                             #
#          >>>>>> IT WORKS INDEPENDENTLY FROM OTHER SCRIPTS <<<<<<            #
#                      20250615 DEVELOPED FROM LULULLA                        #
###############################################################################

### NOTES FOR BACKUP SUITE (LULULLA)
# **GOAL:** Space-efficient backup for MMC/SD cards
# **COLORS:**
# TITLE BLOCK (PURPLE)
# SYSTEM DETECTION (BLUE)
# INITIALIZATION (BLUE)
# ERROR HANDLING (RED)
# DEVICE INFORMATION (PURPLE)
# BACKUP SIZE ESTIMATION (GREEN)
# SIZE WARNING (YELLOW/RED)
# SEPARED LINE (YELLOW)
# PREPARING WORK ENVIRONMENT (BLUE)
# BACKUP START (GREEN)
# KERNEL BACKUP (BLUE)
# ROOT FILESYSTEM BACKUP (GREEN)
# FINALIZING BACKUP (BLUE)
# ZIP ARCHIVE CREATION (GREEN)
# CLEANUP AND STATISTICS (GREEN)
# SUCCESS MESSAGE (GREEN)

## TESTING IF PROGRAM IS RUN FROM COMMANDLINE OR CONSOLE, JUST FOR THE COLORS ##
if tty > /dev/null ; then
    RED='\e[00;31m'
    GREEN='\e[00;32m'
    YELLOW='\e[01;33m'
    BLUE='\e[01;34m'
    PURPLE='\e[01;31m'
    WHITE='\e[00;37m'
else
    RED='\c00??0000'
    GREEN='\c0000??00'
    YELLOW='\c00????00'
    BLUE='\c0000????'
    PURPLE='\c00?:55>7'
    WHITE='\c00??????'
fi

# ========================= TITLE BLOCK (PURPLE) =============================
LINE="------------------------------------------------------------"
echo -n "$YELLOW"
echo "$LINE"
echo -n "$PURPLE"
echo "***   BACKUPSUITE MMC OPTIMIZED BACKUP           ***"
echo "*** https://github.com/persianpros/BackupSuite-PLi ***"
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

# ==================== PARAMETER HANDLING ===================================
LANG="$1"
DEVICE_TYPE="$2"
MEDIA="$3"

# ==================== MEDIA VERIFICATION ===================================
echo -n "$YELLOW"
echo "$LINE"
echo -n "$BLUE"
echo "Verifying media: $MEDIA"

[ ! -d "$MEDIA" ] && {
    echo -n "$RED"
    echo "ERROR: Media path does not exist!"
    echo -n "$WHITE"
    exit 1
}

# Check write permissions
if ! touch "$MEDIA/bs_testfile" 2>/dev/null; then
    echo -n "$RED"
    echo "ERROR: Write permission denied!"
    echo -n "$WHITE"
    exit 1
fi
rm -f "$MEDIA/bs_testfile"

# ==================== SPACE CHECK ==========================================
echo -n "$GREEN"
echo "Checking available space..."
free_kb=$(df -k "$MEDIA" | tail -1 | awk '{print $4}')
free_mb=$((free_kb / 1024))

# Minimum required space (300MB)
min_space_mb=300
if [ "$free_mb" -lt "$min_space_mb" ]; then
    echo -n "$RED"
    echo "ERROR: Insufficient disk space!"
    echo -n "$YELLOW"
    echo "Required: ${min_space_mb}MB, Available: ${free_mb}MB"
    echo -n "$WHITE"
    exit 1
fi

echo -n "$GREEN"
echo "Space available: ${free_mb}MB"
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

# ==================== BACKUP PROCESS =======================================
echo -n "$BLUE"
echo "Phase 1/3: Creating temporary directory"
TMP_DIR="/tmp/mmc_backup_$$"
mkdir -p "$TMP_DIR" || {
    echo -n "$RED"
    echo "ERROR: Cannot create temp directory!"
    exit 1
}

# Backup kernel
echo "Phase 2/3: Backing up kernel"

KERNEL_PARTITION=$(grep -w "/boot" /proc/mounts | awk '{print $1}')
if [ -z "$KERNEL_PARTITION" ]; then
    # Prova a dedurre la partizione root da /proc/mounts
    ROOT_PARTITION=$(grep -w "/" /proc/mounts | awk '{print $1}')
    # Ricava il nome dispositivo (es. sda1 → sda)
    if [ -n "$ROOT_PARTITION" ]; then
        KERNEL_PARTITION=$(basename "$(echo $ROOT_PARTITION | sed 's/[0-9]*$//')")
    fi
fi

if [ -n "$KERNEL_PARTITION" ]; then
    dd if="/dev/$KERNEL_PARTITION" of="$TMP_DIR/kernel.bin" bs=4k 2>/dev/null
else
    echo -n "$YELLOW"
    echo "WARNING: Kernel partition not found, skipping"
fi

# Backup rootfs
echo "Phase 3/3: Backing up root filesystem"
tar -C / -cpf "$TMP_DIR/rootfs.tar" \
    --exclude='./proc/*' \
    --exclude='./sys/*' \
    --exclude='./dev/*' \
    --exclude='./tmp/*' \
    --exclude='./media/*' \
    --exclude='./run/*' \
    --exclude='./mnt/*' \
    . 2>/dev/null

# Create final zip
echo -n "$GREEN"
echo "Creating compressed archive..."
MODEL=$(cat /etc/hostname 2>/dev/null)
[ -z "$MODEL" ] && MODEL=$(cat /proc/stb/info/model 2>/dev/null)
[ -z "$MODEL" ] && MODEL=$(cat /proc/stb/info/boxtype 2>/dev/null)
[ -z "$MODEL" ] && MODEL=$(cat /proc/stb/info/vumodel 2>/dev/null)
[ -z "$MODEL" ] && MODEL=$(grep -m1 -i -E "Hardware|machine|system type|model" /proc/cpuinfo | cut -d: -f2 | tr -d ' ')
[ -z "$MODEL" ] && MODEL=$(uname -m)

ZIP_FILE="$MEDIA/backup_${MODEL}_$(date +%Y%m%d_%H%M).zip"

if command -v zip >/dev/null; then
    cd "$TMP_DIR"
    zip -qr "$ZIP_FILE" *
    cd - >/dev/null
    ZIP_SIZE=$(du -h "$ZIP_FILE" | cut -f1)
    echo -n "$GREEN"
    echo "Backup created: $ZIP_FILE (${ZIP_SIZE})"
else
    echo -n "$YELLOW"
    echo "WARNING: zip not available, using tar.gz"
    tar -czf "$ZIP_FILE.tar.gz" -C "$TMP_DIR" .
    ZIP_SIZE=$(du -h "$ZIP_FILE.tar.gz" | cut -f1)
    echo -n "$GREEN"
    echo "Backup created: $ZIP_FILE.tar.gz (${ZIP_SIZE})"
fi

# Cleanup
rm -rf "$TMP_DIR"
echo -n "$BLUE"
echo "Temporary files cleaned"

echo -n "$GREEN"
echo "Backup completed successfully!"
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

exit 0