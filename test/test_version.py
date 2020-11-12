# A couple tests to make sure that versioning works as expected within GitHub Actions
# So, for example, the build would fail before accidentally publishing a bad version
from unittest.mock import patch
import os


@patch.dict(os.environ, {"GITHUB_REF": "refs/heads/master"})
def test_version__stable_release():
    import pyinaturalist

    print(os.getenv("GITHUB_REF"))
    assert pyinaturalist.get_prerelease_version("1.0.0") == "1.0.0"


@patch.dict(os.environ, {"GITHUB_REF": "refs/heads/dev", "GITHUB_RUN_NUMBER": "123"})
def test_version__pre_release():
    import pyinaturalist

    print(os.getenv("GITHUB_REF"))
    assert pyinaturalist.get_prerelease_version("1.0.0") == "1.0.0.dev123"
