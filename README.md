# binary-diff
Find differences in two binary files. More intelligent than the Windows `fc` utility. Very slow and needs a lot of memory, though.

## Syntax
*options* *input_files*

### *options*
* `-m` *length*, `--minimum-match-length` *length*
  * Only look for matches of at least *length* bytes.
  * The larger the value, the faster the program will run, but the fewer matches will be found.
  * Minimum/default: 1.
  * Maximum: unlimited.
* `-q`, `--quiet`
  * Quiet mode (don't print the `found match` messages that indicate progress).

### *input_files*
* Two binary files to compare.
* The files need not be the same size.

## Output
Excluding the `found match` messages, each output line consists of three values separated by commas:
* Position of the match in the first input file (0 = first byte, empty value = no match).
* Position of the match in the second input file (0 = first byte, empty value = no match).
* Length of the match or the unmatched chunk.

Examples of output lines:
* `123,456,789`: 789 bytes starting from position 123 in the first file are identical to the 789 bytes starting from position 456 in the second file.
* `123,,789`: for the 789 bytes starting from position 123 in the first file, no match was found in the second file.
* `,456,789`: for the 789 bytes starting from position 456 in the second file, no match was found in the first file.

Hint: copy the output to a spreadsheet program as CSV data.

## Example 1
`a.txt`: `ABCDEKLMNOPQRST`

`b.txt`: `FGHIJKLMNOUVWXYZ`

Input: `python binary_diff.py a.txt b.txt`

Output:
```
found match of length 5 (total bytes matched: 5)

"position in a.txt","position in b.txt","length"
0,,5
5,5,5
10,,5
,0,5
,10,6
```

## Example 2
The input files are the PRG ROM data of US and European versions of Super Mario Bros., 32 KiB each.

Input: `python binary_diff.py --minimum-match-length 1024 smb-w.prg smb-e.prg`

Output:
```
found match of length 3543 (total bytes matched: 3543)
found match of length 2538 (total bytes matched: 6081)
found match of length 1355 (total bytes matched: 7436)
found match of length 1128 (total bytes matched: 8564)

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
