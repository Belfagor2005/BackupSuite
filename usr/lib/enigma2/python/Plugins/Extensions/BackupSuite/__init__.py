# -*- coding: utf-8 -*-

from __future__ import print_function  # Per compatibilità print
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import gettext
import os

PluginLanguageDomain = "BackupSuite"
PluginLanguagePath = "Extensions/BackupSuite/locale"


def localeInit():
    lang = language.getLanguage()[:2]
    os.environ["LANGUAGE"] = lang
    gettext.bindtextdomain(
        PluginLanguageDomain,
        resolveFilename(
            SCOPE_PLUGINS,
            PluginLanguagePath))


def _(txt):
    translated = gettext.dgettext(PluginLanguageDomain, txt)
    if translated:
        return translated
    else:
        print(
            "[{0}] fallback to default translation for {1}".format(
                PluginLanguageDomain, txt))
        return gettext.gettext(txt)


localeInit()
language.addCallback(localeInit)
