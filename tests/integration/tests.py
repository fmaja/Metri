import pytest
import customtkinter as ctk
from unittest import mock
import random

from src.metri.views.interval_quiz_view import IntervalQuizView

# Zakres MIDI nut od C3 (48) do B5 (83)
MIDI_NOTE_RANGE = list(range(48, 84))


# --- FIXTURY INTEGRACYJNE ---

@pytest.fixture(autouse=True)
def mock_gui_and_midi():
    """Mockuje midi_player i matplotlib oraz Tkinter/CTkToplevel."""
    with mock.patch('src.metri.views.interval_quiz_view.get_midi_player') as mock_midi:
        mock_midi_player_instance = mock.Mock()
        mock_midi.return_value = mock_midi_player_instance

        # Mockowanie Toplevel (okno modalne)
        with mock.patch('customtkinter.CTkToplevel', autospec=True) as MockToplevel:
            modal_instance = MockToplevel.return_value
            modal_instance.grab_set = mock.Mock()
            modal_instance.destroy = mock.Mock()
            modal_instance.protocol = mock.Mock()
            modal_instance.focus_set = mock.Mock()

            # Wymuszenie użycia 'Agg' dla Matplotlib, aby uniknąć błędów GUI
            with mock.patch('matplotlib.use', return_value=None):
                yield mock_midi_player_instance, modal_instance

@pytest.fixture
def mock_session_management_io():
    """Mockuje funkcje zapisu i odczytu, ale używa ich w testach (do sprawdzania call_args)."""
    with mock.patch('src.metri.views.interval_quiz_view.save_session') as mock_save:
        with mock.patch('src.metri.views.interval_quiz_view.get_last_sessions', autospec=True) as mock_get_sessions:
            # Ustawiamy pustą listę sesji, aby modal nie próbował niczego rysować
            mock_get_sessions.return_value = []
            yield mock_save, mock_get_sessions


@pytest.fixture(scope='session', autouse=True)
def mock_tkinter_environment_root():
    """Tworzy root okno dla widoku."""
    root = ctk.CTk()
    root.withdraw()
    yield root
    root.quit()
    root.destroy()


@pytest.fixture
def quiz_view_integrated(mock_tkinter_environment_root, mock_session_management_io):
    """Tworzy instancję IntervalQuizView z ZINTEGROWANĄ MusicTheory."""
    root = mock_tkinter_environment_root

    # Mockujemy after
    with mock.patch('customtkinter.CTkBaseClass.after', return_value="after_id_mock"):
        # Używamy faktycznej klasy MusicTheory (nie jest mockowana)
        # Wymuszamy wybór nut C4 (60) i Kwarta Czysta (5)
        with mock.patch.object(random, 'choice', side_effect=[60, 5]):
            view = IntervalQuizView(master=root)  # Callbacki są opcjonalne

    view.after = mock.Mock(return_value="after_id_mock")
    view.after_cancel = mock.Mock()

    # Mockujemy modal dla bezpieczeństwa, ale sprawdzamy save_session
    view.show_results_modal = mock.Mock()

    yield view
    view.destroy()


# ==========================================================
# SCENARIUSZE TESTÓW INTEGRACYJNYCH
# ==========================================================

# IT-QUIZ-001: Pełna ścieżka: Poprawna odpowiedź (Integracja View - Logic)
def test_integration_correct_answer(quiz_view_integrated):
    # GIVEN: Pytanie: C4 (60) i Kwarta Czysta (5 półtonów), czyli C4 i F4 (65)

    # WHEN: Użytkownik klika C4 (60) i F4 (65) i sprawdza
    quiz_view_integrated._on_key_press("C4")
    quiz_view_integrated._on_key_press("F4")

    quiz_view_integrated.check_answer()

    # THEN: Wynik jest poprawny (MusicTheory.note_name_to_midi musi działać)
    assert quiz_view_integrated.feedback_label.cget("text") == "BRAWO!"
    assert quiz_view_integrated.correct_count == 1
    assert quiz_view_integrated.wrong_count == 0


# IT-QUIZ-002: Weryfikacja zakresu i pętli (Integracja Logic - Randomness)
def test_integration_range_check(mock_tkinter_environment_root):
    # GIVEN: Przygotowujemy root
    root = mock_tkinter_environment_root

    # WHEN: Mockujemy random.choice, aby WYMUSIĆ niepoprawny wybór na początku:
    # 1. Wybór C2 (36) (Poza zakresem 48-83)
    # 2. Wybór 12 półtonów
    # 3. Wybór F3 (53) (Poprawny)
    # 4. Wybór 5 półtonów (Poprawny)
    mock_choices = [36, 12, 53, 5]

    with mock.patch('customtkinter.CTkBaseClass.after', return_value="after_id_mock"):
        with mock.patch.object(random, 'choice', side_effect=mock_choices) as mock_random_choice:
            view = IntervalQuizView(master=root)

    # THEN:
    # 1. Pętla while powinna być wykonana co najmniej raz, ponieważ 36 < 48.
    # 2. random.choice powinno być wywołane więcej niż 2 razy (ponieważ pętla się powtórzy).
    # 3. Końcowe pytanie powinno być poprawne (note1_midi=53, note2_midi=58)

    # Sprawdzenie, czy logika została uruchomiona ponownie
    assert mock_random_choice.call_count == 3

    # Sprawdzenie, czy finalnie wybrana nuta jest w zakresie (note1_midi=53)
    final_note1 = view.current_question["note1_midi"]
    final_note2 = view.current_question["note2_midi"]

    assert final_note1 >= 48 and final_note1 <= 83
    assert final_note2 >= 48 and final_note2 <= 83

    view.destroy()


# IT-QUIZ-003: Weryfikacja zapisu sesji (Integracja View - Data)
def test_integration_save_session(quiz_view_integrated, mock_session_management_io):
    mock_save, mock_get_sessions = mock_session_management_io

    # GIVEN: Ustawienie wyników
    quiz_view_integrated.correct_count = 5
    quiz_view_integrated.wrong_count = 2

    # WHEN: Wywołano handle_exit (do Menu Głównego - używamy opcjonalnego callbacka)
    mock_exit_callback = mock.Mock()
    quiz_view_integrated.handle_exit(mock_exit_callback)

    # THEN: Funkcja save_session jest wywołana raz z poprawnymi danymi
    expected_data = {"correct": 5, "wrong": 2}
    mock_save.assert_called_once_with("interval", expected_data)

    # Sprawdzenie, czy modal został wywołany po zapisie
    quiz_view_integrated.show_results_modal.assert_called_once()