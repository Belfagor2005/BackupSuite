#!/bin/sh

###############################################################################
#     FULL BACKUP UYILITY FOR ENIGMA2/OPENVISION, SUPPORTS VARIOUS MODELS     #
#                   MAKES A FULLBACK-UP READY FOR FLASHING.                   #
###############################################################################

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

# Terminal color setup
if tty >/dev/null 2>&1 ; then
    RED='-e \e[00;31m'
    GREEN='-e \e[00;32m'
    YELLOW='-e \e[01;33m'
    BLUE='-e \e[00;34m'
    PURPLE='-e \e[01;31m'
    WHITE='-e \e[00;37m'
else
    RED='\c00??0000'
    GREEN='\c0000??00'
    YELLOW='\c00????00'
    BLUE='\c0000????'
    PURPLE='\c00?:55>7'
    WHITE='\c00??????'
fi

# Library directory detection
if [ -d "/usr/lib64" ]; then
    LIBDIR="/usr/lib64"
else
    LIBDIR="/usr/lib"
fi

# Find Python and message script
PYTHON=$(detect_python)
MESSAGE_DIR="$LIBDIR/enigma2/python/Plugins/Extensions/BackupSuite"

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

# Show backup destination message
echo -n $YELLOW
$SHOW "message22" 2>&1  # "Backup media found:"
echo -n $WHITE

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
echo -n $YELLOW
$SHOW "message22" 2>&1  # "Backup media found:"

# Get disk space info
if command -v df >/dev/null; then
    # Try human-readable format first
    SIZE_INFO=$(df -h "$TARGET" | tail -n 1)
    if [ -n "$SIZE_INFO" ]; then
        TOTAL_SIZE=$(echo "$SIZE_INFO" | awk '{print $2}')
        FREE_SIZE=$(echo "$SIZE_INFO" | awk '{print $4}')
        echo -n " -> $TARGET ($TOTAL_SIZE, " ; $SHOW "message16" ; echo "$FREE_SIZE)"
    else
        # Fallback to block size
        SIZE_INFO=$(df -k "$TARGET" | tail -n 1)
        TOTAL_BLOCKS=$(echo "$SIZE_INFO" | awk '{print $2}')
        FREE_BLOCKS=$(echo "$SIZE_INFO" | awk '{print $4}')
        TOTAL_SIZE=$((TOTAL_BLOCKS / 1024))M
        FREE_SIZE=$((FREE_BLOCKS / 1024))M
        echo -n " -> $TARGET (~${TOTAL_SIZE}MB, " ; $SHOW "message16" ; echo "${FREE_SIZE}MB)"
    fi
else
    echo " -> $TARGET"
fi

# Check available space
if command -v df >/dev/null; then
    FREE_KB=$(df -k "$TARGET" | awk 'NR>1 {print $4}')
    if [ -z "$FREE_KB" ] || [ "$FREE_KB" -lt "$NEEDEDSPACE" ]; then
        echo -n $RED
        $SHOW "message30" ; echo -n "$TARGET" ; $SHOW "message31"
        printf '%5s' "$((FREE_KB / 1024))" ; $SHOW "message32"  # Available (MB):
        printf '%5s' "$((NEEDEDSPACE / 1024))" ; $SHOW "message33"  # Needed (MB):
        echo " "
        $SHOW "message34"  # Please free space
        echo $WHITE
        exit 1
    fi
fi

# Execute backup script
BACKUP_SCRIPT="$LIBDIR/enigma2/python/Plugins/Extensions/BackupSuite/scripts/backupdmm.sh"
if [ -f "$BACKUP_SCRIPT" ]; then
    # Ensure executable
    chmod 755 "$BACKUP_SCRIPT" >/dev/null 2>&1
    
    # Run backup
    "$BACKUP_SCRIPT" "$TARGET"
    ret=$?
    sync
    
    if [ $ret -eq 0 ]; then
        echo -n $BLUE
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
