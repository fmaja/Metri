import pytest
import customtkinter as ctk
from unittest import mock
import random
import sys


from src.metri.views.interval_quiz_view import IntervalQuizView

# --- STAŁE I MOCKOWANIE KLASY MUZYCZNEJ ---

# Zakres MIDI nut od C3 (48) do B5 (83), jak w widoku
MIDI_NOTE_RANGE = list(range(48, 84))


# Pomocnicza funkcja do mockowania note_name_to_midi
def mock_note_name_to_midi(note_name):
    # Proste mapowanie dla potrzeb testów
    mapping = {
        "C3": 48, "D3": 50, "E3": 52, "F3": 53, "G3": 55, "A3": 57, "B3": 59,
        "C4": 60, "D4": 62, "E4": 64, "F4": 65, "G4": 67, "A4": 69, "B4": 71,
        "C5": 72, "D5": 74, "E5": 76, "F5": 77, "G5": 79, "A5": 81, "B5": 83
    }
    return mapping.get(note_name, 0)  # Zwraca 0 dla nieznanych nut (np. C#)


@pytest.fixture(autouse=True)
def mock_external_libs():
    """Mockuje midi_player, save_session i MusicTheory."""
    with mock.patch('src.metri.views.interval_quiz_view.get_midi_player') as mock_midi:
        mock_midi_player_instance = mock.Mock()
        mock_midi.return_value = mock_midi_player_instance

        with mock.patch('src.metri.views.interval_quiz_view.MusicTheory') as MockMusicTheory:
            mock_theory_instance = MockMusicTheory.return_value

            # POPRAWKA KLUCZOWA (1/2): Zapewnienie, że zwracana jest lista intów
            mock_theory_instance.get_all_midi_notes.return_value = MIDI_NOTE_RANGE
            mock_theory_instance.get_interval_name.return_value = "Mock Interval"

            # POPRAWKA KLUCZOWA (2/2): Nadpisanie mapowania nazw nut,
            # aby _on_key_press i check_answer mogły działać na liczbach MIDI
            mock_theory_instance.note_name_to_midi = mock.Mock(side_effect=mock_note_name_to_midi)

            yield mock_midi_player_instance, mock_theory_instance


@pytest.fixture
def mock_session_management():
    """Mockuje funkcje zapisu i odczytu wyników quizu."""
    with mock.patch('src.metri.views.interval_quiz_view.save_session') as mock_save:
        with mock.patch('src.metri.views.interval_quiz_view.get_last_sessions') as mock_get_sessions:
            mock_get_sessions.return_value = []
            yield mock_save, mock_get_sessions


@pytest.fixture(scope='session', autouse=True)
def mock_tkinter_environment():
    """Tworzy root okno i mockuje CTkToplevel, aby nie blokowało testu."""
    with mock.patch('customtkinter.CTkToplevel', autospec=True) as MockToplevel:
        modal_instance = MockToplevel.return_value
        modal_instance.grab_set = mock.Mock()
        modal_instance.destroy = mock.Mock()
        modal_instance.protocol = mock.Mock()
        modal_instance.focus_set = mock.Mock()

        root = ctk.CTk()
        root.withdraw()  # Ukryj główne okno

        yield root, modal_instance

        root.quit()
        root.destroy()


@pytest.fixture
def mock_callbacks():
    """Mockuje callbacki używane przy wychodzeniu z widoku."""
    mock_back = mock.Mock()
    mock_main_quiz = mock.Mock()
    return mock_back, mock_main_quiz


@pytest.fixture
def quiz_view(mock_tkinter_environment, mock_callbacks):
    """Tworzy instancję IntervalQuizView."""
    root, _ = mock_tkinter_environment
    mock_back, mock_main_quiz = mock_callbacks

    # Mockujemy after, aby zapobiec opóźnieniom i auto-odtworzeniu
    with mock.patch('customtkinter.CTkBaseClass.after', return_value="after_id_mock"):
        # Wymuszamy wybór nut: C4 (60) i Kwarta Czysta (5) -> Pytanie C4 do F4
        with mock.patch.object(random, 'choice', side_effect=[60, 5]):
            view = IntervalQuizView(
                master=root,
                back_callback=mock_back,
                show_main_quiz_callback=mock_main_quiz
            )

    view.after = mock.Mock(return_value="after_id_mock")
    view.after_cancel = mock.Mock()

    # Resetujemy etykietę nazwy interwału dla łatwiejszego testowania
    view.music_theory.get_interval_name.return_value = "Mock Interval"

    yield view

    view.destroy()


# ==========================================================
# SCENARIUSZE TESTOWE (Zgodne z TC-QUIZ-001 do 005)
# ==========================================================

# TC-QUIZ-001: Prawidłowe sprawdzenie poprawnej odpowiedzi.
def test_correct_answer(quiz_view):
    # GIVEN: Pytanie to C4 (60) i Kwarta Czysta (5 półtonów), czyli C4 i F4 (65)

    # WHEN: Użytkownik klika C4 (60) i F4 (65) i sprawdza
    quiz_view._on_key_press("C4")
    quiz_view._on_key_press("F4")

    quiz_view.check_answer()

    # THEN: Wynik jest poprawny
    assert quiz_view.feedback_label.cget("text") == "BRAWO!"
    assert quiz_view.correct_count == 1
    assert quiz_view.wrong_count == 0
    assert quiz_view.next_button.cget("state") == "normal"


# TC-QUIZ-002: Prawidłowe sprawdzenie błędnej odpowiedzi i wyświetlenie poprawnej.
def test_wrong_answer_shows_correct_name(quiz_view):
    # GIVEN: Pytanie to C4 i Kwarta Czysta. Mock zwraca "Kwarta Czysta"
    quiz_view.music_theory.get_interval_name.return_value = "Kwarta Czysta"

    # WHEN: Użytkownik klika C4 (60) i E4 (64) (4 półtony - Tercja Wielka)
    quiz_view._on_key_press("C4")
    quiz_view._on_key_press("E4")

    quiz_view.check_answer()

    # THEN: Wynik jest błędny, wyświetlana jest poprawna nazwa
    assert "BŁĄD. Poprawny interwał: Kwarta Czysta" in quiz_view.feedback_label.cget("text")
    assert quiz_view.correct_count == 0
    assert quiz_view.wrong_count == 1
    assert quiz_view.next_button.cget("state") == "normal"


# TC-QUIZ-003: Walidacja wyboru nut na klawiaturze (tylko 2 nuty).
def test_key_selection_limit_2_notes(quiz_view):
    # GIVEN: Klawiatura jest czysta
    assert quiz_view.check_button.cget("state") == "disabled"

    # WHEN: Użytkownik klika C4, D4, E4
    quiz_view._on_key_press("C4")
    quiz_view._on_key_press("D4")

    assert quiz_view.check_button.cget("state") == "normal"  # Aktywny po 2 nutach

    quiz_view._on_key_press("E4")  # C4 zostaje usunięte

    # THEN: W selected_notes są tylko D4 i E4
    assert len(quiz_view.selected_notes) == 2
    assert "C4" not in quiz_view.selected_notes
    assert "D4" in quiz_view.selected_notes
    assert "E4" in quiz_view.selected_notes
    assert quiz_view.check_button.cget("state") == "normal"


# TC-QUIZ-004: Poprawne wyjście z quizu bez udzielonych odpowiedzi.
def test_exit_without_answers(quiz_view, mock_callbacks, mock_session_management):
    mock_back, _ = mock_callbacks
    mock_save, _ = mock_session_management

    # GIVEN: Liczniki są zerowe

    # WHEN: Wywołanie wyjścia do menu głównego
    quiz_view.handle_exit(mock_back)

    # THEN:
    mock_save.assert_not_called()
    # Zakładamy, że mock modal_instance.grab_set().destroy() jest pomijany
    mock_back.assert_called_once()


# TC-QUIZ-005: Zapis i wyświetlenie wyników przy wyjściu z aktywnym quizem.
def test_exit_with_answers_and_save(quiz_view, mock_callbacks, mock_session_management):
    _, mock_main_quiz = mock_callbacks
    mock_save, _ = mock_session_management

    # GIVEN: Udzielono odpowiedzi (np. 1 poprawna, 1 błędna)
    quiz_view.correct_count = 1
    quiz_view.wrong_count = 1

    # Mockujemy show_results_modal, aby nie uruchamiać prawdziwego okna CTkToplevel
    quiz_view.show_results_modal = mock.Mock()

    # WHEN: Wywołanie wyjścia do wyboru quizu
    quiz_view.handle_exit(mock_main_quiz)

    # THEN:
    expected_data = {"correct": 1, "wrong": 1}
    mock_save.assert_called_once_with("interval", expected_data)

    # Sprawdzenie, czy modal jest wywołany z funkcją powrotną
    quiz_view.show_results_modal.assert_called_once_with(mock_main_quiz)

    # Główny callback NIE powinien być wywołany, dopóki modal nie zostanie zamknięty (co jest symulowane w modal.protocol)
    mock_main_quiz.assert_not_called()