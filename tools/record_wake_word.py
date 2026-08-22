import sys
import time
import wave
from pathlib import Path

import sounddevice as sd


SAMPLE_RATE = 16000
CHANNELS = 1
RECORD_SECONDS = 1.5

OUTPUT_DIR = (
    Path(__file__).resolve().parent.parent
    / "wake_samples"
)


def record_sample(
    path: Path,
) -> None:
    print()
    print(
        "Через 2 секунды произнеси: "
        "«лёня»"
    )

    time.sleep(2)

    print("🎤 ЗАПИСЬ")

    audio = sd.rec(
        int(
            RECORD_SECONDS
            * SAMPLE_RATE
        ),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
    )

    sd.wait()

    print("✓ Запись завершена")

    with wave.open(
        str(path),
        "wb",
    ) as wav_file:

        wav_file.setnchannels(
            CHANNELS
        )

        wav_file.setsampwidth(2)

        wav_file.setframerate(
            SAMPLE_RATE
        )

        wav_file.writeframes(
            audio.tobytes()
        )


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    existing = sorted(
        OUTPUT_DIR.glob(
            "lenya_*.wav"
        )
    )

    start_number = len(existing) + 1

    print("=== VoiceHelper Wake Word Recorder ===")
    print()
    print(
        "Будем записывать 8 образцов "
        "слова «лёня»."
    )
    print()
    print(
        "Говори естественно, не слишком "
        "медленно и не слишком быстро."
    )

    for index in range(
        start_number,
        start_number + 8,
    ):

        path = OUTPUT_DIR / (
            f"lenya_{index:02d}.wav"
        )

        input(
            f"\nНажми Enter для записи "
            f"{index}/{start_number + 7}..."
        )

        record_sample(path)

        print(
            f"Сохранено: {path}"
        )

    print()
    print(
        "✓ Все образцы сохранены."
    )
    print(
        f"Папка: {OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()