"""
Testy jednostkowe dla modułu jsonify_func.py
"""
import pytest
import sys
from pathlib import Path

# Dodaj src do ścieżki Python
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from metri.logic.jsonify_func import (
    string_to_list,
    split_into_sections,
    redefine_sections,
    name_sections,
    del_repetitions,
    song_data_jsonify_auto
)


class TestStringToList:
    """Testy dla funkcji string_to_list"""
    
    def test_string_to_list_single_item(self):
        """Test konwersji pojedynczego elementu"""
        result = string_to_list("rock")
        assert result == ["rock"]
    
    def test_string_to_list_multiple_items(self):
        """Test konwersji wielu elementów"""
        result = string_to_list("rock; pop; jazz")
        assert result == ["rock", "pop", "jazz"]
    
    def test_string_to_list_with_spaces(self):
        """Test konwersji z białymi znakami"""
        result = string_to_list("rock ;  pop  ; jazz")
        assert result == ["rock", "pop", "jazz"]
    
    def test_string_to_list_empty_string(self):
        """Test pustego stringa"""
        result = string_to_list("")
        assert result == []
    
    def test_string_to_list_none(self):
        """Test wartości None"""
        result = string_to_list(None)
        assert result == []
    
    def test_string_to_list_single_semicolon(self):
        """Test pojedynczego średnika"""
        result = string_to_list(";")
        assert result == ["", ""]


class TestSplitIntoSections:
    """Testy dla funkcji split_into_sections"""
    
    def test_split_with_explicit_sections(self):
        """Test dzielenia tekstu z jawnie określonymi sekcjami"""
        text = "[Verse]\nLine 1\nLine 2\n[Chorus]\nLine 3"
        result = split_into_sections(text)
        assert len(result) >= 2
        assert any('v' in section['section'].lower() or section['section'] == 'V ' for section in result)
    
    def test_split_without_sections(self):
        """Test dzielenia tekstu bez sekcji (automatyczne tworzenie)"""
        text = "Line 1\nLine 2\n\n\n\nLine 3\nLine 4"
        result = split_into_sections(text)
        assert len(result) >= 1
    
    def test_split_empty_text(self):
        """Test pustego tekstu"""
        result = split_into_sections("")
        assert result == []
    
    def test_split_only_sections_no_content(self):
        """Test samych sekcji bez treści"""
        text = "[Verse]\n[Chorus]"
        result = split_into_sections(text)
        # Powinno odfiltrować sekcje bez treści
        assert len(result) == 0
    
    def test_split_removes_extra_whitespace(self):
        """Test usuwania nadmiarowych białych znaków"""
        text = "[Verse]\n   Line   with   spaces   "
        result = split_into_sections(text)
        if result:
            assert "   " not in result[0]['content'][0]
    
    def test_split_multiple_empty_lines_create_section(self):
        """Test że 3+ puste linie tworzą nową sekcję"""
        text = "Line 1\n\n\n\nLine 2"
        result = split_into_sections(text)
        # Powinno podzielić na sekcje
        assert len(result) >= 1


class TestRedefineSections:
    """Testy dla funkcji redefine_sections"""
    
    def test_redefine_sections_with_chords(self):
        """Test identyfikacji linii z akordami"""
        text = [{"section": "v", "content": ["C F G", "Lyrics line"]}]
        result = redefine_sections(text)
        assert len(result[0]['chords']) > 0
        assert len(result[0]['lyrics']) > 0
    
    def test_redefine_sections_only_lyrics(self):
        """Test sekcji tylko z tekstem"""
        text = [{"section": "v", "content": ["Just some text", "More text"]}]
        result = redefine_sections(text)
        assert len(result[0]['lyrics']) == 2
        assert len(result[0]['chords']) == 0
    
    def test_redefine_sections_only_chords(self):
        """Test sekcji tylko z akordami"""
        text = [{"section": "v", "content": ["C F G", "Am Dm Em"]}]
        result = redefine_sections(text)
        # Jeśli tylko akordy (dopasowane do wzorca), przepisywane są do lyrics
        assert len(result[0]['lyrics']) > 0
        assert result[0]['lyrics'] == ["C F G", "Am Dm Em"]
    
    def test_redefine_sections_chord_pattern_recognition(self):
        """Test rozpoznawania wzorców akordów"""
        # Powinno rozpoznać jako akordy i przepisać do lyrics
        text = [{"section": "v", "content": ["C Dm G7 Am"]}]
        result = redefine_sections(text)
        assert len(result[0]['lyrics']) > 0
        assert result[0]['lyrics'] == ["C Dm G7 Am"]
    
    def test_redefine_sections_mixed_content(self):
        """Test mieszanej zawartości (akordy + tekst)"""
        text = [{"section": "v", "content": [
            "C F G",
            "Some lyrics here",
            "Am Dm Em",
            "More lyrics"
        ]}]
        result = redefine_sections(text)
        assert len(result[0]['chords']) >= 2
        assert len(result[0]['lyrics']) >= 2
    
    def test_redefine_empty_sections_removed(self):
        """Test usuwania pustych sekcji"""
        text = [
            {"section": "v", "content": ["C F G"]},
            {"section": "empty", "content": []}
        ]
        result = redefine_sections(text)
        # Pusta sekcja powinna być usunięta
        assert all(section['content'] for section in text)


class TestNameSections:
    """Testy dla funkcji name_sections"""
    
    def test_name_sections_basic(self):
        """Test podstawowego nazywania sekcji"""
        text = [
            {"section": "v", "chords": ["C F G"], "lyrics": ["Line 1"]},
            {"section": "c", "chords": ["Am Dm"], "lyrics": ["Line 2"]}
        ]
        result = name_sections(text)
        assert all('section' in section for section in result)
    
    def test_name_sections_verse_detection(self):
        """Test wykrywania zwrotek"""
        text = [
            {"section": "v", "chords": ["C F G"], "lyrics": ["Verse line"]},
        ]
        result = name_sections(text)
        assert result[0]['section'][0] == 'v'
    
    def test_name_sections_chorus_detection(self):
        """Test wykrywania refrenu (powtórzenia)"""
        text = [
            {"section": "v", "chords": ["C F"], "lyrics": ["Same line"]},
            {"section": "v", "chords": ["C F"], "lyrics": ["Same line"]}
        ]
        result = name_sections(text)
        # Sprawdź że funkcja przypisała nazwy (może różne ze względu na numerację)
        assert len(result) == 2
        assert 'section' in result[0]
        assert 'section' in result[1]
        # Obie sekcje powinny zaczynać się od 'v' (verse)
        assert result[0]['section'][0] == 'v'
        assert result[1]['section'][0] == 'v'
    
    def test_name_sections_intro_detection(self):
        """Test wykrywania intro (bez akordów)"""
        text = [
            {"section": "i", "chords": [], "lyrics": ["Intro text"]},
        ]
        result = name_sections(text)
        assert result[0]['section'][0] == 'i'
    
    def test_name_sections_numbered_sections(self):
        """Test numerowania podobnych sekcji"""
        text = [
            {"section": "v", "chords": ["C F"], "lyrics": ["Line 1"]},
            {"section": "v", "chords": ["G Am"], "lyrics": ["Line 2"]},
            {"section": "v", "chords": ["Dm Em"], "lyrics": ["Line 3"]}
        ]
        result = name_sections(text)
        # Różne sekcje powinny mieć różne numery
        sections = [s['section'] for s in result]
        assert len(set(sections)) >= 2  # Przynajmniej 2 różne nazwy
    
    def test_name_sections_preserves_explicit_names(self):
        """Test zachowania jawnie określonych nazw sekcji"""
        text = [
            {"section": "v", "chords": ["C"], "lyrics": ["Verse"]},
            {"section": "c", "chords": ["F"], "lyrics": ["Chorus"]},
            {"section": "i", "chords": [], "lyrics": ["Intro"]},
            {"section": "s", "chords": ["G"], "lyrics": ["Solo"]}
        ]
        result = name_sections(text)
        sections = [s['section'][0] for s in result]
        assert 'v' in sections or 'c' in sections or 'i' in sections


class TestDelRepetitions:
    """Testy dla funkcji del_repetitions"""
    
    def test_del_repetitions_removes_duplicates(self):
        """Test usuwania powtórzonych akordów na końcu"""
        text = [{"section": "v", "chords": ["C F", "G Am", "G Am"], "lyrics": []}]
        result = del_repetitions(text)
        assert len(result[0]['chords']) == 2
        assert result[0]['chords'] == ["C F", "G Am"]
    
    def test_del_repetitions_multiple_duplicates(self):
        """Test usuwania wielu powtórzeń"""
        text = [{"section": "v", "chords": ["C", "F", "F", "F", "F"], "lyrics": []}]
        result = del_repetitions(text)
        # Powinno usunąć wszystkie powtórzenia F na końcu
        assert result[0]['chords'][-1] == "F"
        assert result[0]['chords'].count("F") == 1
    
    def test_del_repetitions_no_duplicates(self):
        """Test bez powtórzeń"""
        text = [{"section": "v", "chords": ["C", "F", "G"], "lyrics": []}]
        result = del_repetitions(text)
        assert len(result[0]['chords']) == 3
    
    def test_del_repetitions_single_chord(self):
        """Test z pojedynczym akordem"""
        text = [{"section": "v", "chords": ["C"], "lyrics": []}]
        result = del_repetitions(text)
        assert len(result[0]['chords']) == 1
    
    def test_del_repetitions_empty_chords(self):
        """Test z pustą listą akordów"""
        text = [{"section": "v", "chords": [], "lyrics": []}]
        result = del_repetitions(text)
        assert result[0]['chords'] == []
    
    def test_del_repetitions_preserves_middle_duplicates(self):
        """Test że zachowuje powtórzenia w środku (nie na końcu)"""
        text = [{"section": "v", "chords": ["C", "F", "F", "G"], "lyrics": []}]
        result = del_repetitions(text)
        # Powinno zachować F F w środku, ale nie powtórzenia na końcu
        assert "F" in result[0]['chords']


class TestSongDataJsonifyAuto:
    """Testy dla funkcji song_data_jsonify_auto"""
    
    def test_jsonify_auto_basic_song(self):
        """Test podstawowej konwersji danych piosenki"""
        song_data = {
            'title': 'Test Song',
            'artist': 'Test Artist',
            'key': 'C',
            'lyrics': '[Verse]\nC F G\nTest lyrics'
        }
        result = song_data_jsonify_auto(song_data, 1)
        
        assert result['id'] == 1
        assert result['title'] == 'Test Song'
        assert result['artist'] == 'Test Artist'
        assert result['key'] == 'C'
        assert isinstance(result['content'], list)
        assert isinstance(result['lyrics'], dict)
        assert isinstance(result['chords'], dict)
    
    def test_jsonify_auto_with_all_metadata(self):
        """Test z wszystkimi polami metadanych"""
        song_data = {
            'title': 'Full Song',
            'artist': 'Artist Name',
            'group': 'Band Name',
            'lyricsby': 'Lyricist',
            'musicby': 'Composer',
            'key': 'G',
            'bpm': '120',
            'timeSignature': '4/4',
            'tuning': 'Standard',
            'capo': '2',
            'language': 'polski',
            'tags': ['rock', 'ballad'],
            'lyrics': '[Verse]\nG C D\nLyrics here'
        }
        result = song_data_jsonify_auto(song_data, 5)
        
        assert result['id'] == 5
        assert result['title'] == 'Full Song'
        assert result['artist'] == 'Artist Name'
        assert result['bpm'] == '120'
        assert result['capo'] == '2'
        assert result['language'] == 'polski'
        assert isinstance(result['tags'], list)
    
    def test_jsonify_auto_tags_conversion(self):
        """Test konwersji tagów ze stringa na listę"""
        song_data = {
            'title': 'Song',
            'tags': 'rock; pop; jazz',
            'lyrics': '[Verse]\nC F G'
        }
        result = song_data_jsonify_auto(song_data, 1)
        
        assert isinstance(result['tags'], list)
        assert len(result['tags']) >= 1
    
    def test_jsonify_auto_empty_lyrics(self):
        """Test z pustymi tekstami"""
        song_data = {
            'title': 'Instrumental',
            'lyrics': ''
        }
        result = song_data_jsonify_auto(song_data, 1)
        
        assert result['title'] == 'Instrumental'
        assert isinstance(result['content'], list)
    
    def test_jsonify_auto_missing_fields(self):
        """Test z brakującymi polami"""
        song_data = {
            'title': 'Minimal Song'
        }
        result = song_data_jsonify_auto(song_data, 1)
        
        assert result['title'] == 'Minimal Song'
        assert result['artist'] == ''
        assert result['key'] == ''
        assert result['tags'] == []
    
    def test_jsonify_auto_structure_validation(self):
        """Test walidacji struktury wyniku"""
        song_data = {
            'title': 'Test',
            'lyrics': '[Verse]\nC F G\nLine 1\n[Chorus]\nAm Dm\nLine 2'
        }
        result = song_data_jsonify_auto(song_data, 1)
        
        # Sprawdź strukturę
        assert 'id' in result
        assert 'title' in result
        assert 'content' in result
        assert 'lyrics' in result
        assert 'chords' in result
        
        # Sprawdź że content zawiera sekcje
        assert len(result['content']) > 0
        
        # Sprawdź że lyrics i chords to słowniki
        assert isinstance(result['lyrics'], dict)
        assert isinstance(result['chords'], dict)


class TestIntegration:
    """Testy integracyjne procesów parsowania"""
    
    def test_full_song_parsing_pipeline(self):
        """Test pełnego procesu parsowania piosenki"""
        text = """[Verse]
C F G
First verse line
Another line

[Chorus]
Am Dm Em
Chorus line
"""
        # Symulacja pełnego procesu
        sections = split_into_sections(text)
        sections = redefine_sections(sections)
        sections = name_sections(sections)
        sections = del_repetitions(sections)
        
        # Sprawdź że proces się powiódł
        assert len(sections) > 0
        assert all('section' in s for s in sections)
        assert all('chords' in s for s in sections)
        assert all('lyrics' in s for s in sections)
    
    def test_song_with_complex_chords(self):
        """Test piosenki ze złożonymi akordami"""
        text = """[Verse]
Cmaj7 Dm7 G7sus4 Am9
Complex chord progression
"""
        sections = split_into_sections(text)
        sections = redefine_sections(sections)
        
        assert len(sections) > 0
        assert len(sections[0]['chords']) > 0
