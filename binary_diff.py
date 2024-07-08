import argparse, os, sys

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Compare two binary files. See README.md for details."
    )

    parser.add_argument("-m", "--min-match-len", type=int, default=8)
    parser.add_argument(
        "-d", "--max-distance", type=int, default=-1, help="Does not work yet!"
    )
    parser.add_argument("-t", "--tabular", action="store_true")
    parser.add_argument("-p", "--progress", action="store_true")
    parser.add_argument("input_file", nargs=2)

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

def delete_range(dataRanges, delRng, minNewLen):
    # delete a range of file addresses
    # dataRanges: list of range() objects
    # delRng: range() to delete (must fit completely in one of dataRanges)
    # minNewLen: don't recreate leading/trailing parts of old dataRange if
    #            they're shorter than this
    # return: new dataRanges

    # find range to split (should always find one result)
    oldRng = [r for r in dataRanges if delRng.start in r][0]
    # delete the old range
    dataRanges.remove(oldRng)
    # recreate leading part if long enough
    if delRng.start - oldRng.start >= minNewLen:
        dataRanges.append(range(oldRng.start, delRng.start))
    # recreate trailing part if long enough
    if oldRng.stop - delRng.stop >= minNewLen:
        dataRanges.append(range(delRng.stop, oldRng.stop))
    # sort (or find_longest_common_bytestr() won't return the first one of
    # equally long strings)
    return sorted(dataRanges, key=lambda r: r.start)

def find_longest_common_bytestr(handle1, handle2, args):
    # find the longest common bytestrings in two files
    # generate: (position_in_data1, position_in_data2/None, length)

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
        # longest match in all of data2
        bestMatch = range(args.min_match_len - 1)
        for rng2 in data2Ranges:
            # find longest prefix of data1[pos1:] in this chunk of data2
            matchLen = None  # longest match
            for testLen in range(
                len(bestMatch) + 1, min(len(data1) - pos1, len(rng2)) + 1
            ):
                try:
                    offset2 = data2[rng2.start:rng2.stop].index(
                        data1[pos1:pos1+testLen]
                    )
                except ValueError:
                    break  # not found
                if args.max_distance != -1 \
                and abs(rng2.start + offset2 - pos1) > args.max_distance:
                    break  # positions in files too far apart
                matchLen = testLen
            if matchLen is not None:
                # new record found; store it
                bestMatch = range(
                    rng2.start + offset2, rng2.start + offset2 + matchLen
                )

        if len(bestMatch) >= args.min_match_len:
            # match found; output it
            yield (pos1, bestMatch.start, len(bestMatch))
            # delete match from unused chunks of data2
            data2Ranges = delete_range(
                data2Ranges, bestMatch, args.min_match_len
            )
            # skip past the match in data1
            pos1 += len(bestMatch)
        else:
            # no match found; advance to next byte in data1
            pos1 += 1

def invert_ranges(ranges, fileSize):
    # generate address ranges between 0...(fileSize - 1) that are not in ranges
    # ranges: list of range() objects
    # generate: range()

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

def print_results(matches, fileSize1, fileSize2, args):
    # print matches and unmatched parts in both files
    # matches: [(position_in_file1, position_in_file2, length), ...]

    # initialize results with matches
    results = matches.copy()
    # append unmatched parts in file1 (-1 = no match)
    file1Matches = (
        range(pos1, pos1 + length) for (pos1, pos2, length) in matches
    )
    for rng in invert_ranges(file1Matches, fileSize1):
        results.append((rng.start, -1, len(rng)))
    # append unmatched parts in file2 (-1 = no match; sort first)
    file2Matches = (
        range(pos2, pos2 + length) for (pos1, pos2, length) in matches
    )
    for rng in invert_ranges(file2Matches, fileSize2):
        results.append((-1, rng.start, len(rng)))
    # sort (-1 comes after all other values)
    results.sort(key=lambda result: (
        result[0] == -1, result[0], result[1] == -1, result[1]
    ))

    # print (replace -1 with "")
    if args.tabular:
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

    print_results(matches, fileSize1, fileSize2, args)

main()
