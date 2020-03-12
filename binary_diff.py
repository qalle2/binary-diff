"""Compare two binary files."""

import argparse
import os
import sys

def get_file_sizes(files):
    """Get sizes of files in an iterable."""

    try:
        return [os.path.getsize(file) for file in files]
    except OSError:
        sys.exit("Error getting the size of the input files.")

def parse_arguments():
    """Parse command line arguments using argparse."""

    parser = argparse.ArgumentParser(
        description="Compare two binary files by repeatedly finding the longest common bytestring, "
        "not necessarily in the same position.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog="Output lines consist of three integers separated by commas: position in file 1, "
        "position in file 2, length. If one of the positions is empty, the line denotes an "
        "unmatched chunk, otherwise a match. Positions start from 0. E.g. \"10,20,3\" means bytes "
        "10-12 in file 1 are identical to bytes 20-22 in file 2, and \"40,,5\" means no match in "
        "file 2 was found for bytes 40-44 in file 1. Hint: copy the output to a spreadsheet "
        "program as CSV data."
    )

    parser.add_argument(
        "-m", "--minimum-match-length", type=int, default=1,
        help="minimum length of matches to find (smaller = slower)"
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="do not print messages that indicate progress"
    )
    parser.add_argument(
        "input_file", nargs=2, help="two binary files to compare (need not be the same size)"
    )

    args = parser.parse_args()

    # additional validation
    if args.minimum_match_length < 1:
        sys.exit("Invalid minimum match length.")
    if not all(os.path.isfile(file) for file in args.input_file):
        sys.exit("One of the input files does not exist.")
    if min(get_file_sizes(args.input_file)) == 0:
        sys.exit("One of the input files is empty.")

    return args

def find_longest_common_bytestring(data1, data2, data1Ranges, data2Ranges):
    """Find the longest common bytestring in two bytestrings.
    data1, data2: bytes
    data1Ranges, data2Ranges: addresses available in data1/data2: [(start, length), ...]
    return: (position_in_data1/None, position_in_data2/None, length)"""

    # longest common bytestring so far
    maxPos1 = None
    maxPos2 = None
    maxLen = 0

    for (start1, length1) in data1Ranges:
        pos1 = start1
        while start1 + length1 - pos1 >= maxLen + 1:  # bytes_left_in_range1 >= maxLen + 1
            for (start2, length2) in data2Ranges:
                # find longest match (at least maxLen + 1 bytes)
                matchLen = None
                for testLen in range(maxLen + 1, min(start1 + length1 - pos1, length2) + 1):
                    try:
                        pos2 = data2[start2:start2+length2].index(data1[pos1:pos1+testLen])
                    except ValueError:
                        break
                    matchLen = testLen
                # if found, it's a new record
                if matchLen is not None:
                    maxPos1 = pos1
                    maxPos2 = start2 + pos2
                    maxLen = matchLen
            pos1 += 1

    return (maxPos1, maxPos2, maxLen)

def delete_range(dataRanges, delStart, delLength, minNewLength):
    """Delete a range of file addresses.
    dataRanges: [(start, end), ...]
    delStart: position to start deletion from (must be in one of dataRanges)
    delLength: length to delete (must fit in the same dataRange)
    minNewLength: don't recreate leading/trailing parts of old dataRange if they're too short
    return: new dataRanges"""

    # find the range to split
    matches = [
        (start, length) for (start, length) in dataRanges if start <= delStart < start + length
    ]
    assert len(matches) == 1
    (oldStart, oldLength) = matches[0]
    # delete the old range
    dataRanges.remove((oldStart, oldLength))
    # recreate the leading part if it's long enough
    if delStart - oldStart >= minNewLength:
        dataRanges.append((oldStart, delStart - oldStart))
    # recreate the trailing part if it's long enough
    oldEndPlusOne = oldStart + oldLength
    delEndPlusOne = delStart + delLength
    if oldEndPlusOne - delEndPlusOne >= minNewLength:
        dataRanges.append((delEndPlusOne, oldEndPlusOne - delEndPlusOne))
    # sort (or find_longest_common_bytestring() won't return the first one of equally long strings)
    return sorted(dataRanges)

def find_differences(handle1, handle2, settings):
    """Find and differences in two binary files.
    settings: from argparse
    return: matches: [(position_in_file1, position_in_file2, length), ...]"""

    # read the input files
    handle1.seek(0)
    data1 = handle1.read()
    handle2.seek(0)
    data2 = handle2.read()

    # unused chunks in data1/data2: [(start, length), ...]
    data1Ranges = [(0, len(data1))]
    data2Ranges = [(0, len(data2))]

    matches = []  # [(position_in_data1, position_in_data2, length), ...]

    while True:
        # find longest bytestring; exit if too short
        (matchPos1, matchPos2, matchLen) \
        = find_longest_common_bytestring(data1, data2, data1Ranges, data2Ranges)
        if matchLen < settings.minimum_match_length:
            break

        # remember the result
        matches.append((matchPos1, matchPos2, matchLen))

        # mark file address ranges used
        data1Ranges = delete_range(data1Ranges, matchPos1, matchLen, settings.minimum_match_length)
        data2Ranges = delete_range(data2Ranges, matchPos2, matchLen, settings.minimum_match_length)

        if not settings.quiet:
            print("found match of length {:d} (total matched {:d}, unmatched {:d}/{:d})".format(
                matchLen,
                sum(length for (pos1, pos2, length) in matches),
                sum(length for (pos, length) in data1Ranges),
                sum(length for (pos, length) in data2Ranges)
            ))

    return sorted(matches)

def invert_ranges(ranges_, fileSize):
    """Generate address ranges between 0...(fileSize - 1) that are not in ranges_.
    ranges: [(start, length), ...]
    yield: one (start, length) per call"""

    prevStart = None
    for (start, length) in ranges_:
        if prevStart is None:
            # first item
            if start > 0:
                yield (0, start)
        else:
            # other items
            prevEndPlus1 = prevStart + prevLength
            yield (prevEndPlus1, start - prevEndPlus1)
        prevStart = start
        prevLength = length
    # last/only item
    prevEndPlus1 = 0 if prevStart is None else prevStart + prevLength
    if prevEndPlus1 < fileSize:
        yield (prevEndPlus1, fileSize - prevEndPlus1)

def print_results(matches, inputFiles):
    """Print the results (matches and unmatched parts in both files).
    matches: [(position_in_file1, position_in_file2, length), ...]
    inputFiles: iterable of filenames"""

    fileSizes = get_file_sizes(inputFiles)

    # initialize results with matches
    results = matches.copy()
    # append unmatched parts in file1 (-1 = no match)
    file1Matches = ((pos1, length) for (pos1, pos2, length) in matches)
    for (start, length) in invert_ranges(file1Matches, fileSizes[0]):
        results.append((start, -1, length))
    # append unmatched parts in file2 (-1 = no match)
    file2Matches = ((pos2, length) for (pos1, pos2, length) in matches)
    for (start, length) in invert_ranges(file2Matches, fileSizes[1]):
        results.append((-1, start, length))

    # sort (-1 comes after all other values)
    results.sort(key=lambda result: (result[0] == -1, result[0], result[1] == -1, result[1]))
    # print (replace -1 with "")
    for result in results:
        print(",".join(("" if n == -1 else str(n)) for n in result))

def main():
    """The main function."""

    if sys.version_info[0] != 3:
        print("Warning: possibly incompatible Python version.", file=sys.stderr)

    settings = parse_arguments()

    # find matches
    try:
        with open(settings.input_file[0], "rb") as handle1, \
        open(settings.input_file[1], "rb") as handle2:
            matches = find_differences(handle1, handle2, settings)
    except OSError:
        sys.exit("Error reading the input files.")

    if not settings.quiet:
        print()

    # print results
    fileNames = (
        os.path.basename(file).encode("ascii", errors="backslashreplace").decode("ascii")
        for file in settings.input_file
    )
    print('"position in {:s}","position in {:s}","length"'.format(*fileNames))
    print_results(matches, settings.input_file)

if __name__ == "__main__":
    main()
