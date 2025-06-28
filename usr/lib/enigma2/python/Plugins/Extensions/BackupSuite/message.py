# -*- coding: utf-8 -*-
from os import environ as os_environ, path as os_path
import gettext
import sys

if os_path.isdir("/usr/lib64"):
	BACKUPSUITE_LANGUAGE_PATH = "/usr/lib64/enigma2/python/Plugins/Extensions/BackupSuite/locale"
else:
	BACKUPSUITE_LANGUAGE_PATH = "/usr/lib/enigma2/python/Plugins/Extensions/BackupSuite/locale"


def localeInit():
	gettext.bindtextdomain("BackupSuite", BACKUPSUITE_LANGUAGE_PATH)


localeInit()


def _(txt):
	t = gettext.dgettext("BackupSuite", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t


def message01():
	print(_("No supported receiver found!") + '\n')
	return


def message02():
	print(_("BACK-UP TOOL, FOR MAKING A COMPLETE BACK-UP") + '\n')
	return


def message03():
	sys.stdout.write(_("Please be patient, a backup will now be made, this will take about: ") + '\n')
	return


def message04():
	sys.stdout.write(_(" size to be backed up: ") + '\n')
	return


def message05():
	print(_("not found, the backup process will be aborted!") + '\n')
	return


def message06():
	print(_("Some information about the task") + '\n')
	return


def message06a():
	sys.stdout.write(_("Create: root.ubifs") + '\n')
	return


def message07():
	print(_("Create: kerneldump") + '\n')
	return


def message09():
	sys.stdout.write(_("Additional backup -> ") + '\n')
	return


def message10():
	sys.stdout.write(_("USB Image created in: ") + '\n')
	return


def message11():
	sys.stdout.write(_("and there is made an extra copy in: ") + '\n')
	return


def message14():
	print(_("Please check the manual of the receiver on how to restore the image.") + '\n')
	return


def message15():
	print(_("Image creation FAILED!") + '\n')
	return


def message16():
	sys.stdout.write(_("available ") + '\n')
	return


def message17():
	print(_("There is a valid USB-flashdrive detected in one of the USB-ports, therefore an extra copy of the back-up image will now be copied to that USB-flashdrive.") + '\n')
	print(_("This only takes about 20 seconds.....") + '\n')
	return


def message19():
	print(_("Backup finished and copied to your USB-flashdrive.") + '\n')
	return


def message20():
	sys.stdout.write(_("Full back-up to the harddisk") + '\n')
	return


def message21():
	print(_("There is NO valid USB-stick found, so I've got nothing to do.") + '\n')
	print(" ")
	print(_("PLEASE READ THIS:") + '\n')
	print(_("To back-up directly to the USB-stick, the USB-stick MUST contain a file with the name:") + '\n')
	print(_("backupstick or") + '\n')
	print(_("backupstick.txt") + '\n')
	print(" ")
	print(_("If you place an USB-stick containing this file then the back-up will be automatically made onto the USB-stick and can be used to restore the current image if necessary.") + '\n')
	print(_("The program will exit now.") + '\n')
	return


def message22():
	sys.stdout.write(_("Full back-up direct to USB") + '\n')
	return


def message23():
	print(_("The content of the folder is:") + '\n')
	return


def message24():
	sys.stdout.write(_("Time required for this process: ") + '\n')
	return


def message25():
	print(_("minutes") + '\n')
	return


def message26():
	sys.stdout.write(_("Backup done with: ") + '\n')
	return


def message27():
	print(_("KB per second") + '\n')
	return


def message28():
	print(_("Most likely this back-up can't be restored because of it's size, it's simply too big to restore. This is a limitation of the bootloader not of the back-up or the BackupSuite.") + '\n')
	return


def message29():
	print(_("There COULD be a problem with restoring this back-up because the size of the back-up comes close to the maximum size. This is a limitation of the bootloader not of the back-up or the BackupSuite.") + '\n')
	return


def message30():
	print(_("* * * WARNING * * *") + '\n')
	sys.stdout.write(_("Not enough free space on ") + '\n')
	return


def message31():
	print(_(" to make a back-up!") + '\n')
	return


def message32():
	print(_(" MB available space") + '\n')
	return


def message33():
	print(_(" MB needed space") + '\n')
	return


def message34():
	print(_("The program will abort, please try another medium with more free space to create your back-up.") + '\n')
	return


def message35():
	print(_("is not executable...") + '\n')
	return


def message36():
	print(_("Using your own custom lookuptable.txt from the folder /etc") + '\n')
	return


def message37():
	print(_("Version unknown, probably not installed the right way.") + '\n')
	return


def message38():
	print(_("not installed yet, now installing") + '\n')
	return


def message39():
	print(_("Probably you are trying to make the back-up in flash memory") + '\n')
	return


def message40():
	print(_("No additional USB-stick found to copy an extra backup") + '\n')
	return


def message41():
	print(_("Installed packages contained in this backup:") + '\n')
	return


def message42():
	sys.stdout.write(_("NFI Image created in: ") + '\n')
	return


def message42a():
	print(_("Mount point does not exist! Please check your network share configuration.") + '\n')
	return


def message42b():
	print(_("Not a mounted filesystem! Please mount the network share first.") + '\n')
	return


def message42c():
	print(_("Write permission denied! Check share permissions.") + '\n')
	return


def message42d():
	print(_("Insufficient free space on NAS!") + '\n')
	return


def message42e():
	print(_("Unable to create backup directories!") + '\n')
	return


def message42f():
	print(_("Unable to create the backup marker file!") + '\n')
	return


def message43():
	sys.stdout.write(_("Full back-up to the MultiMediaCard") + '\n')
	return


def message44():
	sys.stdout.write(_("Backup started...") + '\n')
	return


def message45():
	sys.stdout.write(_("Phase 1/3: Preparing backup environment") + '\n')
	return


def message46():
	sys.stdout.write(_("Phase 2/3: Creating backup image") + '\n')
	return


def message47():
	sys.stdout.write(_("Phase 3/3: Finalizing backup") + '\n')
	return


def message48():
	sys.stdout.write(_("Backup completed successfully!") + '\n')
	return


def message49():
	sys.stdout.write(_("Backup statistics:") + '\n')
	return


def message49a():
	sys.stdout.write(_("Backup size:") + '\n')
	return


def message50():
	sys.stdout.write(_("Backup progress:") + '\n')
	return


def message50a():
	sys.stdout.write(_("Backup created in:") + '\n')
	return


def message51():
	sys.stdout.write(_("Dumping kernel (25%)") + '\n')
	return


def message52():
	sys.stdout.write(_("Creating root filesystem (50%)") + '\n')
	return


def message53():
	sys.stdout.write(_("Assembling image (75%)") + '\n')
	return


def message54():
	sys.stdout.write(_("Making extra copy (90%)") + '\n')
	return


def message55():
	sys.stdout.write(_("Finalizing (95%)") + '\n')
	return


def message56():
	sys.stdout.write(_("Backup complete (100%)") + '\n')
	return


if __name__ == "__main__":
	if len(sys.argv) < 3:
		sys.exit("Usage: message.py <LANG> <MESSAGE_FUNCTION>")

	os_environ["LANGUAGE"] = sys.argv[1]
	func_name = sys.argv[2]

	if func_name in globals() and callable(globals()[func_name]):
		try:
			globals()[func_name]()
		except Exception as e:
			sys.stderr.write("Error executing " + func_name + ": " + str(e) + "\n")
			sys.exit(1)
	else:
		sys.stderr.write("Invalid message function: " + func_name + "\n")
		sys.exit(2)
