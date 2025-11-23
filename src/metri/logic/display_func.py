from .song_func import get_song
from .keys import transpose
import re

def get_display_lyrics(song_id, transp=0):

    song = get_song(song_id)
    display = ''

    lyrics = song['lyrics']
    content = song['content']

    for section in content:
        disp = True
        display += '['+ section +']'
        if section in lyrics and section.rstrip('0123456789') in lyrics:
            if not (lyrics[section] == lyrics[section.rstrip('0123456789')] and section != section.rstrip('0123456789')):
                for sect in content:
                    if sect == section:
                        break
                    if sect == section.rstrip('0123456789') and lyrics[sect] == lyrics[section]:
                        disp = False
                        break
                if disp:
                    for line in lyrics[section]:
                        if section[0] == 'i':
                            line = transpose(line, song['key'], transp)
                        display += '\n' + line
                        if line == '':
                            display += '\n'
                display += '\n\n'
    return display.strip()

def get_display_chords(song_id, transp=0):
    song = get_song(song_id)
    display = ''

    chords = song['chords']
    content = song['content']

    for section in content:
        if not section or section[0] == 'i' or section[0] == 's':# or any(ch.isdigit() for ch in section):
            continue
        elif section in chords and section.rstrip('0123456789') in chords: 
            if not (chords[section] == chords[section.rstrip('0123456789')] and section != section.rstrip('0123456789')):
                display += '['+ section +']'
                for line in chords[section]:
                    line = transpose(line, song['key'], transp)
                    display += '\n' + line
                display += '\n\n'
    return display.strip()

def get_display_2(song_id):
    """Return [lyrics_text, chords_text] following the original web logic (plain text)."""
    song = get_song(song_id)
    lyrics_output = []
    chords_output = []

    lyrics_parsed = song.get('lyrics', {})
    chords_parsed = song.get('chords', {})
    content = song.get('content', [])

    first_section = True

    for section in content:
        if not first_section:
            lyrics_output.append('')
            chords_output.append('')
        first_section = False

        chord_counter = 0
        section_type = section[0] if section else ''

        if section_type == 'i':
            for line in lyrics_parsed.get(section, []):
                lyrics_output.append(line)
                chords_output.append('')

        elif section_type == 'v':
            section_chords = chords_parsed.get(section, [])
            for lyrics_line in lyrics_parsed.get(section, []):
                cleaned_line = lyrics_line.replace('|', '').replace('!', '')
                lyrics_output.append(cleaned_line)

                if not section_chords:
                    chords_output.append('')
                    continue

                if not lyrics_line or lyrics_line[0] == '!':
                    chords_output.append('')
                    continue

                if chord_counter > len(section_chords) - 1:
                    chord_counter = 0

                chords_output.append(section_chords[chord_counter])
                chord_counter += 1

        elif section_type == 'c':
            section_chords = chords_parsed.get(section, [])
            for lyrics_line in lyrics_parsed.get(section, []):
                cleaned_line = lyrics_line.replace('|', '').replace('!', '')
                lyrics_output.append('\t' + cleaned_line)

                if not section_chords:
                    chords_output.append('')
                    continue

                if not lyrics_line or lyrics_line[0] == '!':
                    chords_output.append('')
                    continue

                if chord_counter > len(section_chords) - 1:
                    chord_counter = 0

                chord_line = section_chords[chord_counter]
                chord_line = transpose(chord_line, song.get('key', ''), 3)
                chords_output.append(chord_line)
                chord_counter += 1

        else:
            # Preserve unknown sections as blank spacers
            for lyrics_line in lyrics_parsed.get(section, []):
                lyrics_output.append(lyrics_line)
                chords_output.append('')

    return ['\n'.join(lyrics_output).strip(), '\n'.join(chords_output).rstrip()]


def get_display(song_id, transp = 0):
    song = get_song(song_id)
    display = ''
    
    lyrics = song['lyrics']
    chords = song['chords']
    content = song['content']
    key = song['key']

    for section in content:
        chord_counter = -1
        match section[0]:
            case 'i':
                for line in lyrics[section]:                                #assign next chord line from current section
                    line = transpose(line, key, transp)                     #transpose chord line
                    #line = re.sub(r'([^\s]+)', r'<code>\1</code>', line)    #wrap each chord in <code> tags
                    display += '\n'+ f"<b>{line}</b>"                          #add line to display

            case 's':
                song_name = song.get('title', 'song')
                section_match = re.search(r'\d+', section)
                section_number = section_match.group(0) if section_match else '0'
                song_name = song_name.lower().replace(' ', '_')
                image_filename = f'static/tab/{song_name}_{section_number}.svg'
                display += f'\n<img src="{image_filename}" alt="missing tab">'

            case 'v' | 'c':
                for i in range(len(lyrics[section])):
                    lyrics_line = lyrics[section][i]

                    if lyrics_line == ''  or lyrics_line[0] == '!': #skip empty lines
                        display += '\n'

                    elif lyrics_line[0] == '(': #skip 2nd voice
                        lyrics_line = lyrics_line.replace('|', '')
                        display += '\n'  + f"<i>{lyrics_line}</i>"
                    
                    else:
                        if not section in chords:   #if section not in chords use base section
                            section = section.rstrip('0123456789')
                        if section in chords and len(chords[section]) > 0:
                            if chord_counter < len(chords[section]) - 1: #if all chords have been used, start over
                                chord_counter += 1

                            chord_line = chords[section][chord_counter]
                            chord_line = transpose(chord_line, song['key'], transp)
                            chord_line = chords_to_scheme(chord_line, lyrics_line)
                            chord_line = re.sub(r'([^\s]+)', r'<code>\1</code>', chord_line)
                            if section[0] == 'c':
                                display += '\n' + f"<b>\t{chord_line}</b>"
                            else:
                                display += '\n' + f"<b>{chord_line}</b>"
                        
                        if section[0] == 'c':
                            display += '\n' + '\t' + lyrics_line.replace('|', '')
                        else:
                            display += '\n' + lyrics_line.replace('|', '')
        display += "\n"
    return display.strip()

def chords_to_scheme(chord_line, lyrics_line):
    scheme_line = ''.join(' ' if char != '|' else '|' for char in lyrics_line)
    if '|' not in scheme_line:
        return chord_line
    
    chords_split = chord_line.split(' ')
    chord_line = ''

    too_right = 0
    chord_counter = 0

    for c in scheme_line:
        if c == ' ':
            if too_right > 0:
                too_right -= 1
            else:
                chord_line += ' '
        elif c == '|':
            chord = chords_split[chord_counter % len(chords_split)]
            chord_line += chord + ' '
            too_right += len(chord) + 1
            chord_counter += 1
    
    while chord_counter < len(chords_split):
        chord_line += chords_split[chord_counter] + ' '
        chord_counter += 1
        
    return chord_line