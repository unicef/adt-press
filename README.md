# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/unicef/adt-press/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                        |    Stmts |     Miss |   Cover |   Missing |
|-------------------------------------------- | -------: | -------: | ------: | --------: |
| adt-press.py                                |       25 |        0 |    100% |           |
| adt\_press/\_\_init\_\_.py                  |        0 |        0 |    100% |           |
| adt\_press/llm/\_\_init\_\_.py              |       20 |        4 |     80% |17-18, 23, 45 |
| adt\_press/llm/glossary\_translation.py     |       14 |        5 |     64% |     24-41 |
| adt\_press/llm/image\_caption.py            |       15 |        5 |     67% |     18-36 |
| adt\_press/llm/image\_crop.py               |       27 |        0 |    100% |           |
| adt\_press/llm/image\_meaningfulness.py     |       14 |        0 |    100% |           |
| adt\_press/llm/metadata\_extraction.py      |       24 |        1 |     96% |        34 |
| adt\_press/llm/page\_sectioning.py          |       44 |        0 |    100% |           |
| adt\_press/llm/section\_explanations.py     |       17 |        5 |     71% |     22-41 |
| adt\_press/llm/section\_glossary.py         |       14 |        5 |     64% |     17-34 |
| adt\_press/llm/section\_quiz.py             |       58 |       35 |     40% |25-27, 32-47, 52-55, 66-93 |
| adt\_press/llm/speech\_generation.py        |       69 |       56 |     19% |31-52, 81-175 |
| adt\_press/llm/text\_easy\_read.py          |       15 |        5 |     67% |     18-34 |
| adt\_press/llm/text\_extraction.py          |       40 |        2 |     95% |    27, 41 |
| adt\_press/llm/text\_translation.py         |       37 |        4 |     89% |27, 31, 38, 40 |
| adt\_press/llm/web\_generation\_activity.py |       66 |       50 |     24% |24-40, 64-161 |
| adt\_press/llm/web\_generation\_edit.py     |       33 |        0 |    100% |           |
| adt\_press/llm/web\_generation\_html.py     |       34 |       10 |     71% | 24, 57-93 |
| adt\_press/llm/web\_generation\_quiz.py     |        8 |        2 |     75% |     17-26 |
| adt\_press/llm/web\_generation\_template.py |        8 |        0 |    100% |           |
| adt\_press/models/\_\_init\_\_.py           |        0 |        0 |    100% |           |
| adt\_press/models/epub.py                   |       61 |        7 |     89% |54-55, 74, 80, 85-86, 117 |
| adt\_press/models/ids.py                    |       14 |        0 |    100% |           |
| adt\_press/models/image.py                  |       11 |        0 |    100% |           |
| adt\_press/models/metadata.py               |       10 |        0 |    100% |           |
| adt\_press/models/pdf.py                    |        4 |        0 |    100% |           |
| adt\_press/models/plate.py                  |       12 |        0 |    100% |           |
| adt\_press/models/quiz.py                   |       15 |        7 |     53% |     21-30 |
| adt\_press/models/section.py                |       11 |        0 |    100% |           |
| adt\_press/models/speech.py                 |        3 |        0 |    100% |           |
| adt\_press/models/text.py                   |        9 |        0 |    100% |           |
| adt\_press/models/web.py                    |       14 |        0 |    100% |           |
| adt\_press/nodes/\_\_init\_\_.py            |        0 |        0 |    100% |           |
| adt\_press/nodes/config\_nodes.py           |      227 |       26 |     89% |103, 125, 144, 178, 259, 266-283, 297-315, 350-352, 357, 362, 372, 377, 427 |
| adt\_press/nodes/epub\_nodes.py             |       29 |        2 |     93% |     61-62 |
| adt\_press/nodes/image\_nodes.py            |      111 |       10 |     91% |53, 104, 126-135 |
| adt\_press/nodes/pdf\_nodes.py              |      134 |       11 |     92% |68-78, 184, 232 |
| adt\_press/nodes/plate\_nodes.py            |      153 |       22 |     86% |45, 65, 91-93, 144, 148-150, 166, 219, 224, 228, 232, 236-240, 314, 328-329 |
| adt\_press/nodes/report\_nodes.py           |       71 |        7 |     90% |186-188, 245-249 |
| adt\_press/nodes/section\_nodes.py          |      105 |       56 |     47% |38, 98-127, 139-164, 186-200 |
| adt\_press/nodes/speech\_nodes.py           |       27 |        6 |     78% |     19-34 |
| adt\_press/nodes/web\_nodes.py              |      242 |       41 |     83% |107-111, 209, 222, 224, 226, 230, 237, 257, 262-263, 281-297, 324-326, 389-392, 397-399, 406, 463-464, 511-515 |
| adt\_press/nodes/webpub\_nodes.py           |       88 |        3 |     97% |    99-101 |
| adt\_press/pipeline.py                      |       35 |        0 |    100% |           |
| adt\_press/utils/\_\_init\_\_.py            |        0 |        0 |    100% |           |
| adt\_press/utils/encoding.py                |       32 |        7 |     78% |10, 57-60, 65-68 |
| adt\_press/utils/file.py                    |       45 |        0 |    100% |           |
| adt\_press/utils/html.py                    |      160 |       14 |     91% |66, 88, 121-123, 224-225, 228, 237, 279, 286, 297, 303, 306 |
| adt\_press/utils/image.py                   |       96 |       37 |     61% |25-34, 41-45, 54-60, 77-82, 85, 124-140 |
| adt\_press/utils/languages.py               |       30 |        1 |     97% |        48 |
| adt\_press/utils/logging.py                 |       83 |       29 |     65% |23-25, 44-51, 77, 112-114, 127-134, 142-161, 169 |
| adt\_press/utils/pdf.py                     |       18 |        3 |     83% | 47, 52-53 |
| adt\_press/utils/report\_assets.py          |       39 |        2 |     95% |   147-148 |
| adt\_press/utils/string.py                  |       10 |        0 |    100% |           |
| adt\_press/utils/sync.py                    |       26 |        2 |     92% |     35-37 |
| adt\_press/utils/web\_assets.py             |      182 |        9 |     95% |98, 185-190, 300, 328, 332 |
| tests/test\_clear\_cache.py                 |       45 |        0 |    100% |           |
| tests/test\_encoding.py                     |       39 |        1 |     97% |        64 |
| tests/test\_html\_utils.py                  |      107 |        0 |    100% |           |
| tests/test\_language\_detection.py          |      128 |        0 |    100% |           |
| tests/test\_page\_sectioning\_validator.py  |       53 |        0 |    100% |           |
| tests/test\_parameter\_validation.py        |       30 |        0 |    100% |           |
| tests/test\_pdf\_extractor.py               |      116 |        0 |    100% |           |
| tests/test\_pipeline.py                     |       94 |        0 |    100% |           |
| tests/test\_report\_assets.py               |       94 |        0 |    100% |           |
| tests/test\_speech\_config.py               |       50 |        0 |    100% |           |
| tests/test\_speech\_generation.py           |       54 |        0 |    100% |           |
| tests/test\_speech\_nodes.py                |       69 |        0 |    100% |           |
| tests/test\_string.py                       |       83 |        0 |    100% |           |
| tests/test\_sync.py                         |       77 |        0 |    100% |           |
| tests/test\_utils\_image.py                 |       20 |        0 |    100% |           |
| tests/test\_web\_assets.py                  |      294 |        0 |    100% |           |
| tests/test\_web\_edit\_validator.py         |       15 |        0 |    100% |           |
| tests/test\_web\_generation\_validator.py   |       75 |        0 |    100% |           |
| tools/pdf\_extractor/models.py              |       15 |        1 |     93% |        63 |
| tools/pdf\_extractor/pdf\_extractor.py      |      183 |       52 |     72% |216-218, 230-234, 237-266, 310, 387-475, 479 |
| tools/pdf\_extractor/utils.py               |      326 |      246 |     25% |27, 61-63, 68, 80-115, 125-140, 153-156, 168-173, 176-189, 192-209, 212-236, 245-252, 395-548, 555-586, 614, 638-640, 647, 650-654, 662, 669-687, 690, 694 |
| **TOTAL**                                   | **4656** |  **791** | **83%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/unicef/adt-press/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/unicef/adt-press/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/unicef/adt-press/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/unicef/adt-press/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Funicef%2Fadt-press%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/unicef/adt-press/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.