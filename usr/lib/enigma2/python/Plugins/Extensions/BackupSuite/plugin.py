#!/usr/bin/python
# -*- coding: utf-8 -*-
from os import listdir, system as os_system  # , remove X_OK, access
from os.path import basename, exists, isfile, join  # , getmtime

from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.FileList import FileList
# from Components.Harddisk import harddiskmanager
from Components.ScrollLabel import ScrollLabel
from Components.Sources.StaticText import StaticText

from Plugins.Plugin import PluginDescriptor

from Screens.Console import Console
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

from Tools.Directories import resolveFilename, SCOPE_PLUGINS

from enigma import getDesktop

from . import _  # , schermen

# Global constants
VERSION = '3.0-r4'
BACKUP_SCRIPTS = {
	'HDD': "backuphdd.sh",
	'USB': "backupusb.sh",
	'MMC': "backupmmc.sh",
	# 'DMM-HDD': "backuphdd-dmm.sh",
	# 'DMM-USB': "backupusb-dmm.sh",
	# 'DMM-MMC': "backupmmc-dmm.sh",
}
LOGFILE = "/tmp/BackupSuite.log"
VERSIONFILE = "imageversion"
ENIGMA2VERSIONFILE = "/tmp/enigma2version"
OFGWRITE_BIN = "/usr/bin/ofgwrite"

# Global variables
autoStartTimer = None
_session = None


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

	if box_type.startswith('dm'):
		script_name = base_script.replace('.sh', '-dmm.sh')
	else:
		script_name = base_script

	script_path = resolveFilename(SCOPE_PLUGINS, f"Extensions/BackupSuite/scripts/{script_name}")

	# Log per debug
	print(f"[BackupSuite] Using script: {script_path} for {box_type}")
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


def get_backup_requirements():
	model = get_box_type()

	if 'dm' in model:
		if 'dm9' in model:
			return ["kernel.bin", "rootfs.tar.bz2"]
		elif any(x in model for x in ['dm520', 'dm7080', 'dm820']):
			return ["*.xz"]
		else:
			return ["*.nfi"]

	elif 'vu' in model:
		if '4k' in model:
			return ["kernel_auto.bin", "rootfs.tar.bz2"]
		elif any(x in model for x in ['vuduo2', 'vusolose', 'vusolo2', 'vuzero']):
			return ["kernel_cfe_auto.bin", "root_cfe_auto.bin"]
		else:
			return ["kernel_cfe_auto.bin", "root_cfe_auto.jffs2"]

	elif any(x in model for x in ['hd51', 'h7', 'sf4008', 'sf5008', 'sf8008', 'sf8008m', 'vs1500', 'et11000', 'et13000']):
		return ["kernel.bin", "rootfs.tar.bz2"]

	elif any(x in model for x in ['h9', 'h9se', 'h9combo', 'h9combose', 'i55plus', 'i55se', 'h10', 'hzero', 'h8']):
		return ["uImage", "rootfs.ubi"]

	elif any(x in model for x in ['hd60', 'hd61', 'multibox', 'multiboxse', 'multiboxplus']):
		return ["uImage", "rootfs.tar.bz2"]

	elif model.startswith(('et4', 'et5', 'et6', 'et7', 'et8', 'et9', 'et10')):
		return ["kernel.bin", "rootfs.bin"]

	elif 'ebox' in model:
		return ["kernel_cfe_auto.bin", "root_cfe_auto.jffs2"]

	return ["kernel.bin", "rootfs.bin"]


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


class BackupStart(Screen):
	def __init__(self, session, args=0):
		self.skin = get_skin("start")
		Screen.__init__(self, session)
		self.session = session
		self.setup_title = _("Make or restore a backup")
		self["key_red"] = Button(_("Close"))
		self["key_green"] = Button(_("Backup > HDD"))
		self["key_yellow"] = Button(_("Backup > USB"))
		self["key_blue"] = Button(_("Restore backup"))
		self["key_menu"] = Button(_("Backup > MMC"))
		self["help"] = StaticText()
		self["setupActions"] = ActionMap(
			["SetupActions", "ColorActions", "EPGSelectActions", "HelpActions"],
			{
				"menu": self.confirmmmc,
				"red": self.cancel,
				"green": self.confirmhdd,
				"yellow": self.confirmusb,
				"blue": self.flash_image,
				"info": self.keyInfo,
				"cancel": self.cancel,
				"displayHelp": self.show_help,
				"help": self.show_help,
			},
			-2
		)
		self.setTitle(self.setup_title)

		self.onShown.append(self.check_dependencies)

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

	def confirmhdd(self):
		self.session.openWithCallback(
			self.backuphdd,
			MessageBox,
			_("Do you want to make a backup on HDD?\n\nThis may take several minutes."),
			MessageBox.TYPE_YESNO
		)

	def confirmusb(self):
		self.session.openWithCallback(
			self.backupusb,
			MessageBox,
			_("Do you want to make a backup on USB?\n\nInsert USB device before continuing."),
			MessageBox.TYPE_YESNO
		)

	def confirmmmc(self):
		self.session.openWithCallback(
			self.backupmmc,
			MessageBox,
			_("Do you want to make a backup on MMC?\n\nWarning: This will overwrite existing data!"),
			MessageBox.TYPE_YESNO
		)

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

	def backuphdd(self, ret=False):
		if ret:
			self.write_enigma2_version()
			self.execute_backup("HDD")

	def backupusb(self, ret=False):
		if ret:
			self.write_enigma2_version()
			self.execute_backup("USB")

	def backupmmc(self, ret=False):
		if ret:
			self.write_enigma2_version()
			self.execute_backup("MMC")

	def execute_backup(self, device_type):
		script_path = get_script_path(device_type)

		if not exists(script_path):
			self.session.open(
				MessageBox,
				_("Backup script not found: %s") % basename(script_path),
				MessageBox.TYPE_ERROR
			)
			return

		title = _("%s Backup") % device_type
		cmd = f"chmod +x '{script_path}'; '{script_path}'"
		self.session.openWithCallback(self.console_closed, Console, title, [cmd])

	def console_closed(self, retval=None):
		if retval is not None and retval != 0:
			# Leggi il log per diagnosticare l'errore
			try:
				with open(LOGFILE, 'r') as f:
					last_lines = ''.join(f.readlines()[-5:])
				error_msg = f"{_('Backup failed! Last errors:')}\n{last_lines}"
			except:
				error_msg = _("Backup failed! Check log: %s") % LOGFILE

			self.session.open(MessageBox, error_msg, MessageBox.TYPE_ERROR)


class WhatisNewInfo(Screen):
	def __init__(self, session):
		self.skin = get_skin("new")
		Screen.__init__(self, session)
		# self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/BackupSuite")
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
		self.filelist = FileList(curdir, matchingPattern=matchingPattern, enableWrapAround=True)
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
				self["key_yellow"].setText(_("Info"))
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
		help_content += _("• HDD Backup: Full system backup to hard drive or NAS.\n")
		help_content += _("• USB Backup: Create a bootable USB recovery stick.\n")
		help_content += _("• MMC Backup: Backup to internal storage (advanced option).\n")
		help_content += _("• Restore: Flash a previously created backup or image.\n\n")

		help_content += _("Usage notes:\n")
		help_content += _("- Always keep a recent backup.\n")
		help_content += _("- Make sure you have sufficient storage space.\n")
		help_content += _("- Do not interrupt the backup or restore process.\n\n")

		help_content += _("Navigation:\n")
		help_content += _("• Use the Blue button to move forward.\n")
		help_content += _("• Use the Yellow button to move backward.\n\n")

		help_content += _("Details:\n")
		help_content += _("- HDD Backup can optionally copy an extra backup to USB if a 'backupstick' file is present.\n")
		help_content += _("- USB Backup requires FAT formatted USB-stick with a 'backupstick' or 'backupstick.txt' file in root.\n")
		help_content += _("- MMC Backup works similarly to HDD, with the same USB-stick conditions.\n")
		help_content += _("- Restore allows flashing backups or images from HDD, USB, NAS or MMC.\n")
		help_content += _("- Always use the 'Standard (root and kernel)' option when restoring.\n\n")
		help_content += _("For more information, please check the detailed help screens or the changelog.\n")
		self["help_text"].setText(help_content)

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
