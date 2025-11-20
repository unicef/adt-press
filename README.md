# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/unicef/adt-press/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                        |    Stmts |     Miss |   Cover |   Missing |
|-------------------------------------------- | -------: | -------: | ------: | --------: |
| adt-press.py                                |       23 |        0 |    100% |           |
| adt\_press/\_\_init\_\_.py                  |        0 |        0 |    100% |           |
| adt\_press/llm/\_\_init\_\_.py              |       18 |        4 |     78% |12-13, 18, 40 |
| adt\_press/llm/glossary\_translation.py     |       16 |        0 |    100% |           |
| adt\_press/llm/image\_caption.py            |       16 |        0 |    100% |           |
| adt\_press/llm/image\_crop.py               |       27 |        0 |    100% |           |
| adt\_press/llm/image\_meaningfulness.py     |       14 |        0 |    100% |           |
| adt\_press/llm/metadata\_extraction.py      |       14 |        0 |    100% |           |
| adt\_press/llm/page\_sectioning.py          |       37 |        0 |    100% |           |
| adt\_press/llm/section\_explanations.py     |       17 |        6 |     65% |     21-41 |
| adt\_press/llm/section\_glossary.py         |       15 |        0 |    100% |           |
| adt\_press/llm/section\_metadata.py         |       22 |        1 |     95% |        24 |
| adt\_press/llm/speech\_generation.py        |       23 |        0 |    100% |           |
| adt\_press/llm/text\_easy\_read.py          |       15 |        0 |    100% |           |
| adt\_press/llm/text\_extraction.py          |       18 |        0 |    100% |           |
| adt\_press/llm/text\_translation.py         |       38 |        4 |     89% |26, 30, 37, 39 |
| adt\_press/llm/web\_generation\_html.py     |       78 |       28 |     64% |24, 31-32, 35, 45, 87, 91, 95, 98, 103-113, 116, 131-165 |
| adt\_press/llm/web\_generation\_template.py |        9 |        0 |    100% |           |
| adt\_press/models/\_\_init\_\_.py           |        0 |        0 |    100% |           |
| adt\_press/models/epub.py                   |       50 |        3 |     94% | 53-54, 87 |
| adt\_press/models/image.py                  |       10 |        0 |    100% |           |
| adt\_press/models/metadata.py               |        6 |        0 |    100% |           |
| adt\_press/models/pdf.py                    |        3 |        0 |    100% |           |
| adt\_press/models/plate.py                  |        7 |        0 |    100% |           |
| adt\_press/models/section.py                |       33 |        0 |    100% |           |
| adt\_press/models/speech.py                 |        2 |        0 |    100% |           |
| adt\_press/models/text.py                   |       36 |        0 |    100% |           |
| adt\_press/models/web.py                    |        4 |        0 |    100% |           |
| adt\_press/nodes/\_\_init\_\_.py            |        0 |        0 |    100% |           |
| adt\_press/nodes/config\_nodes.py           |      126 |        5 |     96% |68, 93, 179, 184, 189 |
| adt\_press/nodes/epub\_nodes.py             |       28 |        2 |     93% |     58-59 |
| adt\_press/nodes/image\_nodes.py            |      109 |        2 |     98% |   49, 100 |
| adt\_press/nodes/pdf\_nodes.py              |      108 |        2 |     98% |  167, 215 |
| adt\_press/nodes/plate\_nodes.py            |      135 |        4 |     97% |42, 117, 199, 273 |
| adt\_press/nodes/report\_nodes.py           |       51 |        0 |    100% |           |
| adt\_press/nodes/section\_nodes.py          |       84 |       20 |     76% |31, 94-119 |
| adt\_press/nodes/speech\_nodes.py           |       24 |        0 |    100% |           |
| adt\_press/nodes/web\_nodes.py              |      116 |        6 |     95% |57, 65, 70, 72, 76, 80 |
| adt\_press/nodes/webpub\_nodes.py           |       72 |        0 |    100% |           |
| adt\_press/pipeline.py                      |       35 |        0 |    100% |           |
| adt\_press/utils/\_\_init\_\_.py            |        0 |        0 |    100% |           |
| adt\_press/utils/encoding.py                |       22 |        1 |     95% |         9 |
| adt\_press/utils/file.py                    |       45 |        0 |    100% |           |
| adt\_press/utils/html.py                    |       34 |        0 |    100% |           |
| adt\_press/utils/image.py                   |       94 |       36 |     62% |25-34, 41-45, 54-60, 77-80, 83, 120-136 |
| adt\_press/utils/languages.py               |        3 |        0 |    100% |           |
| adt\_press/utils/logging.py                 |       72 |       26 |     64% |17-24, 50, 85-87, 100-107, 115-134, 142 |
| adt\_press/utils/pdf.py                     |       18 |        3 |     83% | 47, 52-53 |
| adt\_press/utils/string.py                  |        3 |        0 |    100% |           |
| adt\_press/utils/sync.py                    |       14 |        0 |    100% |           |
| adt\_press/utils/web\_assets.py             |      115 |       13 |     89% |17, 64-71, 127, 152-157 |
| tests/test\_clear\_cache.py                 |       45 |        0 |    100% |           |
| tests/test\_encoding.py                     |       39 |        1 |     97% |        64 |
| tests/test\_page\_sectioning\_validator.py  |       46 |        0 |    100% |           |
| tests/test\_parameter\_validation.py        |       30 |        0 |    100% |           |
| tests/test\_pdf\_extractor.py               |      116 |        0 |    100% |           |
| tests/test\_pipeline.py                     |       78 |        0 |    100% |           |
| tests/test\_utils\_image.py                 |       20 |        0 |    100% |           |
| tests/test\_web\_generation\_validator.py   |       75 |        0 |    100% |           |
| tools/pdf\_extractor/models.py              |       15 |        1 |     93% |        63 |
| tools/pdf\_extractor/pdf\_extractor.py      |      183 |       52 |     72% |216-218, 230-234, 237-266, 310, 387-475, 479 |
| tools/pdf\_extractor/utils.py               |      326 |      246 |     25% |27, 61-63, 68, 80-115, 125-140, 153-156, 168-173, 176-189, 192-209, 212-236, 245-252, 395-548, 555-586, 614, 638-640, 647, 650-654, 662, 669-687, 690, 694 |
|                                   **TOTAL** | **2832** |  **466** | **84%** |           |


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