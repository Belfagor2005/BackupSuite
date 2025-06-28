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

# Portable function to get disk space info
get_disk_space() {
    local path="$1"
    if command -v df >/dev/null; then
        # Try human-readable format
        SIZE_INFO=$(df -h "$path" 2>/dev/null | tail -n 1)
        if [ -n "$SIZE_INFO" ]; then
            # Handle different df output formats
            if echo "$SIZE_INFO" | grep -q '^/dev/'; then
                # Format: /dev/root  Size Used Avail Use% Mounted
                TOTAL=$(echo "$SIZE_INFO" | awk '{print $2}')
                FREE=$(echo "$SIZE_INFO" | awk '{print $4}')
                MOUNT=$(echo "$SIZE_INFO" | awk '{print $6}')
            else
                # Format: Size Used Avail Use% Mounted
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

# Find HDD target
HDD_TARGET=$(find_hdd_target)

if [ -n "$HDD_TARGET" ]; then
    # Get disk space info
    read TOTALSIZE FREESIZE MEDIA <<< $(get_disk_space "$HDD_TARGET")
    
    # Show disk info
    echo -n " -> $HDD_TARGET ($TOTALSIZE, "
    $SHOW "message16"
    echo "$FREESIZE)"
    
    # Execute backup script
    BACKUP_SCRIPT="$LIBDIR/enigma2/python/Plugins/Extensions/BackupSuite/scripts/backupdmm.sh"
    if [ -f "$BACKUP_SCRIPT" ]; then
        # Ensure executable
        chmod 755 "$BACKUP_SCRIPT" >/dev/null 2>&1
        
        # Run backup
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
