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

# Parameters
export LANG="${1:-en}"
MESSAGE_SCRIPT=$(find_message_script)
export SHOW="$PYTHON $MESSAGE_SCRIPT $LANG"

# Device type detection
case "${2:-USB}" in
    "HDD") export HARDDISK=1 ;;
    "USB") export HARDDISK=0 ;;
    "MMC") export HARDDISK=0 ;;
    *)     export HARDDISK=0 ;;
esac

# Portable disk space calculation
calculate_space() {
    # Get used space in /usr
    if command -v du >/dev/null; then
        USEDSIZE=$(du -sk /usr 2>/dev/null | awk '{print $1}')
    else
        # Fallback to df if du not available
        USEDSIZE=$(df -k /usr | awk 'NR>1 {print $3}')
    fi

    # Calculate needed space with buffer (original formula: 4*size/1024)
    NEEDEDSPACE=$(((USEDSIZE * 41) / 10))  # in KB (400% + 2.5% buffer)

    echo "$USEDSIZE $NEEDEDSPACE"
}

# Get space requirements
read USEDSIZE NEEDEDSPACE <<< $(calculate_space)

# Find backup media
find_backup_media() {
    # Try common mount points
    for candidate in /media/usb /media/hdd /media/mmc /media/sdb1 /media/sda1 /mnt/usb /mnt/hdd
    do
        if [ -d "$candidate" ] && grep -q "$candidate" /proc/mounts; then
            # Check for backup indicator (file or directory)
            if [ -f "$candidate/backupstick" ] || [ -d "$candidate/backupstick" ]; then
                echo "$candidate"
                return
            fi

            # Check for writable filesystem
            if touch "$candidate/backup_test_$$" 2>/dev/null; then
                rm -f "$candidate/backup_test_$$"
                echo "$candidate"
                return
            fi
        fi
    done

    # Fallback to scanning /proc/mounts
    grep '^/dev/' /proc/mounts | while read -r device mountpoint fstype _; do
        case "$fstype" in
            vfat|ntfs|ext2|ext3|ext4|btrfs|ufs)
                if touch "$mountpoint/backup_test_$$" 2>/dev/null; then
                    rm -f "$mountpoint/backup_test_$$"
                    echo "$mountpoint"
                    return
                fi
                ;;
        esac
    done

    echo ""
}

# Find backup target
TARGET=$(find_backup_media)

if [ -z "$TARGET" ]; then
    echo -n $RED
    $SHOW "message21" 2>&1  # "No backup media found!"
    echo -n $WHITE
    exit 1
fi

# Show target information
echo -n $PURPLE
$SHOW "message22" 2>&1  # "Backup media found:"
echo -n $WHITE

# Get disk space info
if command -v df >/dev/null; then
    # Try human-readable format first
    SIZE_INFO=$(df -h "$TARGET" | tail -n 1)
    if [ -n "$SIZE_INFO" ]; then
        TOTAL_SIZE=$(echo "$SIZE_INFO" | awk '{print $2}')
        FREE_SIZE=$(echo "$SIZE_INFO" | awk '{print $4}')
        echo -n " -> $TARGET ($TOTAL_SIZE, "
        echo -n $WHITE
        $SHOW "message16"  # "free"
        echo -n $PURPLE
        echo "$FREE_SIZE)"
    else
        # Fallback to block size
        SIZE_INFO=$(df -k "$TARGET" | tail -n 1)
        TOTAL_BLOCKS=$(echo "$SIZE_INFO" | awk '{print $2}')
        FREE_BLOCKS=$(echo "$SIZE_INFO" | awk '{print $4}')
        TOTAL_SIZE=$((TOTAL_BLOCKS / 1024))M
        FREE_SIZE=$((FREE_BLOCKS / 1024))M
        echo -n " -> $TARGET (~${TOTAL_SIZE}MB, "
        echo -n $WHITE
        $SHOW "message16"  # "free"
        echo -n $PURPLE
        echo "${FREE_SIZE}MB)"
    fi
else
    echo " -> $TARGET"
fi

echo -n $WHITE

# Check available space
if command -v df >/dev/null; then
    FREE_KB=$(df -k "$TARGET" | awk 'NR>1 {print $4}')
    if [ -z "$FREE_KB" ] || [ "$FREE_KB" -lt "$NEEDEDSPACE" ]; then
        echo -n $RED
        $SHOW "message30"  # "There is not enough space available on"
        echo -n "$TARGET"
        $SHOW "message31"  # "Only"
        printf '%5s' "$((FREE_KB / 1024))"
        $SHOW "message32"  # "MB available, but"
        printf '%5s' "$((NEEDEDSPACE / 1024))"
        $SHOW "message33"  # "MB are needed. Please free some space."
        echo " "
        $SHOW "message34"  # "and try again."
        echo -n $WHITE
        exit 1
    fi
fi
# Execute backup script
BACKUP_SCRIPT="$LIBDIR/enigma2/python/Plugins/Extensions/BackupSuite/scripts/backupsuite.sh"
if [ -x "$BACKUP_SCRIPT" ]; then
    # Ensure executable
    chmod 755 "$BACKUP_SCRIPT" >/dev/null 2>&1

    # Run backup
    "$BACKUP_SCRIPT" "$TARGET"
    ret=$?
    sync

    if [ $ret -eq 0 ]; then
        echo -n $GREEN
        $SHOW "message48" 2>&1  # Backup completed successfully!
    else
        echo -n $RED
        $SHOW "message15" 2>&1  # Image creation FAILED!
    fi
else
    echo -n $RED
    $SHOW "message05" 2>&1  # Backup script not found!
    ret=1
fi

echo -n $WHITE
exit ${ret:-0}
