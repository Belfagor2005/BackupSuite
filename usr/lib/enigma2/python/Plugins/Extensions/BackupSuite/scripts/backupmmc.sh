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
if command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
elif command -v python2 >/dev/null 2>&1; then
    PYTHON="python2"
elif command -v python >/dev/null 2>&1; then
    PYTHON="python"
else
    echo -n "$RED"
    echo "Unable to find Python!" >&2
    echo -n "$WHITE"
    exit 1
fi

# Get Python version and set extension
PYVERSION=$($PYTHON -V 2>&1 | awk '{print $2}' | cut -d '.' -f 1)
if [ "$PYVERSION" = "3" ]; then
    PYEXT="pyc"
elif [ "$PYVERSION" = "2" ]; then
    PYEXT="pyo"
else
    echo -n "$RED"
    echo "Unsupported Python version: $PYVERSION" >&2
    echo -n "$WHITE"
    exit 1
fi
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

# ====================== INITIALIZATION (BLUE) ==============================
echo -n "$YELLOW"
echo "$LINE"
echo -n "$BLUE"
# Library directory detection
if [ -d "/usr/lib64" ]; then
    LIBDIR="/usr/lib64"
else
    LIBDIR="/usr/lib"
fi

# Set language and show messages
export LANG="$1"
MESSAGE_SCRIPT="$LIBDIR/enigma2/python/Plugins/Extensions/BackupSuite/message.$PYEXT"
if [ ! -f "$MESSAGE_SCRIPT" ]; then
    # Fallback to .py if compiled version not found
    MESSAGE_SCRIPT="$LIBDIR/enigma2/python/Plugins/Extensions/BackupSuite/message.py"
    if [ ! -f "$MESSAGE_SCRIPT" ]; then
        echo -n "$RED"
        echo "Message script not found!" >&2
        echo -n "$WHITE"
        exit 1
    fi
fi

export SHOW="$PYTHON $MESSAGE_SCRIPT $LANG"

# Device type detection
case "$2" in
    "HDD") export HARDDISK=1 ;;
    "USB") export HARDDISK=0 ;;
    "MMC") export HARDDISK=0 ;;
    *)     export HARDDISK=0 ;;
esac
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

# ====================== DEVICE DETECTION (BLUE) =============================
echo -n "$YELLOW"
echo "$LINE"
echo -n "$BLUE"
# Portable function to get disk space
get_disk_space() {
    local media="$1"
    if command -v df >/dev/null; then
        # Use 1K blocks for consistency
        df -k "$media" 2>/dev/null | awk 'NR==2 {print $2, $4}'
    else
        echo "0 0"
    fi
}

# Convert KB to GB
kb_to_gb() {
    local kb="$1"
    echo $((kb / 1048576))
}
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

# ===================== DEVICE INFORMATION (PURPLE) =========================
echo -n "$YELLOW"
echo "$LINE"
echo -n "$PURPLE"
# Show backup destination message
$SHOW "message43"       # "Full back-up to the MultiMediaCard"

# Initialize variables
MEDIA=""
MINIMUM=33              # avoid all sizes below 33GB

# Check MMC availability
if mountpoint -q /mmc; then
    # Test write access
    if touch /mmc/backup_test.$$ >/dev/null 2>&1; then
        rm -f /mmc/backup_test.$$
        read TOTAL_KB FREE_KB <<< $(get_disk_space /mmc)
        if [ -n "$TOTAL_KB" ] && [ "$TOTAL_KB" -gt 0 ]; then
            TOTAL_GB=$(kb_to_gb "$TOTAL_KB")
            FREE_GB=$(kb_to_gb "$FREE_KB")
            if [ "$TOTAL_GB" -ge "$MINIMUM" ]; then
                MEDIA="/mmc"
                echo -n " -> /mmc (${TOTAL_GB}GB, "
                $SHOW "message16"  # Free
                echo "${FREE_GB}GB)"
            fi
        fi
    fi
fi

# If MMC not available, find other media
if [ -z "$MEDIA" ]; then
    # Try other potential media locations
    for candidate in /media/mmc /media/usb /media/hdd /mmc; do
        if [ -d "$candidate" ] && touch "$candidate/backup_test.$$" >/dev/null 2>&1; then
            rm -f "$candidate/backup_test.$$"
            read TOTAL_KB FREE_KB <<< $(get_disk_space "$candidate")
            if [ -n "$TOTAL_KB" ] && [ "$TOTAL_KB" -gt 0 ]; then
                TOTAL_GB=$(kb_to_gb "$TOTAL_KB")
                FREE_GB=$(kb_to_gb "$FREE_KB")
                if [ "$TOTAL_GB" -ge "$MINIMUM" ]; then
                    MEDIA="$candidate"
                    echo -n " -> $candidate (${TOTAL_GB}GB, "
                    $SHOW "message16"  # Free
                    echo "${FREE_GB}GB)"
                    break
                fi
            fi
        fi
    done
fi
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

# ======================== ERROR HANDLING (RED) =============================
echo -n "$YELLOW"
echo "$LINE"
echo -n "$RED"
# Exit if no suitable media found
if [ -z "$MEDIA" ]; then
    $SHOW "message15"  # "No suitable media found"
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
$SHOW "message45" 2>&1  # Phase 1/3: Preparing backup environment
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
    chmod 755 "$BACKUP_SCRIPT" >/dev/null 2>&1
    "$BACKUP_SCRIPT" "$MEDIA"
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