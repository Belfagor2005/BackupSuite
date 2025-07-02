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
if tty > /dev/null ; then
    RED='\e[00;31m'    # Errors/failures
    GREEN='\e[00;32m'  # Success/positive messages
    YELLOW='\e[01;33m' # Warnings/important info
    BLUE='\e[01;34m'   # Phase headers
    PURPLE='\e[01;31m' # Titles/model info
    WHITE='\e[00;37m'  # Normal text
else
    RED='\c00??0000'
    GREEN='\c0000??00'
    YELLOW='\c00????00'
    BLUE='\c0000????'
    PURPLE='\c00?:55>7'
    WHITE='\c00??????'
fi

# ===================== TITLE BLOCK ==========================================
LINE="------------------------------------------------------------"
echo -n "$YELLOW"
echo "$LINE"
echo -n "$PURPLE"
echo "***   UNIVERSAL BACKUP SUITE FOR ENIGMA2/OPENVISION    ***"
echo "*** https://github.com/persianpros/BackupSuite-PLi ***"
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

# ===================== PARAMETER HANDLING ===================================
LANG="$1"
DEVICE_TYPE="${2:-auto}"
MEDIA="$3"

# ===================== MEDIA DETECTION ======================================
detect_media() {
    echo -n "$BLUE"
    echo "Detecting backup media..."

    # Check if media was provided
    if [ -n "$MEDIA" ]; then
        echo "Using provided media: $MEDIA"
        return
    fi

    # Potential media locations
    candidates="/mmc /media/hdd /media/usb /media/mmc /mnt/usb /mnt/mmc"

    for candidate in $candidates; do
        [ ! -d "$candidate" ] && continue
        
        # Dreambox UBIFS check
        if [ "$candidate" = "/mmc" ]; then
            if df -h /mmc | grep -q "ubi0:rootfs"; then
                echo "Skipping UBIFS rootfs at /mmc"
                continue
            fi
        fi

        # Check write permission
        if ! touch "$candidate/bs_testfile" 2>/dev/null; then
            echo "No write permission: $candidate"
            continue
        fi
        rm -f "$candidate/bs_testfile"

        # Check available space
        free_kb=$(df -k "$candidate" | tail -1 | awk '{print $4}')
        free_mb=$((free_kb / 1024))
        
        if [ $free_mb -lt 300 ]; then
            echo "Insufficient space: ${free_mb}MB in $candidate"
            continue
        fi

        MEDIA="$candidate"
        echo -n "$GREEN"
        echo "Selected media: $MEDIA (${free_mb}MB free)"
        echo -n "$WHITE"
        return
    done

    echo -n "$RED"
    echo "ERROR: No suitable backup media found!"
    echo -n "$WHITE"
    exit 1
}

# ===================== KERNEL DETECTION =====================================
find_kernel_partition() {
    # Try /boot mount first
    KERNEL_PARTITION=$(grep -w "/boot" /proc/mounts | awk '{print $1}')
    [ -n "$KERNEL_PARTITION" ] && return

    # Try root partition deduction
    ROOT_PARTITION=$(grep -w "/" /proc/mounts | awk '{print $1}')
    if [ -n "$ROOT_PARTITION" ]; then
        case $ROOT_PARTITION in
            /dev/mmcblk*)
                KERNEL_PARTITION="${ROOT_PARTITION%p*}"
                ;;
            /dev/sd*)
                KERNEL_PARTITION="${ROOT_PARTITION%[0-9]*}"
                ;;
            ubi*)
                # Dreambox UBIFS handling
                for mtd in /sys/class/mtd/mtd*; do
                    [ ! -d "$mtd" ] && continue
                    name=$(cat "$mtd/name" 2>/dev/null)
                    case $name in
                        kernel|Kernel|uImage)
                            mtdnum=${mtd##*mtd}
                            KERNEL_PARTITION="/dev/mtdblock$mtdnum"
                            return
                            ;;
                    esac
                done
                ;;
        esac
    fi

    # Final fallback
    KERNEL_PARTITION=$(ls /dev/mmcblk* /dev/mtdblock* 2>/dev/null | head -1)
}

# ===================== BACKUP PROCESS =======================================
perform_backup() {
    # Create temp directory
    echo -n "$BLUE"
    echo "Creating temporary workspace..."
    TMP_DIR="/tmp/backup_$$"
    mkdir -p "$TMP_DIR" || {
        echo -n "$RED"
        echo "ERROR: Cannot create temp directory!"
        exit 1
    }

    # Backup kernel
    echo -n "$BLUE"
    echo "Backing up kernel partition..."
    find_kernel_partition
    if [ -n "$KERNEL_PARTITION" ] && [ -e "$KERNEL_PARTITION" ]; then
        dd if="$KERNEL_PARTITION" of="$TMP_DIR/kernel.bin" bs=4k 2>/dev/null
        echo "Kernel backup: $KERNEL_PARTITION"
    else
        echo -n "$YELLOW"
        echo "WARNING: Kernel partition not found, skipping"
    fi

    # Backup root filesystem
    echo -n "$GREEN"
    echo "Backing up root filesystem..."
    tar -C / -cpf "$TMP_DIR/rootfs.tar" \
        --exclude='./proc/*' \
        --exclude='./sys/*' \
        --exclude='./dev/*' \
        --exclude='./tmp/*' \
        --exclude='./media/*' \
        --exclude='./run/*' \
        --exclude='./mnt/*' \
        --exclude='./var/volatile/*' \
        --exclude='./var/lib/opkg/lists/*' \
        --exclude='./var/cache/*' \
        --exclude="$TMP_DIR" . 2>/dev/null

    # Create final archive
    echo -n "$GREEN"
    echo "Creating compressed archive..."
    MODEL=$(grep -i "model" /proc/cpuinfo | head -1 | cut -d: -f2 | tr -d ' ' || uname -m)
    TIMESTAMP=$(date +%Y%m%d_%H%M)
    ZIP_FILE="$MEDIA/backup_${MODEL}_${TIMESTAMP}.zip"

    if command -v zip >/dev/null; then
        (cd "$TMP_DIR" && zip -qr "$ZIP_FILE" ./*)
        ZIP_SIZE=$(du -h "$ZIP_FILE" | cut -f1)
        echo "Backup created: $ZIP_FILE (${ZIP_SIZE})"
    else
        echo -n "$YELLOW"
        echo "WARNING: zip not available, using tar.gz"
        tar -czf "$ZIP_FILE.tar.gz" -C "$TMP_DIR" .
        ZIP_SIZE=$(du -h "$ZIP_FILE.tar.gz" | cut -f1)
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
}

# ===================== MAIN EXECUTION =======================================
detect_media
perform_backup
exit 0