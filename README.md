# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/unicef/adt-press/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                        |    Stmts |     Miss |   Cover |   Missing |
|-------------------------------------------- | -------: | -------: | ------: | --------: |
| adt-press.py                                |       23 |        0 |    100% |           |
| adt\_press/\_\_init\_\_.py                  |        0 |        0 |    100% |           |
| adt\_press/llm/\_\_init\_\_.py              |       18 |        4 |     78% |12-13, 18, 40 |
| adt\_press/llm/glossary\_translation.py     |       16 |        7 |     56% |     24-44 |
| adt\_press/llm/image\_caption.py            |       16 |        6 |     62% |     18-38 |
| adt\_press/llm/image\_crop.py               |       27 |        0 |    100% |           |
| adt\_press/llm/image\_meaningfulness.py     |       14 |        0 |    100% |           |
| adt\_press/llm/language\_detection.py       |       23 |        0 |    100% |           |
| adt\_press/llm/metadata\_extraction.py      |       15 |        0 |    100% |           |
| adt\_press/llm/page\_sectioning.py          |       43 |        0 |    100% |           |
| adt\_press/llm/section\_explanations.py     |       17 |        6 |     65% |     21-42 |
| adt\_press/llm/section\_glossary.py         |       15 |        6 |     60% |     17-36 |
| adt\_press/llm/section\_quiz.py             |       51 |        6 |     88% |22, 29, 31, 36, 38, 40 |
| adt\_press/llm/speech\_generation.py        |       27 |       18 |     33% |     14-53 |
| adt\_press/llm/text\_easy\_read.py          |       15 |        6 |     60% |     17-35 |
| adt\_press/llm/text\_extraction.py          |       18 |        0 |    100% |           |
| adt\_press/llm/text\_translation.py         |       38 |        4 |     89% |26, 30, 37, 39 |
| adt\_press/llm/web\_generation\_activity.py |       67 |       51 |     24% |24-40, 63-163 |
| adt\_press/llm/web\_generation\_html.py     |       35 |       11 |     69% | 24, 57-95 |
| adt\_press/llm/web\_generation\_quiz.py     |        9 |        0 |    100% |           |
| adt\_press/llm/web\_generation\_template.py |        9 |        0 |    100% |           |
| adt\_press/models/\_\_init\_\_.py           |        0 |        0 |    100% |           |
| adt\_press/models/epub.py                   |       60 |        7 |     88% |53-54, 73, 79, 84-85, 116 |
| adt\_press/models/image.py                  |       10 |        0 |    100% |           |
| adt\_press/models/metadata.py               |        8 |        0 |    100% |           |
| adt\_press/models/pdf.py                    |        3 |        0 |    100% |           |
| adt\_press/models/plate.py                  |        9 |        0 |    100% |           |
| adt\_press/models/section.py                |       23 |        0 |    100% |           |
| adt\_press/models/speech.py                 |        2 |        0 |    100% |           |
| adt\_press/models/text.py                   |       35 |        0 |    100% |           |
| adt\_press/models/web.py                    |       13 |        0 |    100% |           |
| adt\_press/nodes/\_\_init\_\_.py            |        0 |        0 |    100% |           |
| adt\_press/nodes/config\_nodes.py           |      263 |       34 |     87% |59, 65, 84, 88, 91, 94, 100, 108, 124, 129, 181-183, 205, 224, 238, 324, 331-348, 362-380, 397, 402, 407, 412 |
| adt\_press/nodes/epub\_nodes.py             |       27 |        2 |     93% |     57-58 |
| adt\_press/nodes/image\_nodes.py            |      109 |       10 |     91% |49, 100, 122-131 |
| adt\_press/nodes/pdf\_nodes.py              |      110 |       11 |     90% |53-63, 167, 215 |
| adt\_press/nodes/plate\_nodes.py            |      150 |       14 |     91% |42, 85-87, 138, 142-144, 160, 213, 218, 222, 226, 308 |
| adt\_press/nodes/report\_nodes.py           |       71 |        4 |     94% |   248-252 |
| adt\_press/nodes/section\_nodes.py          |       95 |       35 |     63% |35, 84, 94, 119-144, 166-180 |
| adt\_press/nodes/speech\_nodes.py           |       24 |       11 |     54% |     13-26 |
| adt\_press/nodes/web\_nodes.py              |      169 |       16 |     91% |73, 86, 88, 90, 94, 98, 103-104, 200-202, 209, 265-266, 313-317 |
| adt\_press/nodes/webpub\_nodes.py           |       86 |        0 |    100% |           |
| adt\_press/pipeline.py                      |       35 |        0 |    100% |           |
| adt\_press/utils/\_\_init\_\_.py            |        0 |        0 |    100% |           |
| adt\_press/utils/encoding.py                |       32 |        7 |     78% |10, 57-60, 65-68 |
| adt\_press/utils/file.py                    |       45 |        0 |    100% |           |
| adt\_press/utils/html.py                    |      159 |       31 |     81% |65, 87, 120-122, 179-191, 223-224, 227, 236, 274, 278, 282, 285, 290-302, 305 |
| adt\_press/utils/image.py                   |       94 |       36 |     62% |25-34, 41-45, 54-60, 77-80, 83, 120-136 |
| adt\_press/utils/languages.py               |        3 |        0 |    100% |           |
| adt\_press/utils/logging.py                 |       72 |       26 |     64% |17-24, 50, 85-87, 100-107, 115-134, 142 |
| adt\_press/utils/pdf.py                     |       18 |        3 |     83% | 47, 52-53 |
| adt\_press/utils/report\_assets.py          |       39 |        2 |     95% |   147-148 |
| adt\_press/utils/sync.py                    |       14 |        0 |    100% |           |
| adt\_press/utils/web\_assets.py             |      174 |        9 |     95% |77, 164-169, 279, 307, 311 |
| tests/test\_clear\_cache.py                 |       45 |        0 |    100% |           |
| tests/test\_encoding.py                     |       39 |        1 |     97% |        64 |
| tests/test\_html\_utils.py                  |      107 |        0 |    100% |           |
| tests/test\_language\_detection.py          |      128 |        1 |     99% |       195 |
| tests/test\_page\_sectioning\_validator.py  |       53 |        0 |    100% |           |
| tests/test\_parameter\_validation.py        |       30 |        0 |    100% |           |
| tests/test\_pdf\_extractor.py               |      116 |        0 |    100% |           |
| tests/test\_pipeline.py                     |       88 |        0 |    100% |           |
| tests/test\_report\_assets.py               |       94 |        0 |    100% |           |
| tests/test\_utils\_image.py                 |       20 |        0 |    100% |           |
| tests/test\_web\_assets.py                  |      247 |        0 |    100% |           |
| tests/test\_web\_generation\_validator.py   |       75 |        0 |    100% |           |
| tools/pdf\_extractor/models.py              |       15 |        1 |     93% |        63 |
| tools/pdf\_extractor/pdf\_extractor.py      |      183 |       52 |     72% |216-218, 230-234, 237-266, 310, 387-475, 479 |
| tools/pdf\_extractor/utils.py               |      326 |      246 |     25% |27, 61-63, 68, 80-115, 125-140, 153-156, 168-173, 176-189, 192-209, 212-236, 245-252, 395-548, 555-586, 614, 638-640, 647, 650-654, 662, 669-687, 690, 694 |
| **TOTAL**                                   | **4014** |  **684** | **83%** |           |


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