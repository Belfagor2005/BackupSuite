# -*- coding: utf-8 -*-

"""
BackupSuite Plugin
FULL BACKUP UTILITY FOR ENIGMA2/OPENVISION
SUPPORTS VARIOUS MODELS

Original Developer: @persianpros
GitHub: https://github.com/persianpros/BackupSuite-PLi

SUPPORT FORUM: https://forums.openpli.org/

This is a fully modded code of BackupSuite
by @Lululla (2025-06-15).

The plugin provides a comprehensive backup and restore solution for Enigma2-based receivers.
It supports multiple device types (USB, MMC, HDD, Network shares, Barry Allen multi-boot),
handles automatic device detection, backup script management, and user interaction through
an intuitive GUI.

Features include:
- Automatic detection of mounted storage devices and network shares
- Custom backup scripts for each device type
- User prompts and error handling with detailed log analysis
- Support for flashing backup images and restoring
- Compatibility fixes for OpenPLi systems

This rewrite aims to improve stability, usability, and maintainability compared to the original.
"""

from __future__ import print_function
from os import (
	listdir,
	system as os_system,
	statvfs,
	makedirs,
	getenv,
	access,
	W_OK
)
from os.path import (
	basename,
	ismount,
	exists,
	isfile,
	join,
	realpath
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
from .schermen import *             # fallback for to screen..
from .message import *              # fallback for to compile on test develop..
from .findkerneldevice import *     # fallback for to compile on test develop..

# Global constants
VERSION = '3.0-r10'
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
	if not icon_name:
		return join(ICONS_DIR, "hdd.png")

	if exists(icon_name):
		return icon_name

	base_name = basename(icon_name)
	icon_path = join(ICONS_DIR, base_name)
	if exists(icon_path):
		return icon_path

	return join(ICONS_DIR, "hdd.png")


def BackupDeviceEntryComponent(device):
	raw_icon = device[1]
	icon_path = getIconPath(raw_icon)
	print("[BackupSuite] Loading icon: {0} -> {1}".format(raw_icon, icon_path))

	res = [
		device,
		(
			eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST,
			10, 5, 60, 60,
			LoadPixmap(icon_path)
		),
		(
			eListboxPythonMultiContent.TYPE_TEXT,
			100, 0, 700, 60,
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
	force_models = [
		'h9', 'h9se', 'h9combo', 'h9combose', 'i55plus',
		'i55se', 'h10', 'hzero', 'h8'
	]
	return any(x in model for x in force_models)


def get_skin(type):
	try:
		sz_w = getDesktop(0).size().width()
	except:
		sz_w = 720

	skin_prefix = "skin" + str(type)
	if sz_w >= 1920:
		return globals().get("skin" + skin_prefix + "fullhd", "")
	elif sz_w >= 1280:
		return globals().get("skin" + skin_prefix + "hd", "")
	else:
		return globals().get("skin" + skin_prefix + "sd", "")


def get_backup_files_pattern():
	"""Return the regex pattern for backup file extensions based on the device model."""
	model = get_box_type()

	if "dm" in model:
		if "dm9" in model:
			return r"\.(xz)$"
		elif any(x in model for x in ["dm520", "dm7080", "dm820"]):
			return r"\.(xz)$"
		else:
			return r"\.(nfi)$"

	elif "vu" in model:
		if "4k" in model:
			return r"\.(bin|bz2)$"
		elif any(x in model for x in ["vuduo2", "vusolose", "vusolo2", "vuzero"]):
			return r"\.(bin|jffs2)$"
		else:
			return r"\.(bin|jffs2)$"

	elif any(x in model for x in ["hd51", "h7", "sf4008", "sf5008", "sf8008", "sf8008m", "vs1500", "et11000", "et13000"]):
		return r"\.(bin|bz2)$"

	elif any(x in model for x in ["h9", "h9se", "h9combo", "h9combose", "i55plus", "i55se", "h10", "hzero", "h8"]):
		return r"\.(ubi)$"

	elif any(x in model for x in ["hd60", "hd61", "multibox", "multiboxse", "multiboxplus"]):
		return r"\.(bz2)$"

	elif model.startswith(("et4", "et5", "et6", "et7", "et8", "et9", "et10")):
		return r"\.(bin)$"

	elif "ebox" in model:
		return r"\.(jffs2)$"

	elif any(x in model for x in ["4k", "uhd"]):
		return r"\.(bz2)$"

	return r"\.(zip|bin|bz2)$"


def get_mounted_network_shares():
	"""Detect mounted network shares by reading /proc/mounts"""
	network_shares = []
	processed = set()
	try:
		with open("/proc/mounts", "r") as f:
			for line in f:
				parts = line.split()
				if len(parts) < 3:
					continue

				device, mountpoint, fstype = parts[0], parts[1], parts[2]

				if fstype.lower() in ("cifs", "nfs", "nfs4", "smbfs"):
					try:
						stat = statvfs(mountpoint)
						free_gb = (stat.f_bavail * stat.f_frsize) / (1024 ** 3)
						total_gb = (stat.f_blocks * stat.f_frsize) / (1024 ** 3)
						free_str = "{0:.2f} {1}".format(free_gb, _('GB'))
						total_str = "{0:.2f} {1}".format(total_gb, _('GB'))
					except Exception as e:
						free_str = total_str = _("Unknown")
						print('error: {0}'.format(str(e)))

					server_name = device.split("/")[-1].split(":")[0]
					if not server_name:
						server_name = mountpoint.split("/")[-1]

					# Skip if we've already processed this
					if server_name in processed:
						continue

					processed.add(server_name)

					network_shares.append({
						"server": server_name,
						"mountpoint": mountpoint,
						"freespace": free_str,
						"totalspace": total_str,
						"fstype": fstype.upper()
					})
	except Exception as e:
		print("[BackupSuite] Error reading /proc/mounts: {0}".format(str(e)))
	return network_shares


def get_root_device_type():
	"""Determine the type of the root filesystem device with special cases"""
	try:
		with open("/proc/cmdline", "r") as f:
			cmdline = f.read()

			# Check for special cases before generic checks
			if "root=/dev/mmcblk0p1" in cmdline:
				return "MMC_SWITCH_ERROR"
			elif "root=/dev/mmc" in cmdline:
				return "MMC"
			elif "root=/dev/nand" in cmdline or "root=/dev/mtd" in cmdline:
				return "FLASH"
			elif "root=/dev/sd" in cmdline:
				return "USB"
			elif "root=/dev/hd" in cmdline:
				return "HDD"
	except:
		pass
	return "USB"  # Safer default


def get_device_type_from_sysfs(device_base):
	"""Determine the device type by analyzing sysfs block information."""
	try:
		sysfs_path = "/sys/block/{0}".format(device_base)
		if not exists(sysfs_path):
			return "USB"  # Assume USB if the path doesn't exist

		if device_base.startswith("mmcblk"):
			return "MMC"

		if device_base.startswith("nvme"):
			return "HDD"

		device_path = realpath(join(sysfs_path, "device"))

		if "ata" in device_path or "sata" in device_path:
			return "HDD"

		if "usb" in device_path.lower():
			return "USB"

		uevent_path = join(sysfs_path, "device/uevent")
		if exists(uevent_path):
			with open(uevent_path, "r") as f:
				content = f.read()
				if "DRIVER=mmc" in content:
					return "MMC"
				if "DRIVER=sd" in content and "ata" in content:
					return "HDD"

		rotational_path = join(sysfs_path, "queue/rotational")
		if exists(rotational_path):
			with open(rotational_path, "r") as f:
				if f.read().strip() == "1":
					return "HDD"

	except Exception as e:
		print("[BackupSuite] Error checking sysfs: {0}".format(str(e)))

	return "USB"  # Fallback default


# Global map for icons and scripts
SCRIPTS_DIR = resolveFilename(SCOPE_PLUGINS, "Extensions/BackupSuite/scripts")
ICONS_DIR = resolveFilename(SCOPE_PLUGINS, "Extensions/BackupSuite/img")

DEVICE_PROFILES = {
	"USB": {
		"icon": join(ICONS_DIR, "usb.png"),
		"script": join(SCRIPTS_DIR, "backupusb.sh"),
		"desc": _("USB Storage")
	},
	"MMC": {
		"icon": join(ICONS_DIR, "mmc.png"),
		"script": join(SCRIPTS_DIR, "backupmmc.sh"),
		"desc": _("SD Card")
	},
	"HDD": {
		"icon": join(ICONS_DIR, "hdd.png"),
		"script": join(SCRIPTS_DIR, "backuphdd.sh"),
		"desc": _("Hard Disk")
	},
	"NET": {
		"icon": join(ICONS_DIR, "network.png"),
		"script": join(SCRIPTS_DIR, "backupnet.sh"),
		"desc": _("Network Storage")
	},
	"BA": {
		"icon": join(ICONS_DIR, "multiboot.png"),
		"script": join(SCRIPTS_DIR, "backupba.sh"),
		"desc": _("Barry Allen")
	},
	"RESTORE": {
		"icon": join(ICONS_DIR, "restore.png"),
		"script": "",
		"desc": _("Restore Backup")
	}
}


def get_device_type(device_name, description, model, mountpoint):
	"""Determine device type by combining multiple information sources."""
	# Normalize texts for case-insensitive matching
	desc = (description + " " + model + " " + mountpoint).lower()

	# Search for specific keywords
	if "mmc" in desc or "sd" in desc or "card" in desc or "emmc" in desc:
		return "MMC"
	elif "sata" in desc or "ata" in desc or "hdd" in desc or "hard disk" in desc:
		return "HDD"
	elif "nvme" in desc or "ssd" in desc:
		return "HDD"
	elif "usb" in desc or "flash" in desc or "pen" in desc:
		return "USB"

	# Analyze device name prefix
	if device_name.startswith("mmcblk"):
		return "MMC"
	elif device_name.startswith("nvme"):
		return "HDD"
	elif device_name.startswith("sd"):
		return "USB"

	return "USB"  # Default fallback


def get_available_backup_devices():
	"""Retrieve a list of available backup devices excluding the root filesystem."""
	devices = []
	partitions = harddiskmanager.getMountedPartitions()
	root_device_type = get_root_device_type()

	print("[BackupSuite] Found {0} mounted partitions".format(len(partitions)))
	print("[BackupSuite] Root device type: {0}".format(root_device_type))

	for p in partitions:
		# Always exclude internal root filesystem
		if not p.mountpoint or not ismount(p.mountpoint) or p.mountpoint == "/":
			continue

		# Skip network filesystems (handled separately)
		if hasattr(p, 'filesystem'):
			# Get filesystem type by calling the function
			fs_type = p.filesystem()
			if fs_type and fs_type.lower() in ("cifs", "nfs", "nfs4", "smbfs"):
				print("[BackupSuite] Skipping network filesystem: {0}".format(p.mountpoint))
				continue

		device_name = getattr(p, "device", "") or ""
		description = getattr(p, "description", "") or ""
		model = getattr(p, "model", "") or ""

		# Determine the device type
		device_type = get_device_type(device_name, description, model, p.mountpoint)
		print("[BackupSuite] Device: {0}, Mount: {1}, Desc: {2}, Model: {3} -> Type: {4}".format(
			device_name, p.mountpoint, description, model, device_type))

		# Get device profile with fallback to USB
		profile = DEVICE_PROFILES.get(device_type, DEVICE_PROFILES["USB"])

		# Ensure icon path is valid
		icon_path = getIconPath(profile.get("icon", ""))
		script_path = profile.get("script", "")

		# Verify that the script exists
		if script_path and not exists(script_path):
			print("[BackupSuite] Script not found: {0}".format(script_path))
			script_path = ""

		devices.append({
			"type": device_type,
			"path": p.mountpoint,
			"desc": profile["desc"],
			"icon": icon_path,
			"script": script_path,
			"free": p.free(),
			"total": p.total()
		})

	return devices


def requires_openpli_fix():
	return exists("/usr/lib/enigma2/python/Plugins/PLi")


def get_lang():
	"""Detect the current language code, falling back to 'en' if unsupported or on error."""
	try:
		from Components.config import config
		lng = config.osd.language.value

		if not lng:
			lng = getenv("LANG", "en_US.UTF-8")

		if "." not in lng and "_" in lng:
			lng += ".UTF-8"

		base_lng = lng.split("_")[0] if "_" in lng else lng.split(".")[0]
		base_lng = base_lng[:2] if len(base_lng) > 2 else base_lng

		supported_languages = ["en", "it", "de", "fr", "es", "nl", "pl"]
		return base_lng if base_lng in supported_languages else "en"
	except Exception as e:
		print("[BackupSuite] Language detection error: {0}".format(str(e)))
		return "en"


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
				"blue": self.show_help,
				"info": self.keyInfo,
				"cancel": self.cancel,
				"displayHelp": self.show_help,
				"help": self.show_help,
				"ok": self.deviceSelected,
			},
			-1
		)
		self.setTitle(self.setup_title)
		self.onShown.append(self.init_plugin)
		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		self.setTitle(_("Backup Suite v{0}").format(VERSION))

	def init_plugin(self):
		"""
		# if not self.check_dependencies():
			# self.close()
		# else:
		"""
		self.populateDeviceList()

	def check_dependencies(self):
		"""Verify the presence of required backup scripts for each device type."""
		missing_scripts = []
		print("[BackupSuite] Checking dependencies...")

		for dev_type, profile in DEVICE_PROFILES.items():
			script_path = profile.get("script")
			if not script_path:  # Skip profiles without scripts
				continue

			print("[BackupSuite] Checking script: {0}".format(script_path))

			if not exists(script_path):
				print("[BackupSuite] Script not found: {0}".format(script_path))
				missing_scripts.append(basename(script_path))

		if missing_scripts:
			error_msg = _(
				"Missing backup scripts:\n\n"
				"{0}\n\n"
				"Please reinstall the BackupSuite plugin."
			).format("\n".join(missing_scripts))

			self.session.open(
				MessageBox,
				error_msg,
				MessageBox.TYPE_ERROR
			)
			return False

		print("[BackupSuite] All dependencies satisfied")
		return True

	def populateDeviceList(self):
		"""Populate the device list with available backup devices and special options."""
		print("[BackupSuite] Populating device list...")
		self.devicelist = []
		devices = get_available_backup_devices()
		added_paths = set()

		for dev in devices:
			print("[BackupSuite] Processing device: {0}".format(dev['path']))
			print("  Type: {0}".format(dev['type']))
			print("  Icon: {0} - Exists: {1}".format(dev['icon'], exists(dev['icon'])))
			print("  Script: {0} - Exists: {1}".format(dev['script'], exists(dev['script'])))
			dev_path = dev["path"]

			if dev_path in added_paths:
				print("[BackupSuite] Skipping duplicate path: {0}".format(dev_path))
				continue

			print("[BackupSuite] Processing device at {0} (type: {1})".format(dev_path, dev['type']))

			# Create descriptive name
			short_path = basename(dev_path.rstrip('/'))
			description = "{0} ({1})".format(dev['desc'], short_path)

			self.addDevice(
				_("Backup to {0}").format(description),
				dev["icon"],
				dev["type"],
				dev_path,
				dev["script"]
			)
			added_paths.add(dev_path)
			print("[BackupSuite] Added device: {0} with icon {1}".format(description, dev['icon']))

		# Add special options - only one network option regardless of shares
		network_shares = get_mounted_network_shares()
		if network_shares:
			print("[BackupSuite] Found {0} network shares".format(len(network_shares)))
			print("[BackupSuite] Adding network backup option")
			net_profile = DEVICE_PROFILES["NET"]
			self.addDevice(
				_("Backup to Network"),
				net_profile["icon"],
				"NET",
				None,
				net_profile["script"]
			)

		if exists("/boot/barryhallen"):
			print("[BackupSuite] Adding Barry Allen option")
			ba_profile = DEVICE_PROFILES["BA"]
			self.addDevice(
				_("Barry Allen"),
				ba_profile["icon"],
				"BA",
				None,
				ba_profile["script"]
			)

		print("[BackupSuite] Adding restore option")
		restore_profile = DEVICE_PROFILES["RESTORE"]
		self.addDevice(
			_("Restore Backup"),
			restore_profile["icon"],
			"RESTORE",
			None,
			restore_profile["script"]
		)

		print("[BackupSuite] Total devices in list: {0}".format(len(self.devicelist)))

		# Build the menu items list
		menu_items = []
		for entry in self.devicelist:
			menu_items.append(BackupDeviceEntryComponent(entry))

		self["devicelist"].setList(menu_items)

	def addDevice(self, description, icon, dev_type, dev_path, script_path):
		"""Add a device to the list with all details."""
		self.devicelist.append((description, icon, dev_type, dev_path, script_path))
		print("[BackupSuite] Added device: {0}, {1}, {2}, {3}".format(description, icon, dev_type, dev_path))

	def deviceSelected(self):
		selection = self["devicelist"].getCurrent()
		if selection and isinstance(selection, list) and len(selection) > 0:
			device_tuple = selection[0]
			if isinstance(device_tuple, tuple) and len(device_tuple) >= 5:  # Now 5 elements
				dev_type = device_tuple[2]
				dev_path = device_tuple[3]
				dev_script = device_tuple[4]  # New field for the script

				if dev_type == "NET":
					self.start_net_backup()
				elif dev_type == "RESTORE":
					self.startRestore()
				else:
					# Pass the script to the backup start method
					self.startBackup(dev_type, dev_path, dev_script)
			else:
				print("[BackupSuite] Invalid device tuple: {0}".format(device_tuple))
		else:
			print("[BackupSuite] Invalid selection")

	def startBackup(self, dev_type=None, dev_path=None, dev_script=None):
		"""Start the backup process, optionally using parameters or current selection."""
		if not dev_type or not dev_path:
			selection = self["devicelist"].getCurrent()
			if selection and isinstance(selection, list) and len(selection) > 0:
				device_tuple = selection[0]
				if isinstance(device_tuple, tuple) and len(device_tuple) >= 5:
					if not dev_type:
						dev_type = device_tuple[2]
					if not dev_path:
						dev_path = device_tuple[3]
					if not dev_script:
						dev_script = device_tuple[4]  # Retrieve script if missing

		if dev_type:
			device_names = {
				"MMC": _("SD Card"),
				"USB": _("USB Storage"),
				"HDD": _("Hard Disk"),
				"NET": _("Network Storage"),
				"BA": _("Barry Allen")
			}
			device_name = device_names.get(dev_type, dev_type)

			self.session.openWithCallback(
				# Pass dev_script to confirmation function
				lambda result, dev_type=dev_type, dev_path=dev_path, dev_script=dev_script:
					self.confirmBackup(result, dev_type, dev_path, dev_script),
				MessageBox,
				_("Do you want to make a backup to {0}?\n\nThis may take several minutes.").format(device_name),
				MessageBox.TYPE_YESNO
			)

	def confirmBackup(self, result, dev_type, dev_path, dev_script):
		"""Execute the backup if the user confirmed."""
		if result:
			self.write_enigma2_version()
			self.execute_backup(dev_type, dev_path, dev_script)

	def execute_backup(self, device_type, media_path=None, script_path=None):
		"""Start the backup process using the given script for the device."""
		print("[BackupSuite] Starting backup for: {0} at {1}".format(device_type, media_path or ''))

		if not script_path:
			profile = DEVICE_PROFILES.get(device_type, {})
			script_path = profile.get("script", "")

		# Check if the script exists
		if not script_path or not exists(script_path):
			error_msg = _("Backup script not found for {0}: {1}").format(
				device_type,
				basename(script_path) if script_path else "N/A"
			)
			print("[BackupSuite] {0}".format(error_msg))
			self.session.open(MessageBox, error_msg, MessageBox.TYPE_ERROR)
			return

		print("[BackupSuite] Using script: {0}".format(script_path))

		lang = get_lang()
		title = _("{0} Backup").format(device_type)

		# Build the command
		cmd = "chmod +x '{0}'; '{0}' '{1}' '{2}' '{3}'".format(script_path, lang, device_type, media_path)
		print("[BackupSuite] Executing command: {0}".format(cmd))
		self.session.openWithCallback(self.console_closed, Console, title, [cmd])

	def start_net_backup(self):
		"""Start the network backup process."""
		network_shares = get_mounted_network_shares()

		if not network_shares:
			self.session.open(
				MessageBox,
				_("No network shares mounted! Please mount a share first."),
				MessageBox.TYPE_ERROR
			)
			return

		menu = []
		for share in network_shares:
			display_text = "{0} ({1}) - {2}\n".format(share['server'], share['fstype'], share['mountpoint'])
			display_text += "{0} {1} / {2} {3}".format(_('Free:'), share['freespace'], _('Total:'), share['totalspace'])
			menu.append((display_text, share["mountpoint"]))

		self.session.openWithCallback(
			self.net_share_selected,
			MessageBox,
			_("Select network share for backup:"),
			list=menu
		)

	def net_share_selected(self, selected_path):
		"""Callback for network share selection."""
		if not selected_path:
			return
			
		backup_dir = join(selected_path, "backup")
		
		# Create backup directory if needed
		if not exists(backup_dir):
			try:
				makedirs(backup_dir)
				print("[BackupSuite] Created backup directory: {0}".format(backup_dir))
			except Exception as e:
				error_msg = _("Could not create backup directory: {0}\nError: {1}").format(backup_dir, str(e))
				print("[BackupSuite] {0}".format(error_msg))
				self.session.open(MessageBox, error_msg, MessageBox.TYPE_ERROR)
				return
		
		# Verify we can write to the directory
		if not access(backup_dir, W_OK):
			error_msg = _("No write permission for: {0}").format(backup_dir)
			print("[BackupSuite] {0}".format(error_msg))
			self.session.open(MessageBox, error_msg, MessageBox.TYPE_ERROR)
			return

		self.execute_backup("NET", backup_dir)

	def startRestore(self):
		"""Start the restore process opening the FlashImageConfig with the backup file pattern."""
		file_pattern = get_backup_files_pattern()
		self.session.open(FlashImageConfig, '/media/', file_pattern)

	def flash_image(self):
		"""Open FlashImageConfig to flash a backup image from /media/ with matching file pattern."""
		file_pattern = get_backup_files_pattern()
		self.session.open(FlashImageConfig, '/media/', file_pattern)

	def show_help(self):
		"""Open the help screen."""
		self.session.open(BackupHelpScreen)

	def keyInfo(self):
		"""Open the 'What's New' info screen."""
		self.session.open(WhatisNewInfo)

	def write_enigma2_version(self):
		"""Write the current Enigma2 version string to a file."""
		try:
			from Components.About import getEnigmaVersionString
			with open(ENIGMA2VERSIONFILE, 'w') as f:
				f.write(getEnigmaVersionString())
		except:
			pass

	def console_closed(self, retval=None):
		"""Handle backup process completion and show errors if any."""
		if retval is not None and retval != 0:
			error_msg = ""
			try:
				with open(LOGFILE, "r") as f:
					log_content = f.read()

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
					lines = log_content.splitlines()
					last_lines = "\n".join(lines[-5:]) if len(lines) > 5 else log_content
					error_msg = _("Backup failed! Last errors:") + "\n" + last_lines

			except Exception as e:
				print("[BackupSuite] Error reading log: {0}".format(str(e)))
				error_msg = _("Backup failed! Check log: {0}").format(LOGFILE)

			self.session.open(
				MessageBox,
				error_msg,
				MessageBox.TYPE_ERROR,
				timeout=30
			)

	def cancel(self):
		self.close(False, self.session)


class FlashImageConfig(Screen):
	def __init__(self, session, curdir, matchingPattern=None):
		self.skin = get_skin("flash")
		Screen.__init__(self, session)
		self["Title"].setText(_("Select the folder with backup"))
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText("")
		self["key_yellow"] = StaticText("")
		self["key_blue"] = StaticText("")
		self["curdir"] = StaticText(_("current:  {0}").format(curdir or ''))
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
		self["curdir"].setText(_("Current: {0}").format(current))
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
		"""Handle the green key press: show warning before proceeding with backup."""
		backup_dir = self.get_current_selected()
		if not backup_dir:
			return

		warning_text = "\n"
		if self.dualboot:
			warning_text += _("\nYou are using dual multiboot!")

		message = (
			_("Warning!\nUse at your own risk! Make always a backup before use!\n"
			  "Don't use it if you use multiple ubi volumes in ubi layer!")
			+ warning_text
		)
		self.session.openWithCallback(
			lambda result: self.confirmedWarning(result),
			MessageBox,
			message,
			MessageBox.TYPE_INFO
		)

	def showparameterlist(self):
		"""
		Display parameters and required files information for flashing, depending on the box model.
		"""
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
							text += _("  {0} (maybe ok)").format(name)
							self.founds = True
						if name in no_backup_files:
							text += _("  {0} (maybe error)").format(name)
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
				cmd = "{0} -n '{1}'".format(OFGWRITE_BIN, dir_flash)
			elif ret == "standard":
				text += _("Standard (root and kernel)")
				if self.ForceMode:
					cmd = "{0} -f -r -k '{1}' > /dev/null 2>&1 &".format(OFGWRITE_BIN, dir_flash)
				else:
					cmd = "{0} -r -k '{1}' > /dev/null 2>&1 &".format(OFGWRITE_BIN, dir_flash)
			elif ret == "root":
				text += _("Only root")
				cmd = "{0} -r '{1}' > /dev/null 2>&1 &".format(OFGWRITE_BIN, dir_flash)
			elif ret == "kernel":
				text += _("Only kernel")
				cmd = "{0} -k '{1}' > /dev/null 2>&1 &".format(OFGWRITE_BIN, dir_flash)
			elif ret == "simulate2":
				text += _("Simulate second partition (no write)")
				cmd = "{0} -kmtd3 -rmtd4 -n '{1}'".format(OFGWRITE_BIN, dir_flash)
			elif ret == "standard2":
				text += _("Second partition (root and kernel)")
				cmd = "{0} -kmtd3 -rmtd4 '{1}' > /dev/null 2>&1 &".format(OFGWRITE_BIN, dir_flash)
			elif ret == "rootfs2":
				text += _("Second partition (only root)")
				cmd = "{0} -rmtd4 '{1}' > /dev/null 2>&1 &".format(OFGWRITE_BIN, dir_flash)
			elif ret == "kernel2":
				text += _("Second partition (only kernel)")
				cmd = "{0} -kmtd3 '{1}' > /dev/null 2>&1 &".format(OFGWRITE_BIN, dir_flash)
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
		"""Handle the yellow key action for unzip or backup info display."""
		if self["key_yellow"].getText() == _("Unzip"):
			filename = self.filelist.getFilename()
			if filename and filename.endswith(".zip"):
				self.session.openWithCallback(
					self.doUnzip,
					MessageBox,
					_("Do you really want to unpack {0} ?").format(filename),
					MessageBox.TYPE_YESNO
				)
		elif self["key_yellow"].getText() == _("Backup info"):
			self.session.open(
				MessageBox,
				"\n\n\n{0}".format(self.getBackupInfo()),
				MessageBox.TYPE_INFO
			)

	def getBackupInfo(self):
		"""Return the content of the VERSIONFILE in the selected backup directory."""
		backup_dir = self.getCurrentSelected()
		backup_info = ""
		try:
			with open(join(backup_dir, VERSIONFILE), "r") as f:
				backup_info = f.read()
		except:
			pass
		return backup_info

	def doUnzip(self, answer):
		"""Unpack the selected zip file into its directory if confirmed."""
		if answer is True:
			dirname = self.filelist.getCurrentDirectory()
			filename = self.filelist.getFilename()
			if dirname and filename:
				try:
					os_system('unzip -o "{0}" -d "{1}"'.format(join(dirname, filename), dirname))
					self.filelist.refresh()
					self.update_ui()
				except:
					pass

	def KeyBlue(self):
		"""Handle blue key: prompt confirmation to delete the selected backup."""
		if self["key_blue"].getText() == _("Delete"):
			self.session.openWithCallback(
				self.confirmedDelete,
				MessageBox,
				_("You are about to delete this backup:\n\n{0}\nContinue?").format(self.getBackupInfo()),
				MessageBox.TYPE_YESNO
			)

	def confirmedDelete(self, answer):
		"""Delete the selected backup directory if confirmed."""
		if answer is True:
			backup_dir = self.getCurrentSelected()
			cmdmessage = "echo -e 'Removing backup:   {0}\\n'".format(basename(backup_dir.rstrip('/')))
			cmddelete = "rm -rf '{0}' > /dev/null 2>&1".format(backup_dir)
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

		help_content = _("BackupSuite v{0}\n\n").format(VERSION)
		help_content += _("Welcome to BackupSuite help.\n\n")
		help_content += _("Device List:\n")
		help_content += _("• Use UP/DOWN buttons to navigate through backup options\n")
		help_content += _("• Press OK to select an option\n\n")

		help_content += _("Backup Options:\n")
		help_content += _("• HDD Backup: Full system backup to internal hard drive\n")
		help_content += _("• USB Backup: Create a bootable USB recovery stick\n")
		help_content += _("• MMC Backup: Backup to external storage (eMMC)\n")
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
		whatsnew_path = resolveFilename(SCOPE_PLUGINS, "Extensions/BackupSuite/whatsnew.txt")
		try:
			with open(whatsnew_path) as file:
				self["AboutScrollLabel"].setText(file.read())
		except:
			self["AboutScrollLabel"].setText(_("Change log not available"))


def main(session, **kwargs):
	print("[BackupSuite] Starting plugin...")
	if requires_openpli_fix():
		print("[BackupSuite] OpenPLi detected, applying unmount fix")
		# Only unmount potentially dangerous mounts
		os_system("umount /media/mmc 2>/dev/null")
		os_system("umount /media/sda 2>/dev/null")
		os_system("umount /media/internal 2>/dev/null")
		os_system("umount /media/sdcard 2>/dev/null")  # Added for safety
	else:
		print("[BackupSuite] Not OpenPLi, skipping unmount fix")

	session.open(BackupStart)


def Plugins(path, **kwargs):
	global plugin_path
	plugin_path = path
	description = "{0}, {1}".format(_('Backup and restore your image'), VERSION)
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
