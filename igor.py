#!/usr/bin/env python3

import sys
import argparse
import urllib.request
import re
from bs4 import BeautifulSoup


_is_main = __name__ == "__main__"
PROG_BAR_LEN = 25


def update_progress_bar(current_words, total_words):
    """Updates the syserr progress bar.

    Largely based on JoeLinux's answer to 'Text Progress Bar in the Console' at
    http://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
    """
    percent = min(current_words / total_words, 1)
    hashes = '#' * int(round(percent * PROG_BAR_LEN))
    spaces = ' ' * (PROG_BAR_LEN - len(hashes))
    sys.stderr.write("\rGenerating words: [{0}] {1} of {2}".format(
        hashes + spaces, min(current_words, total_words), total_words))
    sys.stderr.flush()

"""
TODO:
- somehow a y got through as a word? add that to the tests
- alphabetize, add functionality, and clean up argparse tags
- -f option should also create a new file if the passed file doesn't exist? maybe...
- add docs
- add basic message with how-to-use, examples
- move fn's to another file?
- bad-single-letter-words needs to be language-based
- add a short test suite--how do others do it?
- cached words?
- if unique word-count doesn't change after certain threshold, break
- use other sites? i.e. dictionary.com
- deal with weird chars (unicode?)
- cool percentage-finished info used by homebrew, pip, etc
- how to get onto homebrew/pip?

- args:
    - verbose: each word added with its src (article name, article url?)
    - provide url to use as corpus
    - spellchecking functionality? (also how do those work?)
    - -S for a word must occur on a minimum number of pages (instead of just a minimum number
        of times)
    - -P option to scour exactly P pages for words
    - option to allow unicode chars
    - option to stop removing 'misc-words' (wrong single-len words)


"""

# General constants
NEWLINE = "\n"
SPACE = " "

PARSER_DESCRIPTION = "igor scours the grimy depths of the web " + \
    "to generate a custom body of words at your every questionably-evil " + \
    "bidding."

# Error messages
ERR_LANG = "Could not find a page with the given language code."

# Default arg values
DEFAULT_MAX_PAGES = float("inf")
# DEFAULT_MAX_PAGES = 1
DEFAULT_WORD_NUM = 1000
DEFAULT_OVERWRITE = False
DEFAULT_LANGUAGE = "en"
DEFAULT_APPEARANCE_COUNT = 1

# Regex constants
REGEX_APOST_OLD = "\\'"
REGEX_APOST_NEW = "'"
REGEX_BAD_SINGLE_LETTERS = "(?<=\s)[EUYeuy](?=\s)"

# URL's
WIKI_RANDOM_URL_1 = "https://"
WIKI_RANDOM_URL_2 = ".wikipedia.org/wiki/Special:Random"
WIKI_LANG_URL = "https://en.wikipedia.org/wiki/List_of_Wikipedias#Wikipedia_edition_codes"

# Testing...
TEST_TEXT = open("bashing.txt", "r").read() # get from bashing.txt


def escape_every_char(w):
    if len(w) == 0: return ""
    sl = "\\"
    return sl + sl.join(list(w))


def total_regex_with_args(caps=False, chars="", full_regex=None):
    if full_regex is not None: return full_regex

    lookback = "(?<=\s|\()"
    lookahead = "(?=\s|\.|,|;|:|\))"

    caps_first = "A-Z" if caps else ""
    caps_vowels = "AEIOUY" if caps else ""
    extra_chars = escape_every_char(chars)

    first_main_chars = "[" + extra_chars + caps_first + "a-z]*"
    vowel = "[" + caps_vowels + "aeiouy]+"
    second_main_chars = "[" + extra_chars + "a-z]*"

    main = first_main_chars + vowel + second_main_chars
    r = lookback + main + lookahead
    # print(r)
    return r



# Optional tags: format is [args_key, tag_names...]
WORD_NUM = ["n", "-n"]
WORD_NUM_MSG = "number of words to generate"
WORD_NUM_META = "num-words"
MAX_PAGES = ["p", "-p"]
MAX_PAGES_MSG = "max html get-requests"
MAX_PAGES_META = "max-http-calls"
FILE = ["f", "-f"]
FILE_META = "output-file"
FILE_MSG = "write results to " + FILE_META
LANG = ["l", "-l"]
LANG_MSG = "language to draw words from"
LANG_META = "language"
CAPS = ["c", "-c"]
CAPS_MSG = "allow words starting with a capital letter (e.g. proper " + \
    "nouns, start-of-sentences, etc.)"
PRESERVE_CAP = ["o", "-o"]
PRESERVE_CAP_MSG = "preserves words' original capitalization"
APPEARANCE_COUNT = ["s", "-s"]
APPEARANCE_COUNT_MSG = "minimum number of times a word must appear to " + \
    "be added to the word list"
APPEARANCE_COUNT_META = "min-appearances"
WORD_CHARS = ["w", "-w"]
WORD_CHARS_MSG = "string of chars to be included as part of a word; e.g., " + \
    "adding `-w @.` would consider jon@gmail.com to be a word"
WORD_CHARS_META = "string-of-chars"
WORD_REGEX = ["r", "-r"]
WORD_REGEX_MSG = "python3 regex used to determine what constitutes a word " + \
    "(a space is added to the beginning and end of each page's text); " + \
    "the default is " + total_regex_with_args()
WORD_REGEX_META = "python3-regex"
GET_REGEX = ["g", "-g"]
GET_REGEX_MSG = "outputs the regex used to define a word given the " + \
    "current options"


def total_regex():
    return total_regex_with_args(args[CAPS[0]], args[WORD_CHARS[0]], args[WORD_REGEX[0]])


def cleaned_words(w):
    # Add spaces at beg and end for ease-of-regexing purposes
    w = SPACE + w + SPACE
    # print(w)

    # Fix \'
    w = w.replace(REGEX_APOST_OLD, REGEX_APOST_NEW)

    # Get all words
    l = re.findall(total_regex(), w)

    # Remove misc words we don't want... thanks wikipedia
    if args[PRESERVE_CAP[0]]:
        l = [w for w in l if not re.match(REGEX_BAD_SINGLE_LETTERS, w)]
    else:
        l = [w.lower() for w in l if not re.match(REGEX_BAD_SINGLE_LETTERS, w)]

    return l


def is_lang_valid():
    try:
        wiki_random_url = WIKI_RANDOM_URL_1 + args[LANG[0]] + WIKI_RANDOM_URL_2
        str(urllib.request.urlopen(wiki_random_url).read())
    except:
        return False
    return True


# Set up the parser
# TODO: can we simplify this by defining the kwargs/whatever and then calling
# add_argument iteratively?
parser = argparse.ArgumentParser(description=PARSER_DESCRIPTION)
parser.add_argument(*WORD_NUM[1:], default=DEFAULT_WORD_NUM, type=int,
    help=WORD_NUM_MSG, metavar=WORD_NUM_META)
parser.add_argument(*MAX_PAGES[1:], default=DEFAULT_MAX_PAGES, type=int,
    help=MAX_PAGES_MSG, metavar=MAX_PAGES_META)
parser.add_argument(*LANG[1:], default=DEFAULT_LANGUAGE, type=str,
    help=LANG_MSG, metavar=LANG_META)
parser.add_argument(*FILE[1:], type=str, help=FILE_MSG, metavar=FILE_META)
parser.add_argument(*CAPS[1:], default=False, action="store_true",
    help=CAPS_MSG)
parser.add_argument(*PRESERVE_CAP[1:], default=False, action="store_true",
    help=PRESERVE_CAP_MSG)
parser.add_argument(*APPEARANCE_COUNT[1:], default=DEFAULT_APPEARANCE_COUNT,
    type=int, help=APPEARANCE_COUNT_MSG, metavar=APPEARANCE_COUNT_META)
parser.add_argument(*WORD_REGEX[1:], default=None, help=WORD_REGEX_MSG,
    type=str, metavar=WORD_REGEX_META)
parser.add_argument(*WORD_CHARS[1:], default="", help=WORD_CHARS_MSG,
    type=str, metavar=WORD_CHARS_META)
parser.add_argument(*GET_REGEX[1:], default=False, action="store_true",
    help=GET_REGEX_MSG)

args = vars(parser.parse_args())


if args[GET_REGEX[0]] and _is_main:
    regex = total_regex()
    sys.stdout.write(regex + NEWLINE)

else:
    # Generate the url to curl
    wiki_random_url = WIKI_RANDOM_URL_1 + args[LANG[0]] + WIKI_RANDOM_URL_2

    # Is the language option valid?
    if not is_lang_valid():
        raise ValueError(ERR_LANG)

    # Initialize words containers
    # TODO: don't actually need to update words_list as we go
    words_set = set()
    words_list = list()
    words_count = dict()

    # Dealing with piped-in input
    if _is_main and not sys.stdin.isatty():
        # TODO: can we dry the below up a bit?
        l = cleaned_words(sys.stdin.read())
        c = int(args[APPEARANCE_COUNT[0]])
        if c > 1:
            for word in l:
                if word in words_count: words_count[word] += 1
                else: words_count[word] = 1
            words_set = set([w for w in words_count if words_count[w] >= c])
            # words_set = set(filter(lambda w: words_count[w] >= c, words_count))
        else:
            words_list += l
            words_set.update(l)

    # Delving in...
    current_curl = 0
    while current_curl < args[MAX_PAGES[0]]:
        if len(words_set) >= args[WORD_NUM[0]]: break

        current_curl += 1
        # print("Current curl:", current_curl)
        w = str(urllib.request.urlopen(wiki_random_url).read())
        soup = BeautifulSoup(w, "html.parser")

        l = soup.body.find_all("p")
        l = [a.getText() for a in l]
        w = SPACE.join(l)

        # w = TEST_TEXT

        l = cleaned_words(w)

        # print(l)
        # print("-4")

        # Update words containers
        c = int(args[APPEARANCE_COUNT[0]])
        if c > 1:
            for word in l:
                if word in words_count: words_count[word] += 1
                else: words_count[word] = 1
            words_set = set(filter(lambda w: words_count[w] >= c, words_count))
        else:
            words_list += l
            words_set.update(l)

        # if c == 1: print("Non-unique len:", len(words_list))
        # print("Unique len:", len(words_set))
        # print(NEWLINE)

        if _is_main: update_progress_bar(len(words_set), args[WORD_NUM[0]])

        if len(words_set) >= args[WORD_NUM[0]]: break

    # print(words_set)
    # print("-4.5")

    # Final cleanup and output
    # print(NEWLINE)
    # print("Paring...")
    while len(words_set) > args[WORD_NUM[0]]: words_set.pop()
    # print("Sorting...")
    words_list = list(words_set)
    words_list.sort()
    # print("Total unique len:", len(words_list))

    out = NEWLINE.join(words_list) + NEWLINE
    # print(out)
    # print("-5")

    if args[FILE[0]] is not None:
        f = open("wiki_words.txt", "w")
        f.write(out)
        f.close()
    elif _is_main:
        sys.stderr.write(NEWLINE)
        sys.stdout.write(out)
