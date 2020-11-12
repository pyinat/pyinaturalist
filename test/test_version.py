# A couple tests to make sure that versioning works as expected within GitHub Actions
# So, for example, the build would fail before accidentally publishing a bad version
from unittest.mock import patch


# Mocking out getenv() instead of actually setting envars so this doesn't affect other tests
@patch("pyinaturalist.getenv", side_effect=["refs/heads/master", "123"])
def test_version__stable_release(mock_getenv):
    import pyinaturalist

    assert "dev" not in pyinaturalist.__version__


@patch("pyinaturalist.getenv", side_effect=["refs/heads/dev", "123"])
def test_version__pre_release(mock_getenv):
    import pyinaturalist

    assert pyinaturalist.get_prerelease_version("1.0.0") == "1.0.0-dev.123"
