# src/metri/logic/midi_player.py - PEŁNA POPRAWIONA WERSJA

import pygame.midi
import time

_midi_instance = None

def get_midi_player():
    global _midi_instance
    if _midi_instance is None:
        _midi_instance = MidiPlayer()
    return _midi_instance
class MidiPlayer:
    def __init__(self):
        """
        Initializes the MIDI player.
        """
        self.output_port = None
        self._init_midi()

    def _init_midi(self):
        """
        Initializes pygame.midi, checking if it's already running.
        This prevents conflicts when creating multiple instances.
        """
        try:
            # Check if pygame.midi is already initialized
            if not pygame.midi.get_init():
                pygame.midi.init()

            default_id = pygame.midi.get_default_output_id()
            if default_id == -1:
                print("No default MIDI output port found. Searching...")
                # Fallback: find the first available output port
                for i in range(pygame.midi.get_count()):
                    r = pygame.midi.get_device_info(i)
                    (interface, name, is_input, is_output, opened) = r
                    if is_output:
                        default_id = i
                        print(f"Using MIDI port: {name.decode('utf-8')}")
                        break

            if default_id != -1:
                self.output_port = pygame.midi.Output(default_id)
                self.output_port.set_instrument(0)  # 0: Acoustic Grand Piano
                print("MIDI player initialized.")
            else:
                print("Failed to find any MIDI output port.")
        except pygame.midi.MidiException as e:
            print(f"MIDI initialization error: {e}")
            self.output_port = None
        except Exception as e:
            print(f"General MIDI initialization error: {e}")
            self.output_port = None

    def play_note(self, midi_note, velocity=100, duration=0.5):
        """Plays a single MIDI note."""
        if self.output_port:
            self.output_port.note_on(midi_note, velocity)
            time.sleep(duration)
            self.output_port.note_off(midi_note, velocity)
        else:
            print(f"MIDI player not initialized. Can't play note {midi_note}.")

    def play_notes(self, midi_notes, velocity=100, duration=0.5, play_simultaneously=True):
        """Plays multiple notes, simultaneously or sequentially."""
        if not self.output_port:
            print("MIDI player not initialized. Can't play notes.")
            return

        if play_simultaneously:
            for note in midi_notes:
                self.output_port.note_on(note, velocity)
            time.sleep(duration)
            for note in midi_notes:
                self.output_port.note_off(note, velocity)
        else:
            for note in midi_notes:
                self.play_note(note, velocity, duration)

