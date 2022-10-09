# binary-diff
```
usage: binary_diff.py [-h] [-m MIN_MATCH_LEN] [-d MAX_DISTANCE] [-t] [-p]
                      input_file input_file

Compare two binary files. The algorithm: repeatedly find the longest prefix of
file 1 in file 2, advance in file 1 and mark the addresses in file 2 as used.
Output lines consist of three integers separated by commas: position in file
1, position in file 2, length. If one of the positions is empty, the line
denotes an unmatched chunk, otherwise a match. Positions start from 0. E.g.
'10,20,3' means bytes 10-12 in file 1 are identical to bytes 20-22 in file 2,
and '40,,5' means no match in file 2 was found for bytes 40-44 in file 1.

positional arguments:
  input_file            Two binary files to compare (need not be the same
                        size).

options:
  -h, --help            show this help message and exit
  -m MIN_MATCH_LEN, --min-match-len MIN_MATCH_LEN
                        Minimum length of matches to find. Default=8.
  -d MAX_DISTANCE, --max-distance MAX_DISTANCE
                        Maximum absolute difference of addresses in file1 and
                        file2 (default = -1 = no limit); note: does not work
                        at the moment.
  -t, --tabular         Print results in tabular format instead (hexadecimal
                        address ranges).
  -p, --progress        Print messages that indicate progress.
```

## Example
Suppose we have the following files:
* `a.txt`: `abcdefgh ijklmnop qrstuvwx ABCDEFGH`
* `b.txt`: `ijklmnop abcdefgh qrstuvwx IJKLMNOP`

The command `python3 binary_diff.py a.txt b.txt` will print:
```
"position in file1","position in file2","length"
0,9,9
9,0,9
18,18,9
27,,8
,27,8
```

## To do
* If the `--max-distance` option is used (not -1), the program will incorrectly ignore some matches.
