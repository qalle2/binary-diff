import argparse, os, sys

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Compare two binary files. See README.md for details."
    )

    parser.add_argument("-m", "--min-match-len", type=int, default=8)
    parser.add_argument(
        "-d", "--max-distance", type=int, default=-1, help="experimental"
    )
    parser.add_argument("-t", "--tabular", action="store_true")
    parser.add_argument("-p", "--progress", action="store_true")
    parser.add_argument("input_file", nargs=2)

    args = parser.parse_args()

    if args.min_match_len < 1:
        sys.exit("Minimum match length must be 1 or greater.")
    if args.max_distance < -1:
        sys.exit("Maximum match distance must be -1 or greater.")

    if not os.path.isfile(args.input_file[0]):
        sys.exit("file1 not found.")
    if not os.path.isfile(args.input_file[1]):
        sys.exit("file2 not found.")

    return args

def delete_range(dataRanges, delRange, minNewLen):
    # delete a range of file addresses
    # dataRanges: [range1, ...]
    # delRange:   range to delete (must fit completely in one of dataRanges)
    # minNewLen:  don't recreate leading/trailing parts of old dataRange if
    #             they're shorter than this
    # return:     new dataRanges

    # find range to split (should always find one)
    oldRange = [r for r in dataRanges if delRange.start in r][0]
    # delete the old range
    dataRanges.remove(oldRange)
    # recreate leading part if long enough
    range_ = range(oldRange.start, delRange.start)
    if len(range_) >= minNewLen:
        dataRanges.append(range_)
    # recreate trailing part if long enough
    range_ = range(delRange.stop, oldRange.stop)
    if len(range_) >= minNewLen:
        dataRanges.append(range_)
    # sort (otherwise find_longest_common_bytestr() wouldn't return the first
    # one of equally long strings)
    return sorted(dataRanges, key=lambda r: r.start)

def find_longest_common_bytestr(handle1, handle2, args):
    # find the longest common bytestrings in two files
    # generate: (position_in_file1, position_in_file2/None, length)

    # read files
    if handle1.seek(0, 2) == 0:
        sys.exit("file1 is empty.")
    if handle2.seek(0, 2) == 0:
        sys.exit("file2 is empty.")
    handle1.seek(0)
    handle2.seek(0)
    data1 = handle1.read()
    data2 = handle2.read()

    # initialize unused ranges in data2
    data2Ranges = [range(len(data2))]

    # repeatedly find the longest prefix of data1 in data2, advance in data1
    # and mark the range in data2 as used
    pos1 = 0
    while pos1 < len(data1):
        longestMatch = None  # range or None

        for range2 in data2Ranges:
            # ignore range if it can't fulfill the max_distance requirement
            if args.max_distance != -1 and max(
                range2.start - pos1, pos1 - (range2.stop - args.min_match_len)
            ) > args.max_distance:
                continue

            # TODO: ignore remaining matches that violate the max_distance
            # requirement

            if longestMatch is None:
                minTestLen = args.min_match_len
            else:
                minTestLen = len(longestMatch) + 1
            longestMatchInRange2 = None  # int or None
            for testLen in range(
                minTestLen, min(len(data1) - pos1, len(range2)) + 1
            ):
                try:
                    offset2 = data2[range2.start:range2.stop].index(
                        data1[pos1:pos1+testLen]
                    )
                except ValueError:
                    break
                longestMatchInRange2 = testLen

            if longestMatchInRange2 is not None:
                longestMatch = range(
                    range2.start + offset2,
                    range2.start + offset2 + longestMatchInRange2
                )

        if longestMatch is not None:
            yield (pos1, longestMatch.start, len(longestMatch))
            data2Ranges = delete_range(
                data2Ranges, longestMatch, args.min_match_len
            )
            pos1 += len(longestMatch)
        else:
            pos1 += 1

def invert_ranges(ranges, fileSize):
    # generate address ranges between 0...(fileSize - 1) that are not in ranges
    # ranges: list of range() objects
    # generate: range()

    prevRange = None

    for range_ in sorted(ranges, key=lambda r: r.start):
        if prevRange is None and range_.start > 0:
            yield range(range_.start)  # gap before first range
        elif prevRange is not None:
            if range_.start > prevRange.stop:
                # gap between two ranges
                yield range(prevRange.stop, range_.start)
        prevRange = range_

    prevStop = 0 if prevRange is None else prevRange.stop
    if fileSize > prevStop:
        yield range(prevStop, fileSize)  # gap after last range

def print_results(matches, fileSize1, fileSize2, tabularOutput):
    # print matches and unmatched parts in both files
    # matches: [(position_in_file1, position_in_file2, length), ...]

    # initialize results with matches
    results = matches.copy()
    # append unmatched parts in file1 (-1 = no match)
    file1Matches = (
        range(pos1, pos1 + length) for (pos1, pos2, length) in matches
    )
    for range_ in invert_ranges(file1Matches, fileSize1):
        results.append((range_.start, -1, len(range_)))
    # append unmatched parts in file2 (-1 = no match; sort first)
    file2Matches = (
        range(pos2, pos2 + length) for (pos1, pos2, length) in matches
    )
    for range_ in invert_ranges(file2Matches, fileSize2):
        results.append((-1, range_.start, len(range_)))
    # sort (-1 comes after all other values)
    results.sort(key=lambda result: (
        result[0] == -1, result[0], result[1] == -1, result[1]
    ))

    # print (replace -1 with "")
    if tabularOutput:
        for (pos1, pos2, length) in results:
            print("file1 ", end="")
            if pos1 != -1:
                print(f"{pos1:8x}-{pos1+length-1:8x}", end="")
            else:
                print(f"{'(nothing)':17}", end="")
            print(" = file2 ", end="")
            if pos2 != -1:
                print(f"{pos2:8x}-{pos2+length-1:8x}")
            else:
                print("(nothing)")
    else:
        print('"position in file1","position in file2","length"')
        for result in results:
            print(",".join(("" if n == -1 else str(n)) for n in result))

def main():
    args = parse_arguments()

    matches = []  # [(position_in_data1, position_in_data2/None, length), ...]
    try:
        with open(args.input_file[0], "rb") as handle1, \
        open(args.input_file[1], "rb") as handle2:
            for match in find_longest_common_bytestr(handle1, handle2, args):
                matches.append(match)
                if args.progress:
                    print(f"match found at position {match[0]} in file1")
            fileSize1 = handle1.seek(0, 2)
            fileSize2 = handle2.seek(0, 2)
    except OSError:
        sys.exit("Error reading files.")

    print_results(matches, fileSize1, fileSize2, args.tabular)

main()
