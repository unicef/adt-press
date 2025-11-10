# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/unicef/adt-press/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                        |    Stmts |     Miss |   Cover |   Missing |
|-------------------------------------------- | -------: | -------: | ------: | --------: |
| adt-press.py                                |       23 |        0 |    100% |           |
| adt\_press/\_\_init\_\_.py                  |        0 |        0 |    100% |           |
| adt\_press/llm/\_\_init\_\_.py              |        8 |        3 |     62% |  9-10, 15 |
| adt\_press/llm/glossary\_translation.py     |       17 |        0 |    100% |           |
| adt\_press/llm/image\_caption.py            |       17 |        0 |    100% |           |
| adt\_press/llm/image\_crop.py               |       28 |        0 |    100% |           |
| adt\_press/llm/image\_meaningfulness.py     |       15 |        0 |    100% |           |
| adt\_press/llm/page\_sectioning.py          |       38 |        0 |    100% |           |
| adt\_press/llm/section\_explanations.py     |       18 |        0 |    100% |           |
| adt\_press/llm/section\_glossary.py         |       16 |        0 |    100% |           |
| adt\_press/llm/section\_metadata.py         |       23 |        1 |     96% |        25 |
| adt\_press/llm/speech\_generation.py        |       23 |        0 |    100% |           |
| adt\_press/llm/text\_easy\_read.py          |       16 |        0 |    100% |           |
| adt\_press/llm/text\_extraction.py          |       19 |        0 |    100% |           |
| adt\_press/llm/text\_translation.py         |       39 |        4 |     90% |27, 31, 38, 40 |
| adt\_press/llm/web\_generation\_html.py     |       45 |        8 |     82% |    74-104 |
| adt\_press/llm/web\_generation\_template.py |        9 |        0 |    100% |           |
| adt\_press/models/\_\_init\_\_.py           |        0 |        0 |    100% |           |
| adt\_press/models/image.py                  |       10 |        0 |    100% |           |
| adt\_press/models/pdf.py                    |        3 |        0 |    100% |           |
| adt\_press/models/plate.py                  |        7 |        0 |    100% |           |
| adt\_press/models/section.py                |       33 |        0 |    100% |           |
| adt\_press/models/speech.py                 |        2 |        0 |    100% |           |
| adt\_press/models/text.py                   |       35 |        0 |    100% |           |
| adt\_press/models/web.py                    |        4 |        0 |    100% |           |
| adt\_press/nodes/\_\_init\_\_.py            |        0 |        0 |    100% |           |
| adt\_press/nodes/config\_nodes.py           |      121 |        4 |     97% |88, 169, 174, 179 |
| adt\_press/nodes/image\_nodes.py            |      109 |        2 |     98% |   49, 100 |
| adt\_press/nodes/pdf\_nodes.py              |       73 |        0 |    100% |           |
| adt\_press/nodes/plate\_nodes.py            |      127 |        3 |     98% |36, 103, 259 |
| adt\_press/nodes/report\_nodes.py           |       44 |        0 |    100% |           |
| adt\_press/nodes/section\_nodes.py          |       84 |        1 |     99% |        31 |
| adt\_press/nodes/speech\_nodes.py           |       24 |        0 |    100% |           |
| adt\_press/nodes/web\_nodes.py              |      120 |        6 |     95% |56, 64, 69, 71, 75, 79 |
| adt\_press/pipeline.py                      |       35 |        0 |    100% |           |
| adt\_press/utils/\_\_init\_\_.py            |        0 |        0 |    100% |           |
| adt\_press/utils/encoding.py                |       22 |        1 |     95% |         9 |
| adt\_press/utils/file.py                    |       30 |        0 |    100% |           |
| adt\_press/utils/html.py                    |       34 |        0 |    100% |           |
| adt\_press/utils/image.py                   |       50 |       13 |     74% |     49-65 |
| adt\_press/utils/languages.py               |        3 |        0 |    100% |           |
| adt\_press/utils/logging.py                 |       73 |       26 |     64% |16-23, 49, 85-87, 100-107, 115-134, 142 |
| adt\_press/utils/pdf.py                     |       42 |        3 |     93% | 79-80, 85 |
| adt\_press/utils/sync.py                    |       14 |        0 |    100% |           |
| adt\_press/utils/web\_assets.py             |       98 |       13 |     87% |13, 59-66, 119, 144-149 |
| tests/test\_clear\_cache.py                 |       45 |        0 |    100% |           |
| tests/test\_encoding.py                     |       39 |        1 |     97% |        64 |
| tests/test\_page\_sectioning\_validator.py  |       46 |        0 |    100% |           |
| tests/test\_parameter\_validation.py        |       30 |        0 |    100% |           |
| tests/test\_pipeline.py                     |       76 |        0 |    100% |           |
| tests/test\_web\_generation\_validator.py   |       84 |        0 |    100% |           |
|                                   **TOTAL** | **1871** |   **89** | **95%** |           |


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