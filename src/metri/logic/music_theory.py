# src/metri/logic/music_theory.py - FULLY REVISED FILE

import random


class MusicTheory:
    MIDI_NOTE_NAMES = [
        "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"
    ]
    # Diatonic chord definitions (semitones from root)
    DIATONIC_CHORDS_MAJOR = {
        1: {"name": "I (Tonic)", "type": "dur", "intervals": [0, 4, 7]},
        2: {"name": "ii (Supertonic)", "type": "moll", "intervals": [0, 3, 7]},
        3: {"name": "iii (Mediant)", "type": "moll", "intervals": [0, 3, 7]},
        4: {"name": "IV (Subdominant)", "type": "dur", "intervals": [0, 4, 7]},
        5: {"name": "V (Dominant)", "type": "dur", "intervals": [0, 4, 7]},
        6: {"name": "vi (Submediant)", "type": "moll", "intervals": [0, 3, 7]},
        7: {"name": "vii° (Leading)", "type": "zmn", "intervals": [0, 3, 6]},
    }
    # Major scale formula in semitones
    MAJOR_SCALE_SEMITONES = [0, 2, 4, 5, 7, 9, 11]

    def __init__(self):
        pass

    def note_name_to_midi(self, note_name):
        """Converts note name (e.g., C4, G#5) to MIDI value."""
        if not note_name or len(note_name) < 2:
            raise ValueError("Invalid note name.")

        base_name = note_name[:-1].upper()
        octave_str = note_name[-1]

        if not octave_str.isdigit():
            raise ValueError("Octave must be a number (e.g., C4).")
        octave = int(octave_str)

        try:
            note_index = self.MIDI_NOTE_NAMES.index(base_name)
        except ValueError:
            raise ValueError(f"Unknown note name: {base_name}")

        return note_index + (octave + 1) * 12  # MIDI 0 is C-1

    def midi_to_note_name(self, midi_value):
        """Converts MIDI value to note name (e.g., 60 -> C4)."""
        if not (0 <= midi_value <= 127):
            raise ValueError("MIDI value out of range (0-127).")

        note_index = midi_value % 12
        octave = (midi_value // 12) - 1  # MIDI 0 is C-1

        return f"{self.MIDI_NOTE_NAMES[note_index]}{octave}"

    def get_all_midi_notes(self, min_octave=2, max_octave=6):
        """Returns a list of all MIDI notes in the specified octave range."""
        notes = []
        for octave in range(min_octave, max_octave + 1):
            for i in range(12):
                midi_val = i + (octave + 1) * 12
                if 0 <= midi_val <= 127:
                    notes.append(midi_val)
        return notes

    def get_interval_name(self, semitones):
        """Returns the common name for an interval based on semitones."""
        interval_names = {
            0: "P1 (Unison)", 1: "m2 (Minor 2nd)", 2: "M2 (Major 2nd)",
            3: "m3 (Minor 3rd)", 4: "M3 (Major 3rd)", 5: "P4 (Perfect 4th)",
            6: "TT (Tritone)", 7: "P5 (Perfect 5th)", 8: "m6 (Minor 6th)",
            9: "M6 (Major 6th)", 10: "m7 (Minor 7th)", 11: "M7 (Major 7th)",
            12: "P8 (Octave)"
        }
        return interval_names.get(semitones % 12, "Unknown Interval")

    def generate_diatonic_chord(self, root_midi, degree):
        """
        Generates a diatonic chord based on its degree in a major scale.
        :param root_midi: MIDI value of the tonic (I)
        :param degree: Chord degree (1-7)
        :return: Dict with chord info and MIDI notes.
        """
        if degree not in self.DIATONIC_CHORDS_MAJOR:
            raise ValueError("Invalid chord degree (1-7).")

        # 1. Calculate the chord's root note
        semitones_from_tonic = self.MAJOR_SCALE_SEMITONES[degree - 1]
        chord_root_midi = root_midi + semitones_from_tonic

        # 2. Get the chord intervals (e.g., [0, 4, 7] for Major)
        info = self.DIATONIC_CHORDS_MAJOR[degree]
        intervals = info["intervals"]

        # 3. Build the chord
        chord_midi = [chord_root_midi + interval for interval in intervals]

        # 4. Simple voicing: ensure notes are near the root octave
        adjusted_chord_midi = []
        for i, note in enumerate(chord_midi):
            while note < root_midi:
                note += 12
            while note > root_midi + 24:  # Keep within 2 octaves
                note -= 12
            adjusted_chord_midi.append(note)

        adjusted_chord_midi.sort()

        return {
            "name": info["name"],
            "root_midi": chord_root_midi,
            "chord_midi": adjusted_chord_midi,
            "correct_degree": degree,
            "display_name": f"{self.midi_to_note_name(chord_root_midi)[:-1]} {info['type']} ({info['name']})"
        }