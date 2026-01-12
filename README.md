# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/unicef/adt-press/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                        |    Stmts |     Miss |   Cover |   Missing |
|-------------------------------------------- | -------: | -------: | ------: | --------: |
| adt-press.py                                |       23 |        0 |    100% |           |
| adt\_press/\_\_init\_\_.py                  |        0 |        0 |    100% |           |
| adt\_press/llm/\_\_init\_\_.py              |       18 |        4 |     78% |12-13, 18, 40 |
| adt\_press/llm/glossary\_translation.py     |       14 |        5 |     64% |     24-41 |
| adt\_press/llm/image\_caption.py            |       15 |        5 |     67% |     18-36 |
| adt\_press/llm/image\_crop.py               |       27 |        0 |    100% |           |
| adt\_press/llm/image\_meaningfulness.py     |       14 |        0 |    100% |           |
| adt\_press/llm/metadata\_extraction.py      |       23 |        1 |     96% |        33 |
| adt\_press/llm/page\_sectioning.py          |       43 |        0 |    100% |           |
| adt\_press/llm/section\_explanations.py     |       16 |        5 |     69% |     21-40 |
| adt\_press/llm/section\_glossary.py         |       14 |        5 |     64% |     17-34 |
| adt\_press/llm/section\_quiz.py             |       53 |       31 |     42% |23-25, 30-45, 50-53, 64-86 |
| adt\_press/llm/speech\_generation.py        |       68 |       56 |     18% |30-51, 80-174 |
| adt\_press/llm/text\_easy\_read.py          |       14 |        5 |     64% |     17-33 |
| adt\_press/llm/text\_extraction.py          |       37 |        2 |     95% |    24, 38 |
| adt\_press/llm/text\_translation.py         |       36 |        4 |     89% |26, 30, 37, 39 |
| adt\_press/llm/web\_generation\_activity.py |       66 |       50 |     24% |24-40, 64-161 |
| adt\_press/llm/web\_generation\_html.py     |       34 |       10 |     71% | 24, 57-93 |
| adt\_press/llm/web\_generation\_quiz.py     |        8 |        2 |     75% |     17-26 |
| adt\_press/llm/web\_generation\_template.py |        8 |        0 |    100% |           |
| adt\_press/models/\_\_init\_\_.py           |        0 |        0 |    100% |           |
| adt\_press/models/epub.py                   |       60 |        7 |     88% |53-54, 73, 79, 84-85, 116 |
| adt\_press/models/ids.py                    |       11 |        0 |    100% |           |
| adt\_press/models/image.py                  |       11 |        0 |    100% |           |
| adt\_press/models/metadata.py               |       10 |        0 |    100% |           |
| adt\_press/models/pdf.py                    |        4 |        0 |    100% |           |
| adt\_press/models/plate.py                  |       10 |        0 |    100% |           |
| adt\_press/models/quiz.py                   |       15 |        7 |     53% |     21-30 |
| adt\_press/models/section.py                |       12 |        0 |    100% |           |
| adt\_press/models/speech.py                 |        3 |        0 |    100% |           |
| adt\_press/models/text.py                   |        9 |        0 |    100% |           |
| adt\_press/models/web.py                    |       14 |        0 |    100% |           |
| adt\_press/nodes/\_\_init\_\_.py            |        0 |        0 |    100% |           |
| adt\_press/nodes/config\_nodes.py           |      204 |       25 |     88% |64, 86, 105, 139, 220, 227-244, 258-276, 311-313, 318, 323, 328, 333 |
| adt\_press/nodes/epub\_nodes.py             |       28 |        2 |     93% |     58-59 |
| adt\_press/nodes/image\_nodes.py            |      110 |       10 |     91% |50, 101, 123-132 |
| adt\_press/nodes/pdf\_nodes.py              |      133 |       11 |     92% |67-77, 181, 229 |
| adt\_press/nodes/plate\_nodes.py            |      152 |       22 |     86% |44, 64, 87-89, 140, 144-146, 162, 215, 220, 224, 228, 232-236, 310, 324-325 |
| adt\_press/nodes/report\_nodes.py           |       70 |        7 |     90% |185-187, 244-248 |
| adt\_press/nodes/section\_nodes.py          |      101 |       53 |     48% |37, 96-120, 132-157, 179-193 |
| adt\_press/nodes/speech\_nodes.py           |       26 |        6 |     77% |     18-33 |
| adt\_press/nodes/web\_nodes.py              |      170 |       29 |     83% |74, 87, 89, 91, 95, 99, 104-105, 123-132, 193-196, 201-203, 210, 266-267, 314-318 |
| adt\_press/nodes/webpub\_nodes.py           |       86 |        3 |     97% |     96-98 |
| adt\_press/pipeline.py                      |       35 |        0 |    100% |           |
| adt\_press/utils/\_\_init\_\_.py            |        0 |        0 |    100% |           |
| adt\_press/utils/encoding.py                |       32 |        7 |     78% |10, 57-60, 65-68 |
| adt\_press/utils/file.py                    |       45 |        0 |    100% |           |
| adt\_press/utils/html.py                    |      159 |       31 |     81% |65, 87, 120-122, 179-191, 223-224, 227, 236, 274, 278, 282, 285, 290-302, 305 |
| adt\_press/utils/image.py                   |       94 |       36 |     62% |25-34, 41-45, 54-60, 77-80, 83, 120-136 |
| adt\_press/utils/languages.py               |       28 |        1 |     96% |        44 |
| adt\_press/utils/logging.py                 |       72 |       26 |     64% |17-24, 50, 85-87, 100-107, 115-134, 142 |
| adt\_press/utils/pdf.py                     |       18 |        3 |     83% | 47, 52-53 |
| adt\_press/utils/report\_assets.py          |       39 |        2 |     95% |   147-148 |
| adt\_press/utils/string.py                  |       10 |        0 |    100% |           |
| adt\_press/utils/sync.py                    |       24 |        0 |    100% |           |
| adt\_press/utils/web\_assets.py             |      182 |        9 |     95% |98, 185-190, 300, 328, 332 |
| tests/test\_clear\_cache.py                 |       45 |        0 |    100% |           |
| tests/test\_encoding.py                     |       39 |        1 |     97% |        64 |
| tests/test\_html\_utils.py                  |      107 |        0 |    100% |           |
| tests/test\_language\_detection.py          |      128 |        0 |    100% |           |
| tests/test\_page\_sectioning\_validator.py  |       53 |        0 |    100% |           |
| tests/test\_parameter\_validation.py        |       30 |        0 |    100% |           |
| tests/test\_pdf\_extractor.py               |      116 |        0 |    100% |           |
| tests/test\_pipeline.py                     |       88 |        0 |    100% |           |
| tests/test\_report\_assets.py               |       94 |        0 |    100% |           |
| tests/test\_speech\_config.py               |       50 |        0 |    100% |           |
| tests/test\_speech\_generation.py           |       54 |        0 |    100% |           |
| tests/test\_speech\_nodes.py                |       69 |        0 |    100% |           |
| tests/test\_string.py                       |       83 |        0 |    100% |           |
| tests/test\_sync.py                         |      108 |        0 |    100% |           |
| tests/test\_utils\_image.py                 |       20 |        0 |    100% |           |
| tests/test\_web\_assets.py                  |      294 |        0 |    100% |           |
| tests/test\_web\_generation\_validator.py   |       75 |        0 |    100% |           |
| tools/pdf\_extractor/models.py              |       15 |        1 |     93% |        63 |
| tools/pdf\_extractor/pdf\_extractor.py      |      183 |       52 |     72% |216-218, 230-234, 237-266, 310, 387-475, 479 |
| tools/pdf\_extractor/utils.py               |      326 |      246 |     25% |27, 61-63, 68, 80-115, 125-140, 153-156, 168-173, 176-189, 192-209, 212-236, 245-252, 395-548, 555-586, 614, 638-640, 647, 650-654, 662, 669-687, 690, 694 |
| **TOTAL**                                   | **4485** |  **782** | **83%** |           |


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