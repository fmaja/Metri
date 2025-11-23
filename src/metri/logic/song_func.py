from .jsonify_func import song_data_jsonify, song_data_jsonify_auto
from .keys import transpose
import json
import os


def get_objective_key(song_id):
    song = get_song(song_id)
    
    if song is None:
        return None
    
    key = song.get('key', '')
    
    if not key:
        return '-'
    
    # Convert capo to int, default to 0 if it's not a valid number
    capo = 0
    try:
        capo = int(song.get('capo', 0))
    except (ValueError, TypeError):
        pass
    
    key = transpose(key, key, capo)
    return key


def filter_songs(search_args):
    """Filter and sort songs based on search arguments."""
    songs = load_songs()
    filtered_songs = songs.copy()
    
    if not search_args:
        return filtered_songs
    
    if 'search' in search_args and search_args['search']:
        search_term = search_args['search'].lower()
        filtered_songs = [
            song for song in filtered_songs 
            if (search_term in song.get('title', '').lower() or
                search_term in song.get('artist', '').lower() or
                search_term in song.get('group', '').lower())
        ]
    
    if 'language' in search_args and search_args['language']:
        language = search_args['language'].lower()
        filtered_songs = [
            song for song in filtered_songs
            if language in song.get('language', '').lower()
        ]
    
    if 'tags' in search_args and search_args['tags']:
        if isinstance(search_args['tags'], list):
            tags = [tag.lower() for tag in search_args['tags']]
        else:
            tags = [search_args['tags'].lower()]
            
        filtered_songs = [
            song for song in filtered_songs
            if any(tag in [t.lower() for t in song.get('tags', [])] for tag in tags)
        ]
    
    sort_field = search_args.get('filter_by', 'title')
    if 'sort_by' in search_args:
        sort_field = search_args['sort_by']
    
    if sort_field == 'title':
        filtered_songs.sort(key=lambda x: x.get('title', '').lower())
    elif sort_field == 'artist':
        filtered_songs.sort(key=lambda x: x.get('artist', '').lower())
    elif sort_field == 'group':
        filtered_songs.sort(key=lambda x: x.get('group', '').lower())
    elif sort_field == 'language':
        filtered_songs.sort(key=lambda x: x.get('language', '').lower())
    elif sort_field == 'id':
        filtered_songs.sort(key=lambda x: x['id'])
    
    if 'order' in search_args and search_args['order'] == 'desc':
        filtered_songs.reverse()
    
    return filtered_songs


def get_tags():
    songs = load_songs()
    tags = set()
    
    for song in songs:
        if 'tags' in song:
            for tag in song['tags']:
                tags.add(tag.lower())
    
    return sorted(tags)


def get_songs_path():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(current_dir), 'data')
    songs_path = os.path.join(data_dir, 'songs.json')
    return songs_path


def load_songs():
    songs_path = get_songs_path()
    if os.path.exists(songs_path):
        with open(songs_path, 'r', encoding='utf-8') as f:
            songs = json.load(f)
            return [song for song in songs if song is not None]
    return []


def save_songs(songs):
    songs_path = get_songs_path()
    valid_songs = [song for song in songs if song is not None]
    os.makedirs(os.path.dirname(songs_path), exist_ok=True)
    with open(songs_path, 'w', encoding='utf-8') as f:
        json.dump(valid_songs, f, indent=4, ensure_ascii=False)


def get_song(song_id):
    songs = load_songs()
    try:
        song_id = int(song_id)
        valid_songs = [song for song in songs if song is not None]
        song = next((song for song in valid_songs if song['id'] == song_id), None)
        return song
    except ValueError:
        return None


def get_new_song():
    songs = load_songs()
    song_id = max((song['id'] for song in songs), default=0) + 1
    
    song_dict = {
        'id': song_id,
        'title': '',
        'artist': '',
        'lyricsby': [],
        'musicby': [],
        'key': '',
        'bpm': '',
        'timeSignature': '',
        'tuning': '',
        'capo': '',
        'language':'',
        'tags': [],
        'content': [],
        'lyrics': {},
        'chords': {},
        'display': ''
    }
    
    songs.append(song_dict)
    save_songs(songs)
    
    return song_id


def song_create(song_id, song_data):
    songs = load_songs()
    
    song_id = int(song_id)
    song = next((song for song in songs if song['id'] == song_id), None)

    if song is None:
        return None

    song_dict = song_data_jsonify_auto(song_data, song_id)
    songs[songs.index(song)] = song_dict
    save_songs(songs)
    return song_dict


def song_edit(song_id, song_data):
    songs = load_songs()
    
    song_id = int(song_id)
    song = next((song for song in songs if song['id'] == song_id), None)

    if song is None:
        return None

    song_dict = song_data_jsonify(song_data, song_id)
    songs[songs.index(song)] = song_dict
    save_songs(songs)
    return song_dict


def remove_song(song_id):
    songs = load_songs()
    try:
        song_id = int(song_id)
        song = next((song for song in songs if song['id'] == song_id), None)
        if song is not None:
            songs.remove(song)
            save_songs(songs)
            return True
        return False
    except ValueError:
        return False


def get_songs_by_ids(id_list):
    songs = load_songs()
    id_set = set(int(i) for i in id_list)
    return [song for song in songs if song['id'] in id_set]