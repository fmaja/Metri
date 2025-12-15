"""
Testy jednostkowe dla modułu music_theory.py
"""
import pytest
import sys
from pathlib import Path

# Dodaj src do ścieżki Python
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from metri.logic.music_theory import MusicTheory


class TestMusicTheory:
    """Testy dla klasy MusicTheory"""
    
    @pytest.fixture
    def music_theory(self):
        """Fixture zwracający instancję MusicTheory"""
        return MusicTheory()
    
    # ===== Testy dla note_name_to_midi =====
    
    def test_note_name_to_midi_basic(self, music_theory):
        """Test podstawowej konwersji nazw nut na MIDI"""
        assert music_theory.note_name_to_midi("C4") == 60
        assert music_theory.note_name_to_midi("A4") == 69
        assert music_theory.note_name_to_midi("C3") == 48
        
    def test_note_name_to_midi_sharps(self, music_theory):
        """Test konwersji nut z krzyżykami"""
        assert music_theory.note_name_to_midi("C#4") == 61
        assert music_theory.note_name_to_midi("F#4") == 66
        assert music_theory.note_name_to_midi("G#5") == 80
        
    def test_note_name_to_midi_different_octaves(self, music_theory):
        """Test różnych oktaw"""
        assert music_theory.note_name_to_midi("C0") == 12
        assert music_theory.note_name_to_midi("C5") == 72
        assert music_theory.note_name_to_midi("C6") == 84
        
    def test_note_name_to_midi_invalid_input(self, music_theory):
        """Test błędnych danych wejściowych"""
        with pytest.raises(ValueError, match="Invalid note name"):
            music_theory.note_name_to_midi("")
        with pytest.raises(ValueError, match="Invalid note name"):
            music_theory.note_name_to_midi("C")
        with pytest.raises(ValueError, match="Octave must be a number"):
            music_theory.note_name_to_midi("CA")
        with pytest.raises(ValueError, match="Unknown note name"):
            music_theory.note_name_to_midi("H4")
    
    # ===== Testy dla midi_to_note_name =====
    
    def test_midi_to_note_name_basic(self, music_theory):
        """Test podstawowej konwersji MIDI na nazwy nut"""
        assert music_theory.midi_to_note_name(60) == "C4"
        assert music_theory.midi_to_note_name(69) == "A4"
        assert music_theory.midi_to_note_name(48) == "C3"
        
    def test_midi_to_note_name_sharps(self, music_theory):
        """Test konwersji MIDI z krzyżykami"""
        assert music_theory.midi_to_note_name(61) == "C#4"
        assert music_theory.midi_to_note_name(66) == "F#4"
        assert music_theory.midi_to_note_name(80) == "G#5"
        
    def test_midi_to_note_name_edge_cases(self, music_theory):
        """Test przypadków brzegowych MIDI"""
        assert music_theory.midi_to_note_name(0) == "C-1"
        assert music_theory.midi_to_note_name(127) == "G9"
        
    def test_midi_to_note_name_invalid_range(self, music_theory):
        """Test wartości MIDI poza zakresem"""
        with pytest.raises(ValueError, match="MIDI value out of range"):
            music_theory.midi_to_note_name(-1)
        with pytest.raises(ValueError, match="MIDI value out of range"):
            music_theory.midi_to_note_name(128)
    
    def test_midi_note_conversion_roundtrip(self, music_theory):
        """Test dwukierunkowej konwersji MIDI <-> nazwa nuty"""
        test_notes = ["C4", "D#3", "F5", "A#6", "G2"]
        for note in test_notes:
            midi = music_theory.note_name_to_midi(note)
            result = music_theory.midi_to_note_name(midi)
            assert result == note
    
    # ===== Testy dla get_interval_name =====
    
    def test_get_interval_name_basic(self, music_theory):
        """Test nazw podstawowych interwałów"""
        assert music_theory.get_interval_name(0) == "P1 (Unison)"
        assert music_theory.get_interval_name(7) == "P5 (Perfect 5th)"
        # 12 % 12 = 0, więc zwraca Unison
        assert music_theory.get_interval_name(12) == "P1 (Unison)"
        
    def test_get_interval_name_all_intervals(self, music_theory):
        """Test wszystkich interwałów w oktawie"""
        expected = {
            0: "P1 (Unison)",
            1: "m2 (Minor 2nd)",
            2: "M2 (Major 2nd)",
            3: "m3 (Minor 3rd)",
            4: "M3 (Major 3rd)",
            5: "P4 (Perfect 4th)",
            6: "TT (Tritone)",
            7: "P5 (Perfect 5th)",
            8: "m6 (Minor 6th)",
            9: "M6 (Major 6th)",
            10: "m7 (Minor 7th)",
            11: "M7 (Major 7th)",
        }
        for semitones, name in expected.items():
            assert music_theory.get_interval_name(semitones) == name
    
    def test_get_interval_name_modulo(self, music_theory):
        """Test interwałów większych niż oktawa (modulo 12)"""
        assert music_theory.get_interval_name(13) == "m2 (Minor 2nd)"  # 13 % 12 = 1
        assert music_theory.get_interval_name(19) == "P5 (Perfect 5th)"  # 19 % 12 = 7
        assert music_theory.get_interval_name(24) == "P1 (Unison)"  # 24 % 12 = 0
    
    # ===== Testy dla get_all_midi_notes =====
    
    def test_get_all_midi_notes_default_range(self, music_theory):
        """Test domyślnego zakresu nut MIDI"""
        notes = music_theory.get_all_midi_notes()
        assert len(notes) > 0
        assert all(0 <= note <= 127 for note in notes)
        
    def test_get_all_midi_notes_custom_range(self, music_theory):
        """Test niestandardowego zakresu oktaw"""
        notes = music_theory.get_all_midi_notes(min_octave=3, max_octave=5)
        # Oktawy 3, 4, 5 = 3 oktawy * 12 nut = 36 nut
        assert len(notes) == 36
        assert min(notes) >= 48  # C3
        assert max(notes) <= 95  # B5
    
    def test_get_all_midi_notes_single_octave(self, music_theory):
        """Test pojedynczej oktawy"""
        notes = music_theory.get_all_midi_notes(min_octave=4, max_octave=4)
        assert len(notes) == 12
    
    # ===== Testy dla generate_diatonic_chord =====
    
    def test_generate_diatonic_chord_tonic(self, music_theory):
        """Test generowania akordu toniki (I)"""
        result = music_theory.generate_diatonic_chord(60, 1)  # C major tonic
        assert result["name"] == "I (Tonic)"
        assert result["root_midi"] == 60  # C4
        assert len(result["chord_midi"]) == 3  # Triada
        assert result["correct_degree"] == 1
        
    def test_generate_diatonic_chord_dominant(self, music_theory):
        """Test generowania akordu dominanty (V)"""
        result = music_theory.generate_diatonic_chord(60, 5)  # G major
        assert result["name"] == "V (Dominant)"
        assert result["root_midi"] == 67  # G4 (60 + 7 półtonów)
        assert len(result["chord_midi"]) == 3
        
    def test_generate_diatonic_chord_subdominant(self, music_theory):
        """Test generowania akordu subdominanty (IV)"""
        result = music_theory.generate_diatonic_chord(60, 4)  # F major
        assert result["name"] == "IV (Subdominant)"
        assert result["root_midi"] == 65  # F4 (60 + 5 półtonów)
    
    def test_generate_diatonic_chord_minor_chords(self, music_theory):
        """Test generowania akordów molowych"""
        # ii
        result_ii = music_theory.generate_diatonic_chord(60, 2)
        assert "moll" in result_ii["display_name"]
        
        # iii
        result_iii = music_theory.generate_diatonic_chord(60, 3)
        assert "moll" in result_iii["display_name"]
        
        # vi
        result_vi = music_theory.generate_diatonic_chord(60, 6)
        assert "moll" in result_vi["display_name"]
    
    def test_generate_diatonic_chord_diminished(self, music_theory):
        """Test generowania akordu zmniejszonego (vii°)"""
        result = music_theory.generate_diatonic_chord(60, 7)
        assert result["name"] == "vii° (Leading)"
        assert "zmn" in result["display_name"]
    
    def test_generate_diatonic_chord_all_degrees(self, music_theory):
        """Test wszystkich stopni w tonacji C-dur"""
        for degree in range(1, 8):
            result = music_theory.generate_diatonic_chord(60, degree)
            assert result["correct_degree"] == degree
            assert len(result["chord_midi"]) == 3
            assert all(0 <= note <= 127 for note in result["chord_midi"])
    
    def test_generate_diatonic_chord_invalid_degree(self, music_theory):
        """Test błędnych stopni skali"""
        with pytest.raises(ValueError, match="Invalid chord degree"):
            music_theory.generate_diatonic_chord(60, 0)
        with pytest.raises(ValueError, match="Invalid chord degree"):
            music_theory.generate_diatonic_chord(60, 8)
    
    def test_generate_diatonic_chord_different_keys(self, music_theory):
        """Test generowania akordów w różnych tonacjach"""
        # D major (MIDI 62)
        result_d = music_theory.generate_diatonic_chord(62, 1)
        assert result_d["root_midi"] == 62
        
        # G major (MIDI 67)
        result_g = music_theory.generate_diatonic_chord(67, 1)
        assert result_g["root_midi"] == 67
