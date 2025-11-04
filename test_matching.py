import pandas as pd
from reconcile.matching import site_similarity

def test_site_similarity_basic():
    assert site_similarity('Miami HQ', 'Miami Headquarters') > 85
    assert site_similarity('Brickell Tower', 'Brickell Twr') > 85
