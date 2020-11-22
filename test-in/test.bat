@echo off
cls

echo === files a, b ===
python binary_diff.py test\a.txt test\b.txt
echo.

echo === SMB ===
python binary_diff.py --min-match-len 1024 test\smb-w.prg test\smb-e.prg
echo.

echo === SMB with progress ===
python binary_diff.py --min-match-len 1024 --progress test\smb-w.prg test\smb-e.prg
echo.

echo === help ===
python binary_diff.py --help
