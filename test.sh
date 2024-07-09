clear

echo "=== Files a, b ==="
python3 binary_diff.py test/a.txt test/b.txt
echo

echo "=== Files a, b (progress messages) ==="
python3 binary_diff.py --progress test/a.txt test/b.txt
echo

echo "=== Files a, b (tabular) ==="
python3 binary_diff.py --tabular test/a.txt test/b.txt
echo

echo "=== Files a, b (max-distance 0; should print 0,,30 and 30,30,8 when implemented) ==="
python3 binary_diff.py --max-distance 0 test/maxdist1.txt test/maxdist2.txt
echo

echo "=== SMB (min-match-len 1024) ==="
python3 binary_diff.py --min-match-len 1024 test/smb-w.prg test/smb-e.prg
echo
