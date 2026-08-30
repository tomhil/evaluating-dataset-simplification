"""Dataset Task-Profile Metrics pipeline.

Ingests a parallel document corpus (source -> target) and emits a descriptive
metric profile of the transformations the corpus performs. It measures and
reports only: it never classifies the dataset or emits a task verdict.
"""

__version__ = "0.1.0"
