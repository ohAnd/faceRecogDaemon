import pytest
import imageHandling

def test_getImageFromUrl():
    assert imageHandling.getImageFromUrl('http://localhost:1234') == 'connection_timeout'