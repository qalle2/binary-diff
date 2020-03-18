@echo off
cls

echo === test.bat: a, b ===
python binary_diff.py test\a.txt test\b.txt
echo.

echo === test.bat: smb ===
python binary_diff.py --min-match-len 1024 test\smb-w.prg test\smb-e.prg
echo.

echo === test.bat: help ===
python binary_diff.py --help
