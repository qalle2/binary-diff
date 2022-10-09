clear

echo "=== Files a, b ==="
python3 binary_diff.py test/a.txt test/b.txt
echo

echo "=== Files a, b (progress messages) ==="
python3 binary_diff.py -p test/a.txt test/b.txt
echo

echo "=== Files a, b (tabular) ==="
python3 binary_diff.py -t test/a.txt test/b.txt
echo

echo "=== SMB (min-match-len 1024) ==="
python3 binary_diff.py -m 1024 test/smb-w.prg test/smb-e.prg
echo
