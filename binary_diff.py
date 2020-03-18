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
        "-m", "--min-match-len", type=int, default=8, help="minimum length of matches to find"
    )
    parser.add_argument(
        "input_file", nargs=2, help="two binary files to compare (need not be the same size)"
    )

    args = parser.parse_args()

    # additional validation
    if args.min_match_len < 1:
        sys.exit("Invalid minimum match length.")
    if not all(os.path.isfile(file) for file in args.input_file):
        sys.exit("One of the input files does not exist.")
    if min(get_file_sizes(args.input_file)) == 0:
        sys.exit("One of the input files is empty.")

    return args

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

def find_longest_common_bytestring(handle1, handle2, minMatchLen):
    """Find the longest common bytestring in two bytestrings (files).
    handle1, handle2: files
    minMatchLen: minimum length of matches to find
    yield: one (position_in_data1, position_in_data2/None, length) per call"""

    # read the input files
    handle1.seek(0)
    data1 = handle1.read()
    handle2.seek(0)
    data2 = handle2.read()

    # unused chunks in data2: [(start, length), ...]
    data2Ranges = [(0, len(data2))]

    pos1 = 0
    while pos1 < len(data1):
        # find longest prefix of data1[pos1:] in any unused chunk of data2
        maxPos2 = None  # position of longest match in all of data2
        maxMatchLen = minMatchLen - 1  # longest match in all of data2
        for (start2, length2) in data2Ranges:
            haystack = data2[start2:start2+length2]
            # find longest prefix of data1[pos1:] in haystack
            matchLen = None  # longest match in this chunk of data2
            for testLen in range(maxMatchLen + 1, min(len(data1) - pos1, length2) + 1):
                try:
                    offset2 = haystack.index(data1[pos1:pos1+testLen])
                except ValueError:
                    break
                matchLen = testLen
            if matchLen is not None:
                # new record found; store it
                maxPos2 = start2 + offset2
                maxMatchLen = matchLen
        if maxPos2 is not None:
            # match found; output it
            yield (pos1, maxPos2, maxMatchLen)
            # delete match from unused chunks of data2
            data2Ranges = delete_range(data2Ranges, maxPos2, maxMatchLen, minMatchLen)
            # skip past the match in data1
            pos1 += maxMatchLen
        else:
            # no match found; advance to next byte in data1
            pos1 += 1

def invert_ranges(ranges_, fileSize):
    """Generate address ranges between 0...(fileSize - 1) that are not in ranges_.
    ranges_: [(start, length), ...]
    yield: one (start, length) per call"""

    # previous range
    prevStart = None
    prevLength = None

    for (start, length) in ranges_:
        if prevStart is None:
            # possible gap before the first range in ranges_
            if start > 0:
                yield (0, start)
        else:
            # possible gap between two ranges in ranges_
            prevEndPlus1 = prevStart + prevLength
            if start > prevEndPlus1:
                yield (prevEndPlus1, start - prevEndPlus1)
        prevStart = start
        prevLength = length
    # possible gap after the last range in ranges_
    prevEndPlus1 = 0 if prevStart is None else prevStart + prevLength
    if fileSize > prevEndPlus1:
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
    file2Matches = sorted((pos2, length) for (pos1, pos2, length) in matches)  # sort first
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
    matches = []  # [(position_in_data1, position_in_data2/None, length), ...]
    try:
        with open(settings.input_file[0], "rb") as handle1, \
        open(settings.input_file[1], "rb") as handle2:
            for match in find_longest_common_bytestring(handle1, handle2, settings.min_match_len):
                matches.append(match)
    except OSError:
        sys.exit("Error reading the input files.")

    # print results
    fileNames = (
        os.path.basename(file).encode("ascii", errors="backslashreplace").decode("ascii")
        for file in settings.input_file
    )
    print('"position in {:s}","position in {:s}","length"'.format(*fileNames))
    print_results(matches, settings.input_file)

if __name__ == "__main__":
    main()
