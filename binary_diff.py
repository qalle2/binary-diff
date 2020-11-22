"""Compare two binary files."""

import argparse
import os
import sys

def parse_arguments():
    """Parse command line arguments using argparse."""

    parser = argparse.ArgumentParser(
        description="Compare two binary files. The algorithm: repeatedly find the longest prefix "
        "of file 1 in file 2, advance in file 1 and mark the addresses in file 2 as used.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog="Output lines consist of three integers separated by commas: position in file 1, "
        "position in file 2, length. If one of the positions is empty, the line denotes an "
        "unmatched chunk, otherwise a match. Positions start from 0. E.g. \"10,20,3\" means bytes "
        "10-12 in file 1 are identical to bytes 20-22 in file 2, and \"40,,5\" means no match in "
        "file 2 was found for bytes 40-44 in file 1."
    )

    parser.add_argument(
        "-m", "--min-match-len", type=int, default=8, help="minimum length of matches to find"
    )
    parser.add_argument(
        "-d", "--max-distance", type=int, default=-1,
        help="maximum absolute difference of addresses in file1 and file2 (-1 = no limit)"
    )
    parser.add_argument(
        "-p", "--progress", action="store_true",
        help="print messages that indicate progress (to stderr)"
    )
    parser.add_argument(
        "input_file", nargs=2, help="two binary files to compare (need not be the same size)"
    )

    args = parser.parse_args()

    if args.min_match_len < 1:
        sys.exit("Invalid minimum match length.")
    if args.max_distance < -1:
        sys.exit("Invalid maximum match distance.")
    if not os.path.isfile(args.input_file[0]):
        sys.exit("file1 not found.")
    if not os.path.isfile(args.input_file[1]):
        sys.exit("file2 not found.")

    return args

def delete_range(dataRanges, delRng, minNewLength):
    """Delete a range of file addresses.
    dataRanges: list of range() objects
    delRng: range() to delete (must fit completely in one of dataRanges)
    minNewLength: don't recreate leading/trailing parts of old dataRange if they're too short
    return: new dataRanges"""

    # find range to split
    matches = [rng for rng in dataRanges if delRng.start in rng]
    assert len(matches) == 1
    oldRng = matches[0]
    # delete the old range
    dataRanges.remove(oldRng)
    # recreate leading part if long enough
    if delRng.start - oldRng.start >= minNewLength:
        dataRanges.append(range(oldRng.start, delRng.start))
    # recreate trailing part if long enough
    if oldRng.stop - delRng.stop >= minNewLength:
        dataRanges.append(range(delRng.stop, oldRng.stop))
    # sort (or find_longest_common_bytestring() won't return the first one of equally long strings)
    return sorted(dataRanges, key=lambda rng: rng.start)

def find_longest_common_bytestring(handle1, handle2, args):
    """Find the longest common bytestrings in two files.
    args: from argparse
    yield: one (position_in_data1, position_in_data2/None, length) per call"""

    # read file1
    if handle1.seek(0, 2) == 0:
        sys.exit("file1 is empty.")
    handle1.seek(0)
    data1 = handle1.read()

    # read file2
    if handle2.seek(0, 2) == 0:
        sys.exit("file2 is empty.")
    handle2.seek(0)
    data2 = handle2.read()

    # unused chunks in data2
    data2Ranges = [range(len(data2))]

    pos1 = 0
    while pos1 < len(data1):
        # find longest prefix of data1[pos1:] in any unused chunk of data2
        bestMatch = range(args.min_match_len - 1)  # longest match in all of data2
        for rng2 in data2Ranges:
            # find longest prefix of data1[pos1:] in this chunk of data2
            matchLen = None  # longest match
            for testLen in range(len(bestMatch) + 1, min(len(data1) - pos1, len(rng2)) + 1):
                try:
                    offset2 = data2[rng2.start:rng2.stop].index(data1[pos1:pos1+testLen])
                except ValueError:
                    break  # not found
                if args.max_distance != -1 \
                and abs(rng2.start + offset2 - pos1) > args.max_distance:
                    break  # positions in files too far apart
                matchLen = testLen
            if matchLen is not None:
                # new record found; store it
                bestMatch = range(rng2.start + offset2, rng2.start + offset2 + matchLen)

        if len(bestMatch) >= args.min_match_len:
            # match found; output it
            yield (pos1, bestMatch.start, len(bestMatch))
            # delete match from unused chunks of data2
            data2Ranges = delete_range(data2Ranges, bestMatch, args.min_match_len)
            # skip past the match in data1
            pos1 += len(bestMatch)
        else:
            # no match found; advance to next byte in data1
            pos1 += 1

def invert_ranges(ranges, fileSize):
    """Generate address ranges between 0...(fileSize - 1) that are not in ranges.
    ranges: list of range() objects
    yield: one range() per call"""

    prevRng = None  # previous range

    for rng in sorted(ranges, key=lambda r: r.start):
        if prevRng is None and rng.start > 0:
            yield range(rng.start)  # gap before first range
        elif prevRng is not None:
            if rng.start > prevRng.stop:
                yield range(prevRng.stop, rng.start)  # gap between two ranges
        prevRng = rng

    prevStop = 0 if prevRng is None else prevRng.stop
    if fileSize > prevStop:
        yield range(prevStop, fileSize)  # gap after last range

def print_results(matches, inputFiles):
    """Print the results (matches and unmatched parts in both files).
    matches: [(position_in_file1, position_in_file2, length), ...]
    inputFiles: iterable of filenames"""

    try:
        fileSizes = [os.path.getsize(file) for file in inputFiles]
    except OSError:
        sys.exit("Error getting sizes of input files.")

    # initialize results with matches
    results = matches.copy()
    # append unmatched parts in file1 (-1 = no match)
    file1Matches = (range(pos1, pos1 + length) for (pos1, pos2, length) in matches)
    for rng in invert_ranges(file1Matches, fileSizes[0]):
        results.append((rng.start, -1, len(rng)))
    # append unmatched parts in file2 (-1 = no match; sort first)
    file2Matches = (range(pos2, pos2 + length) for (pos1, pos2, length) in matches)
    for rng in invert_ranges(file2Matches, fileSizes[1]):
        results.append((-1, rng.start, len(rng)))
    # sort (-1 comes after all other values)
    results.sort(key=lambda result: (result[0] == -1, result[0], result[1] == -1, result[1]))
    # print (replace -1 with "")
    for result in results:
        print(",".join(("" if n == -1 else str(n)) for n in result))

def main():
    """The main function."""

    args = parse_arguments()

    # find matches
    matches = []  # [(position_in_data1, position_in_data2/None, length), ...]
    try:
        with open(args.input_file[0], "rb") as handle1, open(args.input_file[1], "rb") as handle2:
            for match in find_longest_common_bytestring(handle1, handle2, args):
                matches.append(match)
                if args.progress:
                    print(f"match found at position {match[0]} in file1", file=sys.stderr)
    except OSError:
        sys.exit("Error reading the input files.")

    # print results
    print('"position in file1","position in file2","length"')
    print_results(matches, args.input_file)

if __name__ == "__main__":
    main()
