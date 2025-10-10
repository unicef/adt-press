# Repository Coverage



| Name                                            |    Stmts |     Miss |   Cover |   Missing |
|------------------------------------------------ | -------: | -------: | ------: | --------: |
| adt-press.py                                    |       23 |        0 |    100% |           |
| adt\_press/\_\_init\_\_.py                      |        0 |        0 |    100% |           |
| adt\_press/llm/\_\_init\_\_.py                  |        8 |        3 |     62% |  9-10, 15 |
| adt\_press/llm/glossary\_translation.py         |       21 |        0 |    100% |           |
| adt\_press/llm/image\_caption.py                |       19 |        0 |    100% |           |
| adt\_press/llm/image\_crop.py                   |       32 |        0 |    100% |           |
| adt\_press/llm/image\_meaningfulness.py         |       17 |        0 |    100% |           |
| adt\_press/llm/page\_sectioning.py              |       41 |        0 |    100% |           |
| adt\_press/llm/section\_explanations.py         |       20 |        0 |    100% |           |
| adt\_press/llm/section\_glossary.py             |       18 |        0 |    100% |           |
| adt\_press/llm/section\_metadata.py             |       26 |        1 |     96% |        24 |
| adt\_press/llm/speech\_generation.py            |       18 |        0 |    100% |           |
| adt\_press/llm/text\_easy\_read.py              |       18 |        0 |    100% |           |
| adt\_press/llm/text\_extraction.py              |       25 |        0 |    100% |           |
| adt\_press/llm/text\_translation.py             |       19 |        0 |    100% |           |
| adt\_press/llm/web\_generation\_html.py         |       46 |        8 |     83% |    73-103 |
| adt\_press/llm/web\_generation\_rows.py         |       49 |        9 |     82% |    72-111 |
| adt\_press/llm/web\_generation\_template.py     |        9 |        0 |    100% |           |
| adt\_press/llm/web\_generation\_two\_column.py  |       69 |       22 |     68% |62-65, 68-76, 81, 84, 100-140 |
| adt\_press/models/\_\_init\_\_.py               |        0 |        0 |    100% |           |
| adt\_press/models/image.py                      |       37 |        0 |    100% |           |
| adt\_press/models/pdf.py                        |        8 |        0 |    100% |           |
| adt\_press/models/plate.py                      |       31 |        0 |    100% |           |
| adt\_press/models/section.py                    |       54 |        0 |    100% |           |
| adt\_press/models/speech.py                     |        6 |        0 |    100% |           |
| adt\_press/models/text.py                       |       53 |        0 |    100% |           |
| adt\_press/models/web.py                        |       14 |        0 |    100% |           |
| adt\_press/nodes/\_\_init\_\_.py                |        0 |        0 |    100% |           |
| adt\_press/nodes/config\_nodes.py               |      122 |        4 |     97% |87, 168, 173, 178 |
| adt\_press/nodes/image\_nodes.py                |      109 |        0 |    100% |           |
| adt\_press/nodes/pdf\_nodes.py                  |       73 |        0 |    100% |           |
| adt\_press/nodes/plate\_nodes.py                |      110 |        0 |    100% |           |
| adt\_press/nodes/report\_nodes.py               |       44 |        0 |    100% |           |
| adt\_press/nodes/section\_nodes.py              |       84 |        0 |    100% |           |
| adt\_press/nodes/speech\_nodes.py               |       24 |        0 |    100% |           |
| adt\_press/nodes/web\_nodes.py                  |      130 |       10 |     92% |58, 66, 71, 74, 76, 78, 82, 86, 90, 92 |
| adt\_press/pipeline.py                          |       35 |        0 |    100% |           |
| adt\_press/utils/\_\_init\_\_.py                |        0 |        0 |    100% |           |
| adt\_press/utils/file.py                        |       30 |        0 |    100% |           |
| adt\_press/utils/html.py                        |       34 |        0 |    100% |           |
| adt\_press/utils/image.py                       |       50 |       13 |     74% |     49-65 |
| adt\_press/utils/languages.py                   |        3 |        0 |    100% |           |
| adt\_press/utils/logging.py                     |       73 |       26 |     64% |16-23, 49, 85-87, 100-107, 115-134, 142 |
| adt\_press/utils/pdf.py                         |       42 |        3 |     93% | 79-80, 85 |
| adt\_press/utils/sync.py                        |       14 |        0 |    100% |           |
| adt\_press/utils/web\_assets.py                 |       74 |        7 |     91% | 13, 59-66 |
| tests/test\_clear\_cache.py                     |       45 |        0 |    100% |           |
| tests/test\_page\_sectioning\_validator.py      |       46 |        0 |    100% |           |
| tests/test\_parameter\_validation.py            |       30 |        0 |    100% |           |
| tests/test\_pipeline.py                         |       75 |        0 |    100% |           |
| tests/test\_two\_column.py                      |       21 |        5 |     76% | 47, 54-57 |
| tests/test\_web\_generation\_rows\_validator.py |       55 |        0 |    100% |           |
| tests/test\_web\_generation\_validator.py       |       84 |        0 |    100% |           |
|                                       **TOTAL** | **2088** |  **111** | **95%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://github.com/unicef/adt-press/raw/python-coverage-comment-action-data/badge.svg)](https://github.com/unicef/adt-press/tree/python-coverage-comment-action-data)

This is the one to use if your repository is private or if you don't want to customize anything.



## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.