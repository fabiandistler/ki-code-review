from importlib.metadata import version

import ki_review


def test_package_version_matches_distribution_metadata() -> None:
    assert ki_review.__version__ == version("ki-review")
