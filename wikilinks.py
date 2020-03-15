#!/usr/local/bin/python3
# 20200314161751

import re
import subprocess
import sys
import urllib.parse
from collections import defaultdict

DEFAULT_SEARCH_COMMAND = "/usr/local/bin/rg"
ZETTEL_DIRS = ["/Users/iantay/Library/Mobile Documents/com~apple~CloudDocs/zk"]
uid_title_regex = re.compile(r"\[\[(\d\d\d\d\d\d\d\d\d\d\d\d\d\d)_?([\w ]*)\]\]")
reference_regex = re.compile(r"\[\[(.*)\]\]")
block_reference_regex = re.compile(r"\(\((.*)\)\)")
reference_uid_regex = re.compile(r"\[\[(\d*)_?([\w ]*)\]\]")


class ExternalSearch:
    def __init__(self):
        self.search_cmd = DEFAULT_SEARCH_COMMAND

    def rg_search_in(self, folders, regexp):
        """
        Perform an external search for regexp in folder.
        """
        # -l to return only matching filenames.
        args = [
            self.search_cmd,
            "--iglob",
            "*.md",
            "--ignore-case",
            "-l",
            regexp,
            " ".join(folders),
        ]
        raw_res = self.run(args)
        return [r for r in raw_res.split("\n") if r != ""]

    def rg_search_for_file(self, folders, glob):
        """
        Perform an external search for file names matching glob in folder.
        """
        args = [
            self.search_cmd,
            "--files",
            "--iglob",
            glob,
            " ".join(folders),
        ]
        raw_res = self.run(args)
        return [r for r in raw_res.split("\n") if r != ""]

    def rg_search_for_text(self, folders, regexp):
        """
        Perform an external search for regexp in folder.
        Returns dictionary with filename as key, list of (linenum, line) as value.
        """
        args = [
            self.search_cmd,
            "--iglob",
            "*.md",
            "--line-number",
            "--ignore-case",
            regexp,
            " ".join(folders),
        ]
        raw_res = self.run(args)
        res_split = [r for r in raw_res.split("\n") if r != ""]
        file_to_lines = defaultdict(list)
        for r in res_split:
            # filename:linenum:text
            split_line = r.split(":")
            filename, linenum, line = (
                split_line[0],
                int(split_line[1]),
                split_line[2].strip(" "),
            )
            file_to_lines[filename].append((linenum, line))
        return file_to_lines

    def run(self, args):
        """
        Execute SEARCH_COMMAND to run a search, handle errors & timeouts.
        Return output of stdout as string.
        """
        output = b""
        verbose = False
        if verbose:
            print("cmd:", " ".join(args))
        try:
            output = subprocess.check_output(args, shell=False, timeout=10000)
        except subprocess.CalledProcessError as e:
            if verbose:
                print(
                    "search unsuccessful. retcode={}, cmd={}".format(
                        e.returncode, e.cmd
                    )
                )
                for line in e.output.decode("utf-8", errors="ignore").split("\n"):
                    print("    ", line)
        except subprocess.TimeoutExpired:
            if verbose:
                print("sublime_zk: search timed out:", " ".join(args))
        if verbose:
            print("run verbose logs:")
            print(output.decode("utf-8", errors="ignore"))
        return output.decode("utf-8", errors="ignore").replace("\r", "")


def main():
    data = sys.stdin.readlines()
    search = ExternalSearch()
    for line in data:
        # group 0: 20200314062439_Simple Zettel
        # group 1: 20200314062439
        # group 2: Simple Zettel
        match = uid_title_regex.search(line)
        while match:
            link_text = match.group(1)
            if match.lastindex >= 2 and match.group(2) != "":
                link_text = match.group(2)
            link_uid = match.group(1)
            files = search.rg_search_for_file(ZETTEL_DIRS, "*{}*".format(link_uid))
            if len(files) == 0:
                link_text += " - no link"
                link = ""
            else:
                link = files[0]
                link = urllib.parse.quote(link)
            full_link = "[\[\[{}\]\]]({})".format(link_text, link)
            line = line[:match.start()] + full_link + line[match.end():]
            match = uid_title_regex.search(line)
        print(line)


if __name__ == "__main__":
    main()
