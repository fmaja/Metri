import pytest

from metri.logic import display_func, jsonify_func, song_func

pytestmark = [pytest.mark.perf]


@pytest.fixture(autouse=True)
def skip_if_not_benchmark(request):
    """Skip perf tests unless explicitly run with --benchmark-only."""
    if not request.config.getoption("--benchmark-only"):
        pytest.skip("Perf test: run with --benchmark-only")


@pytest.fixture(scope="module")
def songs_dataset():
    songs = []
    for idx in range(1, 201):
        songs.append(
            {
                "id": idx,
                "title": f"Song {idx}",
                "artist": "Test Artist",
                "group": "Test Group",
                "tags": ["folk", "live"] if idx % 2 == 0 else ["rock"],
                "lyrics": {
                    "v": ["Line|one", "Line two"],
                    "c": ["Ref|rain", "Ref two"],
                    "i1": ["|----|"],
                },
                "chords": {
                    "v": ["C G", "F C"],
                    "c": ["Am F", "G C"],
                },
                "content": ["v", "c", "i1"],
            }
        )
    return songs


@pytest.fixture(scope="module")
def raw_song_inputs():
    base_block = """[v]\nC G\nLine one|here\n[c]\nAm F\nRef line|there\n"""
    return [
        {
            "title": f"Raw {idx}",
            "artist": "Perf Artist",
            "group": "Perf Group",
            "tags": "folk;test",
            "lyrics": base_block,
        }
        for idx in range(1, 301)
    ]


@pytest.fixture(scope="module")
def large_songbook():
    songs = []
    for idx in range(1, 1001):
        songs.append(
            {
                "id": idx,
                "title": f"Title {idx}",
                "artist": "Artist" if idx % 2 == 0 else "Other",
                "group": "Group" if idx % 3 == 0 else "Alt",
                "language": "polski" if idx % 4 == 0 else "angielski",
                "tags": ["folk", "rock"] if idx % 5 == 0 else ["live"],
            }
        )
    return songs


@pytest.fixture(scope="module")
def huge_songbook():
    songs = []
    for idx in range(1, 10001):
        songs.append(
            {
                "id": idx,
                "title": f"Ballada o {idx}",
                "artist": "Artysta" if idx % 2 == 0 else "Inny",
                "group": "Grupa" if idx % 3 == 0 else "Zespół",
                "language": "polski" if idx % 4 == 0 else "angielski",
                "tags": ["rock", "live"] if idx % 5 == 0 else ["folk"],
            }
        )
    return songs


@pytest.fixture(scope="module")
def very_long_song_text():
    verse = "|C G Am F| " + "lorem ipsum " * 10
    chorus = "|F G C| " + "dolor sit amet " * 8
    long_lyrics = "[v]\n" + "\n".join([verse] * 80) + "\n[c]\n" + "\n".join([chorus] * 40)
    return {
        "title": "Bardzo długa",
        "artist": "Perf",
        "group": "Perf",
        "tags": "long;stress",
        "lyrics": long_lyrics,
    }


@pytest.fixture(scope="module")
def very_long_song_text_dense_chords():
    complex_chords = [
        "A#sus4/D",
        "Gmbadd9/F",
        "Edim",
        "Csus2/E",
        "Bbmaj7#11",
        "F#7b9",
        "Eadd9/G#",
        "Bdim/F",
    ]
    verse = "|" + "|".join(complex_chords) + "| " + "la " * 20
    chorus = "|" + "|".join(complex_chords[::-1]) + "| " + "la " * 25
    long_lyrics = "[v]\n" + "\n".join([verse] * 60) + "\n[c]\n" + "\n".join([chorus] * 60)
    return {
        "title": "Długa z gęstymi akordami",
        "artist": "Perf",
        "group": "Perf",
        "tags": "dense;stress",
        "lyrics": long_lyrics,
    }


def test_display_html_many_songs(benchmark, monkeypatch, songs_dataset):
    songs_by_id = {song["id"]: song for song in songs_dataset}
    monkeypatch.setattr(display_func, "get_song", lambda song_id: songs_by_id[song_id])
    monkeypatch.setattr(song_func, "get_song", lambda song_id: songs_by_id[song_id])

    def run():
        for song in songs_dataset:
            display_func.get_display(song["id"])

    benchmark(run)


def test_display_plaintext_many_songs(benchmark, monkeypatch, songs_dataset):
    songs_by_id = {song["id"]: song for song in songs_dataset}
    monkeypatch.setattr(display_func, "get_song", lambda song_id: songs_by_id[song_id])
    monkeypatch.setattr(song_func, "get_song", lambda song_id: songs_by_id[song_id])

    def run():
        for song in songs_dataset:
            display_func.get_display_2(song["id"])

    benchmark(run)


def test_jsonify_auto_bulk(benchmark, raw_song_inputs):
    def run():
        for idx, raw in enumerate(raw_song_inputs, start=1):
            jsonify_func.song_data_jsonify_auto(raw, idx)

    benchmark(run)


def test_filter_songs_large_dataset(benchmark, monkeypatch, large_songbook):
    monkeypatch.setattr(song_func, "load_songs", lambda: large_songbook)

    def run():
        song_func.filter_songs({"search": "title", "language": "polski", "tags": ["folk"]})

    benchmark(run)


def test_get_tags_large_dataset(benchmark, monkeypatch, large_songbook):
    monkeypatch.setattr(song_func, "load_songs", lambda: large_songbook)

    def run():
        song_func.get_tags()

    benchmark(run)


def test_filter_songs_huge_dataset(benchmark, monkeypatch, huge_songbook):
    monkeypatch.setattr(song_func, "load_songs", lambda: huge_songbook)

    def run():
        song_func.filter_songs({"search": "ballada", "language": "polski", "tags": ["rock"]})

    benchmark(run)


def test_list_many_songs_mapping(benchmark, monkeypatch, huge_songbook):
    monkeypatch.setattr(song_func, "load_songs", lambda: huge_songbook)

    def run():
        songs = song_func.load_songs()
        return [
            {
                "id": s.get("id"),
                "title": s.get("title", ""),
                "artist": s.get("artist", ""),
                "language": s.get("language", ""),
                "tags": s.get("tags", []),
            }
            for s in songs
        ]

    benchmark(run)


def test_add_very_long_song_jsonify(benchmark, very_long_song_text):
    def run():
        jsonify_func.song_data_jsonify_auto(very_long_song_text, 999_001)

    benchmark(run)


def test_add_dense_chords_song_jsonify(benchmark, very_long_song_text_dense_chords):
    def run():
        jsonify_func.song_data_jsonify_auto(very_long_song_text_dense_chords, 999_002)

    benchmark(run)
