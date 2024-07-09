# binary-diff
Compare two binary files. The algorithm: repeatedly find the longest prefix of file 1 in file 2, advance in file 1 and mark the addresses in file 2 as used.

Table of contents:
* [Command line arguments](#command-line-arguments)
* [Output format](#output-format)
* [Examples](#examples)
* [To do](#to-do)

## Command line arguments
*options* *file1* *file2*
* *options*: Zero or more of the following, separated by spaces:
  * `-m N` or `--min-match-len N`: Only find matches of at least `N` bytes.
    * `N` is a positive integer.
    * The default is 8.
  * `-d N` or `--max-distance N`: Do not find matches whose addresses differ by more than `N` bytes.
    * `N` is -1 or a greater integer.
    * -1 means there is no limit.
    * The default is -1.
    * This option is experimental! It will let many matches through that don't fulfill the requirement. It should not eliminate correct matches anymore, however.
  * `-t` or `--tabular`: See "Output format" below.
  * `-p` or `--progress`: Print messages that indicate progress.
* *file1* and *file2*: Two binary files to compare.
  * Neither file may be empty.
  * The files need not be the same size.

## Output format
If the `-t` or `--tabular` option is not specified, the output lines will consist of three integers separated by commas: position in file 1, position in file 2, length. If one of the positions is empty, the line denotes an unmatched chunk, otherwise a match. Positions start from 0. E.g. `10,20,3` means bytes 10&ndash;12 in file 1 are identical to bytes 20&ndash;22 in file 2, and `40,,5` means no match in file 2 was found for bytes 40&ndash;44 in file 1.

If the `-t` or `--tabular` option is specified, the results will be printed as a table of inclusive hexadecimal address ranges instead.

## Examples
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

The command `python3 binary_diff.py --tabular a.txt b.txt` will print:
```
file1        0-       8 = file2        9-      11
file1        9-      11 = file2        0-       8
file1       12-      1a = file2       12-      1a
file1       1b-      22 = file2 (nothing)
file1 (nothing)         = file2       1b-      22
```

## To do
* Fix the `--max-distance` option.
