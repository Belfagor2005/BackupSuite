DESCRIPTION = "Backup Suite"
LICENSE = "GPLv3"
AUTHOR = "Pedro Newbie <pedro.newbie@gmail.com>"

SRC_URI = "git://github.com/Belfagor2005/BackupSuite.git;protocol=https"
S = "${WORKDIR}/git"

PV = "git${SRCPV}"
PKGV = "git${GITPKGV}"

# Classi corrette che esistono veramente
inherit gitpkgv gettext

RDEPENDS:${PN} = " \
    mtd-utils \
    mtd-utils-ubifs \
    ofgwrite \
    ${@bb.utils.contains("IMAGE_FSTYPES", "tar.bz2", "bzip2", "", d)} \
    ${@bb.utils.contains("MACHINE", "dm8000", "dreambox-buildimage mtd-utils-jffs2", "", d)} \
"

FILES:${PN} = "/usr/* /var/*"

do_install() {
    cp -af --no-preserve=ownership ${S}/usr ${S}/var ${D}/
}

do_install:append() {
    find "${D}" -name '*.sh' -exec chmod a+x '{}' ';'
}