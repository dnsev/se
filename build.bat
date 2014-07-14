:: http://sevenzip.sourceforge.jp/chm/cmdline/syntax.htm


ren src SubEdit


:: No script
del .\SubEdit\settings.txt
7z a -t7z package.7z SubEdit\* -mx=9 -mtm=off
del .\Scripts\package.7z
move .\package.7z .\Scripts\package.7z


:: Script
set script=klk
copy .\Scripts\%script%\settings.txt .\SubEdit\settings.txt
7z a -t7z package.7z SubEdit\* -mx=9 -mtm=off
del .\Scripts\%script%\package.7z
del .\SubEdit\settings.txt
move .\package.7z .\Scripts\%script%\package.7z

:: Script
set script=honorifics
copy .\Scripts\%script%\settings.txt .\SubEdit\settings.txt
7z a -t7z package.7z SubEdit\* -mx=9 -mtm=off
del .\Scripts\%script%\package.7z
del .\SubEdit\settings.txt
move .\package.7z .\Scripts\%script%\package.7z


:: 7z a -tzip package.zip SubEdit\* -mx=9 -mtc=off
ren SubEdit src
