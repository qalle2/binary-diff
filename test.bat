@echo off
cls

echo === test.bat: a, b (quiet) ===
python binary_diff.py --quiet test\a.txt test\b.txt
echo.

echo === test.bat: a, b ===
python binary_diff.py test\a.txt test\b.txt
echo.

echo === test.bat: smb ===
python binary_diff.py --minimum-match-length 1024 test\smb-w.prg test\smb-e.prg
