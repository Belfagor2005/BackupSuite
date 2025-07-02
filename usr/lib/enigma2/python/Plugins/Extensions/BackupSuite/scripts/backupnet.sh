#!/bin/sh

###############################################################################
#                    BACKUP SUITE LAUNCHER - BACKUP ON NET                    #
#                https://github.com/persianpros/BackupSuite-PLi               #
#                                                                             #
#     FULL BACKUP UTILITY FOR ENIGMA2/OPENVISION, SUPPORTS VARIOUS MODELS     #
#                   MAKES A FULL BACKUP READY FOR FLASHING.                   #
#               SUPPORT FORUM: https://forums.openpli.org/                    #
#                                                                             #
#                      20250615 DEVELOPED FROM LULULLA                        #
###############################################################################

### NOTES FOR BACKUP SUITE (LULULLA)
# **GOAL:** Backup script style unification
# **COLORS:**
# TITLE BLOCK (PURPLE)
# SYSTEM DETECTION (BLUE)
# INITIALIZATION (BLUE)
# ERROR HANDLING (RED)
# DEVICE DETECTION (BLUE)
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
# EXTRA COPY TO USB (GREEN)
# CLEANUP AND STATISTICS (GREEN)
# PACKAGE LIST (WHITE)
# FINAL LOG COPY (WHITE)
# SUCCESS MESSAGE (GREEN)

## TESTING IF PROGRAM IS RUN FROM COMMANDLINE OR CONSOLE, JUST FOR THE COLORS ##
if tty > /dev/null ; then    # Commandline
    RED='\e[00;31m'    # Errors/failures
    GREEN='\e[00;32m'  # Success/positive messages
    YELLOW='\e[01;33m' # Warnings/important info
    BLUE='\e[01;34m'   # Phase headers
    PURPLE='\e[01;31m' # Titles/model info
    WHITE='\e[00;37m'  # Normal text
else                     # On the STB
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
echo "***   BACKUPSUITE PLUGIN FOR ENIGMA2/OPENVISION    ***"
echo "*** https://github.com/persianpros/BackupSuite-PLi ***"
echo -n "$YELLOW"
# echo "$LINE"
# echo -n "$WHITE"

# ==================== SYSTEM DETECTION (BLUE) ==============================
# echo -n "$YELLOW"
# echo "$LINE"
echo -n "$BLUE"

# Robust Python detection
detect_python() {
    if command -v python3 >/dev/null 2>&1; then
        echo "python3"
    elif command -v python2 >/dev/null 2>&1; then
        echo "python2"
    elif command -v python >/dev/null 2>&1; then
        echo "python"
    else
        echo "Unable to find Python!" >&2
        exit 1
    fi
}

# Library directory detection
if [ -d "/usr/lib64" ]; then
    LIBDIR="/usr/lib64"
else
    LIBDIR="/usr/lib"
fi

# Find Python and message script
PYTHON=$(detect_python)
MESSAGE_DIR="$LIBDIR/enigma2/python/Plugins/Extensions/BackupSuite"
MESSAGE_SCRIPT=""

# Find the best message script version
find_message_script() {
    # Check for compiled versions first
    for ext in pyc pyo; do
        if [ -f "$MESSAGE_DIR/message.$ext" ]; then
            echo "$MESSAGE_DIR/message.$ext"
            return
        fi
    done

    # Fallback to source version
    if [ -f "$MESSAGE_DIR/message.py" ]; then
        echo "$MESSAGE_DIR/message.py"
        return
    fi

    echo "Error: No message script found!" >&2
    exit 1
}

# Parameters
export LANG="${1:-en}"
export DEVICE_TYPE="${2:-NET}"
MEDIA="${3:-/media/net}"
export HARDDISK=0

# Find and validate message script
MESSAGE_SCRIPT=$(find_message_script)
export SHOW="$PYTHON $MESSAGE_SCRIPT $LANG"

# echo -n "$YELLOW"
# echo "$LINE"
echo -n "$WHITE"


# ===================== DEVICE INFORMATION (PURPLE) =========================
# echo -n "$YELLOW"
# echo "$LINE"
# echo -n "$PURPLE"
# Create required directory structure
BASE_BACKUP_DIR="$MEDIA"
IMAGE_DIR="$MEDIA/image"

# Create directories if they don't exist
mkdir -p "$IMAGE_DIR" || {
    echo -n "$RED"
    $SHOW "message42e" 2>&1  # Failed to create backup directories!
    echo -n "$WHITE"
    exit 1
}

# Create marker file
touch "$BASE_BACKUP_DIR/backupstick" || {
    echo -n "$RED"
    $SHOW "message42f" 2>&1  # Failed to create backup marker!
    echo -n "$WHITE"
    exit 1
}

# echo -n "$YELLOW"
# echo "$LINE"
# echo -n "$WHITE"





# ====================== DEVICE DETECTION (BLUE) =============================
# echo -n "$YELLOW"
# echo "$LINE"
# echo -n "$BLUE"
# Portable mount point validation
validate_network_path() {
    local path="$1"

    # Simplified check: directory exists and writable
    if [ ! -d "$path" ]; then
        $SHOW "message42a" 2>&1  # Directory does not exist!
        return 1
    fi

    # Check write permissions
    local temp_test="$path/backup_test_$$.tmp"
    if ! touch "$temp_test" 2>/dev/null; then
        $SHOW "message42c" 2>&1  # Write permission denied!
        return 1
    fi
    rm -f "$temp_test"

    return 0
}

# Validate network path
if ! validate_network_path "$MEDIA"; then
    echo -n "$RED"
    $SHOW "message42" 2>&1  # Invalid network path!
    echo -n "$WHITE"
    exit 1
fi
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"



# ==================== BACKUP SIZE ESTIMATION (GREEN) =======================
echo -n "$YELLOW"
echo "$LINE"
echo -n "$GREEN"
# Calculate required space - portable method
calculate_space() {
    # Get used space in /usr
    if command -v du >/dev/null; then
        USEDSIZE=$(du -sk /usr 2>/dev/null | awk '{print $1}')
    else
        # Fallback to df if du not available
        USEDSIZE=$(df -k /usr | awk 'NR>1 {print $3}')
    fi

    # Calculate needed space with 20% buffer
    NEEDEDSPACE=$((USEDSIZE * 12 / 10))  # in KB

    # Get free space on target
    if command -v df >/dev/null; then
        FREESIZE=$(df -P -k "$MEDIA" 2>/dev/null | tail -1 | awk '{print $(NF-2)}')
    else
        FREESIZE=0
    fi

    echo "$USEDSIZE $NEEDEDSPACE $FREESIZE"
}

# Check available space
read USEDSIZE NEEDEDSPACE FREESIZE <<< $(calculate_space)
# echo -n "$YELLOW"
# echo "$LINE"
# echo -n "$WHITE"

# ========================= SIZE WARNING (RED) ==============================
if [ -z "$FREESIZE" ] || [ "$FREESIZE" -lt "$NEEDEDSPACE" ]; then
    echo -n "$RED"
    $SHOW "message42d" 2>&1  # Insufficient free space!
    printf '%5s' "$((FREESIZE / 1024))"
    $SHOW "message32"  # Available (MB):
    printf '%5s' "$((NEEDEDSPACE / 1024))"
    $SHOW "message33"  # Needed (MB):
    echo -n "$WHITE"
    exit 1
fi
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

# ================ PREPARING WORK ENVIRONMENT (BLUE) ========================
echo -n "$YELLOW"
echo "$LINE"
echo -n "$BLUE"
# Preparation message
$SHOW "message45" 2>&1  # Phase 1/3: Preparing backup environment

# Create version files
cp /etc/image-version "$BASE_BACKUP_DIR/imageversion" 2>/dev/null
cp /tmp/enigma2version "$BASE_BACKUP_DIR/enigma2version" 2>/dev/null

# Log NAS info
{
    echo "===== BackupSuite Network Backup ====="
    date
    echo "Backup directory: $BASE_BACKUP_DIR"
    echo "Image directory: $IMAGE_DIR"
    echo "Mount details:"
    grep "$MEDIA" /proc/mounts || echo "No mount info found"
    echo "Disk space:"
    df -h "$MEDIA"
    echo "======================================"
} > "$BASE_BACKUP_DIR/BackupSuite.log"
# echo -n "$YELLOW"
# echo "$LINE"
# echo -n "$WHITE"

# ========================== BACKUP START (GREEN) ===========================
echo -n "$YELLOW"
echo "$LINE"
echo -n "$GREEN"
# Execute main backup script
BACKUP_SCRIPT="$LIBDIR/enigma2/python/Plugins/Extensions/BackupSuite/scripts/backupsuite.sh"
if [ -x "$BACKUP_SCRIPT" ]; then
    # Set executable permission
    chmod 755 "$BACKUP_SCRIPT" >/dev/null 2>&1

    # Run backup
    "$BACKUP_SCRIPT" "$BASE_BACKUP_DIR"
    ret=$?

    # Append backup log to our logfile
    if [ -f "$BASE_BACKUP_DIR/BackupSuite.log" ]; then
        cat "$BASE_BACKUP_DIR/BackupSuite.log" >> "$BASE_BACKUP_DIR/BackupSuite_full.log"
    fi
else
    echo -n "$RED"
    $SHOW "message47" 2>&1  # Backup script not found!
    echo -n "$WHITE"
    ret=1
fi

sync
# # echo -n "$YELLOW"
# # echo "$LINE"
# echo -n "$WHITE"

# ==================== CLEANUP AND STATISTICS (GREEN) =======================
# echo -n "$YELLOW"
# echo "$LINE"
echo -n "$GREEN"
# Completion message
if [ ${ret:-1} -eq 0 ]; then
    $SHOW "message48" 2>&1  # Backup completed successfully!

    # Calculate backup size
    SIZE=$(du -sh "$IMAGE_DIR" 2>/dev/null | awk '{print $1}')
    if [ -n "$SIZE" ]; then
        echo -n "$YELLOW"
        $SHOW "message49a" 2>&1  # Backup size:
        echo " $SIZE"
        echo -n "$GREEN"
    fi

    # Show backup location
    $SHOW "message50a" 2>&1  # Backup created in:
    echo " $IMAGE_DIR"

    # Clean up old backups (keep last 3)
    find "$MEDIA/backup" -maxdepth 1 -type d -name 'backup_*' 2>/dev/null |
        sort |
        head -n -3 |
        xargs rm -rf 2>/dev/null
else
    echo -n "$RED"
    $SHOW "message15" 2>&1  # Image creation FAILED!
fi
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

exit ${ret:-1}