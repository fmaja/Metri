import re

def transpose(line, key, n):
    if key == '':
        key = 'C'

    interval = {
        'C':0, 'C#':1, 'Db':1, 'D':2, 'D#':3, 'Eb':3,
        'E':4, 'Fb':4, 'E#':5, 'F':5, 'F#':6, 'Gb':6,
        'G':7, 'G#':8 ,'Ab':8, 'A':9, 'A#':10, 'Bb':10,
        'B':11, 'Cb':11, 'B#':0
    }

    int_key = interval.get(key.rstrip("m"))  # strip "m" for minor root
    if int_key is None:
        raise ValueError(f"Unknown key: {key}")

    key_table = get_key_table(key)

    def t_match(match):
        chord = match.group(1)
        suffix = match.group(2)

        if chord in interval:
            int_chord = interval[chord]
            new_int = (int_chord - int_key + n) % 12
            new_chord = key_table[new_int]
            return new_chord + suffix
        return match.group(0)

    pattern = r"\b([A-G](?:#|b)?)([^ \n]*)"
    return re.sub(pattern, t_match, line)


def get_key_table(key):
    """Return a 12-note chromatic scale spelled according to the key signature."""
    major_sharp_keys = ["C", "G", "D", "A", "E", "B", "F#", "C#"]
    major_flat_keys  = ["F", "Bb", "Eb", "Ab", "Db", "Gb", "Cb"]

    minor_sharp_keys = ["Am", "Em", "Bm", "F#m", "C#m", "G#m", "D#m", "A#m"]
    minor_flat_keys  = ["Dm", "Gm", "Cm", "Fm", "Bbm", "Ebm", "Abm"]

    sharp_scale = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
    flat_scale  = ['C','Db','D','Eb','E','F','Gb','G','Ab','A','Bb','B']

    if key in major_sharp_keys or key in minor_sharp_keys:
        return sharp_scale
    if key in major_flat_keys or key in minor_flat_keys:
        return flat_scale

    return sharp_scale  # default to sharps