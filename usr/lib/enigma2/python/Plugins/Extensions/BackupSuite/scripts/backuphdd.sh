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
export SHOW="$PYTHON $(find_message_script) $LANG"

# Device type detection
case "${2:-HDD}" in
    "HDD") export HARDDISK=1 ;;
    "USB") export HARDDISK=0 ;;
    "MMC") export HARDDISK=0 ;;
    *)     export HARDDISK=1 ;;  # Default to HDD
esac

# Show backup destination message
echo -n $YELLOW
$SHOW "message20" 2>&1  # "Full back-up to the harddisk"
echo -n $WHITE

# Portable HDD detection and validation
detect_hdd() {
    # Check common HDD mount points
    local candidates="/hdd /media/hdd /media/usb/hdd /mnt/hdd"
    for path in $candidates; do
        if [ -d "$path" ] && mountpoint -q "$path" 2>/dev/null; then
            # Test write access
            if touch "$path/hdd_test.$$" 2>/dev/null; then
                rm -f "$path/hdd_test.$$"
                echo "$path"
                return 0
            fi
        fi
    done
    
    # Check mounted devices
    grep '^/dev/' /proc/mounts | while read -r dev mountpoint fstype _; do
        case "$fstype" in
            ext*|ntfs|vfat|btrfs|xfs)
                if touch "$mountpoint/hdd_test.$$" 2>/dev/null; then
                    rm -f "$mountpoint/hdd_test.$$"
                    echo "$mountpoint"
                    return 0
                fi
                ;;
        esac
    done
    
    # No valid HDD found
    return 1
}

# Get disk space info in portable way
get_disk_space() {
    local path="$1"
    if command -v df >/dev/null; then
        # Try human-readable format first
        df -h "$path" 2>/dev/null | awk 'NR>1 {print $2, $4, $6}'
    else
        # Fallback to parsing /proc/mounts
        echo "?? ?? unknown"
    fi
}

# Find HDD target
HDD_TARGET=$(detect_hdd)

if [ -n "$HDD_TARGET" ]; then
    # Get disk space info
    read TOTALSIZE FREESIZE MEDIA <<< $(get_disk_space "$HDD_TARGET")
    
    # Show disk info
    echo -n " -> $HDD_TARGET ($TOTALSIZE, "
    $SHOW "message16"
    echo "$FREESIZE)"
    
    # Execute backup script
    BACKUP_SCRIPT="$LIBDIR/enigma2/python/Plugins/Extensions/BackupSuite/scripts/backupsuite.sh"
    if [ -x "$BACKUP_SCRIPT" ]; then
        chmod 755 "$BACKUP_SCRIPT" >/dev/null 2>&1
        "$BACKUP_SCRIPT" "$HDD_TARGET"
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
else
    echo -n $RED
    $SHOW "message15" 2>&1  # No suitable media found!
    ret=1
fi

echo -n $WHITE
exit $ret
