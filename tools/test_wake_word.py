import queue
import time
from pathlib import Path

import numpy as np
import sounddevice as sd

from core.wake_dtw import WakeWordDTW


SAMPLE_RATE = 16000

WINDOW_SECONDS = 1.4
STEP_SECONDS = 0.35

THRESHOLD = 35.0

SAMPLES_DIR = (
    Path(__file__).resolve().parent.parent
    / "wake_samples"
)


def main():
    print(
        "=== VoiceHelper DTW Wake Test ==="
    )

    detector = WakeWordDTW(
        SAMPLES_DIR,
        sample_rate=SAMPLE_RATE,
    )

    audio_queue = queue.Queue()

    def callback(
        indata,
        frames,
        time_info,
        status,
    ):
        if status:
            print(
                f"[Audio] {status}"
            )

        audio_queue.put(
            np.array(
                indata[:, 0],
                dtype=np.float32,
            ).copy()
        )

    window_size = int(
        WINDOW_SECONDS
        * SAMPLE_RATE
    )

    step_size = int(
        STEP_SECONDS
        * SAMPLE_RATE
    )

    buffer = np.zeros(
        0,
        dtype=np.float32,
    )

    print()
    print(
        "Говори «лёня» и обычные слова."
    )
    print(
        "Для выхода: Ctrl+C"
    )
    print()
    print(
        f"Порог: {THRESHOLD}"
    )
    print()

    last_detection = 0.0

    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=512,
            callback=callback,
            latency="high",
        ):

            while True:

                data = audio_queue.get()

                buffer = np.concatenate(
                    (
                        buffer,
                        data,
                    )
                )

                if len(buffer) < window_size:
                    continue

                window = buffer[
                    -window_size:
                ]

                score = detector.score(
                    window
                )

                detected = (
                    score <= THRESHOLD
                )

                now = time.monotonic()

                if detected:

                    # Защита от многократного
                    # срабатывания на одно слово.
                    if (
                        now
                        - last_detection
                        > 1.5
                    ):
                        print(
                            f"[WAKE] "
                            f"ОБНАРУЖЕНО "
                            f"score={score:.2f}"
                        )

                        last_detection = now

                else:

                    print(
                        f"[----] "
                        f"score={score:.2f}"
                    )

                buffer = buffer[
                    -(
                        window_size
                        - step_size
                    ):
                ]

    except KeyboardInterrupt:
        print()
        print(
            "Тест остановлен."
        )


if __name__ == "__main__":
    main()