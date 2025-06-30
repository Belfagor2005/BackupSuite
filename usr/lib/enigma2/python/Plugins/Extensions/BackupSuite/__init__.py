# -*- coding: utf-8 -*-

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import gettext
import os

PluginLanguageDomain = "BackupSuite"
PluginLanguagePath = "Extensions/BackupSuite/locale"


def localeInit():
	lang = language.getLanguage()[:2]
	os.environ["LANGUAGE"] = lang
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
	translated = gettext.dgettext(PluginLanguageDomain, txt)
	if translated:
		return translated
	else:
		print(f"[{PluginLanguageDomain}] fallback to default translation for {txt}")
		return gettext.gettext(txt)


localeInit()
language.addCallback(localeInit)
