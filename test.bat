@echo off
cls

echo === test.bat: test 1 ===
python binary_diff.py --quiet test\a.txt test\b.txt
echo.

echo === test.bat: test 2 ===
python binary_diff.py --minimum-match-length 1024 test\smb-w.prg test\smb-e.prg
