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


def write(text, newline=True):
	if newline:
		sys.stdout.write(text + "\n")
	else:
		sys.stdout.write(text)
	sys.stdout.flush()


def message01():
	write(_("No supported receiver found!"))


def message02():
	write(_("BACK-UP TOOL, FOR MAKING A COMPLETE BACK-UP"))


def message03():
	write(_("Please be patient, a backup will now be made, this will take about:"))


def message04():
	write(_(" size to be backed up:"))


def message05():
	write(_("not found, the backup process will be aborted!"))


def message06():
	write(_("Some information about the task"))


def message06a():
	write(_("Create: root.ubifs"))


def message07():
	write(_("Create: kerneldump"))


def message09():
	write(_("Additional backup ->"))


def message10():
	write(_("USB Image created in:"))


def message11():
	write(_("and there is made an extra copy in:"))


def message14():
	write(_("Please check the manual of the receiver on how to restore the image."))


def message15():
	write(_("Image creation FAILED!"))


def message16():
	write(_("available"))


def message17():
	write(_("There is a valid USB-flashdrive detected in one of the USB-ports, therefore an extra copy of the back-up image will now be copied to that USB-flashdrive."))
	write(_("This only takes about 20 seconds....."))


def message19():
	write(_("Backup finished and copied to your USB-flashdrive."))


def message20():
	write(_("Full back-up to the harddisk"))


def message21():
	write(_("There is NO valid USB-stick found, so I've got nothing to do."))
	write(" ")
	write(_("PLEASE READ THIS:"))
	write(_("To back-up directly to the USB-stick, the USB-stick MUST contain a file with the name:"))
	write(_("backupstick or"))
	write(_("backupstick.txt"))
	write(" ")
	write(_("If you place an USB-stick containing this file then the back-up will be automatically made onto the USB-stick and can be used to restore the current image if necessary."))
	write(_("The program will exit now."))


def message22():
	write(_("Full back-up direct to USB"))


def message23():
	write(_("The content of the folder is:"))


def message24():
	write(_("Time required for this process:"))


def message25():
	write(_("minutes"))


def message26():
	write(_("Backup done with:"))


def message27():
	write(_("KB per second"))


def message28():
	write(_("Most likely this back-up can't be restored because of it's size, it's simply too big to restore. This is a limitation of the bootloader not of the back-up or the BackupSuite."))


def message29():
	write(_("There COULD be a problem with restoring this back-up because the size of the back-up comes close to the maximum size. This is a limitation of the bootloader not of the back-up or the BackupSuite."))


def message30():
	write(_("* * * WARNING * * *"))
	write(_("Not enough free space on"))


def message31():
	write(_(" to make a back-up!"))


def message32():
	write(_(" MB available space"))


def message33():
	write(_(" MB needed space"))


def message34():
	write(_("The program will abort, please try another medium with more free space to create your back-up."))


def message35():
	write(_("is not executable..."))


def message36():
	write(_("Using your own custom lookuptable.txt from the folder /etc"))


def message37():
	write(_("Version unknown, probably not installed the right way."))


def message38():
	write(_("not installed yet, now installing"))


def message39():
	write(_("Probably you are trying to make the back-up in flash memory"))


def message40():
	write(_("No additional USB-stick found to copy an extra backup"))


def message41():
	write(_("Installed packages contained in this backup:"))


def message42():
	write(_("NFI Image created in:"))


def message42a():
	write(_("Mount point does not exist! Please check your network share configuration."))


def message42b():
	write(_("Not a mounted filesystem! Please mount the network share first."))


def message42c():
	write(_("Write permission denied! Check share permissions."))


def message42d():
	write(_("Insufficient free space on NAS!"))


def message42e():
	write(_("Unable to create backup directories!"))


def message42f():
	write(_("Unable to create the backup marker file!"))


def message43():
	write(_("Full back-up to the MultiMediaCard"))


def message44():
	write(_("Backup started..."))


def message45():
	write(_("Phase 1/3: Preparing backup environment"), newline=True)


def message46():
	write(_("Phase 2/3: Creating backup image"), newline=True)


def message47():
	write(_("Phase 3/3: Finalizing backup"), newline=True)


def message48():
	write(_("Backup completed successfully!"), newline=True)


def message49():
	write(_("Backup statistics:"))


def message49a():
	write(_("Backup size:"))


def message50():
	write(_("Backup progress:"))


def message50a():
	write(_("Backup created in:"))


def message51():
	write(_("Dumping kernel (25%)"))


def message52():
	write(_("Creating root filesystem (50%)"))


def message53():
	write(_("Assembling image (75%)"))


def message54():
	write(_("Making extra copy (90%)"))


def message55():
	write(_("Finalizing (95%)"))


def message56():
	write(_("Backup complete (100%)"))


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
