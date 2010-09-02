# `comicnamer`

`comicnamer` is a utility which to rename files from `some.comic.01.cbr` to `Some Comic - [01] - The Issue Name.cbr` (by retrieving the issue name using data from [`comicvine_api`](http://github.com/swc/comicvine_api))

## To install

You can easily install `comicnamer` via `easy_install`

    sudo easy_install comicnamer

This installs the `comicnamer` command-line tool (and the `comicvine_api` module as a requirement)

If you wish to install the latest (non-stable) development version from source, download the latest version of the code, either from <http://github.com/swc/comicnamer/tarball/master> or by running:

    git clone git://github.com/swc/comicnamer.git

..then `cd` into the directory, and run:

    sudo python setup.py install

Example terminal session (you can skip the `curl` line if you have already downloaded and extracted [the above link](http://github.com/swc/comicnamer/tarball/master)):

    $ cd Downloads/
    $ curl -L http://github.com/swc/comicnamer/tarball/master | gunzip - | tar -x -
    $ ls
    swc-comicnamer-02b9a4c/
    $ cd swc-comicnamer-02b9a4c/
    $ sudo python setup.py install
    Password:
    [...]
    Finished processing dependencies for comicnamer==1.0

## Bugs?

Please make tickets for any possible bugs or feature requests, or if you discover a filename format that comicnamer cannot parse (as long as a reasonably common format, and has enough information to be parsed!), or if you are struggling with the a custom configuration (please state your desired filename output, and what problems you are encountering)

## Basic usage

From the command line, simply run:

    comicnamer the.file.01.cbr

For example:

    $ comicnamer y.the.last.man.01.cbr
    ####################
    # Starting comicnamer
    # Found 1 issues
    # Processing file: y.the.last.man.01.cbr
	# Detected series: Y - The Last Man (issue: 1)
    ComicVine Search Results:
	1 -> Y: The Last Man # http://api.comicvine.com/series/9419/
    Automatically selecting only result
    ####################
    # Old filename: y.the.last.man.01.cbr
    # New filename: Y The Last Man - [001] - Unmanned.cbr
    Rename?
    ([y]/n/a/q) 

Enter `y` then press `return` and the file will be renamed to "Y The Last Man - [001] - Unmanned.cbr". You can also simply press `return` to select the default option, denoted by the surrounding `[]`

If there are multiple series' with the same (or similar) names or languages, you will be asked to select the correct one - "The Walking Dead" is a good example of this:

    $ comicnamer the.walking.dead.01.cbr
    ####################
    # Starting comicnamer
    # Found 1 issues
    # Processing the.walking.dead.01.cbr
    ComicVine Search Results:
    1 -> The Walking Dead # http://api.comicvine.com/series/18166/
	2 -> The Walking Dead # http://api.comicvine.com/series/30345/
	3 -> The Walking Dead # http://api.comicvine.com/series/19273/
	4 -> Image Firsts: The Walking Dead # http://api.comicvine.com/series/32361/
	5 -> The Walking Dead Special Edition # http://api.comicvine.com/series/34065/
	6 -> Deadman: Deadman Walking # http://api.comicvine.com/series/29972/
    Enter choice (first number, ? for help):    

To select the first result, enter `1` then `return`, to select the second enter `2` and so on. The link after `#` goes to the relevant [comicvine.com][comicvine] page, which will contain information and images to help you select the correct series.

You can rename multiple files, or an entire directory by using the files or directories as arguments:

    $ comicnamer file1.cbr file2.cbr etc
    $ comicnamer .
    $ comicnamer /path/to/my/folder/
    $ comicnamer ./folder/1/ ./folder/2/

You can skip a specific file by entering `n` (no). If you enter `a` (always) `comicnamer` will rename the remaining files automatically. The suggested use of this is check the first few issues are named correctly, then use `a` to rename the rest.

Note, comicnamer will only descend one level into directories unless the `-r` (or `--recursive`) flag is specified. For example, if you have the following directory structure:

    dir1/
        file1.cbr
        dir2/
            file2.cbr
            file3.cbr

..then running `comicnamer dir1/` will only rename `file1.cbr`, ignoring `dir2/` and its contents.

If you wish to rename all files (file1, file2 and file3), you would run:

    comicnamer --recursive dir1/

## Command line arguments

There are various flags you can use with `comicnamer`, run..

    comicnamer --help

..to see them, and a short description of each.

The most useful are most likely `--batch`, `--selectfirst` and `--always`:

`--selectfirst` will select the first series the search found, but will not automatically rename any issues.

`--always` will ask you select the correct series, then automatically rename all files.

`--batch` will not prompt you for anything. It automatically selects the first series search result, and automatically rename all files (identical to using both `--selectfirst` and `--always`). Use carefully!

## Configs

comicnamer allows you to customise behaviour without modifying the code. To write the default JSON configuration file, which is a good starting point for your modifications, simply run:

    comicnamer --save=./mycomicnamerconfig.json

To use your custom configuration, you must either specify the location using `comicnamer --config=/path/to/mycomicnamerconfig.json` or place the file at `~/.comicnamer.json` (a file named `.comicnamer.json` in your home directory)

**Important:** If comicnamer's default settings change and your saved config contains the old settings, you may experience strange behaviour or bugs (the config may contain a buggy `filename_patterns` regex, for example). It is recommended you remove config options you are not altering (particularly `filename_patterns`). If you experience any strangeness, try disabling your custom configuration (moving it away from `~/.comicnamer.json`)

If for example you wish to change the default extensions recognized by comicnamer, modify the extensions listed in `valid_extensions`. Your config file would look something like:

    {
        "valid_extensions": ["cbr", "cbz"]
    }

For an always up-to-date description of all config options, see the comments in [`config_defaults.py`](http://github.com/swc/comicnamer/blob/master/comicnamer/config_defaults.py)

# Custom output filenames

If you wish to change the output filename format, there are several options you must change:

- One for a file with an issue name (`filename_with_issue`). Example input: `y.the.last.man.01.unmanned.cbr`
- One for a file *without* an issue name (`filename_without_issue`). Example input: `the.walking.dead.01.cbr`

Say you want the format `Series Name 001 Issue Name.cbr`, your `filename_with_issue` option would be:

    %(seriesname)s %(issue)s %(issuename)s%(ext)s

The formatting language used is Python's string formatting feature, which you can read about in the Python documentation, [6.6.2. String Formatting Operations](http://docs.python.org/library/stdtypes.html#string-formatting). Basically it's just `%()s` and the name element you wish to use between `( )`

Note `ext` contains the extension separator symbol, usually `.` - for example `.cbr`

Then you need to make a variant without the `issuename` section:

`filename_without_issue`:

    %(seriesname)s %(issue)s%(ext)s

There are yet two more options you may want to change, `issue_single` and `issue_separator`

`issue_single` is the Python string formatting pattern used to format the issue number. By default it is `%02d` - this simply turns the number `1` to `01`, and keeps `24` as `24`

If you do not want any padding in your numbers, you could change this to `%d` - this would result in filenames such as `Series - [3] - Issue Name.cbr` (or `Series 3 Issue Name.cbr` using your custom name, as described above)

The `issue_separator` option is for multi-issue files. When multiple issues are detected in one file (such as `Air.01-02.cbr`), this string is used to join the issue numbers together. By default it is `-` which results in filenames such as `Air - [01-02] - ... .cbr`

You could change this to `, `, and by altering the `filename_*` options you could create filenames such as..

    Series - [01, 02] - Issue Name.cbr

By default, comicnamer will sanitise files for the current operating system - either POSIX-compatible (OS X, Linux, FreeBSD) or Windows. You can force Windows compatible filenames by setting the option `windows_safe_filenames` to True

You can remove spaces in characters by adding a space to the option `custom_filename_character_blacklist` and changing the option `replace_blacklisted_characters_with` to `.`

`normalize_unicode_filenames` attempts to replace Unicode characters with their unaccented ASCII equivalent (`å` becomes `a` etc). Any untranslatable characters are removed.

`selectfirst` and `always_rename` mirror the command line arguments `--selectfirst` and `--always` - one automatically selects the first series search result, the other always renames files. Setting both to True is equivalent to `--batch`. `recursive` also mirrors the command line argument

# Custom filename parsing pattern

`comicnamer` comes with a set of patterns to parse a majority of common (and many uncommon) comic file names. If these don't parse your files, you can write custom patterns.

The patterns are regular expressions, compiled with the [`re.VERBOSE` flag](http://docs.python.org/library/re.html#re.VERBOSE). Each pattern must contain several named groups.

Named groups are like regular groups, but the group starts with `?P<thegroupname>`. For example:

    (?P<seriesname>.+?)

All patterns must contain a named group `seriesname` - this is of course the name of the series the filename contains.

You must also match an issue number group. For simple, single issue files use the group `issuenumber`

If you wish to match multiple issues in one file, there two options:

- `issuenumber1` `issuenumber2` etc - match any number of issue numbers (can be non-consecutive), or..
- Two groups, `issuenumberstart` and `issuenumberend` - you match the first and last numbers in the filename. If the start number is 2, and the end number is 5, the file contains issues [2, 3, 4, 5].
