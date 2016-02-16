"""
hotfuzz v4 - June 2015
MIT License
Kamil Mansuri
github.com/kmans/hotfuzz


Changelog:

v3 - Significant code refactoring, significant speed improvements,
significantly optimized Python 3+ comptability, forced unicode,
removed unicode_literals import dependance, added 'hotfuzz' rapid lookup,
written for speed, returns 1 result
v2 - Removed Levenshtein sequencematching and ext dependancies
v1 - initial fork of fuzzywuzzy by Adam Cohen

"""
"""
The MIT License (MIT)

Copyright (c) 2015 Kamil Mansuri, Adam Cohen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import itertools
from difflib import SequenceMatcher
import re


#Ensures future comptability with Python 3+
import sys
PY3 = sys.version_info[0] >= 3
if PY3:
    unicode = str


class StringProcessor(object):
    """
    This class defines method to process strings in the most
    efficient way. We force unicode for both input and output.
    """

    regex = re.compile(r"(?ui)\W")

    @classmethod
    def replace_with_whitespace(cls, a_string):
        """
        This function replaces any sequence of non letters and non
        numbers with a single white space.
        """
        return cls.regex.sub(u" ", a_string)

    strip = staticmethod(unicode.strip)
    to_lower_case = staticmethod(unicode.lower)
    to_upper_case = staticmethod(unicode.upper)


def full_process(s):
    """Process string by
        -- removing all but letters and numbers
        -- trim whitespace
        -- force to lower case"""

    if s is None:
        return ""

    # Here we will force a return of "" if it is of None, empty, or not valid
    # Merged from validate_string
    try:
        s = unicode(s)
        len(s) > 0
    except:
        return ""

    # Keep only Letters and Numbers (see Unicode docs).
    string_out = StringProcessor.replace_with_whitespace(s)
    # Force into lowercase.
    string_out = StringProcessor.to_lower_case(string_out)
    # Remove leading and trailing whitespaces.
    string_out = StringProcessor.strip(string_out)
    return string_out


def intr(n):
    '''Returns a correctly rounded integer'''
    return int(round(n))


###########################
# Basic Scoring Functions #
###########################

def ratio(s1, s2):

    if s1 is None:
        raise TypeError("s1 is None")
    if s2 is None:
        raise TypeError("s2 is None")
    if len(s1) == 0 or len(s2) == 0:
        return 0

    m = SequenceMatcher(None, s1, s2)
    return intr(100 * m.ratio())


# todo: skip duplicate indexes for a little more speed
def partial_ratio(s1, s2):
    """"Return the ratio of the most similar substring
    as a number between 0 and 100."""

    if s1 is None:
        raise TypeError("s1 is None")
    if s2 is None:
        raise TypeError("s2 is None")
    if len(s1) == 0 or len(s2) == 0:
        return 0

    if len(s1) <= len(s2):
        shorter = s1
        longer = s2
    else:
        shorter = s2
        longer = s1

    m = SequenceMatcher(None, shorter, longer)
    blocks = m.get_matching_blocks()

    # each block represents a sequence of matching characters in a string
    # of the form (idx_1, idx_2, len)
    # the best partial match will block align with at least one of those blocks
    #   e.g. shorter = "abcd", longer = XXXbcdeEEE
    #   block = (1,3,3)
    #   best score === ratio("abcd", "Xbcd")
    scores = []
    for block in blocks:
        long_start = block[1] - block[0] if (block[1] - block[0]) > 0 else 0
        long_end = long_start + len(shorter)
        long_substr = longer[long_start:long_end]

        m2 = SequenceMatcher(None, shorter, long_substr)
        r = m2.ratio()
        if r > .995:
            return 100
        else:
            scores.append(r)

    return int(100 * max(scores))


##############################
# Advanced Scoring Functions #
##############################

def _process_and_sort(s):
    """Return a cleaned string with token sorted."""
    # pull tokens
    tokens = full_process(s).split()

    # sort tokens and join
    sorted_string = u" ".join(sorted(tokens))
    return sorted_string.strip()


# Sorted Token
#   find all alphanumeric tokens in the string
#   sort those tokens and take ratio of resulting joined strings
#   controls for unordered string elements
def _token_sort(s1, s2, partial=True):

    if s1 is None:
        raise TypeError("s1 is None")
    if s2 is None:
        raise TypeError("s2 is None")

    sorted1 = _process_and_sort(s1)
    sorted2 = _process_and_sort(s2)

    if partial:
        return partial_ratio(sorted1, sorted2)
    else:
        return ratio(sorted1, sorted2)


def token_sort_ratio(s1, s2):
    """Return a measure of the sequences' similarity between 0 and 100
    but sorting the token before comparing.
    """
    return _token_sort(s1, s2, partial=False)


def partial_token_sort_ratio(s1, s2):
    """Return the ratio of the most similar substring as a number between
    0 and 100 but sorting the token before comparing.
    """
    return _token_sort(s1, s2, partial=True)


def _token_set(s1, s2, partial=True):
    """Find all alphanumeric tokens in each string...
        - treat them as a set
        - construct two strings of the form:
            <sorted_intersection><sorted_remainder>
        - take ratios of those two strings
        - controls for unordered partial matches"""

    if s1 is None:
        raise TypeError("s1 is None")
    if s2 is None:
        raise TypeError("s2 is None")

    p1 = full_process(s1)
    p2 = full_process(s2)

    # pull tokens
    tokens1 = set(full_process(p1).split())
    tokens2 = set(full_process(p2).split())

    intersection = tokens1.intersection(tokens2)
    diff1to2 = tokens1.difference(tokens2)
    diff2to1 = tokens2.difference(tokens1)

    sorted_sect = " ".join(sorted(intersection))
    sorted_1to2 = " ".join(sorted(diff1to2))
    sorted_2to1 = " ".join(sorted(diff2to1))

    combined_1to2 = sorted_sect + " " + sorted_1to2
    combined_2to1 = sorted_sect + " " + sorted_2to1

    # strip
    sorted_sect = sorted_sect.strip()
    combined_1to2 = combined_1to2.strip()
    combined_2to1 = combined_2to1.strip()

    if partial:
        ratio_func = partial_ratio
    else:
        ratio_func = ratio

    pairwise = [
        ratio_func(sorted_sect, combined_1to2),
        ratio_func(sorted_sect, combined_2to1),
        ratio_func(combined_1to2, combined_2to1)
    ]
    return max(pairwise)


def token_set_ratio(s1, s2):
    return _token_set(s1, s2, partial=False)


def partial_token_set_ratio(s1, s2):
    return _token_set(s1, s2, partial=True)

###################
# Combination API #
###################


# Weighted Ratio
def WRatio(s1, s2):
    """Return a measure of the sequences' similarity between 0 and 100,
    using different algorithms.
    """

    p1 = full_process(s1)
    p2 = full_process(s2)

    # should we look at partials?
    try_partial = True
    unbase_scale = .95
    partial_scale = .90

    base = ratio(p1, p2)
    try:
        len_ratio = float(max(len(p1), len(p2))) / min(len(p1), len(p2))
    except ZeroDivisionError:
        len_ratio = 0

    # if strings are similar length, don't use partials
    if len_ratio < 1.5:
        try_partial = False

    # if one string is much much shorter than the other
    if len_ratio > 8:
        partial_scale = .6

    if try_partial:
        partial = partial_ratio(p1, p2) * partial_scale
        ptsor = partial_token_sort_ratio(p1, p2) * unbase_scale * partial_scale
        ptser = partial_token_set_ratio(p1, p2)  * unbase_scale * partial_scale

        return int(max(base, partial, ptsor, ptser))
    else:
        tsor = token_sort_ratio(p1, p2) * unbase_scale
        tser = token_set_ratio(p1, p2) * unbase_scale

        return int(max(base, tsor, tser))


###############################################
# Use extract(), extractBests(), extractOne() #
###############################################


def extract(query, choices, limit=5):
    """Find best matches in a list or dictionary of choices, return a
    list of tuples containing the match and its score. If a dictionery
    is used, also returns the key for each match.
    Arguments:
        query       -- an object representing the thing we want to find
        choices     -- a list or dictionary of objects we are attempting
                       to extract values from. The dictionary should
                       consist of {key: str} pairs.
        limit       -- how many objects we want to return
    """

    if choices is None:
        return []

    # Catch generators without lengths
    try:
        if len(choices) == 0:
            return []
    except TypeError:
        pass

    # Enforce unicode
    query = unicode(query)

    sl = list()

    if isinstance(choices, dict):
        for key, choice in choices.items():
            processed = full_process(choice)
            score = WRatio(query, processed)
            tup = (choice, score, key)
            sl.append(tup)

    else:
        for choice in choices:
            processed = full_process(choice)
            score = WRatio(query, processed)
            tup = (choice, score)
            sl.append(tup)

    sl.sort(key=lambda i: i[1], reverse=True)
    return sl[:limit]


def extractBests(query, choices, score_cutoff=0, limit=5):
    """Find best matches above a score in a list of choices, return a
    list of tuples containing the match and its score.
    Convenience method which returns the choices with best scores, see
    extract() for full arguments list
    Optional parameter: score_cutoff.
        If the choice has a score of less than or equal to score_cutoff
        it will not be included on result list
    """
    best_list = extract(query, choices, limit)
    return list(itertools.takewhile(lambda x: x[1] >= score_cutoff, best_list))


def extractOne(query, choices, score_cutoff=0):
    """Find the best match above a score in a list of choices, return a
    tuple containing the match and its score if it's above the threshold
    or None.
    Convenience method which returns the single best choice, see
    extract() for full arguments list
    Optional parameter: score_cutoff.
        If the best choice has a score of less than or equal to
        score_cutoff we will return none (intuition: not a good enough
        match)
    """
    best_list = extract(query, choices, limit=1)
    if len(best_list) > 0 and best_list[0][1] >= score_cutoff:
        return best_list[0]
    return None


# Simplified hotfuzz quick search using SequenceMatching
def hotfuzz(query, choices):
    seq = {item: SequenceMatcher(None, query, item).ratio() for item in choices}
    return max(seq, key=seq.get)
