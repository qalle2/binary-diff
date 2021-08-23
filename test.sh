clear

echo "=== Files a, b ==="
python3 binary_diff.py test-in/a.txt test-in/b.txt
echo

echo "=== Files a, b (progress messages) ==="
python3 binary_diff.py --progress test-in/a.txt test-in/b.txt
echo

echo "=== SMB (min-match-len 1024) ==="
python3 binary_diff.py --min-match-len 1024 test-in/smb-w.prg test-in/smb-e.prg
echo
