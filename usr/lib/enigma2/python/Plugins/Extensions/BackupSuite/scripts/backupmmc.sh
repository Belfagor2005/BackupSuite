#!/bin/sh

###############################################################################
#     FULL BACKUP UYILITY FOR ENIGMA2/OPENVISION, SUPPORTS VARIOUS MODELS     #
#                   MAKES A FULLBACK-UP READY FOR FLASHING.                   #
###############################################################################

# Robust Python detection
PYTHON=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
elif command -v python2 >/dev/null 2>&1; then
    PYTHON="python2"
elif command -v python >/dev/null 2>&1; then
    PYTHON="python"
else
    echo "Unable to find Python!" >&2
    exit 1
fi

# Get Python version and set extension
PYVERSION=$($PYTHON -V 2>&1 | awk '{print $2}')
case "$PYVERSION" in
    2.*) PYEXT="pyo" ;;
    3.*) PYEXT="pyc" ;;
    *)   echo "Unsupported Python version: $PYVERSION" >&2; exit 1 ;;
esac

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

# Set language and show messages
export LANG="$1"
export SHOW="$PYTHON $LIBDIR/enigma2/python/Plugins/Extensions/BackupSuite/message.$PYEXT $LANG"

# Device type detection
case "$2" in
    "HDD") export HARDDISK=1 ;;
    "USB") export HARDDISK=0 ;;
    "MMC") export HARDDISK=0 ;;
    *)     export HARDDISK=0 ;;
esac

# # Show backup start message
# echo -n $GREEN
# $SHOW "message44" 2>&1  # Backup started...
echo -n $WHITE

# Show backup destination message
echo -n $YELLOW
$SHOW "message43"       # "Full back-up to the MultiMediaCard"
echo -n $WHITE

# Initialize variables
FREESIZE_0=0
TOTALSIZE_0=0
MEDIA=0
MINIMUN=33              # avoid all sizes below 33GB
BACKUP_SCRIPT="$LIBDIR/enigma2/python/Plugins/Extensions/BackupSuite/scripts/backupsuite.sh"

# Portable function to get filesystem type
get_fs_type() {
    if command -v lsblk >/dev/null; then
        lsblk -no FSTYPE "$1" 2>/dev/null
    else
        df -T "$1" 2>/dev/null | awk 'NR==2 {print $2}'
    fi
}

# Portable function to get disk space
get_disk_space() {
    local media="$1"
    if command -v stat >/dev/null && command -v df >/dev/null; then
        # Use 1K blocks for consistency
        local total_blocks=$(df -P -k "$media" 2>/dev/null | awk 'NR==2 {print $2}')
        local free_blocks=$(df -P -k "$media" 2>/dev/null | awk 'NR==2 {print $4}')
        
        # Convert to human-readable (GB)
        local total_gb=$((total_blocks / 1048576))
        local free_gb=$((free_blocks / 1048576))
        
        echo "$total_gb $free_gb"
    else
        echo "0 0"
    fi
}

# Check MMC availability
if mountpoint -q /mmc; then
    # Portable MMC check
    if touch /mmc/backup_test.$$ >/dev/null 2>&1; then
        rm -f /mmc/backup_test.$$
        
        # Get disk space
        read TOTALSIZE FREESIZE <<< $(get_disk_space /mmc)
        
        if [ -n "$TOTALSIZE" ] && [ -n "$FREESIZE" ]; then
            MEDIA="/mmc"
            echo -n " -> /mmc ($TOTALSIZE GB, "; $SHOW "message16"; echo "$FREESIZE GB)"
        fi
    fi
fi

# If MMC not available, find other media
if [ "$MEDIA" = "0" ]; then
    # Try other potential media locations
    for candidate in /media/mmc /media/usb /media/hdd /mmc
    do
        if [ -d "$candidate" ] && touch "$candidate/backup_test.$$" >/dev/null 2>&1; then
            rm -f "$candidate/backup_test.$$"
            
            # Get disk space
            read TOTALSIZE FREESIZE <<< $(get_disk_space "$candidate")
            
            if [ -n "$TOTALSIZE" ] && [ "$TOTALSIZE" -gt "$MINIMUN" ]; then
                MEDIA="$candidate"
                echo -n " -> $candidate ($TOTALSIZE GB, "; $SHOW "message16"; echo "$FREESIZE GB)"
                break
            fi
        fi
    done
fi

# Exit if no suitable media found
if [ "$MEDIA" = "0" ]; then
    echo -n $RED
    $SHOW "message15"  # "No suitable media found"
    echo -n $WHITE
    exit 1
fi

# Phase 1: Preparing backup environment
echo -n $BLUE
$SHOW "message45" 2>&1  # Phase 1/3: Preparing backup environment
echo -n $WHITE

# Execute backup script
if [ -x "$BACKUP_SCRIPT" ]; then
    chmod 755 "$BACKUP_SCRIPT" >/dev/null 2>&1
    "$BACKUP_SCRIPT" "$MEDIA"
    ret=$?
else
    echo -n $RED
    $SHOW "message05" 2>&1  # "Backup script not found!"
    echo -n $WHITE
    exit 1
fi

# Show completion message
if [ $ret -eq 0 ]; then
    echo -n $BLUE
    $SHOW "message48" 2>&1  # Backup completed successfully!
else
    echo -n $RED
    $SHOW "message15" 2>&1  # Image creation FAILED!
fi

echo -n $WHITE
exit $ret
