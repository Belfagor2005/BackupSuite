#!/bin/sh

###############################################################################
#          THIS BACKUP IS CREATED WITH THE BACKUPSUITE PLUGIN                 #
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

# Open Vision version detection
mkdir -p /tmp/test >/dev/null 2>&1
if ls -1 /tmp/test >/dev/null 2>&1; then
    VISIONVERSION="7"
else
    VISIONVERSION="9"
fi

# Standard ls options
LS_OPTIONS="-1rSh"
if ! ls $LS_OPTIONS / >/dev/null 2>&1; then
    LS_OPTIONS="-lSr"
fi

# Improved Python detection
find_python() {
    for py in python3 python2 python; do
        if command -v $py >/dev/null; then
            echo $py
            return
        fi
    done
    echo "python"  # Fallback
}

PYTHON_BIN=$(find_python)
PY_EXT=$($PYTHON_BIN -c "import sys; print('pyc' if sys.version_info[0] == 3 else 'pyo')" 2>/dev/null || echo "py")

# Python module name
PYNAME="message"

# Python file path
PYBASE="$LIBDIR/enigma2/python/Plugins/Extensions/BackupSuite"
LANG="$1"

# Fallback to .py if .pyc doesn't exist
if [ -f "$PYBASE/$PYNAME.$PY_EXT" ]; then
    SHOW="$PYTHON_BIN $PYBASE/$PYNAME.$PY_EXT $LANG"
elif [ -f "$PYBASE/$PYNAME.py" ]; then
    SHOW="$PYTHON_BIN $PYBASE/$PYNAME.py $LANG"
else
    echo -n "$RED"
    echo "Neither $PYBASE/$PYNAME.$PY_EXT nor .py found!" >&2
    echo -n "$WHITE"
    exit 1
fi

export SHOW
# echo -n "$YELLOW"
# echo "$LINE"
# echo -n "$WHITE"

# ====================== INITIALIZATION (BLUE) ==============================
echo -n "$YELLOW"
echo "$LINE"
echo -n "$BLUE"
# Dynamic HARDDISK setting based on device type
if [ "$2" = "HDD" ]; then
    export HARDDISK=1
elif [ "$2" = "USB" ]; then
    export HARDDISK=0
elif [ "$2" = "MMC" ]; then
    export HARDDISK=0
else
    export HARDDISK=0
fi

echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

# ====================== DEVICE DETECTION (BLUE) =============================
# echo -n "$YELLOW"
# echo "$LINE"
# echo -n "$BLUE"
## ADD A POSTRM ROUTINE TO ENSURE A CLEAN UNINSTALL
POSTRM="/var/lib/opkg/info/enigma2-plugin-extensions-backupsuite.postrm"
if [ ! -f $POSTRM ] ; then
    echo "#!/bin/sh" > "$POSTRM"
    echo "rm -rf $LIBDIR/enigma2/python/Plugins/Extensions/BackupSuite" >> "$POSTRM"
    echo 'echo "Plugin removed!"' >> "$POSTRM"
    echo "exit 0" >> "$POSTRM"
    chmod 755 "$POSTRM"
fi
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

###################### FIRST DEFINE SOME PROGRAM BLOCKS #######################
############################# START LOGGING ###################################
log()
{
echo "$*" >> $LOGFILE
}
########################## DEFINE CLEAN-UP ROUTINE ############################
clean_up()
{
umount /tmp/bi/root > /dev/null 2>&1
rmdir /tmp/bi/root > /dev/null 2>&1
rmdir /tmp/bi > /dev/null 2>&1
rm -rf "$WORKDIR" > /dev/null 2>&1
}
###################### BIG OOPS!, HOLY SH... (SHELL SCRIPT :-))################
big_fail()
{
if [ -d $WORKDIR ] ; then
    log "FAIL!"
    log "Content so far of the working directory $WORKDIR "
    ls $LS_OPTIONS $WORKDIR >> $LOGFILE
fi
clean_up
echo -n "$RED"
$SHOW "message15" 2>&1 | tee -a $LOGFILE # Image creation FAILED!
echo -n "$WHITE"
exit 0
}
############################ DEFINE IMAGE_VERSION #############################
image_version()
{
echo "Back-up = $BACKUPDATE"
echo "Version = $IMVER"
echo "Flashed = $FLASHED"
echo "Updated = $LASTUPDATE"
echo -n "Drivers = "
opkg list-installed | grep dvb-modules
echo "Enigma2 = $ENIGMA2DATE"
echo
echo $LINE
}
#################### CLEAN UP AND MAKE DESTINATION FOLDERS ####################
make_folders()
{
rm -rf "$MAINDEST"
log "Removed directory  = $MAINDEST"
mkdir -p "$MAINDEST"
log "Created directory  = $MAINDEST"
}
################ CHECK FOR THE NEEDED BINARIES IF THEY EXIST ##################
checkbinary()
{
if [ ! -f "$1" ] ; then {
    echo -n "$1 " ; $SHOW "message05"
    } 2>&1 | tee -a $LOGFILE
    big_fail
elif [ ! -x "$1" ] ; then
    {
    echo "Error: $1 " ; $SHOW "message35"
    } 2>&1 | tee -a $LOGFILE
    big_fail
fi
}
################### BACK-UP MADE AND REPORTING SIZE ETC. ######################
backup_made()
{
{
echo $LINE
$SHOW "message10" ; echo "$MAINDEST"     # USB Image created in:
$SHOW "message23"        # "The content of the folder is:"
ls $LS_OPTIONS "$MAINDEST" | awk '{print $5, $9}'
echo $LINE
if  [ $HARDDISK != 1 ]; then
    $SHOW "message11" ; echo "$EXTRA"        # and there is made an extra copy in:
    echo $LINE
fi
} 2>&1 | tee -a $LOGFILE
}
############################## END PROGRAM BLOCKS #############################
########################## DECLARATION OF VARIABLES ###########################
BACKUPDATE=`date +%Y.%m.%d_%H:%M`
DATE=`date +%Y%m%d_%H%M`
if [ -f "$LIBDIR/enigma2/python/Plugins/Extensions/BackupSuite/speed.txt" ] ; then
    ESTSPEED=`cat $LIBDIR/enigma2/python/Plugins/Extensions/BackupSuite/speed.txt`
    if [ $ESTSPEED -lt 50 ] ; then
        ESTSPEED="250"
    fi
else
    ESTSPEED="250"
fi
FLASHED=`date -r /etc/version +%Y.%m.%d_%H:%M`
ISSUE=`cat /etc/issue | grep . | tail -n 1 `
IMVER=${ISSUE%?????}
LASTUPDATE=`date -r /var/lib/opkg/status +%Y.%m.%d_%H:%M`
ENIGMA2DATE=`cat /tmp/enigma2version`
LOGFILE=/tmp/BackupSuite.log
MEDIA="$1"
MKFS=/usr/sbin/mkfs.ubifs
MTDPLACE=`cat /proc/mtd | grep -w "kernel" | cut -d ":" -f 1`
NANDDUMP=/usr/sbin/nanddump
START=$(date +%s)
if [ -f "/etc/lookuptable.txt" ] ; then
    LOOKUP="/etc/lookuptable.txt"
    $SHOW "message36"
else
    LOOKUP="$LIBDIR/enigma2/python/Plugins/Extensions/BackupSuite/lookuptable.txt"
fi
TARGET="XX"
UBINIZE=/usr/sbin/ubinize
USEDsizebytes=`df -B 1 /usr/ | grep [0-9]% | tr -s " " | cut -d " " -f 3`
USEDsizekb=`df -k /usr/ | grep [0-9]% | tr -s " " | cut -d " " -f 3`
if [ -f "/var/lib/opkg/info/enigma2-plugin-extensions-backupsuite.control" ] ; then
    VERSION="Version: "`cat /var/lib/opkg/info/enigma2-plugin-extensions-backupsuite.control | grep "Version: " | cut -d "+" -f 2`
else
    VERSION=`$SHOW "message37"`
fi
WORKDIR="$MEDIA/bi"

# ====================== DEVICE INFORMATION (PURPLE) =========================
echo -n "$YELLOW"
echo "$LINE"
echo -n "$PURPLE"
# TEST IF RECEIVER IS SUPPORTED AND READ THE VARIABLES FROM THE LOOKUPTABLE #
if [ -f /etc/modules-load.d/dreambox-dvb-modules-dm*.conf ] || [ -f /etc/modules-load.d/10-dreambox-dvb-modules-dm*.conf ] ; then
    log "It's a dreambox! Not compatible with this script."
    exit 1
else
    if [ -f /etc/openvision/model ] ; then
        log "Open Vision detected"
        SEARCH=$( cat /etc/openvision/model )
    else
        log "Not Open Vision, OpenPLi or SatDreamGr maybe?"
        if [ -f /proc/stb/info/hwmodel ] ; then
            SEARCH=$( cat /proc/stb/info/hwmodel | tr "A-Z" "a-z" | tr -d '[:space:]' )
        elif [ -f /proc/stb/info/gbmodel ] ; then
            SEARCH=$( cat /proc/stb/info/gbmodel | tr "A-Z" "a-z" | tr -d '[:space:]' )
        elif [ -f /proc/stb/info/boxtype ] ; then
            if grep H9 /proc/stb/info/boxtype > /dev/null ; then
                SEARCH=$( cat /proc/stb/info/model )
            elif grep H1 /proc/stb/info/boxtype > /dev/null ; then
                SEARCH=$( cat /proc/stb/info/model )
            else
                SEARCH=$( cat /proc/stb/info/boxtype | tr "A-Z" "a-z" | tr -d '[:space:]' )
            fi
        elif [ -f /proc/stb/info/vumodel ] ; then
            SEARCH=$( cat /proc/stb/info/vumodel | tr "A-Z" "a-z" | tr -d '[:space:]' )
        else
            echo -n "$RED"
            $SHOW "message01" 2>&1 | tee -a $LOGFILE # No supported receiver found!
            big_fail
        fi
    fi
fi
cat $LOOKUP | cut -f 2 | grep -qw "$SEARCH"
if [ "$?" = "1" ] ; then
    echo -n "$RED"
    $SHOW "message01" 2>&1 | tee -a $LOGFILE # No supported receiver found!
    big_fail
else
    MODEL=`cat $LOOKUP | grep -w -m1 "$SEARCH" | cut -f 2`
    SHOWNAME=`cat $LOOKUP | grep -w -m1 "$SEARCH" | cut -f 3`
    FOLDER="`cat $LOOKUP | grep -w -m1 "$SEARCH" | cut -f 4`"
    EXTR1="`cat $LOOKUP | grep -w -m1 "$SEARCH" | cut -f 5`/$DATE"
    EXTR2="`cat $LOOKUP | grep -w -m1 "$SEARCH" | cut -f 6`"
    EXTRA="$MEDIA$EXTR1$EXTR2"
    if  [ $HARDDISK = 1 ]; then
        MAINDEST="$MEDIA$EXTR1$FOLDER"
    else
        MAINDEST="$MEDIA$FOLDER"
    fi
    MKUBIFS_ARGS=`cat $LOOKUP | grep -w -m1 "$SEARCH" | cut -f 7`
    UBINIZE_ARGS=`cat $LOOKUP | grep -w -m1 "$SEARCH" | cut -f 8`
    ROOTNAME=`cat $LOOKUP | grep -w -m1 "$SEARCH" | cut -f 9`
    KERNELNAME=`cat $LOOKUP | grep -w -m1 "$SEARCH" | cut -f 10`
    ACTION=`cat $LOOKUP | grep -w -m1 "$SEARCH" | cut -f 11`
    if [ $ROOTNAME = "rootfs.tar.bz2" ] ; then
        MKFS=/bin/tar
        checkbinary $MKFS
        BZIP2=/usr/bin/bzip2
        if [ ! -f "$BZIP2" ] ; then
            echo "$BZIP2 " ; $SHOW "message38"
            opkg update > /dev/null 2>&1
            opkg install bzip2 > /dev/null 2>&1
            checkbinary $MKFS
        fi
    fi
fi
log "Destination        = $MAINDEST"
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

# ==================== BACKUP SIZE ESTIMATION (GREEN) =======================
echo -n "$YELLOW"
echo "$LINE"
echo -n "$GREEN"
############# START TO SHOW SOME INFORMATION ABOUT BRAND & MODEL ##############
echo -n "$SHOWNAME " | tr  a-z A-Z        # Shows the receiver brand and model
$SHOW "message02"            # BACK-UP TOOL FOR MAKING A COMPLETE BACK-UP
echo -n "$BLUE"
log "RECEIVER = $SHOWNAME "
log "MKUBIFS_ARGS = $MKUBIFS_ARGS"
log "UBINIZE_ARGS = $UBINIZE_ARGS"
echo "$VERSION"
echo -n "$WHITE"
############ CALCULATE SIZE, ESTIMATED SPEED AND SHOW IT ON SCREEN ############
echo -n "$GREEN"
$SHOW "message06"     #"Some information about the task:"
echo -n "$WHITE"
if [ $ROOTNAME != "rootfs.tar.bz2" ] ; then
    KERNELHEX=`cat /proc/mtd | grep -w "kernel" | cut -d " " -f 2` # Kernelsize in Hex
else
    KERNELHEX=800000 # Not the real size (will be added later)
fi
KERNEL=$((0x$KERNELHEX))            # Total Kernel size in bytes
TOTAL=$(($USEDsizebytes+$KERNEL))   # Total ROOTFS + Kernel size in bytes
KILOBYTES=$(($TOTAL/1024))          # Total ROOTFS + Kernel size in KB
MEGABYTES=$(($KILOBYTES/1024))
{
echo -n "KERNEL" ; $SHOW "message04" ; printf '%6s' $(($KERNEL/1024)); echo ' KB'
echo -n "ROOTFS" ; $SHOW "message04" ; printf '%6s' $USEDsizekb; echo ' KB'
echo -n "=TOTAL" ; $SHOW "message04" ; printf '%6s' $KILOBYTES; echo " KB (= $MEGABYTES MB)"
} 2>&1 | tee -a $LOGFILE
if [ $ROOTNAME = "rootfs.tar.bz2" ] ; then
    ESTTIMESEC=$(($KILOBYTES/($ESTSPEED*3)))
else
    ESTTIMESEC=$(($KILOBYTES/$ESTSPEED))
fi
ESTMINUTES=$(( $ESTTIMESEC/60 ))
ESTSECONDS=$(( $ESTTIMESEC-(( 60*$ESTMINUTES ))))

echo -n "$YELLOW"
echo "$LINE"
echo -n "$GREEN"
{
$SHOW "message03"  ; printf "%d.%02d " $ESTMINUTES $ESTSECONDS ; $SHOW "message25" # estimated time in minutes
echo $LINE
} 2>&1 | tee -a $LOGFILE
echo -n "$WHITE"
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

# ========================= SIZE WARNING (RED) ==============================
echo -n "$YELLOW"
echo "$LINE"
echo -n "$RED"
####### WARNING IF THE IMAGE SIZE OF THE XTRENDS GETS TOO BIG TO RESTORE ########
if [ ${MODEL:0:2} = "et" -a ${MODEL:0:3} != "et8" -a ${MODEL:0:3} != "et1" -a ${MODEL:0:3} != "et7" ] ; then
    if [ $MEGABYTES -gt 120 ] ; then
    $SHOW "message28" 2>&1 | tee -a $LOGFILE #Image probably too big to restore
    elif [ $MEGABYTES -gt 110 ] ; then
    $SHOW "message29" 2>&1 | tee -a $LOGFILE #Image between 111 and 120MB could cause problems
    fi
fi
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

# ================ PREPARING WORK ENVIRONMENT (BLUE) ========================
echo -n "$YELLOW"
echo "$LINE"
echo -n "$BLUE"
##################### PREPARING THE BUILDING ENVIRONMENT ######################
log "*** FIRST SOME HOUSEKEEPING ***"
rm -rf "$WORKDIR"        # GETTING RID OF THE OLD REMAINS IF ANY
log "Remove directory   = $WORKDIR"
mkdir -p "$WORKDIR"      # MAKING THE WORKING FOLDER WHERE EVERYTHING HAPPENS
log "Recreate directory = $WORKDIR"
mkdir -p /tmp/bi/root # this is where the complete content will be available
log "Create directory   = /tmp/bi/root"
sync
mount --bind / /tmp/bi/root # the complete root at /tmp/bi/root
## TEMPORARY WORKAROUND TO REMOVE
##      /var/lib/samba/private/msg.sock
## WHICH GIVES AN ERROR MESSAGE WHEN NOT REMOVED
if [ -d /tmp/bi/root/var/lib/samba/private/msg.sock ] ; then
    rm -rf /tmp/bi/root/var/lib/samba/private/msg.sock
fi
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

# ========================== BACKUP START (GREEN) ===========================
echo -n "$YELLOW"
echo "$LINE"
echo -n "$GREEN"
# Inizio del backup - Messaggio di progresso
$SHOW "message44" 2>&1 | tee -a $LOGFILE   # Backup started...
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

# ========================= KERNEL BACKUP (BLUE) ============================
echo -n "$YELLOW"
echo "$LINE"
echo -n "$BLUE"
####################### START THE REAL BACK-UP PROCESS ########################
############################# MAKING UBINIZE.CFG ##############################
if [ $ROOTNAME != "rootfs.tar.bz2" ] ; then
    echo \[ubifs\] > "$WORKDIR/ubinize.cfg"
    echo mode=ubi >> "$WORKDIR/ubinize.cfg"
    echo image="$WORKDIR/root.ubi" >> "$WORKDIR/ubinize.cfg"
    echo vol_id=0 >> "$WORKDIR/ubinize.cfg"
    echo vol_type=dynamic >> "$WORKDIR/ubinize.cfg"
    echo vol_name=rootfs >> "$WORKDIR/ubinize.cfg"
    echo vol_flags=autoresize >> "$WORKDIR/ubinize.cfg"
    log $LINE
    log "UBINIZE.CFG CREATED WITH THE CONTENT:"
    cat "$WORKDIR/ubinize.cfg"  >> $LOGFILE
    touch "$WORKDIR/root.ubi"
    chmod 644 "$WORKDIR/root.ubi"
    log "--------------------------"
fi
############################## MAKING KERNEL DUMP ##############################
log $LINE
echo -n $BLUE
$SHOW "message46" 2>&1 | tee -a $LOGFILE   # Phase 2/3: Creating backup image
echo -n $GREEN
$SHOW "message51" 2>&1 | tee -a $LOGFILE   # Dumping kernel (25%)
$SHOW "message07" 2>&1 | tee -a $LOGFILE   # Create: kernel dump
echo -n $WHITE
if [ $ROOTNAME != "rootfs.tar.bz2" -o $SEARCH = "h9" -o $SEARCH = "i55plus" -o $SEARCH = "i55se" -o $SEARCH = "hzero" -o $SEARCH = "h8" -o $SEARCH = "h8.2h" -o $SEARCH = "h9.s" -o $SEARCH = "h9.t" -o $SEARCH = "h9.2h" -o $SEARCH = "h9.2s" ] ; then
    log "Kernel resides on $MTDPLACE"                     # Just for testing purposes
    $NANDDUMP /dev/$MTDPLACE -qf "$WORKDIR/$KERNELNAME"
    if [ -f "$WORKDIR/$KERNELNAME" ] ; then
        echo -n "Kernel dumped  :"  >> $LOGFILE
        ls $LS_OPTIONS "$WORKDIR/$KERNELNAME" | awk 'END{print $9}' >> $LOGFILE
    else
        log "$WORKDIR/$KERNELNAME NOT FOUND"
        big_fail
    fi
    log "--------------------------"
else
    if [ $SEARCH = "solo4k" -o $SEARCH = "vusolo4k" -o $SEARCH = "ultimo4k" -o $SEARCH = "vuultimo4k" -o $SEARCH = "uno4k" -o $SEARCH = "vuuno4k" -o $SEARCH = "uno4kse" -o $SEARCH = "vuuno4kse" -o $SEARCH = "lunix3-4k" -o $SEARCH = "lunix4k" -o $SEARCH = "galaxy4k" ] ; then
        dd if=/dev/mmcblk0p1 of=$WORKDIR/$KERNELNAME
        log "Kernel resides on /dev/mmcblk0p1"
    elif [ $SEARCH = "h7" -o $SEARCH = "h17" -o $SEARCH = "hd51" -o $SEARCH = "vs1500" -o $SEARCH = "e4hd" ] ; then
        dd if=/dev/mmcblk0p2 of=$WORKDIR/$KERNELNAME
        log "Kernel resides on /dev/mmcblk0p2"
    elif [ $SEARCH = "osmini4k" -o $SEARCH = "osmio4k" -o $SEARCH = "osmio4kplus" ] ; then
        dd if=/dev/mmcblk1p2 of=$WORKDIR/$KERNELNAME
        log "Kernel resides on /dev/mmcblk0p2"
    elif [ $SEARCH = "sf4008" -o $SEARCH = "et11000" ] ; then
        dd if=/dev/mmcblk0p3 of=$WORKDIR/$KERNELNAME
        log "Kernel resides on /dev/mmcblk0p3"
    elif [ $SEARCH = "zero4k" -o $SEARCH = "vuzero4k" -o $SEARCH = "gbquad4k" -o $SEARCH = "gbue4k" -o $SEARCH = "gbx34k" ] ; then
        dd if=/dev/mmcblk0p4 of=$WORKDIR/$KERNELNAME
        log "Kernel resides on /dev/mmcblk0p4"
    elif [ $SEARCH = "duo4k" -o $SEARCH = "vuduo4k" -o $SEARCH = "duo4kse" -o $SEARCH = "vuduo4kse" ] ; then
        dd if=/dev/mmcblk0p6 of=$WORKDIR/$KERNELNAME
        log "Kernel resides on /dev/mmcblk0p6"
    elif [ $SEARCH = "sf8008" -o $SEARCH = "sf8008m" -o $SEARCH = "ustym4kpro" -o $SEARCH = "ustym4ks2ottx" -o $SEARCH = "gbtrio4k" -o $SEARCH = "gbip4k" -o $SEARCH = "viper4k" -o $SEARCH = "beyonwizv2" ] ; then
        dd if=/dev/mmcblk0p12 of=$WORKDIR/$KERNELNAME
        log "Kernel resides on /dev/mmcblk0p12"
    elif [ $SEARCH = "hd60" -o $SEARCH = "hd61" -o $SEARCH = "hd66se" -o $SEARCH = "h9se" -o $SEARCH = "h9combo" -o $SEARCH = "h9twin" -o $SEARCH = "h9combose" -o $SEARCH = "h9twinse" -o $SEARCH = "h10" -o $SEARCH = "h11" -o $SEARCH = "pulse4k" -o $SEARCH = "pulse4kmini" -o $SEARCH = "multibox" -o $SEARCH = "multiboxse" -o $SEARCH = "dual" -o $SEARCH = "sx88v2" ] ; then
        $LIBDIR/enigma2/python/Plugins/Extensions/BackupSuite/findkerneldevice.sh
        KERNEL=`readlink -n /dev/kernel`
        log "Kernel resides on $KERNEL"
        dd if=/dev/kernel of=$WORKDIR/$KERNELNAME > /dev/null 2>&1
    else
        $PYTHON_BIN $LIBDIR/enigma2/python/Plugins/Extensions/BackupSuite/findkerneldevice.$PY_EXT
        KERNEL=`cat /sys/firmware/devicetree/base/chosen/kerneldev`
        KERNELNAME=${KERNEL:11:7}.bin
        echo "$KERNELNAME = STARTUP_${KERNEL:17:1}"
        log "$KERNELNAME = STARTUP_${KERNEL:17:1}"
        dd if=/dev/kernel of=$WORKDIR/$KERNELNAME > /dev/null 2>&1
    fi
fi
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

# ==================== ROOT FILESYSTEM BACKUP (GREEN) =======================
echo -n "$YELLOW"
echo "$LINE"
echo -n "$GREEN"
#############################  MAKING ROOT.UBI(FS) ############################
echo -n $GREEN
$SHOW "message52" 2>&1 | tee -a $LOGFILE   # Creating root filesystem (50%)
$SHOW "message06a" 2>&1 | tee -a $LOGFILE   # Create: root.ubifs
echo -n $WHITE
log $LINE
if [ $ROOTNAME != "rootfs.tar.bz2" ] ; then
    $MKFS -r /tmp/bi/root -o "$WORKDIR/root.ubi" $MKUBIFS_ARGS
    if [ -f "$WORKDIR/root.ubi" ] ; then
        echo -n "ROOT.UBI MADE  :" >> $LOGFILE
        ls $LS_OPTIONS "$WORKDIR/root.ubi" | awk 'END{print $9}' >> $LOGFILE
        UBISIZE=`cat "$WORKDIR/root.ubi" | wc -c`
        if [ "$UBISIZE" -eq 0 ] ; then
            $SHOW "message39" 2>&1 | tee -a $LOGFILE
            big_fail
        fi
    else
        log "$WORKDIR/root.ubi NOT FOUND"
        big_fail
    fi
    log $LINE
    $SHOW "message53" 2>&1 | tee -a $LOGFILE   # Assembling image (75%)
    echo "Start UBINIZING" >> $LOGFILE
    $UBINIZE -o "$WORKDIR/$ROOTNAME" $UBINIZE_ARGS "$WORKDIR/ubinize.cfg" >/dev/null
    chmod 644 "$WORKDIR/$ROOTNAME"
    if [ -f "$WORKDIR/$ROOTNAME" ] ; then
        echo -n "$ROOTNAME MADE:" >> $LOGFILE
        ls $LS_OPTIONS "$WORKDIR/$ROOTNAME" | awk 'END{print $9}' >> $LOGFILE
    else
        echo "$WORKDIR/$ROOTNAME NOT FOUND"  >> $LOGFILE
        big_fail
    fi
    echo
else
    if [ $VISIONVERSION == "7" ]; then
        $MKFS -cf $WORKDIR/rootfs.tar -C /tmp/bi/root --exclude=/var/nmbd/* .
    else
        $MKFS -cf $WORKDIR/rootfs.tar -C /tmp/bi/root .
    fi
    $BZIP2 $WORKDIR/rootfs.tar
fi
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

# ======================== FINALIZING BACKUP (BLUE) =========================
echo -n "$YELLOW"
echo "$LINE"
echo -n "$BLUE"
############################ ASSEMBLING THE IMAGE #############################
echo -n $BLUE
$SHOW "message47" 2>&1 | tee -a $LOGFILE   # Phase 3/3: Finalizing backup
echo -n $WHITE
make_folders
mv "$WORKDIR/$ROOTNAME" "$MAINDEST/$ROOTNAME"
mv "$WORKDIR/$KERNELNAME" "$MAINDEST/$KERNELNAME"
if [ $ACTION = "noforce" ] ; then
    echo "rename this file to 'force' to force an update without confirmation" > "$MAINDEST/noforce";
elif [ $ACTION = "reboot" ] ; then
    echo "rename this file to 'force.update' to force an update without confirmation" > "$MAINDEST/reboot.update"
elif [ $ACTION = "force" ] ; then
    echo "rename this file to 'force.update' to be able to flash this backup" > "$MAINDEST/noforce.update"
    echo "Rename the file in the folder /vuplus/$SEARCH/noforce.update to /vuplus/$SEARCH/force.update to flash this image"
fi
if [ $SEARCH = "zero4k" -o $SEARCH = "uno4k" -o $SEARCH = "uno4kse" -o $SEARCH = "ultimo4k" -o $SEARCH = "solo4k" -o $SEARCH = "duo4k" -o $SEARCH = "duo4kse" ] ; then
    echo "rename this file to 'mkpart.update' for forces create partition and kernel update." > "$MAINDEST/nomkpart.update"
fi
image_version > "$MAINDEST/imageversion"
if [ $SEARCH = "lunix3-4k" -o $SEARCH = "lunix4k" -o $SEARCH = "galaxy4k" -o $SEARCH = "revo4k" ] ; then
    if [ -f /boot/initrd_run.bin ] ; then
        cp /boot/initrd_run.bin "$MAINDEST/initrd_run.bin"
    fi
fi
if [ $SEARCH = "h9" -o $SEARCH = "h9se" -o $SEARCH = "h9combo" -o $SEARCH = "h9combose" -o $SEARCH = "i55plus" -o $SEARCH = "i55se" -o $SEARCH = "h10" -o $SEARCH = "hzero" -o $SEARCH = "h8" -o $SEARCH = "h8.2h" -o $SEARCH = "h9.s" -o $SEARCH = "h9.t" -o $SEARCH = "h9.2h" -o $SEARCH = "h9.2s" -o $SEARCH = "h9twin" -o $SEARCH = "h9twinse" ] ; then
    log "Zgemma hisilicon found, copying additional files for flashing"
    dd if=/dev/mtd0 of=$MAINDEST/fastboot.bin > /dev/null 2>&1
    dd if=/dev/mtd1 of=$MAINDEST/bootargs.bin > /dev/null 2>&1
    cp -r "$MAINDEST/fastboot.bin" "$MEDIA/zgemma/fastboot.bin" > /dev/null 2>&1
    cp -r "$MAINDEST/bootargs.bin" "$MEDIA/zgemma/bootargs.bin" > /dev/null 2>&1
    dd if=/dev/mtd2 of=$MAINDEST/baseparam.bin > /dev/null 2>&1
    dd if=/dev/mtd3 of=$MAINDEST/pq_param.bin > /dev/null 2>&1
fi
if  [ $HARDDISK != 1 ]; then
    mkdir -p "$EXTRA"
    echo "Created directory  = $EXTRA" >> $LOGFILE
    cp -r "$MAINDEST" "$EXTRA"     #copy the made back-up to images
fi
if [ -f "$MAINDEST/$ROOTNAME" -a -f "$MAINDEST/$KERNELNAME" ] ; then
        backup_made
        $SHOW "message14"             # Instructions on how to restore the image.
        echo $LINE
else
    big_fail
fi
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

# ====================== ZIP ARCHIVE CREATION (GREEN) =======================
echo -n "$YELLOW"
echo "$LINE"
echo -n "$GREEN"

############# CREATE FOLDER imagebackups AND ZIP ARCHIVE ####################
# if ! [ -d $MEDIA/imagebackups ] ; then
    # mkdir -p $MEDIA/imagebackups
# fi
# if [ -d $MEDIA/imagebackups ] ; then
    # ZIP=/usr/bin/zip
    # if [ ! -f "$ZIP" ] ; then
        # opkg update > /dev/null 2>&1
        # opkg install zip > /dev/null 2>&1
        # checkbinary $ZIP
    # fi
    # ISSUE1=`cat /etc/issue | grep . | tail -n 1 | sed -e 's/[\t ]//g;/^$/d'`
    # VER=${ISSUE1%????}
    # $ZIP -r $MEDIA/imagebackups/backup-$VER-$MODEL-$DATE.zip /$MAINDEST/*
# fi

if ! [ -d $MEDIA/imagebackups ] ; then
    mkdir -p $MEDIA/imagebackups
fi
if [ -d $MEDIA/imagebackups ] ; then
    ZIP=/usr/bin/zip
    if [ ! -f "$ZIP" ] ; then
        opkg update > /dev/null 2>&1
        opkg install zip > /dev/null 2>&1
        checkbinary $ZIP
    fi
    ISSUE1=`cat /etc/issue | grep . | tail -n 1 | sed -e 's/[\t ]//g;/^$/d'`
    VER=${ISSUE1%????}
    
    # Check if MODEL is empty, fallback to hostname short name
    if [ -z "$MODEL" ]; then
        MODEL=$(hostname -s 2>/dev/null)
    fi
    if [ -z "$MODEL" ]; then
        MODEL="unknownmodel"
    fi

    $ZIP -r $MEDIA/imagebackups/backup-$VER-$MODEL-$DATE.zip /$MAINDEST/*
fi

echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

# ====================== EXTRA COPY TO USB (GREEN) ==========================
echo -n "$YELLOW"
echo "$LINE"
echo -n "$GREEN"
#################### CHECKING FOR AN EXTRA BACKUP STORAGE #####################
if  [ $HARDDISK = 1 ]; then                     # looking for a valid usb-stick
    for candidate in `cut -d ' ' -f 2 /proc/mounts | grep '^/media/'`
    do
        if [ -f "${candidate}/"*[Bb][Aa][Cc][Kk][Uu][Pp][Ss][Tt][Ii][Cc][Kk]* ]
        then
        TARGET="${candidate}"
        fi
    done
    if [ "$TARGET" != "XX" ] ; then
        echo -n $GREEN
        $SHOW "message17" 2>&1 | tee -a $LOGFILE     # Valid USB-flashdrive detected, making an extra copy
        $SHOW "message54" 2>&1 | tee -a $LOGFILE   # Making extra copy (90%)
        echo $LINE
        TOTALSIZE="$(df -h "$TARGET" | tail -n 1 | awk {'print $2'})"
        FREESIZE="$(df -h "$TARGET" | tail -n 1 | awk {'print $4'})"
        {
        $SHOW "message09" ; echo -n "$TARGET ($TOTALSIZE, " ; $SHOW "message16" ; echo "$FREESIZE)"
        } 2>&1 | tee -a $LOGFILE
        rm -rf "$TARGET$FOLDER"
        mkdir -p "$TARGET$FOLDER"
        cp -r "$MAINDEST/." "$TARGET$FOLDER"
        echo $LINE >> $LOGFILE
        echo "MADE AN EXTRA COPY IN: $TARGET" >> $LOGFILE
        df -h "$TARGET"  >> $LOGFILE
        $SHOW "message19" 2>&1 | tee -a $LOGFILE    # Backup finished and copied to your USB-flashdrive
    else
        $SHOW "message40" >> $LOGFILE
    fi
sync
fi
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

# ==================== CLEANUP AND STATISTICS (GREEN) =======================
echo -n "$YELLOW"
echo "$LINE"
echo -n "$GREEN"
################## CLEANING UP AND REPORTING SOME STATISTICS ##################
echo -n $GREEN
$SHOW "message55" 2>&1 | tee -a $LOGFILE   # Finalizing (95%)
clean_up
$SHOW "message56" 2>&1 | tee -a $LOGFILE   # Backup complete (100%)
echo -n $WHITE
END=$(date +%s)
DIFF=$(( $END - $START ))
MINUTES=$(( $DIFF/60 ))
SECONDS=$(( $DIFF-(( 60*$MINUTES ))))
echo -n $YELLOW
{
$SHOW "message24"  ; printf "%d.%02d " $MINUTES $SECONDS ; $SHOW "message25"
} 2>&1 | tee -a $LOGFILE

# Calculate file sizes (portable method)
ROOTSIZE=$(stat -c%s "$MAINDEST/$ROOTNAME" 2>/dev/null || du -b "$MAINDEST/$ROOTNAME" | awk '{print $1}')
KERNELSIZE=$(stat -c%s "$MAINDEST/$KERNELNAME" 2>/dev/null || du -b "$MAINDEST/$KERNELNAME" | awk '{print $1}')

TOTALSIZE=$((($ROOTSIZE+$KERNELSIZE)/1024))
SPEED=$(( $TOTALSIZE/$DIFF ))
echo $SPEED > $LIBDIR/enigma2/python/Plugins/Extensions/BackupSuite/speed.txt
echo $LINE >> $LOGFILE
# "Back up done with $SPEED KB per second"
{
$SHOW "message26" ; echo -n "$SPEED" ; $SHOW "message27"
} 2>&1 | tee -a $LOGFILE
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

# ======================== PACKAGE LIST (WHITE) =============================
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"
#### ADD A LIST OF THE INSTALLED PACKAGES TO THE BackupSuite.LOG ####
echo $LINE >> $LOGFILE
echo $LINE >> $LOGFILE
$SHOW "message41" >> $LOGFILE
echo "--------------------------------------------" >> $LOGFILE
opkg list-installed >> $LOGFILE
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"

# ======================= FINAL LOG COPY (WHITE) =============================
echo -n "$YELLOW"
echo "$LINE"
echo -n "$WHITE"
######################## COPY LOGFILE TO MAINDESTINATION ######################
echo -n $WHITE
cp $LOGFILE "$MAINDEST"
if  [ $HARDDISK != 1 ]; then
    cp $LOGFILE "$MEDIA$EXTR1"
    mv "$MEDIA$EXTR1$FOLDER"/imageversion "$MEDIA$EXTR1"
else
    mv -f "$MAINDEST"/BackupSuite.log "$MEDIA$EXTR1"
    cp "$MAINDEST"/imageversion "$MEDIA$EXTR1"
fi
if [ "$TARGET" != "XX" ] ; then
    cp $LOGFILE "$TARGET$FOLDER"
fi
exit