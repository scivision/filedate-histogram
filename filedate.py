#!/usr/bin/env python
"""
Plots histogram of dates of files in directory.

Works for Hugo, Jekyll and Git.
"""
from pathlib import Path
from datetime import datetime
import yaml
import re
import shutil
import typing
import subprocess

try:
    import pandas
    from matplotlib.pyplot import show
except ImportError:
    pandas = show = None

GIT = shutil.which("git")
use_git = GIT is not None


def filedates(path: Path, ext: str, debug: bool = False) -> typing.Iterator[datetime]:
    root = Path(p.path).expanduser()
    if not root.is_dir():
        raise NotADirectoryError(root)

    use_header = True
    use_filename = True

    for file in root.glob("*{}".format(p.ext)):
        if use_header:
            date = get_markdown_date(file)
            if debug:
                print('header', file, date)
            if date is not None:
                yield date
                continue
        if use_filename:
            try:
                if debug:
                    print('filename', file)
                yield datetime.strptime(file.name[:10], "%Y-%m-%d")
                continue
            except ValueError:
                pass
        if use_git:
            date = get_gitcommit_date(file)
            if debug:
                print('git', file, date)
            if date is not None:
                yield date
                continue

        if debug:
            print('stat', file)
        yield datetime.utcfromtimestamp(file.stat().st_mtime)


def get_markdown_date(path: Path) -> datetime:
    content = path.read_text(errors="ignore")
    pat = re.compile(r"^-{3}\s*\n([\S\s]+?)\n-{3}\s*\n([\S\s]+)")

    mat = pat.search(content)
    if mat:
        meta = yaml.load(mat.groups()[0], Loader=yaml.BaseLoader)
        if "date" in meta:
            return datetime.strptime(meta["date"], "%Y-%m-%d")

    return None


def get_gitcommit_date(path: Path) -> datetime:

    if not path.is_file():
        return None

    cmd = [GIT, "-C", str(path.parent), "log", "-1", "--format=%cd", "--date=iso", path.name]
    datestr = subprocess.run(cmd, universal_newlines=True, stdout=subprocess.PIPE)
    try:
        date = datetime.strptime(datestr.stdout[:10], "%Y-%m-%d")
    except ValueError:
        date = None

    return date


if __name__ == "__main__":
    from argparse import ArgumentParser

    p = ArgumentParser()
    p.add_argument("path", help="path to filename to analyze")
    p.add_argument("-e", "--ext", help="file extension to analyze", default=".md")
    p.add_argument("--debug", help="print method used to get date", action="store_true")
    p = p.parse_args()

    dates = filedates(p.path, p.ext, p.debug)

    if pandas is not None:
        # http://stackoverflow.com/questions/27365467/python-pandas-plot-histogram-of-dates
        ds = pandas.Series(dates)
        bins = ds.groupby([ds.dt.year, ds.dt.month]).count()
        if show is not None:
            bins.plot(kind="bar")
            show()
