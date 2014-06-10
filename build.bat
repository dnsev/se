:: http://sevenzip.sourceforge.jp/chm/cmdline/syntax.htm
ren src SubEdit
7z a -t7z package.7z SubEdit\* -mx=9 -mtm=off
7z a -tzip package.zip SubEdit\* -mx=9 -mtc=off
ren SubEdit src
