import re
import json

def song_data_jsonify_auto(song_data, song_id):
    song_dict = {
        'id': song_id,
        'title': song_data.get('title', ''),
        'artist': song_data.get('artist', ''),
        'group': song_data.get('group', ''),
        'lyricsby': song_data.get('lyricsby', ''),
        'musicby': song_data.get('musicby', ''),
        'key': song_data.get('key', ''),
        'bpm': song_data.get('bpm', ''),
        'timeSignature': song_data.get('timeSignature', ''),
        'tuning': song_data.get('tuning', ''),
        'capo': song_data.get('capo', ''),
        'language': song_data.get('language', ''),
        'tags': song_data.get('tags', []),
        'content': [],
        'lyrics': {},
        'chords': {}
    }

    if isinstance(song_dict['tags'], str):
        song_dict['tags'] = string_to_list(song_dict['tags'])

    text = song_data.get('lyrics', '')
    text = split_into_sections(text)
    text = redefine_sections(text)
    text = name_sections(text)
    text = del_repetitions(text)

    for section in text:
        song_dict['content'].append(section['section'])
        song_dict['lyrics'][section['section']] = section['lyrics']
        song_dict['chords'][section['section']] = section['chords']

    return song_dict

def del_repetitions(text):
    for section in text:
        while len(section['chords']) > 1 and section['chords'][-1] == section['chords'][-2]:
            section['chords'].pop()

    return text

def song_data_jsonify(song_data, song_id):
    song_dict = {
        'id': song_id,
        'title': song_data.get('title', ''),
        'artist': song_data.get('artist', ''),
        'group': song_data.get('group', ''),
        'lyricsby': string_to_list(song_data.get('lyricsby', '')),
        'musicby': string_to_list(song_data.get('musicby', '')),
        'key': song_data.get('key', ''),
        'bpm': song_data.get('bpm', ''),
        'timeSignature': song_data.get('timeSignature', ''),
        'tuning': song_data.get('tuning', ''),
        'capo': song_data.get('capo', ''),
        'language': song_data.get('language', ''),
        'tags': string_to_list(song_data.get('tags', '')),
        'content': [],
        'lyrics': {},
        'chords': {}
    }

    lyrics = song_data.get('lyrics', '')
    chords = song_data.get('chords', '')

    content = []
    section_counts = {}
    lyrics_parsed = {}
    chords_parsed = {}

    for line in lyrics.splitlines():
        line = line.strip()
        if line:
            if line[0] == '[' and line[-1] == ']':
                section = line[1:-1].rstrip('0123456789').strip()
                
                if section != 'c' or section != 'C':
                    if section in section_counts:
                        section_counts[section] += 1
                        section = f"{section}{section_counts[section]}"
                    else:
                        section_counts[section] = 1

                lyrics_parsed[section] = []
                content.append(section)
            elif line[0] == '/':
                lyrics_parsed[section].append('')
            else:
                if content[-1]:
                    lyrics_parsed[content[-1]].append(line)
            

    for line in chords.splitlines():
        line = line.strip()
        if line:
            if line[0] == '[' and line[-1] == ']':
                section = line[1:-1].strip()
                chords_parsed[section] = []
            elif line[0] == '/':
                if section in chords_parsed:
                    chords_parsed[section].append('')
            else:
                if section in chords_parsed:
                    chords_parsed[section].append(line)

    for section in content: 
        if not section in chords_parsed:
            if section.rstrip('0123456789') in chords_parsed:
                chords_parsed[section] = chords_parsed[section.rstrip('0123456789')]
        if lyrics_parsed[section] == []:
            if section.rstrip('0123456789') in lyrics_parsed:
                lyrics_parsed[section] = lyrics_parsed[section.rstrip('0123456789')]

    song_dict['lyrics'] = lyrics_parsed
    song_dict['chords'] = chords_parsed
    song_dict['content'] = content

    return song_dict

def split_into_sections(text):
    p_section = r"\[[A-Za-z0-9 ]*\]"
    text_split = []
    
    if '[' not in text or ']' not in text: 
        text = re.sub(r'(\n\s*){3,}', '\n[]\n', text)

    text_lines = text.splitlines()

    for line in text_lines:
        if line.strip() != "":
            line = re.sub(r'\s+', ' ', line).strip()
            if re.match(p_section, line):
                section = line[1:-1].strip() + " "
                text_split.append({"section": section[0], "content": []})
            else:
                if not text_split:
                    text_split.append({"section": " ", "content": []})
                text_split[-1]["content"].append(line.strip())

    text_split = [section for section in text_split if section["content"]]

    return text_split

def redefine_sections(text):
    p_chord = r"^((\s?)*[CDEFGAHB](#|b)?(m?)([maj|sus|dim]?([1-9]?)*(\/[CDEFGAHB](#|b)?(m?))?)*(\s?)*)*$"

    for section in text:
        section['chords'] = []
        section['lyrics'] = []

        for i in range(len(section["content"])):
            line = section["content"][i]
            if re.match(p_chord, section["content"][i]):
                while len(section['chords']) < len(section['lyrics']):
                    section['chords'].append("")
                section['chords'].append(line)
            else:
                section['lyrics'].append(line)
        
    for section in text:
        if section['lyrics'] == []:
            if section['chords'] == []:
                text.remove(section)
            else:
                section['lyrics'] = section['chords']
                section['chords'] = []

    return text

def name_sections(text):
    for section in text:
        section['section'] = section['section'].lower()
        if section['section'] != 'v' and section['section'] != 'c' and section['section'] != 'i' and section['section'] != 's':
            if section['chords'] == []:
                section['section'] = 'i'
            else:
                section['section'] = 'v'
        for section_2 in text:
            if section == section_2:
                break
            if section['lyrics'] == section_2['lyrics'] and section['chords'] == section_2['chords']:
                section_2['section'] = 'c'
                section['section'] = 'c'
                break
                

    sect = ['', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    section_counts = {}
    skip_nember = False
    
    for section in text:
        skip_nember = False
        i = 0

        while i < len(sect) and  f"{section['section']}{sect[i]}" in section_counts:
            i += 1

        section['section'] = f"{section['section']}{sect[i]}"

        for section_2 in text:
            if section == section_2:
                break
            if section['chords'] == section_2['chords']:
                section['section'] = section_2['section']
                break
            if section['lyrics'] == section_2['lyrics'] and section['chords'] == section_2['chords']:
                section['section'] = section_2['section']
                skip_nember = True
                break
        
        if not skip_nember:
            if section['section'] in section_counts:
                section_counts[section['section']] += 1
                section['section'] = f"{section['section']}{section_counts[section['section']]}"
            else:
                section_counts[section['section']] = 0
                
    return text

def string_to_list(string):
        if not string:
            return []
        return [item.strip() for item in string.split(';')]