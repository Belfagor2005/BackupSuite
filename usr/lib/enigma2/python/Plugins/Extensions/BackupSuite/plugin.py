# -*- coding: utf-8 -*-

from os.path import join, isfile, basename, exists
from os import listdir, system as os_system, chmod, stat as os_stat
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Console import Console
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.FileList import FileList
from Components.ScrollLabel import ScrollLabel
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from enigma import getDesktop
import stat
from . import _
from .message import *

# Global constants
versienummer = '3.0-r2'
BACKUP_SCRIPTS = {
    'HDD': ("backuphdd.sh", "backuphdd-dmm.sh"),
    'USB': ("backupusb.sh", "backupusb-dmm.sh"),
    'MMC': ("backupmmc.sh", "backupmmc-dmm.sh")
}
LOGFILE = "BackupSuite.log"
VERSIONFILE = "imageversion"
ENIGMA2VERSIONFILE = "/tmp/enigma2version"
ofgwrite_bin = "/usr/bin/ofgwrite"


# Helper functions
def get_box_type():
    """Safe box type retrieval"""
    try:
        from enigma import getBoxType
        return getBoxType()
    except ImportError:
        from boxbranding import getBoxType
        return getBoxType()


def get_script_path(device_type):
    """Get the appropriate backup script path based on device type and box model"""
    scripts = BACKUP_SCRIPTS[device_type]
    script_name = scripts[1] if get_box_type().startswith("dm") else scripts[0]
    script_path = resolveFilename(SCOPE_PLUGINS, f"Extensions/BackupSuite/scripts/{script_name}")
    
    # Ensure execution permission is set
    if exists(script_path):
        current_mode = os_stat(script_path).st_mode
        if not (current_mode & stat.S_IXUSR):
            chmod(script_path, current_mode | stat.S_IXUSR)

    return script_path


def get_skin(skin_type):
    """Return appropriate skin based on screen resolution"""
    try:
        sz_w = getDesktop(0).size().width()
    except:
        sz_w = 720

    skins = {
        1920: f"skin{skin_type}fullhd",
        1280: f"skin{skin_type}hd",
        'default': f"skin{skin_type}sd"
    }
    return skins.get(sz_w, skins['default'])


def get_backup_files_pattern():
    """Determine file pattern based on box model"""
    model = get_box_type()

    patterns = {
        # DM models
        'dm9': r"^.*\.(xz)$",
        'dm520|dm7080|dm820': r"^.*\.(xz)$",
        'dm': r"^.*\.(nfi)$",

        # VU models
        'vu.*4k': r"^.*\.(bin|bz2)$",
        'vuduo2|vusolose|vusolo2|vuzero': r"^.*\.(bin|jffs2)$",
        'vu': r"^.*\.(bin|jffs2)$",

        # Other models
        'hd51|h7|sf4008|sf5008|sf8008|sf8008m|vs1500|et11000|et13000|bre2ze4k|spycat4k|spycat4kmini|protek4k|e4hdultra|arivacombo|arivatwin|dual|anadol.*|axashis4|dinobot4|ferguson4|mediabox4|axashisc4':
            r"^.*\.(bin|bz2)$",
        'h9|h9se|h9combo|h9combose|i55plus|i55se|h10|hzero|h8|dinobotu55|iziboxx3|dinoboth265|axashistwin|protek4kx1':
            r"^.*\.(ubi)$",
        'hd60|hd61|multibox|multiboxse|multiboxplus|pulse4k|pulse4kmini':
            r"^.*\.(bz2)$",
        'et4|et5|et6|et7|et8|et9|et10':
            r"^.*\.(bin)$",
        'ebox': r"^.*\.(jffs2)$",
        'fusion|pure|optimus|force|iqon|ios|tm2|tmn|tmt|tms|lunix|mediabox|vala':
            r"^.*\.(bin)$",
        '4k|uhd': r"^.*\.(bz2)$",
    }

    for pattern, file_pat in patterns.items():
        if pattern in model:
            return file_pat

    return r"^.*\.(zip|bin)$"  # Default pattern


def get_backup_requirements():
    """Get required files for backup based on box model"""
    model = get_box_type()
    requirements = {
        # DM models
        'dm9': r"^.*\.(xz)$",
        'dm520|dm7080|dm820': r"^.*\.(xz)$",
        'dm': r"^.*\.(nfi)$",

        # VU models
        'vu.*4k': r"^.*\.(bin|bz2)$",
        'vuduo2|vusolose|vusolo2|vuzero': r"^.*\.(bin|jffs2)$",
        'vu': r"^.*\.(bin|jffs2)$",

        # Other models
        'hd51|h7|sf4008|sf5008|sf8008|sf8008m|vs1500|et11000|et13000|bre2ze4k|spycat4k|spycat4kmini|protek4k|e4hdultra|arivacombo|arivatwin|dual|anadol.*|axashis4|dinobot4|ferguson4|mediabox4|axashisc4':
            r"^.*\.(bin|bz2)$",
        'h9|h9se|h9combo|h9combose|i55plus|i55se|h10|hzero|h8|dinobotu55|iziboxx3|dinoboth265|axashistwin|protek4kx1':
            r"^.*\.(ubi)$",
        'hd60|hd61|multibox|multiboxse|multiboxplus|pulse4k|pulse4kmini':
            r"^.*\.(bz2)$",
        'et4|et5|et6|et7|et8|et9|et10':
            r"^.*\.(bin)$",
        'ebox': r"^.*\.(jffs2)$",
        'fusion|pure|optimus|force|iqon|ios|tm2|tmn|tmt|tms|lunix|mediabox|vala':
            r"^.*\.(bin)$",
        '4k|uhd': r"^.*\.(bz2)$",
    }

    for pattern, req_files in requirements.items():
        if pattern in model:
            return req_files

    return [("kernel.bin"), ("rootfs.bin")]  # Default requirements


# Global variables
autoStartTimer = None
_session = None


class BackupStart(Screen):
    def __init__(self, session, args=0):
        Screen.__init__(self, session)
        self.skin = get_skin("start")
        self.session = session
        self.setup_title = _("Make a backup or restore a backup")
        self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/BackupSuite")
        self["key_menu"] = Button(_("Backup > MMC"))
        self["key_red"] = Button(_("Close"))
        self["key_green"] = Button(_("Backup > HDD"))
        self["key_yellow"] = Button(_("Backup > USB"))
        self["key_blue"] = Button(_("Restore backup"))
        self["help"] = StaticText()
        self["setupActions"] = ActionMap(
            ["SetupActions", "ColorActions", "EPGSelectActions", "HelpActions"],
            {
                "menu": self.confirmmmc,
                "red": self.cancel,
                "green": self.confirmhdd,
                "yellow": self.confirmusb,
                "blue": self.flashimage,
                "info": self.keyInfo,
                "cancel": self.cancel,
                "displayHelp": self.showHelp,
            },
            -2
        )
        self.setTitle(self.setup_title)

    def confirmhdd(self):
        self.session.openWithCallback(
            self.backuphdd,
            MessageBox,
            _("Do you want to make an USB-back-up image on HDD? \n\nThis only takes a few minutes and is fully automatic.\n"),
            MessageBox.TYPE_YESNO,
            timeout=20,
            default=True
        )

    def confirmusb(self):
        self.session.openWithCallback(
            self.backupusb,
            MessageBox,
            _("Do you want to make a back-up on USB?\n\nThis only takes a few minutes depending on the used filesystem and is fully automatic.\n\nMake sure you first insert an USB flash drive before you select Yes."),
            MessageBox.TYPE_YESNO,
            timeout=20,
            default=True
        )

    def confirmmmc(self):
        self.session.openWithCallback(
            self.backupmmc,
            MessageBox,
            _("Do you want to make an USB-back-up image on MMC? \n\nThis only takes a few minutes and is fully automatic.\n"),
            MessageBox.TYPE_YESNO,
            timeout=20,
            default=True
        )

    def showHelp(self):
        try:
            from .plugin import backupsuiteHelp
            if backupsuiteHelp:
                backupsuiteHelp.open(self.session)
        except ImportError:
            pass

    def flashimage(self):
        model = get_box_type()
        patterns = {
            "vuduo|vusolo|vuultimo|vuuno|ebox.*": r"^.*\.(zip|bin|jffs2)",
            "4k|uhd|hd51|hd60|hd61|h7|sf4008|sf5008|sf8008|sf8008m|vs1500|et11000|et13000|multibox|multiboxplus|e4hdultra": r"^.*\.(zip|bin|bz2)",
            "h9|h9se|h9combo|h9combose|i55plus|i55se|h10|hzero|h8|dinobotu55|iziboxx3|dinoboth265|axashistwin|protek4kx1": r"^.*\.(zip|bin|ubi)",
            "dm.*": r"^.*\.(zip|bin|nfi|xz)"
        }

        file_pattern = r"^.*\.(zip|bin)"  # Default pattern
        for pattern, file_pat in patterns.items():
            if pattern in model:
                file_pattern = file_pat
                break

        self.session.open(FlashImageConfig, '/media/', file_pattern)

    def cancel(self):
        self.close(False, self.session)

    def keyInfo(self):
        self.session.open(WhatisNewInfo)

    def writeEnigma2VersionFile(self):
        from Components.About import getEnigmaVersionString
        try:
            with open(ENIGMA2VERSIONFILE, 'wt') as f:
                f.write(getEnigmaVersionString())
        except OSError:
            pass

    def backuphdd(self, ret=False):
        if ret:
            self.writeEnigma2VersionFile()
            text = _('Full back-up on HDD')
            cmd = f"{get_script_path('HDD')} en_EN"
            self.session.openWithCallback(self.consoleClosed, Console, text, [cmd])

    def backupusb(self, ret=False):
        if ret:
            self.writeEnigma2VersionFile()
            text = _('Full back-up to USB')
            cmd = f"{get_script_path('USB')} en_EN"
            self.session.openWithCallback(self.consoleClosed, Console, text, [cmd])

    def backupmmc(self, ret=False):
        if ret:
            self.writeEnigma2VersionFile()
            text = _('Full back-up on MMC')
            cmd = f"{get_script_path('MMC')} en_EN"
            self.session.openWithCallback(self.consoleClosed, Console, text, [cmd])

    def consoleClosed(self, answer=None):
        return


class WhatisNewInfo(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.skin = get_skin("new")
        self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/BackupSuite")
        self["Title"] = StaticText(_("What is new since the last release?"))
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

        try:
            with open(resolveFilename(SCOPE_PLUGINS, "Extensions/BackupSuite/scripts/whatsnew.txt")) as file:
                self["AboutScrollLabel"].setText(file.read())
        except OSError:
            self["AboutScrollLabel"].setText(_("Release notes not available"))


class FlashImageConfig(Screen):
    def __init__(self, session, curdir, matchingPattern=None):
        Screen.__init__(self, session)
        self.skin = get_skin("flash")
        self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/BackupSuite")
        self.setTitle(_("Select the folder with backup"))
        self["key_red"] = StaticText(_("Close"))
        self["key_green"] = StaticText("")
        self["key_yellow"] = StaticText("")
        self["key_blue"] = StaticText("")
        self["curdir"] = StaticText(_("current:  %s") % (curdir or ''))
        # Initialize state
        self.founds = False
        self.dualboot = self.is_dual_boot()
        self.force_mode = self.is_force_mode()
        self.filelist = FileList(
            curdir,
            matchingPattern=matchingPattern,
            enableWrapAround=True
        )
        self.filelist.onSelectionChanged.append(self.__selChanged)
        self["filelist"] = self.filelist
        self["FilelistActions"] = ActionMap(
            ["SetupActions", "ColorActions"],
            {
                "green": self.keyGreen,
                "red": self.keyRed,
                "yellow": self.keyYellow,
                "blue": self.KeyBlue,
                "ok": self.keyOk,
                "cancel": self.keyRed
            }
        )
        self.onLayoutFinish.append(self.__layoutFinished)

    def __layoutFinished(self):
        pass

    def is_dual_boot(self):
        """Check if device supports dual boot"""
        if get_box_type() != "et8500":
            return False

        try:
            with open("/proc/mtd") as f:
                content = f.read()
                return 'rootfs2' in content and 'kernel2' in content
        except OSError:
            return False

    def is_force_mode(self):
        """Check if device requires force mode"""
        return get_box_type() in (
            "h9", "h9se", "h9combo", "h9combose", "i55plus", "i55se",
            "h10", "hzero", "h8"
        )

    def dualBoot(self):
        if get_box_type() == "et8500":
            rootfs2 = False
            kernel2 = False
            f = open("/proc/mtd")
            lz = f.readlines()
            for x in lz:
                if 'rootfs2' in x:
                    rootfs2 = True
                if 'kernel2' in x:
                    kernel2 = True
            f.close()
            if rootfs2 and kernel2:
                return True
        return False

    def ForceMode(self):
        if get_box_type() in ("h9", "h9se", "h9combo", "h9combose", "i55plus", "i55se", "h10", "hzero", "h8"):
            return True
        return False

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

    def __selChanged(self):
        self["key_yellow"].setText("")
        self["key_green"].setText("")
        self["key_blue"].setText("")
        self["curdir"].setText(_("current:  %s") % self.getCurrentSelected())
        try:
            file_name = self.getCurrentSelected()
            if not self.filelist.canDescent() and file_name and file_name != '/':
                if file_name.endswith(".zip"):
                    self["key_yellow"].setText(_("Unzip"))
            elif self.filelist.canDescent() and file_name and file_name != '/':
                self["key_green"].setText(_("Run flash"))
                if isfile(join(file_name, LOGFILE)) and \
                   isfile(join(file_name, VERSIONFILE)):
                    self["key_yellow"].setText(_("Backup info"))
                    self["key_blue"].setText(_("Delete"))
        except Exception:
            pass

    def keyOk(self):
        if self.filelist.canDescent():
            self.filelist.descent()

    def keyGreen(self):
        if self["key_green"].getText() == _("Run flash"):
            warning = _("Warning!\nUse at your own risk! Make always a backup before use!\nDon't use it if you use multiple ubi volumes in ubi layer!")
            if self.dualboot:
                warning += _("\n\nYou are using dual multiboot!")
            self.session.openWithCallback(
                self.show_parameter_list,
                MessageBox,
                warning,
                MessageBox.TYPE_INFO
            )

    def show_parameter_list(self, result):
        if result:
            self.founds = False
            self.show_flash_options()

    def show_flash_options(self):
        if self["key_green"].getText() == _("Run flash"):
            dirname = self.getCurrentSelected()
            if not dirname:
                return

            model = get_box_type()
            requirements = self.get_backup_requirements(model)
            text = _("Select parameter for start flash!\n")
            text += _('For flashing your receiver files are needed:\n')
            text += ", ".join(requirements["backup_files"])

            try:
                found_items = []
                for name in listdir(dirname):
                    if name in requirements["backup_files"]:
                        found_items.append(f"{name} (maybe ok)")
                        self.founds = True
                    elif name in requirements["no_backup_files"]:
                        found_items.append(f"{name} (maybe error)")
                        self.founds = True

                text += _('\n\nThe found files:')
                text += "\n" + "\n".join(found_items) if found_items else _(' nothing!')
            except OSError:
                pass

            if self.founds:
                options = [
                    (_("Simulate (no write)"), "simulate"),
                    (_("Standard (root and kernel)"), "standard"),
                    (_("Only root"), "root"),
                    (_("Only kernel"), "kernel"),
                ]
                if self.dualboot:
                    options += [
                        (_("Simulate second partition (no write)"), "simulate2"),
                        (_("Second partition (root and kernel)"), "standard2"),
                        (_("Second partition (only root)"), "rootfs2"),
                        (_("Second partition (only kernel)"), "kernel2"),
                    ]
            else:
                options = [(_("Exit"), "exit")]

            self.session.openWithCallback(
                self.execute_flash_command,
                MessageBox,
                text,
                simple=True,
                list=options
            )

    def showparameterlist(self):
        if self["key_green"].getText() == _("Run flash"):
            dirname = self.getCurrentSelected()
            model = get_box_type()
            if dirname:
                backup_files = []
                no_backup_files = []
                text = _("Select parameter for start flash!\n")
                text += _('For flashing your receiver files are needed:\n')
                if model.startswith("dm"):
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
                
                """
                dir_flash = self.getCurrentSelected()
                text = _("Flashing: ")
                cmd = "echo -e"
                if ret == "simulate":
                    text += _("Simulate (no write)")
                    cmd = "%s -n '%s'" % (ofgwrite_bin, dir_flash)
                elif ret == "standard":
                    text += _("Standard (root and kernel)")
                    if self.ForceMode:
                        cmd = "%s -f -r -k '%s' > /dev/null 2>&1 &" % (ofgwrite_bin, dir_flash)
                    else:
                        cmd = "%s -r -k '%s' > /dev/null 2>&1 &" % (ofgwrite_bin, dir_flash)
                elif ret == "root":
                    text += _("Only root")
                    cmd = "%s -r '%s' > /dev/null 2>&1 &" % (ofgwrite_bin, dir_flash)
                elif ret == "kernel":
                    text += _("Only kernel")
                    cmd = "%s -k '%s' > /dev/null 2>&1 &" % (ofgwrite_bin, dir_flash)
                elif ret == "simulate2":
                    text += _("Simulate second partition (no write)")
                    cmd = "%s -kmtd3 -rmtd4 -n '%s'" % (ofgwrite_bin, dir_flash)
                elif ret == "standard2":
                    text += _("Second partition (root and kernel)")
                    cmd = "%s -kmtd3 -rmtd4 '%s' > /dev/null 2>&1 &" % (ofgwrite_bin, dir_flash)
                elif ret == "rootfs2":
                    text += _("Second partition (only root)")
                    cmd = "%s -rmtd4 '%s' > /dev/null 2>&1 &" % (ofgwrite_bin, dir_flash)
                elif ret == "kernel2":
                    text += _("Second partition (only kernel)")
                    cmd = "%s -kmtd3 '%s' > /dev/null 2>&1 &" % (ofgwrite_bin, dir_flash)
                """
            else:
                options = [(_("Exit"), "exit")]
            text = _("Flashing: ")
            self.session.openWithCallback(
                self.execute_flash_command,
                MessageBox,
                text,
                simple=True,
                list=options
            )

    def get_backup_requirements(self, model):
        """Get required files for backup based on box model"""
        patterns = {
            r"dm9": {
                "backup_files": ["kernel.bin", "rootfs.tar.bz2"],
                "no_backup_files": ["kernel_cfe_auto.bin", "rootfs.bin", "root_cfe_auto.jffs2",
                                    "root_cfe_auto.bin", "oe_kernel.bin", "oe_rootfs.bin",
                                    "kernel_auto.bin", "uImage", "rootfs.ubi"]
            },
            r"dm520|dm7080|dm820": {
                "backup_files": ["*.xz"],
                "no_backup_files": ["kernel_cfe_auto.bin", "rootfs.bin", "root_cfe_auto.jffs2",
                                    "root_cfe_auto.bin", "oe_kernel.bin", "oe_rootfs.bin",
                                    "kernel_auto.bin", "kernel.bin", "rootfs.tar.bz2",
                                    "uImage", "rootfs.ubi"]
            },
            r"dm.*": {
                "backup_files": ["*.nfi"],
                "no_backup_files": ["kernel_cfe_auto.bin", "rootfs.bin", "root_cfe_auto.jffs2",
                                    "root_cfe_auto.bin", "oe_kernel.bin", "oe_rootfs.bin",
                                    "kernel_auto.bin", "kernel.bin", "rootfs.tar.bz2",
                                    "uImage", "rootfs.ubi"]
            },

        }

        # Default requirements
        default = {
            "backup_files": ["kernel.bin", "rootfs.bin"],
            "no_backup_files": ["kernel_cfe_auto.bin", "root_cfe_auto.jffs2",
                                "root_cfe_auto.bin", "oe_kernel.bin", "oe_rootfs.bin",
                                "rootfs.tar.bz2", "kernel_auto.bin", "uImage", "rootfs.ubi"]
        }

        for pattern, reqs in patterns.items():
            if pattern in model:
                return reqs
        return default

    def execute_flash_command(self, ret):
        if not ret:
            return

        if ret == "exit":
            self.close()
            return

        if self.session.nav.RecordTimer.isRecording():
            self.session.open(
                MessageBox,
                _("A recording is currently running. Please stop the recording before trying to start a flashing."),
                MessageBox.TYPE_ERROR
            )
            return

        dir_flash = self.getCurrentSelected()
        commands = {
            "simulate": (ofgwrite_bin + " -n", _("Simulate (no write)")),
            "standard": (ofgwrite_bin + (" -f -r -k" if self.force_mode else " -r -k"),
                         _("Standard (root and kernel)")),
            "root": (ofgwrite_bin + " -r", _("Only root")),
            "kernel": (ofgwrite_bin + " -k", _("Only kernel")),
            "simulate2": (ofgwrite_bin + " -kmtd3 -rmtd4 -n", _("Simulate second partition (no write)")),
            "standard2": (ofgwrite_bin + " -kmtd3 -rmtd4", _("Second partition (root and kernel)")),
            "rootfs2": (ofgwrite_bin + " -rmtd4", _("Second partition (only root)")),
            "kernel2": (ofgwrite_bin + " -kmtd3", _("Second partition (only kernel)")),
        }

        if ret not in commands:
            return

        cmd, description = commands[ret]
        full_cmd = f"{cmd} '{dir_flash}'"

        if not ret.startswith("simulate"):
            full_cmd += " > /dev/null 2>&1 &"

        message = _("ofgwrite will stop enigma2 now to run the flash.\n")
        message += _("Your STB will freeze during the flashing process.\n")
        message += _("Please: DO NOT reboot your STB and turn off the power.\n")
        message += _("The image or kernel will be flashing and auto booted in few minutes.\n")

        self.session.open(
            Console,
            f"{_('Flashing:')} {description}",
            [f"echo -e '{message}'", full_cmd]
        )

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
                except:
                    pass

    def confirmedDelete(self, answer):
        if answer is True:
            backup_dir = self.getCurrentSelected()
            cmdmessage = "echo -e 'Removing backup:   %s\n'" % basename(backup_dir.rstrip('/'))
            cmddelete = "rm -rf %s > /dev/null 2>&1" % backup_dir
            self.session.open(Console, _("Delete backup"), [cmdmessage, cmddelete], self.filelist.refresh)

    def KeyBlue(self):
        if self["key_blue"].getText() == _("Delete"):
            self.session.openWithCallback(self.confirmedDelete, MessageBox, _("You are about to delete this backup:\n\n%s\nContinue?") % self.getBackupInfo(), MessageBox.TYPE_YESNO)


def main(session, **kwargs):
    session.open(BackupStart)


def Plugins(path, **kwargs):
    version = "unknown"
    try:
        with open("/var/lib/opkg/info/enigma2-plugin-extensions-backupsuite.control") as f:
            for line in f:
                if line.startswith("Version: "):
                    version = line.split('+', 1)[1].strip() if '+' in line else line.split(':', 1)[1].strip()
                    break
    except OSError:
        pass

    return [
        PluginDescriptor(
            name=_("BackupSuite"),
            description=f"{_('Backup and restore your image')}, {version}",
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon='plugin.png',
            fnc=main
        ),
        PluginDescriptor(
            name=_("BackupSuite"),
            description=f"{_('Backup and restore your image')}, {version}",
            where=PluginDescriptor.WHERE_EXTENSIONSMENU,
            fnc=main
        )
    ]
