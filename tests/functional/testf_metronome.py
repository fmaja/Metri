import pytest
import customtkinter as ctk
import time
from unittest import mock
from threading import Thread
from PIL import Image

from src.metri.views.metronome import MetronomeView, MetronomeLogic


# ==========================================================
# FIXTURY (KONFIGURACJA TESTÓW)
# ==========================================================

# 1. Mockowanie Audio (Pygame)
@pytest.fixture(autouse=True)
def mock_pygame():
    with mock.patch('pygame.mixer.init'):
        with mock.patch('pygame.mixer.Sound'):
            yield


@pytest.fixture(autouse=True)
def disable_image_rendering():

    with mock.patch('customtkinter.CTkButton._update_image'):

        with mock.patch('customtkinter.CTkImage', return_value=mock.MagicMock()):
            with mock.patch('PIL.Image.open', return_value=mock.MagicMock()):
                yield


# 3. Mockowanie głównego okna (Scope session - jedno okno na wszystkie testy)
@pytest.fixture(scope='session')
def mock_master():
    root = ctk.CTk()
    root.withdraw()  # Ukrywamy okno, żeby nie wyskakiwało

    mock_sidebar = mock.Mock()
    mock_back_callback = mock.Mock()

    yield root, mock_sidebar, mock_back_callback

    # Sprzątanie na koniec wszystkich testów
    root.quit()
    root.destroy()


# 4. Tworzenie widoku (SUT - System Under Test)
@pytest.fixture
def metronome_view(mock_master):
    root, mock_sidebar, mock_back_callback = mock_master

    view = MetronomeView(
        master=root,
        sidebar=mock_sidebar,
        back_callback=mock_back_callback
    )

    # Mockujemy callback wskaźnika, aby wątek nie próbował rysować po GUI
    view.update_beat_indicator = mock.Mock()

    # Inicjalizacja logiki (jeśli widok tego nie robi sam w __init__)
    view.metronome_thread = MetronomeLogic(
        view.bpm_var, view.is_running_var,
        view.time_signature_var, view.update_beat_indicator,
        view.click_obj, view.strong_click_obj
    )

    yield view

    # CLEANUP: Zatrzymujemy wątek po każdym teście
    view.stop_metronome_thread()


# ==========================================================
# TESTY
# ==========================================================

# TC-MET-001: Prawidłowe uruchomienie i zatrzymanie Metronomu.
def test_metronome_toggle_start_stop(metronome_view):
    # GIVEN
    assert metronome_view.is_running_var.get() == False
    assert metronome_view.start_stop_button.cget("text") == "START"

    # WHEN: START
    metronome_view.toggle_metronome()

    # [WAŻNE] Zapisujemy referencję do działającego wątku, zanim zostanie wyzerowana!
    started_thread = metronome_view.metronome_thread

    # THEN: Start
    assert metronome_view.is_running_var.get() == True
    assert metronome_view.start_stop_button.cget("text") == "STOP"
    assert started_thread.is_alive() == True

    # WHEN: STOP
    metronome_view.toggle_metronome()

    # THEN: Stop
    assert metronome_view.is_running_var.get() == False
    assert metronome_view.start_stop_button.cget("text") == "START"

    # Czekamy na zakończenie wątku używając zapisanej zmiennej
    if started_thread:
        started_thread.join(timeout=0.2)

    # Sprawdzamy czy widok wyczyścił pole
    assert metronome_view.metronome_thread is None


# TC-MET-002: Dolna granica BPM
def test_bpm_lower_limit_40(metronome_view):
    metronome_view.bpm_var.set(40)
    metronome_view._adjust_bpm(-1)
    assert metronome_view.bpm_var.get() == 40

    metronome_view.bpm_var.set(41)
    metronome_view._adjust_bpm(-1)
    assert metronome_view.bpm_var.get() == 40


# TC-MET-003: Górna granica BPM
def test_bpm_upper_limit_240(metronome_view):
    metronome_view.bpm_var.set(240)
    metronome_view._adjust_bpm(1)
    assert metronome_view.bpm_var.get() == 240

    metronome_view.bpm_var.set(239)
    metronome_view._adjust_bpm(1)
    assert metronome_view.bpm_var.get() == 240


# TC-MET-004: Zmiana metrum (wskaźniki)
def test_time_signature_changes_indicators(metronome_view):
    # Wymuszamy utworzenie wskaźników jeśli ich nie ma
    if not metronome_view.beat_indicators:
        metronome_view.create_beat_indicators()

    assert len(metronome_view.beat_indicators) == 4

    metronome_view._set_time_signature("5/4")
    assert metronome_view.time_signature_var.get() == "5/4"
    assert len(metronome_view.beat_indicators) == 5

    metronome_view._set_time_signature("12/4")
    assert len(metronome_view.beat_indicators) == 12


# TC-MET-005: Tap Tempo limity
def test_tap_tempo_limits(metronome_view):
    # Symulacja 300 BPM (0.2s przerwy)
    interval = 0.2

    with mock.patch('time.time', side_effect=[0, interval, interval * 2, interval * 3, interval * 4]):
        for _ in range(5):
            metronome_view._on_tap_tempo()

    # Limit powinien obciąć do 240
    assert metronome_view.bpm_var.get() == 240