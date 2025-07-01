#!/bin/sh

###############################################################################
#          BACKUP SUITE LAUNCHER - DETECTS MEDIA AND STARTS BACKUP            #
#                https://github.com/persianpros/BackupSuite-PLi               #
#                                                                             #
#     FULL BACKUP UTILITY FOR ENIGMA2/OPENVISION, SUPPORTS VARIOUS MODELS     #
#                   MAKES A FULL BACKUP READY FOR FLASHING.                   #
#               SUPPORT FORUM: https://forums.openpli.org/                    #
#                                                                             #
#                       UPDATE 20250615 BY LULULLA                            #
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
# echo -n "$YELLOW"
# echo "$LINE"
# echo -n "$WHITE"

# ====================== INITIALIZATION (BLUE) ==============================
# echo -n "$YELLOW"
# echo "$LINE"
# echo -n "$BLUE"
# Parameters
export LANG="${1:-en}"
MESSAGE_SCRIPT=$(find_message_script)
export SHOW="$PYTHON $MESSAGE_SCRIPT $LANG"

# Device type detection
case "${2:-HDD}" in
    "HDD") export HARDDISK=1 ;;
    "USB") export HARDDISK=0 ;;
    "MMC") export HARDDISK=0 ;;
    *)     export HARDDISK=1 ;;
esac

# Show backup destination message
$SHOW "message20" 2>&1  # "Full back-up to the harddisk"
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

# ====================== DEVICE DETECTION (BLUE) =============================
echo -n "$YELLOW"
echo "$LINE"
echo -n "$BLUE"
# Portable function to get disk space info
get_disk_space() {
    local path="$1"
    if command -v df >/dev/null; then
        # Try human-readable format
        SIZE_INFO=$(df -h "$path" 2>/dev/null | tail -n 1)
        if [ -n "$SIZE_INFO" ]; then
            # Handle different df output formats
            if echo "$SIZE_INFO" | grep -q '^/dev/'; then
                TOTAL=$(echo "$SIZE_INFO" | awk '{print $2}')
                FREE=$(echo "$SIZE_INFO" | awk '{print $4}')
                MOUNT=$(echo "$SIZE_INFO" | awk '{print $6}')
            else
                TOTAL=$(echo "$SIZE_INFO" | awk '{print $1}')
                FREE=$(echo "$SIZE_INFO" | awk '{print $3}')
                MOUNT=$(echo "$SIZE_INFO" | awk '{print $5}')
            fi
            echo "$TOTAL $FREE $MOUNT"
        else
            echo "?? ?? unknown"
        fi
    else
        echo "?? ?? unknown"
    fi
}

# Find HDD target
find_hdd_target() {
    # Check common HDD locations
    for candidate in /hdd /media/hdd /media/usb/hdd /mnt/hdd; do
        if [ -d "$candidate" ] && mountpoint -q "$candidate" 2>/dev/null; then
            # Test write access
            if touch "$candidate/hdd_test.$$" 2>/dev/null; then
                rm -f "$candidate/hdd_test.$$"
                echo "$candidate"
                return 0
            fi
        fi
    done

    # Check mounted devices
    while IFS= read -r line; do
        dev=$(echo "$line" | cut -d ' ' -f 1)
        mountpoint=$(echo "$line" | cut -d ' ' -f 2)
        fstype=$(echo "$line" | cut -d ' ' -f 3)

        # Only consider valid filesystems
        case "$fstype" in
            ext*|vfat|ntfs|btrfs|ufs)
                if touch "$mountpoint/hdd_test.$$" 2>/dev/null; then
                    rm -f "$mountpoint/hdd_test.$$"
                    echo "$mountpoint"
                    return 0
                fi
                ;;
        esac
    done < /proc/mounts

    # No valid HDD found
    return 1
}
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

# ===================== DEVICE INFORMATION (PURPLE) =========================
echo -n "$YELLOW"
echo "$LINE"
echo -n "$PURPLE"
# Find HDD target
HDD_TARGET=$(find_hdd_target)
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

# ======================== ERROR HANDLING (RED) =============================
echo -n "$YELLOW"
echo "$LINE"
echo -n "$RED"
if [ -z "$HDD_TARGET" ]; then
    $SHOW "message15" 2>&1  # No suitable media found!
    echo -n "$WHITE"
    exit 1
fi
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

# ===================== DEVICE INFORMATION (PURPLE) =========================
echo -n "$YELLOW"
echo "$LINE"
echo -n "$PURPLE"
# Get disk space info
read TOTALSIZE FREESIZE MEDIA <<< $(get_disk_space "$HDD_TARGET")

# Show disk info
echo -n " -> $HDD_TARGET ($TOTALSIZE, "
$SHOW "message16"  # Free
echo "$FREESIZE)"
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

# ========================== BACKUP START (GREEN) ===========================
echo -n "$YELLOW"
echo "$LINE"
echo -n "$GREEN"
# Execute backup script
BACKUP_SCRIPT="$LIBDIR/enigma2/python/Plugins/Extensions/BackupSuite/scripts/backupsuite.sh"
if [ -x "$BACKUP_SCRIPT" ]; then
    # Ensure executable
    chmod 755 "$BACKUP_SCRIPT" >/dev/null 2>&1

    # Run backup
    "$BACKUP_SCRIPT" "$HDD_TARGET"
    ret=$?
    sync
else
    echo -n "$RED"
    $SHOW "message05" 2>&1  # Backup script not found!
    ret=1
fi
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

# ==================== CLEANUP AND STATISTICS (GREEN) =======================
echo -n "$YELLOW"
echo "$LINE"
echo -n "$GREEN"
# Completion message
if [ ${ret:-1} -eq 0 ]; then
    $SHOW "message48" 2>&1  # Backup completed successfully!
else
    echo -n "$RED"
    $SHOW "message15" 2>&1  # Image creation FAILED!
fi
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

exit ${ret:-1}