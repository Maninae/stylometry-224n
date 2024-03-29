import os
from os.path import join, isdir
import pickle
import random

"""
This script is designed for one-time use.
It will take the directories of authors, with files of books inside,
and reorganize it into one file of all the author's text.

After trimming, the file is split into consecutive chunks of 100 words,
and distributed into train/val/test with ratio 80/10/10 resp.
"""

DATA_DIR = "Gutenberg" # change this to be actual dir
OUTPUT_DIR = "data"
TRAIN_DIR = join(OUTPUT_DIR, "train")
VAL_DIR = join(OUTPUT_DIR, "val")
TEST_DIR = join(OUTPUT_DIR, "test")


TRIM_MARGIN = 300
THRESHOLD = 4 * TRIM_MARGIN
CHUNK_LENGTH = 150

def get_author_dirs(path=DATA_DIR):
    print("Retrieving the authors under: %s" % path)

    def is_author_name(dirname, sep=' '):
        for word in dirname.split(sep):
            if not word.isalpha():
                return False
        return True

    alist = [d for d in os.listdir(path) if is_author_name(d, sep='_')]
    print("We found authors: %s" % str(alist))
    return alist

def get_texts_in_dir(adir):
    author_text = [] # enourmous list of words from all texts under the author

    print("Getting texts from author %s." % adir)
    author_files = [f for f in os.listdir(join(DATA_DIR, adir)) if f[-4:] == '.txt']
    print("Found texts: %s" % author_files)

    for fil in author_files:
        with open(join(DATA_DIR, adir, fil), 'r') as f:
            contents = f.read().split()

        print("length of content (# tokens) for %s, %d." % (fil, len(contents)))
        if len(contents) < THRESHOLD:
            print("File %s has < %d words. Skipping." % (fil, THRESHOLD))

        # Trim each document, to get rid of table of contents and the like
        contents = contents[TRIM_MARGIN:-TRIM_MARGIN]

        # Cut to multiple of 150. Don't want a chunk bridging two documents later
        truncate_length = (len(contents) // CHUNK_LENGTH) * CHUNK_LENGTH
        contents = contents[:truncate_length]
        author_text.extend(contents)

    print("Aggregated text has %d tokens (author %s)." % (len(author_text), adir))
    return author_text

def distribute_into_output_dir(authorname, author_text):
    assert(len(author_text) % CHUNK_LENGTH == 0)
    print("Distributing chunks into dir for %s" % authorname)

    for split in [TRAIN_DIR, VAL_DIR, TEST_DIR]:
        if not isdir(join(split, authorname)):
            print("Made new dir for %s, split %s" % (authorname, split))
            os.makedirs(join(split, authorname))

    index = 0
    chop = 0
    while chop < len(author_text):

        # access a chunk
        chunk = author_text[chop:chop+CHUNK_LENGTH]
        payload = ' '.join(chunk)
        chop += CHUNK_LENGTH

        # Determine if it goes into train, dev, test
        diceroll = random.random()
        split_dir = TRAIN_DIR if diceroll < 0.8 else (VAL_DIR if diceroll < 0.9 else TEST_DIR)

        chunk_name = "%s__%010d.txt" % (authorname, index) # have author, and index padded up to 10 places

        destination = join(split_dir, authorname, chunk_name)

        # put in destination under author with that name
        with open(destination, 'w') as f:
            f.write(payload)

        index += 1
        if index % 100 == 0:
            print("At index %d..." % index)

    print("Done. total %d chunks (of 150 words) created." % index)

if __name__ == "__main__":
    author_dirs = get_author_dirs()
    existing_adirs = get_author_dirs(path=TEST_DIR) # any split works (except train, removed from those for space)

    remaining_adirs = set(author_dirs) - set(existing_adirs)
    print("The remaining authors are: %s" % str(remaining_adirs))
    errored_authors = []

    for adir in remaining_adirs: # adir is the author name string
        try:
            author_text = get_texts_in_dir(adir)
            distribute_into_output_dir(adir, author_text)
        except Exception as e:
            print("Got error: %s" % str(e))
            print("Author %s may not be finished!" % adir)
            errored_authors.append(adir)
