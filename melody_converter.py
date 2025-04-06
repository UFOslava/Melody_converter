import sounddevice as sd
import numpy as np
import mido


def play_tone(frequency, duration: float, duty_cycle=0.05, volume=0.2, sample_rate=44100):
    """Generates and plays a tone to the PC speakers

    TODO fix tone inconsistency"""
    num_samples = int(duration * sample_rate)
    period_samples = int(sample_rate / frequency)
    high_samples = int(period_samples * duty_cycle)

    tone = np.zeros(num_samples)  # Create an array of zeros with the correct length
    for i in range(num_samples):
        sample_index = i % period_samples
        if sample_index < high_samples:
            tone[i] = volume
        else:
            tone[i] = -volume

    sd.play(tone, samplerate=sample_rate)
    sd.wait()


def midi_note_to_frequency(midi_note: int) -> float:
    frequency: float = 2 ** ((midi_note - 69) / 12) * 440
    return frequency


def play_note(midi_note: int, duration: float):
    frequency = midi_note_to_frequency(midi_note)
    play_tone(frequency, duration)


def note_name_to_midi(note_name: str) -> int:
    """
    Converts a note name (e.g., "C4") to a MIDI note number.
    """
    notes = {'C': 0,
             'C#': 1,
             'Db': 1,
             'D': 2,
             'D#': 3,
             'Eb': 3,
             'E': 4,
             'F': 5,
             'F#': 6,
             'Gb': 6,
             'G': 7,
             'G#': 8,
             'Ab': 8,
             'A': 9,
             'A#': 10,
             'Bb': 10,
             'B': 11}
    note = note_name[:-1]
    octave = int(note_name[-1])
    midi_note = 12 * (octave + 1) + notes[note]
    return midi_note


def play_melody_from_file(filename: str):
    """
    Plays a melody from a text file.
    """
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split(':')
            note_or_pause = parts[0]
            duration = float(parts[1])

            if note_or_pause.startswith('P'):
                sd.sleep(int(duration * 1000))  # Pause in milliseconds
            else:
                midi_note = note_name_to_midi(note_or_pause)
                play_note(midi_note, duration)


def preview_midi_tracks(midi_file: str):
    """
    Previews the tracks in a MIDI file, including their names and events.
    """
    mid = mido.MidiFile(midi_file)

    for i, track in enumerate(mid.tracks):
        track_name = f'Track {i + 1}'
        if len(track) < 10:
            continue
        for msg in track:
            if msg.type == 'track_name':
                track_name = msg.name
                break  # Track name found, no need to look further

        print(f'{track_name}:')
        for msg in track[:10]:  # Preview the first 5 events
            print(f'  {msg}')
        if len(track) > 10:
            print("  ...")
        print()


# Example usage: Preview the tracks in "twinkle.mid"
preview_midi_tracks('Melodies/BeverlyHillsCopThemeSong.mid')

# play_melody_from_file("Melodies/Twinkle.txt")
