"""
Testy jednostkowe dla modułu song_func.py
"""
import pytest
import sys
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Dodaj src do ścieżki Python
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from metri.logic.song_func import (
    get_objective_key,
    filter_songs,
    get_tags,
    get_song,
    load_songs,
    save_songs,
    get_new_song,
    remove_song,
    get_songs_by_ids
)


class TestGetObjectiveKey:
    """Testy dla funkcji get_objective_key"""
    
    @patch('metri.logic.song_func.get_song')
    def test_get_objective_key_no_capo(self, mock_get_song):
        """Test obliczania tonacji bez kapodastra"""
        mock_get_song.return_value = {'key': 'C', 'capo': 0}
        result = get_objective_key(1)
        assert result == 'C'
    
    @patch('metri.logic.song_func.get_song')
    def test_get_objective_key_with_capo(self, mock_get_song):
        """Test obliczania tonacji z kapodastrem"""
        mock_get_song.return_value = {'key': 'C', 'capo': 2}
        result = get_objective_key(1)
        assert result == 'D'
    
    @patch('metri.logic.song_func.get_song')
    def test_get_objective_key_with_capo_5(self, mock_get_song):
        """Test transpozycji o 5 półtonów"""
        mock_get_song.return_value = {'key': 'C', 'capo': 5}
        result = get_objective_key(1)
        assert result == 'F'
    
    @patch('metri.logic.song_func.get_song')
    def test_get_objective_key_empty_key(self, mock_get_song):
        """Test pustej tonacji"""
        mock_get_song.return_value = {'key': '', 'capo': 0}
        result = get_objective_key(1)
        assert result == '-'
    
    @patch('metri.logic.song_func.get_song')
    def test_get_objective_key_no_key_field(self, mock_get_song):
        """Test braku pola key"""
        mock_get_song.return_value = {'capo': 0}
        result = get_objective_key(1)
        assert result == '-'
    
    @patch('metri.logic.song_func.get_song')
    def test_get_objective_key_invalid_capo(self, mock_get_song):
        """Test nieprawidłowej wartości capo"""
        mock_get_song.return_value = {'key': 'C', 'capo': 'invalid'}
        result = get_objective_key(1)
        assert result == 'C'  # Domyślnie capo = 0
    
    @patch('metri.logic.song_func.get_song')
    def test_get_objective_key_song_not_found(self, mock_get_song):
        """Test nieistniejącej piosenki"""
        mock_get_song.return_value = None
        result = get_objective_key(999)
        assert result is None


class TestFilterSongs:
    """Testy dla funkcji filter_songs"""
    
    @patch('metri.logic.song_func.load_songs')
    def test_filter_songs_no_filters(self, mock_load):
        """Test bez filtrów - zwraca wszystkie piosenki"""
        mock_songs = [
            {'id': 1, 'title': 'Song A'},
            {'id': 2, 'title': 'Song B'}
        ]
        mock_load.return_value = mock_songs
        
        result = filter_songs({})
        assert len(result) == 2
    
    @patch('metri.logic.song_func.load_songs')
    def test_filter_songs_by_search_title(self, mock_load):
        """Test filtrowania po tytule"""
        mock_songs = [
            {'id': 1, 'title': 'Rock Song', 'artist': '', 'group': ''},
            {'id': 2, 'title': 'Pop Song', 'artist': '', 'group': ''},
            {'id': 3, 'title': 'Another Rock', 'artist': '', 'group': ''}
        ]
        mock_load.return_value = mock_songs
        
        result = filter_songs({'search': 'rock'})
        assert len(result) == 2
        assert all('rock' in song['title'].lower() for song in result)
    
    @patch('metri.logic.song_func.load_songs')
    def test_filter_songs_by_search_artist(self, mock_load):
        """Test filtrowania po artyście"""
        mock_songs = [
            {'id': 1, 'title': 'Song 1', 'artist': 'Beatles', 'group': ''},
            {'id': 2, 'title': 'Song 2', 'artist': 'Queen', 'group': ''},
            {'id': 3, 'title': 'Song 3', 'artist': 'The Beatles', 'group': ''}
        ]
        mock_load.return_value = mock_songs
        
        result = filter_songs({'search': 'beatles'})
        assert len(result) == 2
    
    @patch('metri.logic.song_func.load_songs')
    def test_filter_songs_by_language(self, mock_load):
        """Test filtrowania po języku"""
        mock_songs = [
            {'id': 1, 'title': 'Song 1', 'language': 'polski', 'artist': '', 'group': ''},
            {'id': 2, 'title': 'Song 2', 'language': 'english', 'artist': '', 'group': ''},
            {'id': 3, 'title': 'Song 3', 'language': 'polski', 'artist': '', 'group': ''}
        ]
        mock_load.return_value = mock_songs
        
        result = filter_songs({'language': 'polski'})
        assert len(result) == 2
        assert all(song['language'] == 'polski' for song in result)
    
    @patch('metri.logic.song_func.load_songs')
    def test_filter_songs_by_tags_single(self, mock_load):
        """Test filtrowania po pojedynczym tagu"""
        mock_songs = [
            {'id': 1, 'title': 'Song 1', 'tags': ['rock', 'ballad'], 'artist': '', 'group': ''},
            {'id': 2, 'title': 'Song 2', 'tags': ['pop'], 'artist': '', 'group': ''},
            {'id': 3, 'title': 'Song 3', 'tags': ['rock'], 'artist': '', 'group': ''}
        ]
        mock_load.return_value = mock_songs
        
        result = filter_songs({'tags': 'rock'})
        assert len(result) == 2
    
    @patch('metri.logic.song_func.load_songs')
    def test_filter_songs_by_tags_multiple(self, mock_load):
        """Test filtrowania po wielu tagach"""
        mock_songs = [
            {'id': 1, 'title': 'Song 1', 'tags': ['rock', 'ballad'], 'artist': '', 'group': ''},
            {'id': 2, 'title': 'Song 2', 'tags': ['pop'], 'artist': '', 'group': ''},
            {'id': 3, 'title': 'Song 3', 'tags': ['jazz', 'ballad'], 'artist': '', 'group': ''}
        ]
        mock_load.return_value = mock_songs
        
        result = filter_songs({'tags': ['rock', 'ballad']})
        assert len(result) >= 2
    
    @patch('metri.logic.song_func.load_songs')
    def test_filter_songs_sort_by_title(self, mock_load):
        """Test sortowania po tytule"""
        mock_songs = [
            {'id': 1, 'title': 'Zebra Song', 'artist': '', 'group': ''},
            {'id': 2, 'title': 'Apple Song', 'artist': '', 'group': ''},
            {'id': 3, 'title': 'Banana Song', 'artist': '', 'group': ''}
        ]
        mock_load.return_value = mock_songs
        
        result = filter_songs({'sort_by': 'title'})
        assert result[0]['title'] == 'Apple Song'
        assert result[-1]['title'] == 'Zebra Song'
    
    @patch('metri.logic.song_func.load_songs')
    def test_filter_songs_sort_by_artist(self, mock_load):
        """Test sortowania po artyście"""
        mock_songs = [
            {'id': 1, 'title': 'Song 1', 'artist': 'Zebra Band', 'group': ''},
            {'id': 2, 'title': 'Song 2', 'artist': 'Alpha Band', 'group': ''},
            {'id': 3, 'title': 'Song 3', 'artist': 'Beta Band', 'group': ''}
        ]
        mock_load.return_value = mock_songs
        
        result = filter_songs({'sort_by': 'artist'})
        assert result[0]['artist'] == 'Alpha Band'
        assert result[-1]['artist'] == 'Zebra Band'
    
    @patch('metri.logic.song_func.load_songs')
    def test_filter_songs_sort_descending(self, mock_load):
        """Test sortowania malejącego"""
        mock_songs = [
            {'id': 1, 'title': 'Apple', 'artist': '', 'group': ''},
            {'id': 2, 'title': 'Banana', 'artist': '', 'group': ''},
            {'id': 3, 'title': 'Cherry', 'artist': '', 'group': ''}
        ]
        mock_load.return_value = mock_songs
        
        result = filter_songs({'sort_by': 'title', 'order': 'desc'})
        assert result[0]['title'] == 'Cherry'
        assert result[-1]['title'] == 'Apple'
    
    @patch('metri.logic.song_func.load_songs')
    def test_filter_songs_combined_filters(self, mock_load):
        """Test kombinacji filtrów"""
        mock_songs = [
            {'id': 1, 'title': 'Rock Song A', 'artist': 'Band X', 'language': 'polski', 'tags': ['rock'], 'group': ''},
            {'id': 2, 'title': 'Rock Song B', 'artist': 'Band Y', 'language': 'english', 'tags': ['rock'], 'group': ''},
            {'id': 3, 'title': 'Pop Song', 'artist': 'Band Z', 'language': 'polski', 'tags': ['pop'], 'group': ''}
        ]
        mock_load.return_value = mock_songs
        
        result = filter_songs({
            'search': 'rock',
            'language': 'polski',
            'sort_by': 'title'
        })
        assert len(result) == 1
        assert result[0]['id'] == 1


class TestGetTags:
    """Testy dla funkcji get_tags"""
    
    @patch('metri.logic.song_func.load_songs')
    def test_get_tags_from_songs(self, mock_load):
        """Test pobierania tagów z piosenek"""
        mock_songs = [
            {'id': 1, 'tags': ['rock', 'ballad']},
            {'id': 2, 'tags': ['pop', 'rock']},
            {'id': 3, 'tags': ['jazz']}
        ]
        mock_load.return_value = mock_songs
        
        result = get_tags()
        assert 'rock' in result
        assert 'pop' in result
        assert 'ballad' in result
        assert 'jazz' in result
    
    @patch('metri.logic.song_func.load_songs')
    def test_get_tags_unique(self, mock_load):
        """Test że tagi są unikalne"""
        mock_songs = [
            {'id': 1, 'tags': ['rock', 'rock', 'pop']},
            {'id': 2, 'tags': ['rock', 'jazz']}
        ]
        mock_load.return_value = mock_songs
        
        result = get_tags()
        assert result.count('rock') == 1
    
    @patch('metri.logic.song_func.load_songs')
    def test_get_tags_sorted(self, mock_load):
        """Test że tagi są posortowane"""
        mock_songs = [
            {'id': 1, 'tags': ['zebra', 'apple', 'banana']}
        ]
        mock_load.return_value = mock_songs
        
        result = get_tags()
        assert result == sorted(result)
    
    @patch('metri.logic.song_func.load_songs')
    def test_get_tags_case_insensitive(self, mock_load):
        """Test że tagi są normalizowane do małych liter"""
        mock_songs = [
            {'id': 1, 'tags': ['Rock', 'JAZZ', 'Pop']}
        ]
        mock_load.return_value = mock_songs
        
        result = get_tags()
        assert all(tag.islower() for tag in result)
    
    @patch('metri.logic.song_func.load_songs')
    def test_get_tags_no_tags(self, mock_load):
        """Test piosenek bez tagów"""
        mock_songs = [
            {'id': 1},
            {'id': 2, 'tags': []}
        ]
        mock_load.return_value = mock_songs
        
        result = get_tags()
        assert result == []


class TestGetSong:
    """Testy dla funkcji get_song"""
    
    @patch('metri.logic.song_func.load_songs')
    def test_get_song_found(self, mock_load):
        """Test znalezienia piosenki"""
        mock_songs = [
            {'id': 1, 'title': 'Song 1'},
            {'id': 2, 'title': 'Song 2'}
        ]
        mock_load.return_value = mock_songs
        
        result = get_song(1)
        assert result is not None
        assert result['id'] == 1
        assert result['title'] == 'Song 1'
    
    @patch('metri.logic.song_func.load_songs')
    def test_get_song_not_found(self, mock_load):
        """Test nieznalezionej piosenki"""
        mock_songs = [{'id': 1, 'title': 'Song 1'}]
        mock_load.return_value = mock_songs
        
        result = get_song(999)
        assert result is None
    
    @patch('metri.logic.song_func.load_songs')
    def test_get_song_string_id(self, mock_load):
        """Test z ID jako string"""
        mock_songs = [{'id': 1, 'title': 'Song 1'}]
        mock_load.return_value = mock_songs
        
        result = get_song('1')
        assert result is not None
        assert result['id'] == 1
    
    @patch('metri.logic.song_func.load_songs')
    def test_get_song_invalid_id(self, mock_load):
        """Test z nieprawidłowym ID"""
        mock_songs = [{'id': 1, 'title': 'Song 1'}]
        mock_load.return_value = mock_songs
        
        result = get_song('invalid')
        assert result is None
    
    @patch('metri.logic.song_func.load_songs')
    def test_get_song_filters_none_values(self, mock_load):
        """Test filtrowania wartości None"""
        mock_songs = [
            {'id': 1, 'title': 'Song 1'},
            None,
            {'id': 2, 'title': 'Song 2'}
        ]
        mock_load.return_value = mock_songs
        
        result = get_song(1)
        assert result is not None


class TestGetSongsByIds:
    """Testy dla funkcji get_songs_by_ids"""
    
    @patch('metri.logic.song_func.load_songs')
    def test_get_songs_by_ids_single(self, mock_load):
        """Test pobierania pojedynczej piosenki"""
        mock_songs = [
            {'id': 1, 'title': 'Song 1'},
            {'id': 2, 'title': 'Song 2'}
        ]
        mock_load.return_value = mock_songs
        
        result = get_songs_by_ids([1])
        assert len(result) == 1
        assert result[0]['id'] == 1
    
    @patch('metri.logic.song_func.load_songs')
    def test_get_songs_by_ids_multiple(self, mock_load):
        """Test pobierania wielu piosenek"""
        mock_songs = [
            {'id': 1, 'title': 'Song 1'},
            {'id': 2, 'title': 'Song 2'},
            {'id': 3, 'title': 'Song 3'}
        ]
        mock_load.return_value = mock_songs
        
        result = get_songs_by_ids([1, 3])
        assert len(result) == 2
        assert any(s['id'] == 1 for s in result)
        assert any(s['id'] == 3 for s in result)
    
    @patch('metri.logic.song_func.load_songs')
    def test_get_songs_by_ids_not_found(self, mock_load):
        """Test z nieistniejącymi ID"""
        mock_songs = [{'id': 1, 'title': 'Song 1'}]
        mock_load.return_value = mock_songs
        
        result = get_songs_by_ids([999])
        assert len(result) == 0
    
    @patch('metri.logic.song_func.load_songs')
    def test_get_songs_by_ids_empty_list(self, mock_load):
        """Test z pustą listą ID"""
        mock_songs = [{'id': 1, 'title': 'Song 1'}]
        mock_load.return_value = mock_songs
        
        result = get_songs_by_ids([])
        assert len(result) == 0


class TestRemoveSong:
    """Testy dla funkcji remove_song"""
    
    @patch('metri.logic.song_func.save_songs')
    @patch('metri.logic.song_func.load_songs')
    def test_remove_song_success(self, mock_load, mock_save):
        """Test pomyślnego usunięcia piosenki"""
        mock_songs = [
            {'id': 1, 'title': 'Song 1'},
            {'id': 2, 'title': 'Song 2'}
        ]
        mock_load.return_value = mock_songs
        
        result = remove_song(1)
        assert result is True
        mock_save.assert_called_once()
    
    @patch('metri.logic.song_func.save_songs')
    @patch('metri.logic.song_func.load_songs')
    def test_remove_song_not_found(self, mock_load, mock_save):
        """Test usuwania nieistniejącej piosenki"""
        mock_songs = [{'id': 1, 'title': 'Song 1'}]
        mock_load.return_value = mock_songs
        
        result = remove_song(999)
        assert result is False
    
    @patch('metri.logic.song_func.save_songs')
    @patch('metri.logic.song_func.load_songs')
    def test_remove_song_invalid_id(self, mock_load, mock_save):
        """Test nieprawidłowego ID"""
        mock_songs = [{'id': 1, 'title': 'Song 1'}]
        mock_load.return_value = mock_songs
        
        result = remove_song('invalid')
        assert result is False


class TestLoadSaveSongs:
    """Testy dla funkcji load_songs i save_songs"""
    
    def test_load_save_round_trip(self):
        """Test zapisywania i odczytywania piosenek"""
        # Użyj tymczasowego pliku
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = os.path.join(tmpdir, 'test_songs.json')
            
            test_songs = [
                {'id': 1, 'title': 'Test Song 1'},
                {'id': 2, 'title': 'Test Song 2'}
            ]
            
            # Mock get_songs_path
            with patch('metri.logic.song_func.get_songs_path', return_value=test_path):
                save_songs(test_songs)
                loaded = load_songs()
                
                assert len(loaded) == 2
                assert loaded[0]['title'] == 'Test Song 1'
                assert loaded[1]['title'] == 'Test Song 2'
    
    def test_load_songs_file_not_exists(self):
        """Test ładowania gdy plik nie istnieje"""
        with patch('metri.logic.song_func.get_songs_path', return_value='/nonexistent/path.json'):
            result = load_songs()
            assert result == []
    
    def test_save_songs_filters_none(self):
        """Test że save_songs filtruje wartości None"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = os.path.join(tmpdir, 'test_songs.json')
            
            test_songs = [
                {'id': 1, 'title': 'Song 1'},
                None,
                {'id': 2, 'title': 'Song 2'}
            ]
            
            with patch('metri.logic.song_func.get_songs_path', return_value=test_path):
                save_songs(test_songs)
                loaded = load_songs()
                
                # Nie powinno być None w załadowanych piosenkach
                assert len(loaded) == 2
                assert all(song is not None for song in loaded)
