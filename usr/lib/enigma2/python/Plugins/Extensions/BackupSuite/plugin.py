# -*- coding: utf-8 -*-

from os import (
    listdir,
    system as os_system,
    popen,
    access,
    W_OK,
    statvfs,
    makedirs
)
from os.path import (
    basename,
    ismount,
    exists,
    isfile,
    join,
    # getmtime
)

from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.FileList import FileList
from Components.MenuList import MenuList
from Components.ScrollLabel import ScrollLabel
from Components.Sources.StaticText import StaticText
from Components.Harddisk import harddiskmanager

from Plugins.Plugin import PluginDescriptor
from enigma import (
    RT_HALIGN_LEFT,
    RT_VALIGN_CENTER,
    eListboxPythonMultiContent,
    gFont,
    getDesktop
)

from Screens.Console import Console
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

from . import _
from .schermen import *  # fallback for to screen..
from .message import *  # fallback for to compile..


# Global constants
VERSION = '3.0-r6'
BACKUP_SCRIPTS = {
    'HDD': "backuphdd.sh",
    'USB': "backupusb.sh",
    'MMC': "backupmmc.sh",
    'NET': "backupnet.sh",
}


LOGFILE = "/tmp/BackupSuite.log"
VERSIONFILE = "imageversion"
ENIGMA2VERSIONFILE = "/tmp/enigma2version"
OFGWRITE_BIN = "/usr/bin/ofgwrite"

# Global variables
autoStartTimer = None
_session = None


class BackupDeviceList(MenuList):
    def __init__(self, list):
        MenuList.__init__(self, list, False, eListboxPythonMultiContent)
        self.l.setFont(0, gFont("Regular", 42))
        self.l.setItemHeight(80)


def getIconPath(icon_name):
    icon_path = resolveFilename(SCOPE_PLUGINS, "Extensions/BackupSuite/img/" + icon_name)
    if exists(icon_path):
        return icon_path
    return resolveFilename(SCOPE_PLUGINS, "Extensions/BackupSuite/img/hdd.png")


def BackupDeviceEntryComponent(device):
    res = [
        device,
        (
            eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST,
            10, 5, 60, 60,
            LoadPixmap(getIconPath(device[1]))
        ),
        (
            eListboxPythonMultiContent.TYPE_TEXT,
            100, 0, 620, 60,
            0, RT_HALIGN_LEFT | RT_VALIGN_CENTER,
            device[0]
        )
    ]
    return res


def get_box_type():
    try:
        from enigma import getBoxType
        return getBoxType().lower()
    except ImportError:
        try:
            from boxbranding import getBoxType
            return getBoxType().lower()
        except ImportError:
            return "unknown"


def is_dual_boot():
    if get_box_type() != "et8500":
        return False
    try:
        with open("/proc/mtd") as f:
            content = f.read()
            return 'rootfs2' in content and 'kernel2' in content
    except:
        return False


def requires_force_mode():
    model = get_box_type()

    return any(x in model for x in [
        'h9', 'h9se', 'h9combo', 'h9combose', 'i55plus',
        'i55se', 'h10', 'hzero', 'h8'
    ])


def get_script_path(device_type):
    base_script = BACKUP_SCRIPTS.get(device_type, "backuphdd.sh")
    box_type = get_box_type()

    if box_type.startswith("dm"):
        script_name = base_script.replace(".sh", "-dmm.sh")
    else:
        script_name = base_script

    script_path = resolveFilename(
        SCOPE_PLUGINS,
        "Extensions/BackupSuite/scripts/" + script_name
    )

    print("[BackupSuite] Using script: " + script_path + " for " + box_type)

    return script_path


def get_skin(type):
    try:
        sz_w = getDesktop(0).size().width()
    except:
        sz_w = 720

    if sz_w >= 1920:
        return globals().get("skin" + type + "fullhd", "")
    elif sz_w >= 1280:
        return globals().get("skin" + type + "hd", "")
    else:
        return globals().get("skin" + type + "sd", "")


def get_backup_files_pattern():
    model = get_box_type()

    if 'dm' in model:
        if 'dm9' in model:
            return r"\.(xz)$"
        elif any(x in model for x in ['dm520', 'dm7080', 'dm820']):
            return r"\.(xz)$"
        else:
            return r"\.(nfi)$"

    elif 'vu' in model:
        if '4k' in model:
            return r"\.(bin|bz2)$"
        elif any(x in model for x in ['vuduo2', 'vusolose', 'vusolo2', 'vuzero']):
            return r"\.(bin|jffs2)$"
        else:
            return r"\.(bin|jffs2)$"

    elif any(x in model for x in ['hd51', 'h7', 'sf4008', 'sf5008', 'sf8008', 'sf8008m', 'vs1500', 'et11000', 'et13000']):
        return r"\.(bin|bz2)$"

    elif any(x in model for x in ['h9', 'h9se', 'h9combo', 'h9combose', 'i55plus', 'i55se', 'h10', 'hzero', 'h8']):
        return r"\.(ubi)$"

    elif any(x in model for x in ['hd60', 'hd61', 'multibox', 'multiboxse', 'multiboxplus']):
        return r"\.(bz2)$"

    elif model.startswith(('et4', 'et5', 'et6', 'et7', 'et8', 'et9', 'et10')):
        return r"\.(bin)$"

    elif 'ebox' in model:
        return r"\.(jffs2)$"

    elif any(x in model for x in ['4k', 'uhd']):
        return r"\.(bz2)$"

    return r"\.(zip|bin|bz2)$"


def get_mounted_network_shares():
    """Detect mounted network shares by reading /proc/mounts"""
    network_shares = []
    try:
        # Read /proc/mounts to find network filesystems
        with open("/proc/mounts", "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) < 3:
                    continue

                device, mountpoint, fstype = parts[0], parts[1], parts[2]

                # Check for network filesystem types
                if fstype.lower() in ("cifs", "nfs", "nfs4", "smbfs"):
                    try:
                        # Get storage information
                        stat = statvfs(mountpoint)
                        free_gb = (stat.f_bavail * stat.f_frsize) / (1024 ** 3)
                        total_gb = (stat.f_blocks * stat.f_frsize) / (1024 ** 3)
                        free_str = "%.2f %s" % (free_gb, _("GB"))
                        total_str = "%.2f %s" % (total_gb, _("GB"))
                    except Exception as e:
                        free_str = total_str = _("Unknown")
                        print('error:', str(e))

                    # Extract server name from device path
                    server_name = device.split("/")[-1].split(":")[0]
                    if not server_name:
                        server_name = mountpoint.split("/")[-1]

                    network_shares.append({
                        "server": server_name,
                        "mountpoint": mountpoint,
                        "freespace": free_str,
                        "totalspace": total_str,
                        "fstype": fstype.upper()
                    })
    except Exception as e:
        print("[BackupSuite] Error reading /proc/mounts: " + str(e))
    return network_shares


def get_available_backup_devices():
    """Detect available backup devices using Enigma2's harddisk manager"""

    devices = []
    mounted_partitions = harddiskmanager.getMountedPartitions()
    for partition in mounted_partitions:
        if not partition.mountpoint or not ismount(partition.mountpoint):
            continue

        try:
            if not access(partition.mountpoint, W_OK):
                continue
        except:
            continue

        device_type = "HDD"  # Default to HDD
        if ("usb" in partition.mountpoint.lower() or
                "stick" in partition.description.lower() or
                partition.device and partition.device.startswith("sd")):
            device_type = "USB"

        elif ("mmc" in partition.mountpoint.lower() or
                "card" in partition.description.lower() or
                partition.device and partition.device.startswith("mmc")):
            device_type = "MMC"

        elif ("net" in partition.mountpoint.lower() or
                "network" in partition.description.lower()):
            device_type = "NET"

        devices.append({
            "path": partition.mountpoint,
            "type": device_type,
            "description": partition.description,
            "free": partition.free(),
            "total": partition.total()
        })

    if access("/", W_OK):
        devices.append({
            "path": "/",
            "type": "FLASH",
            "description": _("Internal Flash"),
            "free": None,
            "total": None
        })

    return devices


def get_lang():
    try:
        from Components.config import config
        lng = config.osd.language.value

        if not lng:
            import os
            lng = os.getenv('LANG', 'en_US.UTF-8')

        if '.' not in lng and '_' in lng:
            lng += '.UTF-8'

        base_lng = lng.split('_')[0] if '_' in lng else lng.split('.')[0]
        base_lng = base_lng[:2] if len(base_lng) > 2 else base_lng

        supported_languages = ['en', 'it', 'de', 'fr', 'es', 'nl', 'pl']
        return base_lng if base_lng in supported_languages else 'en'
    except Exception as e:
        print("[BackupSuite] Language detection error: " + str(e))
        return 'en'


class BackupStart(Screen):
    def __init__(self, session, args=0):
        # self.skin = get_skin("start")
        self.skin = """
        <screen position="center,center" size="700,500" title="Backup Suite">
            <widget name="devicelist" position="0,0" size="700,400" scrollbarMode="showOnDemand" itemHeight='80'/>
            <ePixmap position="20,410" size="35,25" pixmap="skin_default/buttons/red.png" zPosition="1" alphatest="on" />
            <widget source="key_red" render="Label" position="60,410" size="140,25" zPosition="2" font="Regular;20" halign="left" valign="center" transparent="1" />
            <ePixmap position="180,410" size="35,25" pixmap="skin_default/buttons/green.png" zPosition="1" alphatest="on" />
            <widget source="key_green" render="Label" position="220,410" size="140,25" zPosition="2" font="Regular;20" halign="left" valign="center" transparent="1" />
            <ePixmap position="340,410" size="35,25" pixmap="skin_default/buttons/yellow.png" zPosition="1" alphatest="on" />
            <widget source="key_yellow" render="Label" position="380,410" size="140,25" zPosition="2" font="Regular;20" halign="left" valign="center" transparent="1" />
            <ePixmap position="500,410" size="35,25" pixmap="skin_default/buttons/blue.png" zPosition="1" alphatest="on" />
            <widget source="key_blue" render="Label" position="540,410" size="140,25" zPosition="2" font="Regular;20" halign="left" valign="center" transparent="1" />
        </screen>"""

        Screen.__init__(self, session)
        self.session = session
        self.setup_title = _("Make or restore a backup")
        self["key_menu"] = StaticText()
        self["key_red"] = StaticText(_("Close"))
        self["key_green"] = StaticText(_("Backup"))
        self["key_yellow"] = StaticText(_("Restore"))
        self["key_blue"] = StaticText(_("Help"))

        self.devicelist = []
        self["devicelist"] = BackupDeviceList([])
        self["help"] = StaticText()
        self["actions"] = ActionMap(
            ["SetupActions", "ColorActions", "EPGSelectActions", "HelpActions"],
            {
                "red": self.cancel,
                "green": self.startBackup,
                "yellow": self.startRestore,
                "blue": self.showHelp,
                "info": self.keyInfo,
                "cancel": self.cancel,
                "displayHelp": self.show_help,
                "help": self.show_help,
                "ok": self.deviceSelected,
            },
            -1
        )
        self.setTitle(self.setup_title)
        self.onShown.append(self.populateDeviceList)
        self.onLayoutFinish.append(self.setCustomTitle)

    def setCustomTitle(self):
        self.setTitle(_("Backup Suite v%s") % VERSION)

    def check_dependencies(self):
        missing_scripts = []
        for device_type, script_name in BACKUP_SCRIPTS.items():
            script_path = get_script_path(device_type)
            if not exists(script_path):
                missing_scripts.append(basename(script_path))

        if missing_scripts:
            self.session.open(
                MessageBox,
                _("Missing backup scripts: %s\nPlease install the complete package") % ", ".join(missing_scripts),
                MessageBox.TYPE_ERROR
            )

    def populateDeviceList(self):
        # Clear existing list
        self.devicelist = []

        # Get available devices
        try:
            devices = get_available_backup_devices()
        except Exception as e:
            print("[BackupSuite] Error detecting devices: " + str(e))
            devices = []

        # Device type map
        device_types = {
            "HDD": {"name": _("Internal Hard Drive"), "icon": "hdd.png"},
            "USB": {"name": _("USB Storage"), "icon": "usb.png"},
            "MMC": {"name": _("MMC Memory"), "icon": "mmc.png"},
            "FLASH": {"name": _("Internal Flash"), "icon": "flash.png"}
        }

        # Add detected physical devices
        added_types = set()
        for device in devices:
            dev_type = device["type"]
            if dev_type in device_types and dev_type not in added_types:
                label = _("Backup to %s") % device_types[dev_type]["name"]
                self.addDevice(label, device_types[dev_type]["icon"], dev_type)
                added_types.add(dev_type)

        # Always show NET option (user can mount shares)
        self.addDevice(_("Backup to Network Storage"), "network.png", "NET")

        # Add Barry Allen if detected
        if exists("/boot/barryhallen"):
            self.addDevice(_("Barry Allen Multiboot"), "multiboot.png", "BA")

        # Add restore option
        self.addDevice(_("Restore Backup"), "restore.png", "RESTORE")

        self["devicelist"].setList([
            BackupDeviceEntryComponent(entry) for entry in self.devicelist
        ])

    def addDevice(self, description, icon, dev_type):
        # Create list entry with icon and text
        self.devicelist.append((description, icon, dev_type))

    def deviceSelected(self):
        selection = self["devicelist"].getCurrent()
        if selection and isinstance(selection, list) and len(selection) > 0:
            device_tuple = selection[0]
            if isinstance(device_tuple, tuple) and len(device_tuple) >= 3:
                dev_type = device_tuple[2]
                if dev_type == "NET":
                    self.start_net_backup()

                elif dev_type == "RESTORE":
                    self.startRestore()

                else:
                    self.startBackup(dev_type)
            else:
                print("[BackupSuite] Invalid device tuple: " + str(device_tuple))
        else:
            print("[BackupSuite] Invalid selection format")

    def get_mounted_shares(self):
        """Returns a list of mounted network shares"""
        network_shares = []
        try:
            # Read /proc/mounts to get actual mount information
            with open("/proc/mounts", "r") as f:
                mounts = f.readlines()

            for line in mounts:
                parts = line.split()
                if len(parts) < 4:
                    continue

                device, mountpoint, fstype, options = parts[:4]

                # Skip non-network filesystems
                if fstype.lower() not in ("cifs", "nfs", "nfs4", "smbfs"):
                    continue

                # Get storage information
                try:
                    stat = statvfs(mountpoint)
                    free_gb = (stat.f_bavail * stat.f_frsize) / (1024 ** 3)
                    total_gb = (stat.f_blocks * stat.f_frsize) / (1024 ** 3)
                    free_str = "%.2f %s" % (free_gb, _("GB"))
                    total_str = "%.2f %s" % (total_gb, _("GB"))
                except Exception as e:
                    free_str = total_str = _("Unknown")
                    print("[BackupSuite] Error getting space: " + str(e))

                # Get server name from device path
                server_name = device.split("/")[-1].split(":")[0]
                if not server_name:
                    server_name = mountpoint.split("/")[-1]

                network_shares.append({
                    "server": server_name,
                    "mountpoint": mountpoint,
                    "freespace": free_str,
                    "totalspace": total_str,
                    "fstype": fstype.upper()
                })

        except Exception as e:
            print("[BackupSuite] Error getting mounted shares: " + str(e))
        return network_shares

    def get_free_space(self, path):
        """Returns the free space in GB"""
        try:
            df_output = popen("df -BG '" + path + "' | tail -1").read().split()
            return df_output[3] + " GB"
        except:
            return "0 GB"

    def get_total_space(self, path):
        """Returns the total space in GB"""
        try:
            df_output = popen("df -BG '" + path + "' | tail -1").read().split()
            return df_output[1] + " GB"
        except:
            return "0 GB"

    def start_net_backup(self):
        """Start the network backup process"""
        network_shares = get_mounted_network_shares()

        if not network_shares:
            self.session.open(
                MessageBox,
                _("No network shares mounted! Please mount a share first."),
                MessageBox.TYPE_ERROR
            )
            return

        # Create selection menu
        menu = []
        for share in network_shares:
            display_text = share["server"] + " (" + share["fstype"] + ") - " + share["mountpoint"] + "\n"
            display_text += _("Free:") + " " + share["freespace"] + " / " + _("Total:") + " " + share["totalspace"]
            menu.append((display_text, share["mountpoint"]))

        self.session.openWithCallback(
            self.net_share_selected,
            MessageBox,
            _("Select network share for backup:"),
            list=menu
        )

    def open_network_setup(self):
        """Open network mount configuration"""
        try:
            from Screens.NetworkSetup import NetworkAdapterSelection
            self.session.open(NetworkAdapterSelection)
        except ImportError:
            self.session.open(
                MessageBox,
                _("Network configuration not available"),
                MessageBox.TYPE_ERROR
            )

    def net_share_selected(self, selected_path):
        """Callback for share selection"""
        if selected_path:
            # Create backup directory if needed
            backup_dir = join(selected_path, "backup")
            if not exists(backup_dir):
                try:
                    makedirs(backup_dir)
                except Exception as e:
                    self.session.open(
                        MessageBox,
                        _("Could not create backup directory: %s\nError: %s") % (backup_dir, str(e)),
                        MessageBox.TYPE_ERROR
                    )
                    return

            self.execute_backup("NET", backup_dir)

    def startBackup(self, dev_type=None):
        if not dev_type:
            selection = self["devicelist"].getCurrent()
            if selection and isinstance(selection, list) and len(selection) > 0:
                device_tuple = selection[0]
                if isinstance(device_tuple, tuple) and len(device_tuple) >= 3:
                    dev_type = device_tuple[2]

        if dev_type:
            # Get the device name for display
            device_name = {
                "HDD": _("Internal Hard Drive"),
                "USB": _("USB Storage"),
                "MMC": _("Internal Memory"),
                "NET": _("Network Storage"),
                "BA": _("Barry Allen")
            }.get(dev_type, dev_type)

            self.session.openWithCallback(
                lambda result: self.confirmBackup(result, dev_type),
                MessageBox,
                _("Do you want to make a backup to %s?\n\nThis may take several minutes.") % device_name,
                MessageBox.TYPE_YESNO
            )

    def confirmBackup(self, result, dev_type):
        if result:
            self.write_enigma2_version()
            self.execute_backup(dev_type)

    def startRestore(self):
        file_pattern = get_backup_files_pattern()
        self.session.open(FlashImageConfig, '/media/', file_pattern)

    def showHelp(self):
        self.session.open(BackupHelpScreen)

    def show_help(self):
        self.session.open(BackupHelpScreen)

    def flash_image(self):
        file_pattern = get_backup_files_pattern()
        self.session.open(FlashImageConfig, '/media/', file_pattern)

    def cancel(self):
        self.close(False, self.session)

    def keyInfo(self):
        self.session.open(WhatisNewInfo)

    def write_enigma2_version(self):
        try:
            from Components.About import getEnigmaVersionString
            with open(ENIGMA2VERSIONFILE, 'w') as f:
                f.write(getEnigmaVersionString())
        except:
            pass

    def execute_backup(self, device_type, media_path=None):
        print("[BackupSuite] Starting backup for: " + device_type)

        script_path = get_script_path(device_type)
        if not exists(script_path):
            self.session.open(
                MessageBox,
                _("Backup script not found: %s") % basename(script_path),
                MessageBox.TYPE_ERROR
            )
            return

        lang = get_lang()
        title = _("%s Backup") % device_type

        if device_type == "NET":
            if not media_path:
                self.session.open(MessageBox, _("Network path not specified!"), MessageBox.TYPE_ERROR)
                return

            backup_dir = join(media_path, "backup")
            image_dir = join(backup_dir, "image")

            try:
                makedirs(backup_dir, exist_ok=True)
                makedirs(image_dir, exist_ok=True)

                marker_path = join(backup_dir, "backupstick")
                with open(marker_path, "w") as f:
                    f.write("")

            except Exception as e:
                error_msg = _(
                    "Failed to create backup directory:\n"
                    "Path: {}\n"
                    "Error: {}"
                ).format(backup_dir, str(e))

                self.session.open(MessageBox, error_msg, MessageBox.TYPE_ERROR)
                return

            cmd = "chmod +x '" + script_path + "'; '" + script_path + "' '" + lang + "' 'NET' '" + backup_dir + "'"
        else:
            cmd = "chmod +x '" + script_path + "'; '" + script_path + "' '" + lang + "' '" + device_type + "'"

        # Execute backup
        print("[BackupSuite] Executing command: " + cmd)
        self.session.openWithCallback(self.console_closed, Console, title, [cmd])

    def console_closed(self, retval=None):
        if retval is not None and retval != 0:
            # Try to extract meaningful error information
            error_msg = ""
            try:
                with open(LOGFILE, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()

                # Look for common error patterns
                if "No space left" in log_content:
                    error_msg = _("Backup failed: Not enough free space on device!")
                elif "Permission denied" in log_content:
                    error_msg = _("Backup failed: Write permission denied!")
                elif "Read-only file system" in log_content:
                    error_msg = _("Backup failed: Device is read-only!")
                elif "No such file or directory" in log_content:
                    error_msg = _("Backup failed: Required files not found!")
                elif "Connection refused" in log_content or "Host is down" in log_content:
                    error_msg = _("Backup failed: Network connection lost!")
                else:
                    # Extract the last 5 lines of the log
                    lines = log_content.splitlines()
                    if len(lines) > 5:
                        last_lines = "\n".join(lines[-5:])
                    else:
                        last_lines = log_content
                    error_msg = _("Backup failed! Last errors:") + "\n" + last_lines

            except Exception as e:
                print("[BackupSuite] Error reading log: " + str(e))
                error_msg = _("Backup failed! Check log: %s") % LOGFILE

            # Provide detailed error message
            self.session.open(
                MessageBox,
                error_msg,
                MessageBox.TYPE_ERROR,
                timeout=30
            )


class FlashImageConfig(Screen):
    def __init__(self, session, curdir, matchingPattern=None):
        self.skin = get_skin("flash")
        Screen.__init__(self, session)
        self["Title"].setText(_("Select the folder with backup"))
        self["key_red"] = StaticText(_("Close"))
        self["key_green"] = StaticText("")
        self["key_yellow"] = StaticText("")
        self["key_blue"] = StaticText("")
        self["curdir"] = StaticText(_("current:  %s") % (curdir or ''))
        self.founds = False
        self.dualboot = is_dual_boot()
        self.ForceMode = requires_force_mode()

        if matchingPattern:
            original_extensions = matchingPattern.split("(")[-1].rstrip(")$")
            combined_pattern = r"\.(" + original_extensions + "|zip)$"
        else:
            combined_pattern = r"\.(zip)$"

        self.filelist = FileList(curdir, matchingPattern=combined_pattern, enableWrapAround=True)
        self.filelist.onSelectionChanged.append(self.__selChanged)
        self["filelist"] = self.filelist
        self["FilelistActions"] = ActionMap(
            ["SetupActions", "ColorActions"],
            {
                "green": self.keyGreen,
                "red": self.keyRed,
                "yellow": self.keyYellow,
                "blue": self.KeyBlue,
                "ok": self.key_ok,
                "cancel": self.keyRed
            }
        )
        self.onLayoutFinish.append(self.update_ui)

    def update_ui(self):
        self.__selChanged()

    def __selChanged(self):
        self["key_yellow"].setText("")
        self["key_green"].setText("")
        self["key_blue"].setText("")
        current = self.get_current_selected()
        self["curdir"].setText(_("Current: %s") % current)

        if not self.filelist.canDescent() and current and current.endswith(".zip"):
            self["key_yellow"].setText(_("Unzip"))

        elif self.filelist.canDescent() and current and current != '/':
            self["key_green"].setText(_("Flash"))
            if isfile(join(current, LOGFILE)) and isfile(join(current, VERSIONFILE)):
                self["key_yellow"].setText(_("About"))
                self["key_blue"].setText(_("Delete"))

    def getCurrentSelected(self):
        dirname = self.filelist.getCurrentDirectory()
        filename = self.filelist.getFilename()
        if not filename and not dirname:
            cur = ''
        elif not filename:
            cur = dirname
        elif not dirname:
            cur = filename
        else:
            if not self.filelist.canDescent() or len(filename) <= len(dirname):
                cur = dirname
            else:
                cur = filename
        return cur or ''

    def key_ok(self):
        if self.filelist.canDescent():
            self.filelist.descent()
            self.update_ui()

    def confirmedWarning(self, result):
        if result:
            self.founds = False
            self.showparameterlist()

    def get_current_selected(self):
        dirname = self.filelist.getCurrentDirectory()
        filename = self.filelist.getFilename()
        return filename if filename else dirname

    def keyGreen(self):
        backup_dir = self.get_current_selected()
        if not backup_dir:
            return

        warning_text = "\n"
        if self.dualboot:
            warning_text += _("\nYou are using dual multiboot!")
        self.session.openWithCallback(lambda r: self.confirmedWarning(r), MessageBox, _("Warning!\nUse at your own risk! Make always a backup before use!\nDon't use it if you use multiple ubi volumes in ubi layer!") + warning_text, MessageBox.TYPE_INFO)

    def showparameterlist(self):
        if self["key_green"].getText() == _("Run flash"):
            dirname = self.getCurrentSelected()
            model = get_box_type()
            if dirname:
                backup_files = []
                no_backup_files = []
                text = _("Select parameter for start flash!\n")
                text += _('For flashing your receiver files are needed:\n')
                if exists('/var/lib/dpkg/info'):
                    if "dm9" in model:
                        backup_files = [("kernel.bin"), ("rootfs.tar.bz2")]
                        no_backup_files = [("kernel_cfe_auto.bin"), ("rootfs.bin"), ("root_cfe_auto.jffs2"), ("root_cfe_auto.bin"), ("oe_kernel.bin"), ("oe_rootfs.bin"), ("kernel_auto.bin"), ("uImage"), ("rootfs.ubi")]
                        text += "kernel.bin, rootfs.tar.bz2"
                    elif model in ("dm520", "dm7080", "dm820"):
                        backup_files = [("*.xz")]
                        no_backup_files = [("kernel_cfe_auto.bin"), ("rootfs.bin"), ("root_cfe_auto.jffs2"), ("root_cfe_auto.bin"), ("oe_kernel.bin"), ("oe_rootfs.bin"), ("kernel_auto.bin"), ("kernel.bin"), ("rootfs.tar.bz2"), ("uImage"), ("rootfs.ubi")]
                        text += "*.xz"
                    else:
                        backup_files = [("*.nfi")]
                        no_backup_files = [("kernel_cfe_auto.bin"), ("rootfs.bin"), ("root_cfe_auto.jffs2"), ("root_cfe_auto.bin"), ("oe_kernel.bin"), ("oe_rootfs.bin"), ("kernel_auto.bin"), ("kernel.bin"), ("rootfs.tar.bz2"), ("uImage"), ("rootfs.ubi")]
                        text += "*.nfi"
                elif model.startswith("gb"):
                    if "4k" not in model:
                        backup_files = [("kernel.bin"), ("rootfs.bin")]
                        no_backup_files = [("kernel_cfe_auto.bin"), ("root_cfe_auto.jffs2"), ("root_cfe_auto.bin"), ("oe_kernel.bin"), ("oe_rootfs.bin"), ("rootfs.tar.bz2"), ("kernel_auto.bin"), ("uImage"), ("rootfs.ubi")]
                        text += "kernel.bin, rootfs.bin"
                    else:
                        backup_files = [("kernel.bin"), ("rootfs.tar.bz2")]
                        no_backup_files = [("kernel_cfe_auto.bin"), ("rootfs.bin"), ("root_cfe_auto.jffs2"), ("root_cfe_auto.bin"), ("oe_kernel.bin"), ("oe_rootfs.bin"), ("kernel_auto.bin"), ("uImage"), ("rootfs.ubi")]
                        text += "kernel.bin, rootfs.tar.bz2"
                elif model.startswith("vu"):
                    if "4k" in model:
                        backup_files = [("kernel_auto.bin"), ("rootfs.tar.bz2")]
                        no_backup_files = [("kernel_cfe_auto.bin"), ("rootfs.bin"), ("root_cfe_auto.jffs2"), ("root_cfe_auto.bin"), ("oe_kernel.bin"), ("oe_rootfs.bin"), ("kernel.bin"), ("uImage"), ("rootfs.ubi")]
                        text += "kernel_auto.bin, rootfs.tar.bz2"
                    elif model in ("vuduo2", "vusolose", "vusolo2", "vuzero"):
                        backup_files = [("kernel_cfe_auto.bin"), ("root_cfe_auto.bin")]
                        no_backup_files = [("rootfs.bin"), ("root_cfe_auto.jffs2"), ("oe_kernel.bin"), ("oe_rootfs.bin"), ("kernel.bin"), ("rootfs.tar.bz2"), ("kernel_auto.bin"), ("uImage"), ("rootfs.ubi")]
                        text += "kernel_cfe_auto.bin, root_cfe_auto.bin"
                    else:
                        backup_files = [("kernel_cfe_auto.bin"), ("root_cfe_auto.jffs2")]
                        no_backup_files = [("rootfs.bin"), ("root_cfe_auto.bin"), ("oe_kernel.bin"), ("oe_rootfs.bin"), ("kernel.bin"), ("rootfs.tar.bz2"), ("kernel_auto.bin"), ("uImage"), ("rootfs.ubi")]
                        text += "kernel_cfe_auto.bin, root_cfe_auto.jffs2"

                else:
                    if model in ("hd51", "h7", "sf4008", "sf5008", "sf8008", "sf8008m", "vs1500", "et11000", "et13000", "bre2ze4k", "spycat4k", "spycat4kmini", "protek4k", "e4hdultra", "arivacombo", "arivatwin", "dual") or model.startswith(("anadol", "axashis4", "dinobot4", "ferguson4", "mediabox4", "axashisc4")):
                        backup_files = [("kernel.bin"), ("rootfs.tar.bz2")]
                        no_backup_files = [("kernel_cfe_auto.bin"), ("rootfs.bin"), ("root_cfe_auto.jffs2"), ("root_cfe_auto.bin"), ("oe_kernel.bin"), ("oe_rootfs.bin"), ("kernel_auto.bin"), ("uImage"), ("rootfs.ubi")]
                        text += "kernel.bin, rootfs.tar.bz2"
                    elif model in ("h9", "h9se", "h9combo", "h9combose", "i55plus", "i55se", "h10", "hzero", "h8", "dinobotu55", "iziboxx3", "dinoboth265", "axashistwin", "protek4kx1"):
                        backup_files = [("uImage"), ("rootfs.ubi")]
                        no_backup_files = [("kernel_cfe_auto.bin"), ("root_cfe_auto.jffs2"), ("root_cfe_auto.bin"), ("oe_kernel.bin"), ("oe_rootfs.bin"), ("rootfs.tar.bz2"), ("kernel_auto.bin"), ("kernel.bin"), ("rootfs.tar.bz2")]
                        text += "uImage, rootfs.ubi"
                    elif model in ("hd60", "hd61", "multibox", "multiboxse", "multiboxplus", "pulse4k", "pulse4kmini"):
                        backup_files = [("uImage"), ("rootfs.tar.bz2")]
                        no_backup_files = [("kernel_cfe_auto.bin"), ("root_cfe_auto.jffs2"), ("root_cfe_auto.bin"), ("oe_kernel.bin"), ("oe_rootfs.bin"), ("rootfs.ubi"), ("kernel_auto.bin"), ("kernel.bin")]
                        text += "uImage, rootfs.tar.bz2"
                    elif model.startswith(("et4", "et5", "et6", "et7", "et8", "et9", "et10")):
                        backup_files = [("kernel.bin"), ("rootfs.bin")]
                        no_backup_files = [("kernel_cfe_auto.bin"), ("root_cfe_auto.jffs2"), ("root_cfe_auto.bin"), ("oe_kernel.bin"), ("oe_rootfs.bin"), ("rootfs.tar.bz2"), ("kernel_auto.bin"), ("uImage"), ("rootfs.ubi")]
                        text += "kernel.bin, rootfs.bin"
                    elif model.startswith("ebox"):
                        backup_files = [("kernel_cfe_auto.bin"), ("root_cfe_auto.jffs2")]
                        no_backup_files = [("rootfs.bin"), ("root_cfe_auto.bin"), ("oe_kernel.bin"), ("oe_rootfs.bin"), ("kernel.bin"), ("rootfs.tar.bz2"), ("kernel_auto.bin"), ("uImage"), ("rootfs.ubi")]
                        text += "kernel_cfe_auto.bin, root_cfe_auto.jffs2"
                    elif model.startswith(("fusion", "pure", "optimus", "force", "iqon", "ios", "tm2", "tmn", "tmt", "tms", "lunix", "mediabox", "vala")):
                        backup_files = [("oe_kernel.bin"), ("oe_rootfs.bin")]
                        no_backup_files = [("kernel_cfe_auto.bin"), ("rootfs.bin"), ("root_cfe_auto.jffs2"), ("root_cfe_auto.bin"), ("kernel.bin"), ("rootfs.tar.bz2"), ("kernel_auto.bin"), ("uImage"), ("rootfs.ubi")]
                        text += "oe_kernel.bin, oe_rootfs.bin"
                    elif "4k" or "uhd" in model:
                        backup_files = [("oe_kernel.bin"), ("rootfs.tar.bz2")]
                        no_backup_files = [("kernel_cfe_auto.bin"), ("rootfs.bin"), ("root_cfe_auto.jffs2"), ("root_cfe_auto.bin"), ("oe_rootfs.bin"), ("kernel.bin"), ("kernel_auto.bin"), ("uImage"), ("rootfs.ubi")]
                        text += "oe_kernel.bin, rootfs.tar.bz2"
                    else:
                        backup_files = [("kernel.bin"), ("rootfs.bin")]
                        no_backup_files = [("kernel_cfe_auto.bin"), ("root_cfe_auto.jffs2"), ("root_cfe_auto.bin"), ("oe_kernel.bin"), ("oe_rootfs.bin"), ("rootfs.tar.bz2"), ("kernel_auto.bin"), ("uImage"), ("rootfs.ubi")]
                        text += "kernel.bin, rootfs.bin"
                try:
                    self.founds = False
                    text += _('\nThe found files:')
                    for name in listdir(dirname):
                        if name in backup_files:
                            text += _("  %s (maybe ok)") % name
                            self.founds = True
                        if name in no_backup_files:
                            text += _("  %s (maybe error)") % name
                            self.founds = True
                    if not self.founds:
                        text += _(' nothing!')
                except:
                    pass

                if self.founds:
                    open_list = [
                        (_("Simulate (no write)"), "simulate"),
                        (_("Standard (root and kernel)"), "standard"),
                        (_("Only root"), "root"),
                        (_("Only kernel"), "kernel"),
                    ]
                    open_list2 = [
                        (_("Simulate second partition (no write)"), "simulate2"),
                        (_("Second partition (root and kernel)"), "standard2"),
                        (_("Second partition (only root)"), "rootfs2"),
                        (_("Second partition (only kernel)"), "kernel2"),
                    ]
                    if self.dualboot:
                        open_list += open_list2
                else:
                    open_list = [
                        (_("Exit"), "exit"),
                    ]
                self.session.openWithCallback(self.Callbackflashing, MessageBox, text, simple=True, list=open_list)

    def Callbackflashing(self, ret):
        if ret:
            if ret == "exit":
                self.close()
                return

            if self.session.nav.RecordTimer.isRecording():
                self.session.open(MessageBox, _("A recording is currently running. Please stop the recording before trying to start a flashing."), MessageBox.TYPE_ERROR)
                self.founds = False
                return

            dir_flash = self.getCurrentSelected()
            text = _("Flashing: ")
            cmd = "echo -e"
            if ret == "simulate":
                text += _("Simulate (no write)")
                cmd = "%s -n '%s'" % (OFGWRITE_BIN, dir_flash)
            elif ret == "standard":
                text += _("Standard (root and kernel)")
                if self.ForceMode:
                    cmd = "%s -f -r -k '%s' > /dev/null 2>&1 &" % (OFGWRITE_BIN, dir_flash)
                else:
                    cmd = "%s -r -k '%s' > /dev/null 2>&1 &" % (OFGWRITE_BIN, dir_flash)
            elif ret == "root":
                text += _("Only root")
                cmd = "%s -r '%s' > /dev/null 2>&1 &" % (OFGWRITE_BIN, dir_flash)
            elif ret == "kernel":
                text += _("Only kernel")
                cmd = "%s -k '%s' > /dev/null 2>&1 &" % (OFGWRITE_BIN, dir_flash)
            elif ret == "simulate2":
                text += _("Simulate second partition (no write)")
                cmd = "%s -kmtd3 -rmtd4 -n '%s'" % (OFGWRITE_BIN, dir_flash)
            elif ret == "standard2":
                text += _("Second partition (root and kernel)")
                cmd = "%s -kmtd3 -rmtd4 '%s' > /dev/null 2>&1 &" % (OFGWRITE_BIN, dir_flash)
            elif ret == "rootfs2":
                text += _("Second partition (only root)")
                cmd = "%s -rmtd4 '%s' > /dev/null 2>&1 &" % (OFGWRITE_BIN, dir_flash)
            elif ret == "kernel2":
                text += _("Second partition (only kernel)")
                cmd = "%s -kmtd3 '%s' > /dev/null 2>&1 &" % (OFGWRITE_BIN, dir_flash)
            else:
                return

            message = "echo -e '\n"
            message += _('NOT found files for flashing!\n')
            message += "'"

            if ret == "simulate" or ret == "simulate2":
                if self.founds:
                    message = "echo -e '\n"
                    message += _('Show only found image and mtd partitions.\n')
                    message += "'"
            else:
                if self.founds:
                    message = "echo -e '\n"
                    message += _('ofgwrite will stop enigma2 now to run the flash.\n')
                    message += _('Your STB will freeze during the flashing process.\n')
                    message += _('Please: DO NOT reboot your STB and turn off the power.\n')
                    message += _('The image or kernel will be flashing and auto booted in few minutes.\n')
                    message += "'"
            self.session.open(Console, text, [message, cmd])

    def keyRed(self):
        self.close()

    def keyYellow(self):
        if self["key_yellow"].getText() == _("Unzip"):
            filename = self.filelist.getFilename()
            if filename and filename.endswith(".zip"):
                self.session.openWithCallback(self.doUnzip, MessageBox, _("Do you really want to unpack %s ?") % filename, MessageBox.TYPE_YESNO)
        elif self["key_yellow"].getText() == _("Backup info"):
            self.session.open(MessageBox, "\n\n\n%s" % self.getBackupInfo(), MessageBox.TYPE_INFO)

    def getBackupInfo(self):
        backup_dir = self.getCurrentSelected()
        backup_info = ""
        for line in open(backup_dir + VERSIONFILE, "r"):
            backup_info += line
        return backup_info

    def doUnzip(self, answer):
        if answer is True:
            dirname = self.filelist.getCurrentDirectory()
            filename = self.filelist.getFilename()
            if dirname and filename:
                try:
                    os_system('unzip -o %s%s -d %s' % (dirname, filename, dirname))
                    self.filelist.refresh()
                    self.update_ui()
                except:
                    pass

    def KeyBlue(self):
        if self["key_blue"].getText() == _("Delete"):
            self.session.openWithCallback(self.confirmedDelete, MessageBox, _("You are about to delete this backup:\n\n%s\nContinue?") % self.getBackupInfo(), MessageBox.TYPE_YESNO)

    def confirmedDelete(self, answer):
        if answer is True:
            backup_dir = self.getCurrentSelected()
            cmdmessage = "echo -e 'Removing backup:   %s\n'" % basename(backup_dir.rstrip('/'))
            cmddelete = "rm -rf %s > /dev/null 2>&1" % backup_dir
            self.update_ui()
            self.session.open(Console, _("Delete backup"), [cmdmessage, cmddelete], self.filelist.refresh)


class BackupHelpScreen(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.skin = """
        <screen position="center,center" size="700,850" title="BackupSuite Help">
            <widget name="help_text" position="17,21" size="675,800" font="Regular;24" />
        </screen>"""

        self.setTitle(_("BackupSuite Help"))
        self["help_text"] = ScrollLabel()

        help_content = _("BackupSuite v%s\n\n") % VERSION
        help_content += _("Welcome to BackupSuite help.\n\n")
        help_content += _("Device List:\n")
        help_content += _("• Use UP/DOWN buttons to navigate through backup options\n")
        help_content += _("• Press OK to select an option\n\n")

        help_content += _("Backup Options:\n")
        help_content += _("• HDD Backup: Full system backup to internal hard drive\n")
        help_content += _("• USB Backup: Create a bootable USB recovery stick\n")
        help_content += _("• MMC Backup: Backup to internal storage (eMMC)\n")
        help_content += _("• NET Backup: Backup to network storage (NAS/SMB)\n")
        help_content += _("• Barry Allen: Multiboot backup (if installed)\n")
        help_content += _("• Restore: Flash a previously created backup or image\n\n")

        help_content += _("Button Functions:\n")
        help_content += _("• GREEN: Start backup for selected device\n")
        help_content += _("• YELLOW: Start restore process\n")
        help_content += _("• BLUE: Show this help screen\n")
        help_content += _("• RED: Close BackupSuite\n\n")

        help_content += _("NET Backup Instructions:\n")
        help_content += _("1. Mount your network share first:\n")
        help_content += _("   - Go to Main Menu > Setup > System > Storage Manager\n")
        help_content += _("   - Select 'Network Storage' and add your NAS/SMB share\n")
        help_content += _("   - Enter server IP, share name, username and password\n")
        help_content += _("   - Mount the share and assign a name (e.g., NET_BACKUP)\n\n")
        help_content += _("2. Select 'NET Backup' from the device list\n")
        help_content += _("3. Choose your mounted network share\n")
        help_content += _("4. Confirm and start the backup process\n\n")

        help_content += _("Best Practices:\n")
        help_content += _("- Keep regular backups of your system\n")
        help_content += _("- Verify you have enough free storage space\n")
        help_content += _("- Never interrupt backup/restore processes\n")
        help_content += _("- Use quality USB drives for recovery sticks\n")
        help_content += _("- For network backups, use wired connection instead of Wi-Fi\n\n")

        help_content += _("Technical Notes:\n")
        help_content += _("- HDD backups: Stored in /media/hdd/backup\n")
        help_content += _("- USB backups: Require FAT32-formatted drive with 'backupstick' file\n")
        help_content += _("- NET backups: Require mounted CIFS/NFS share with write permissions\n")
        help_content += _("- Restore: Works from HDD, USB, NET or MMC storage\n")
        help_content += _("- Always choose 'Standard (root and kernel)' when restoring\n\n")

        help_content += _("Troubleshooting NET Backup:\n")
        help_content += _("- Ensure NAS is powered on and accessible\n")
        help_content += _("- Verify username/password are correct\n")
        help_content += _("- Check share permissions (read/write)\n")
        help_content += _("- Test connection with ping command\n")
        help_content += _("- Use IP address instead of hostname if DNS fails\n\n")

        help_content += _("For detailed instructions and support:\n")
        help_content += _("Visit our GitHub repository:\n")
        help_content += _("https://github.com/persianpros/BackupSuite-PLi\n")

        self["actions"] = ActionMap(
            ["NavigationActions", "SetupActions"],
            {
                "up": self["help_text"].pageUp,
                "down": self["help_text"].pageDown,
                "left": self["help_text"].pageUp,
                "right": self["help_text"].pageDown,
                "pageUp": self["help_text"].pageUp,
                "pageDown": self["help_text"].pageDown,
                "cancel": self.close,
                "ok": self.close
            }
        )


class WhatisNewInfo(Screen):
    def __init__(self, session):
        self.skin = get_skin("new")
        Screen.__init__(self, session)
        self["Title"].setText(_("What is new since the last release?"))
        self["key_red"] = Button(_("Close"))
        self["AboutScrollLabel"] = ScrollLabel(_("Please wait"))
        self["actions"] = ActionMap(
            ["SetupActions", "DirectionActions"],
            {
                "cancel": self.close,
                "ok": self.close,
                "up": self["AboutScrollLabel"].pageUp,
                "down": self["AboutScrollLabel"].pageDown
            }
        )
        with open(resolveFilename(SCOPE_PLUGINS, "Extensions/BackupSuite/whatsnew.txt")) as file:
            whatsnew = file.read()
        self["AboutScrollLabel"].setText(whatsnew)


def main(session, **kwargs):
    session.open(BackupStart)


def Plugins(path, **kwargs):
    global plugin_path
    plugin_path = path
    description = _("Backup and restore your image") + ", " + VERSION
    return [
        PluginDescriptor(
            name="BackupSuite",
            description=description,
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon='plugin.png',
            fnc=main
        ),
        PluginDescriptor(
            name="BackupSuite",
            description=description,
            where=PluginDescriptor.WHERE_EXTENSIONSMENU,
            fnc=main
        )
    ]
