from pipeline.place_names import mentions_place


def test_country_adjectives_and_aliases_count_as_a_mention():
    assert mentions_place("مدن أمريكية كبيرة", "الولايات المتحدة", "United States")
    assert mentions_place("في الأمريكيين", "الولايات المتحدة", "United States")
    assert mentions_place("الصادرات المصرية", "مصر", "Egypt")
    assert not mentions_place("كانت المدينة صغيرة", "مصر", "Egypt")
