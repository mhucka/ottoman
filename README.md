Ottoman
=======

Ottoman (_"**O**mniOutliner **T**ext **T**ransf**O**r**ma**tio**n**s"_) is a tool to manipulate metadata and text in an OmniOutliner&nbsp;5 document.

[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg?style=flat-square)](https://choosealicense.com/licenses/bsd-3-clause)
[![Latest release](https://img.shields.io/github/v/release/mhucka/ottoman.svg?style=flat-square&color=b44e88)](https://github.com/mhucka/ottoman/releases)
[![Python](https://img.shields.io/badge/Python-3.6+-brightgreen.svg?style=flat-square)](http://shields.io)


Table of contents
-----------------

* [Introduction](#introduction)
* [Installation](#installation)
* [Usage](#usage)
* [Known issues and limitations](#known-issues-and-limitations)
* [Getting help](#getting-help)
* [Contributing](#contributing)
* [License](#license)
* [Authors and history](#authors-and-history)
* [Acknowledgments](#authors-and-acknowledgments)


Introduction
------------

[OmniOutliner](https://www.omnigroup.com/omnioutliner/) is an outline-oriented, structured document editor for the Mac.  For fans of [this type of program](https://en.wikipedia.org/wiki/Outliner) (and related programs such as the now-defunct [NoteBook](https://www.macworld.com/article/3019913/app-developer-circus-ponies-calls-it-quits.html)), it is an indispensable tool for writing notes, organizing information, planning, and more.  People who also use other tools such as [DEVONthink](https://www.devontechnologies.com/apps/devonthink) will naturally want to put OmniOutliner documents into their databases.   However, when viewing and editing documents in applications outside the database, it can be difficult to determine where the document came from: nothing about the document itself (e.g., not the file path) directly indicates its location in the information hierarchy of the database.  This quickly leads to a problem: when looking at a given document in OmniOutliner, _how do you find out where you stored it in your databse_?

The only practical option is to annotate your OmniOutliner documents with information relevant to how you store them in your database, so that you can find the information somewhere in the document itself.  Adding such annotations manually becomes tedious and error-prone; you want automation to do this for you, but here's the rub: OmniOutliner's scripting facilities (as of version 5.8) _does not provide any access to the [metadata fields](https://support.omnigroup.com/documentation/omnioutliner/mac/5.0.1/en/print/#format-and-metadata) of a document_, nor is there an easy way to perform text substitutions using placeholders in the body of a document.  This frustrating situation drove the author to create Ottoman (_"**O**mniOutliner **T**ext **T**ransf**O**r**ma**tio**n**s"_), a program to manipulate metadata and text in OmniOutliner&nbsp;5 documents.

Ottoman is a command-line tool that offers the ability to add or replace values in a document's metadata as well as perform placeholder text substitutions in the body of a document.  Thus, you can execute command such as

```
ottoman --document mydoc.ooutline --metadata  comments="my comment"  project="my project"
```

Ottoman works by manipulating the document outside of and independently of OmniOutliner &ndash; OmniOutliner does not even have to be running.  Ottoman can modify a document in-place or write it as a new document.  Note that there is the potential for document corruption to occur, so take appropriate precautions and keep backups of all your files. **The author assumes no responsibility for any data corruption or loss that occurs as a result of using Ottoman.**  Ottoman is free software and comes with no guarantees whatsoever.


Installation
------------


Usage
-----



Known issues and limitations
----------------------------

Ottoman works by performing all operations in memory.  If you have an extremely large OmniOutliner document and not enough RAM in your computer, problems may arise.  It is hard to quantify what "extremely large" means, but at a guess, I would say it's probably greater than 1 gigabyte.  While it seems unlikely that anyone could practically work with OmniOutliner documents _that_ large, it is also the case that Ottoman does not check for out-of-memory errors and will behave unpredicably.


Getting help
------------


Contributing
------------


License
-------

This software is Copyright (C) 2020, by Michael Hucka and the California Institute of Technology (Pasadena, California, USA).  This software is freely distributed under a 3-clause BSD type license.  Please see the [LICENSE](LICENSE) file for more information.


Authors and history
---------------------------



Acknowledgments
---------------

This work is a personal project developed by the author, using computing facilities and other resources of the [California Institute of Technology Library](https://www.library.caltech.edu).
