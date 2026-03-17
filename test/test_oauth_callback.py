import base64
import hashlib

from pyinaturalist.oauth_callback import _generate_pkce_pair, build_authorize_url

# _generate_pkce_pair
# -------------------


def test_generate_pkce_pair():
    verifier, challenge = _generate_pkce_pair()
    # Verifier should be 86 chars (64 bytes base64url-encoded without padding)
    assert len(verifier) == 86
    # Challenge should be the base64url(SHA256(verifier)) without padding
    expected_digest = hashlib.sha256(verifier.encode('ascii')).digest()
    expected_challenge = base64.urlsafe_b64encode(expected_digest).rstrip(b'=').decode('ascii')
    assert challenge == expected_challenge


# build_authorize_url
# -------------------


def test_build_authorize_url__urlencode():
    """redirect_uri with special characters is properly percent-encoded."""
    url = build_authorize_url('my_app', 'http://127.0.0.1:8080', state='abc123')
    assert 'redirect_uri=http%3A%2F%2F127.0.0.1%3A8080' in url
    assert 'state=abc123' in url


def test_build_authorize_url__pkce():
    """PKCE parameters are included when a code_challenge is provided."""
    url = build_authorize_url('my_app', 'http://127.0.0.1:8080', code_challenge='challenge_val')
    assert 'code_challenge=challenge_val' in url
    assert 'code_challenge_method=S256' in url
