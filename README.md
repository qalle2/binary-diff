# binary-diff
```
usage: binary_diff.py [-h] [-m MINIMUM_MATCH_LENGTH] [-q] input_file input_file

Compare two binary files by repeatedly finding the longest common bytestring, not necessarily in the same position.

positional arguments:
  input_file            two binary files to compare (need not be the same size)

optional arguments:
  -h, --help            show this help message and exit
  -m MINIMUM_MATCH_LENGTH, --minimum-match-length MINIMUM_MATCH_LENGTH
                        minimum length of matches to find (smaller = slower) (default: 1)
  -q, --quiet           do not print messages that indicate progress (default: False)

Output lines consist of three integers separated by commas: position in file 1, position in file 2, length. If one of
the positions is empty, the line denotes an unmatched chunk, otherwise a match. Positions start from 0. E.g. "10,20,3"
means bytes 10-12 in file 1 are identical to bytes 20-22 in file 2, and "40,,5" means no match in file 2 was found for
bytes 40-44 in file 1. Hint: copy the output to a spreadsheet program as CSV data.
```

## Examples
```
C:\>type a.txt
ABCDEKLMNOPQRST

C:\>type b.txt
FGHIJKLMNOUVWXYZ

C:\>python binary_diff.py a.txt b.txt
found match of length 5 at 5/5

"position in a.txt","position in b.txt","length"
0,,5
5,5,5
10,,5
,0,5
,10,6
```

```
C:\>python binary_diff.py --minimum-match-length 1024 smb-w.prg smb-e.prg
found match of length 3543 at 8293/8293
found match of length 2538 at 1869/1869
found match of length 1355 at 31156/31157
found match of length 1128 at 7160/7160

"position in smb-w.prg","position in smb-e.prg","length"
0,,1869
1869,1869,2538
4407,,2753
7160,7160,1128
8288,,5
8293,8293,3543
11836,,19320
31156,31157,1355
32511,,257
,0,1869
,4407,2753
,8288,5
,11836,19321
,32512,256
```
