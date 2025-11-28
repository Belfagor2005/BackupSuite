DESCRIPTION = "Backup Suite"
LICENSE = "GPLv3"
AUTHOR = "Pedro Newbie <pedro.newbie@gmail.com>"
SRC_ORIGIN ?= "git://github.com/Belfagor2005/BackupSuite.git;protocol=https "
SRC_URI := "${SRC_ORIGIN} "
S = "${WORKDIR}/git"

PV = "git${SRCPV}"
PKGV = "git${GITPKGV}"
S = "${WORKDIR}/git"

# don't inherit allarch, it can't work with arch-dependent RDEPENDS
inherit gitpkgv distutils-openplugins gettext python3-compileall

RDEPENDS_${PN} = " \
	mtd-utils \
	mtd-utils-ubifs \
	ofgwrite \
	${@bb.utils.contains("IMAGE_FSTYPES", "tar.bz2", "bzip2" , "", d)} \
	${@bb.utils.contains("MACHINE", "dm8000", "dreambox-buildimage mtd-utils-jffs2" , "", d)} \
	"



FILES_${PN} = "/usr/* /var*"

do_install() {
    cp -af --no-preserve=ownership ${S}/usr* /var* ${D}/
}


do_install_append() {
	find "${D}" -name '*.sh' -exec chmod a+x '{}' ';'
}
