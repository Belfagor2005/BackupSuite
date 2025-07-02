#!/bin/bash
# Script to generate .po and .mo files for BackupSuite translations
#
# Prerequisites:
# Requires: gawk, find, xgettext, sed (GNU), python3, msguniq, msgmerge, msgattrib, msgfmt, msginit
#
# Run this script from within the "locale" folder.
# Author: Pr2 (adapted and corrected)
# Version: 1.1-fixed

Plugin="BackupSuite"
FilePath="LC_MESSAGES"

echo "Po files update/creation from script starting..."

# Detect available languages (folders in ./locale/)
languages=($(ls -d ./*/ | sed 's|/$||' | sed 's|./||'))

# Check for GNU sed
localgsed="gsed"
sed --version 2> /dev/null | grep -q "GNU"
if [ $? -eq 0 ]; then
    localgsed="sed"
else
    "$localgsed" --version 2> /dev/null | grep -q "GNU"
    if [ $? -eq 0 ]; then
        echo "GNU sed found: [$localgsed]"
    else
        echo "Error: GNU sed is required."
        exit 1
    fi
fi

# Generate .pot from Python
echo "Creating temporary file: $Plugin-py.pot"
find .. -name "*.py" -exec xgettext --no-wrap -L Python --from-code=UTF-8 -kpgettext:1c,2 --add-comments="TRANSLATORS:" -d $Plugin -o $Plugin-py.pot {} \+
"$localgsed" --in-place $Plugin-py.pot --expression='s/CHARSET/UTF-8/'

# Generate .pot from XML (via xml2po.py)
echo "Creating temporary file: $Plugin-xml.pot"
find .. -name "*.xml" -exec python3 xml2po.py {} \+ > $Plugin-xml.pot

# Merge into a single .pot file
echo "Merging .pot files into: $Plugin.pot"
cat $Plugin-py.pot $Plugin-xml.pot | msguniq --no-wrap -o $Plugin.pot -

# Process each language
for lang in "${languages[@]}" ; do
    POFILE="$lang/$FilePath/$Plugin.po"
    MOFILE="$lang/$FilePath/$Plugin.mo"

    if [ -f "$POFILE" ]; then
        echo "Updating existing translation file: $POFILE"
        msgmerge --backup=none --no-wrap -U "$POFILE" "$Plugin.pot" && touch "$POFILE"
        msgattrib --no-wrap --no-obsolete "$POFILE" -o "$POFILE"
        msgfmt -o "$MOFILE" "$POFILE"
    else
        echo "Creating new translation structure for: $lang"
        mkdir -p "$lang/$FilePath"
        msginit -l "$lang" -o "$POFILE" -i "$Plugin.pot" --no-translator
        msgfmt -o "$MOFILE" "$POFILE"
        echo "New file created: $POFILE (please add it to GitHub)"
    fi
done

# Clean up
rm -f $Plugin-py.pot $Plugin-xml.pot
echo "Po files update/creation from script finished!"
