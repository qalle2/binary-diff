# binary-diff
```
usage: binary_diff.py [-h] [-m MIN_MATCH_LEN] [-p] input_file input_file

Compare two binary files. The algorithm: repeatedly find the longest prefix of file 1 in file 2, advance in file 1 and
mark the addresses in file 2 as used.

positional arguments:
  input_file            two binary files to compare (need not be the same size)

optional arguments:
  -h, --help            show this help message and exit
  -m MIN_MATCH_LEN, --min-match-len MIN_MATCH_LEN
                        minimum length of matches to find (default: 8)
  -p, --progress        print messages that indicate progress (default: False)

Output lines consist of three integers separated by commas: position in file 1, position in file 2, length. If one of
the positions is empty, the line denotes an unmatched chunk, otherwise a match. Positions start from 0. E.g. "10,20,3"
means bytes 10-12 in file 1 are identical to bytes 20-22 in file 2, and "40,,5" means no match in file 2 was found for
bytes 40-44 in file 1.
```

## Examples
```
C:\>type a.txt
abcdefgh ijklmnop qrstuvwx ABCDEFGH

C:\>type b.txt
ijklmnop abcdefgh qrstuvwx IJKLMNOP

C:\>python binary_diff.py a.txt b.txt
"position in a.txt","position in b.txt","length"
0,9,9
9,0,9
18,18,9
27,,8
,27,8
```

```
C:\>python binary_diff.py --minimum-match-length 1024 smb-w.prg smb-e.prg
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
