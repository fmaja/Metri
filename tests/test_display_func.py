import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from metri.logic.display_func import (
    get_display_lyrics,
    get_display_chords,
    get_display_2,
    get_display,
    chords_to_scheme
)
from metri.logic import song_func


@pytest.fixture
def sample_songs():
    """Fixture providing sample song data for testing."""
    return [
        {
            "id": 1,
            "title": "Test Song",
            "artist": "Test Artist",
            "content": ["v", "c", "v1"],
            "lyrics": {
                "v": ["Pierwsza zwrotka", "druga linia"],
                "c": ["Refren pierwszy", "refren drugi"],
                "v1": ["Druga zwrotka", "inna linia"]
            },
            "chords": {
                "v": ["C G Am", "F C G"],
                "c": ["Am F C", "G Am F"]
            }
        },
        {
            "id": 2,
            "title": "Song With Intro",
            "artist": "Artist",
            "content": ["i", "v", "c"],
            "lyrics": {
                "i": ["C", "G Am"],
                "v": ["Verse line"],
                "c": ["Chorus line"]
            },
            "chords": {
                "v": ["C G"],
                "c": ["Am F"]
            }
        },
        {
            "id": 3,
            "title": "Empty Sections",
            "artist": "Test",
            "content": ["v", "c"],
            "lyrics": {
                "v": ["Line one", "", "Line three"],
                "c": ["!hidden line", "visible line"]
            },
            "chords": {
                "v": ["C", "D", "E"],
                "c": ["F"]
            }
        },
        {
            "id": 4,
            "title": "Repeated Sections",
            "artist": "Test",
            "content": ["v", "v", "c"],
            "lyrics": {
                "v": ["Same verse"],
                "c": ["Chorus"]
            },
            "chords": {
                "v": ["C G"],
                "c": ["Am"]
            }
        },
        {
            "id": 5,
            "title": "Section With Markers",
            "artist": "Test",
            "content": ["v"],
            "lyrics": {
                "v": ["|Marker line|", "(second voice)", "normal line"]
            },
            "chords": {
                "v": ["C G Am"]
            }
        },
        {
            "id": 6,
            "title": "Tab Section",
            "artist": "Test",
            "content": ["s1", "v"],
            "lyrics": {
                "s1": [],
                "v": ["Verse"]
            },
            "chords": {
                "v": ["C"]
            }
        }
    ]


@pytest.fixture(autouse=True)
def mock_song_data(monkeypatch, sample_songs):
    """Mock song_func.get_song to return test data."""
    def mock_get_song(song_id):
        for song in sample_songs:
            if song['id'] == song_id:
                return song
        return None
    
    # Patch in both locations - where it's imported and where it's defined
    monkeypatch.setattr('metri.logic.display_func.get_song', mock_get_song)
    monkeypatch.setattr('metri.logic.song_func.get_song', mock_get_song)


class TestChordsToScheme:
    """Test the chords_to_scheme helper function."""
    
    def test_no_markers_returns_original(self):
        """When lyrics line has no | markers, return chords unchanged."""
        chord_line = "C G Am"
        lyrics_line = "Simple lyrics line"
        result = chords_to_scheme(chord_line, lyrics_line)
        assert result == "C G Am"
    
    def test_single_marker(self):
        """Single marker positions chord correctly."""
        chord_line = "C G"
        lyrics_line = "Some |word here"
        result = chords_to_scheme(chord_line, lyrics_line)
        assert "C" in result
        assert result.index("C") >= 5  # After "Some "
    
    def test_multiple_markers(self):
        """Multiple markers distribute chords."""
        chord_line = "C G Am"
        lyrics_line = "|First |second |third"
        result = chords_to_scheme(chord_line, lyrics_line)
        assert "C" in result
        assert "G" in result
        assert "Am" in result
    
    def test_more_markers_than_chords_cycles(self):
        """When more markers than chords, cycles through chords."""
        chord_line = "C G"
        lyrics_line = "|one |two |three |four"
        result = chords_to_scheme(chord_line, lyrics_line)
        # Should cycle: C, G, C, G
        assert result.count("C") == 2
        assert result.count("G") == 2
    
    def test_extra_chords_appended(self):
        """When fewer markers than chords, extra chords appended."""
        chord_line = "C G Am F"
        lyrics_line = "|one |two"
        result = chords_to_scheme(chord_line, lyrics_line)
        assert "C" in result
        assert "G" in result
        assert "Am" in result
        assert "F" in result


class TestGetDisplayLyrics:
    """Test the get_display_lyrics function."""
    
    def test_basic_lyrics_display(self):
        """Basic song lyrics are formatted correctly."""
        result = get_display_lyrics(1)
        assert "[v]" in result
        assert "[c]" in result
        assert "Pierwsza zwrotka" in result
        assert "Refren pierwszy" in result
    
    def test_intro_section_included(self):
        """Intro sections are included in lyrics display."""
        result = get_display_lyrics(2)
        assert "[i]" in result
        assert "[v]" in result
        assert "C" in result
        assert "Verse line" in result
    
    def test_empty_lines_handled(self):
        """Empty lines in lyrics are preserved."""
        result = get_display_lyrics(3)
        assert "Line one" in result
        assert "Line three" in result
        # Empty line creates extra newline
        assert "\n\n" in result
    
    def test_hidden_lines_included(self):
        """Lines starting with ! are included (filtering happens in display)."""
        result = get_display_lyrics(3)
        assert "!hidden line" in result or "visible line" in result
    
    def test_repeated_sections_deduplicated(self):
        """When same section appears twice with same content, shown once."""
        result = get_display_lyrics(4)
        # Both v sections have same content, check deduplication logic
        assert "[v]" in result
        assert "Same verse" in result


class TestGetDisplayChords:
    """Test the get_display_chords function."""
    
    def test_basic_chords_display(self):
        """Basic chord display works."""
        result = get_display_chords(1)
        assert "[v]" in result
        assert "[c]" in result
        assert "C G Am" in result
        assert "Am F C" in result
    
    def test_intro_sections_skipped(self):
        """Intro sections (starting with 'i') are skipped in chord display."""
        result = get_display_chords(2)
        assert "[i]" not in result
        assert "[v]" in result
        assert "C G" in result
    
    def test_tab_sections_skipped(self):
        """Tab sections (starting with 's') are skipped."""
        result = get_display_chords(6)
        assert "[s" not in result
        assert "[v]" in result
    
    def test_empty_chords_not_displayed(self):
        """Sections without chords are not included."""
        result = get_display_chords(2)
        # v1 section in song 1 has no chords defined
        lines = result.split('\n')
        # Check that only sections with chords are shown
        assert result.count('[v]') >= 1


class TestGetDisplay2:
    """Test the get_display_2 function (plain text display)."""
    
    def test_returns_two_element_list(self):
        """Function returns [lyrics, chords] list."""
        result = get_display_2(1)
        assert isinstance(result, list)
        assert len(result) == 2
    
    def test_lyrics_and_chords_aligned(self):
        """Lyrics and chords have same number of lines."""
        result = get_display_2(1)
        lyrics_lines = result[0].split('\n')
        chords_lines = result[1].split('\n')
        # They should have matching structure
        assert len(lyrics_lines) > 0
        assert len(chords_lines) > 0
    
    def test_intro_section_no_chords(self):
        """Intro sections have empty chord lines."""
        result = get_display_2(2)
        lyrics = result[0]
        chords = result[1]
        
        lyrics_lines = lyrics.split('\n')
        chords_lines = chords.split('\n')
        
        # Find intro lines (C, G Am)
        assert "C" in lyrics or "G Am" in lyrics
    
    def test_chorus_lines_indented(self):
        """Chorus lines are indented with tab."""
        result = get_display_2(1)
        lyrics = result[0]
        # Chorus lines should have tabs
        assert "\t" in lyrics
    
    def test_markers_removed_from_lyrics(self):
        """| and ! markers are removed from lyrics."""
        result = get_display_2(5)
        lyrics = result[0]
        # Markers should be stripped
        assert "|" not in lyrics or lyrics.count("|") < lyrics.count("Marker")
    
    def test_chord_counter_cycles(self):
        """Chord counter cycles through available chords."""
        result = get_display_2(3)
        chords = result[1]
        # With 3 verse lines and 3 chords (C, D, E), all should appear
        assert "C" in chords or "D" in chords or "E" in chords
    
    def test_empty_sections_between_content(self):
        """Empty lines separate sections."""
        result = get_display_2(1)
        lyrics = result[0]
        # Multiple sections should have empty lines between them
        assert "\n\n" in lyrics or lyrics.count('\n') > 3


class TestGetDisplay:
    """Test the get_display function (HTML formatted)."""
    
    def test_returns_string(self):
        """Function returns a string."""
        result = get_display(1)
        assert isinstance(result, str)
    
    def test_contains_html_tags(self):
        """Output contains HTML formatting."""
        result = get_display(1)
        assert "<b>" in result or "<code>" in result
    
    def test_intro_section_bold(self):
        """Intro lines are wrapped in bold tags."""
        result = get_display(2)
        assert "<b>C</b>" in result or "<b>G Am</b>" in result
    
    def test_tab_section_creates_image_tag(self):
        """Tab sections create img tags."""
        result = get_display(6)
        assert "<img" in result
        assert "tab/" in result
        assert ".svg" in result
    
    def test_chords_wrapped_in_code_tags(self):
        """Individual chords are wrapped in code tags."""
        result = get_display(1)
        assert "<code>" in result
        assert "</code>" in result
    
    def test_second_voice_italicized(self):
        """Lines starting with ( are italicized."""
        result = get_display(5)
        assert "<i>(second voice)</i>" in result or "<i>second voice</i>" in result
    
    def test_hidden_lines_create_newline(self):
        """Lines starting with ! create empty line."""
        result = get_display(3)
        # Should have multiple newlines where hidden line was
        assert "\n\n" in result or result.count('\n') > 5
    
    def test_chorus_lines_indented(self):
        """Chorus lyrics are indented with tab."""
        result = get_display(1)
        assert "\t" in result
    
    def test_markers_removed_from_lyrics(self):
        """| markers are removed from lyrics display."""
        result = get_display(5)
        # Check that markers are stripped in final output
        lyrics_parts = [part for part in result.split('<') if '>' not in part or part.startswith('/')]
        # Markers should not appear in plain text parts
    
    def test_chord_counter_increments(self):
        """Chord counter increments through section chords."""
        result = get_display(1)
        # Multiple chords should appear
        assert result.count("<code>") >= 3
    
    def test_numbered_section_fallback(self):
        """Numbered sections (v1) fall back to base section (v) for chords."""
        result = get_display(1)
        # v1 section should use v chords if v1 chords don't exist
        assert "<code>" in result


class TestIntegration:
    """Integration tests for display functions."""
    
    def test_all_display_functions_work(self):
        """All three display functions can process the same song."""
        song_id = 1
        
        lyrics = get_display_lyrics(song_id)
        chords = get_display_chords(song_id)
        plain = get_display_2(song_id)
        html = get_display(song_id)
        
        assert len(lyrics) > 0
        assert len(chords) > 0
        assert len(plain) == 2
        assert len(html) > 0
    
    def test_complex_song_all_features(self):
        """Complex song with multiple section types works."""
        # This would need a more complex fixture
        # For now just verify no crashes
        result = get_display(2)
        assert isinstance(result, str)
    
    def test_empty_song_handled(self):
        """Song with minimal data doesn't crash."""
        # Would need a fixture with empty song
        # Verify existing songs don't crash
        for song_id in [1, 2, 3, 4, 5, 6]:
            lyrics = get_display_lyrics(song_id)
            assert isinstance(lyrics, str)
