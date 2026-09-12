import os

from scripts.setup_local_model import ensure_model


def main() -> None:
    try:
        model = ensure_model()
        os.environ["FINDUPTO_MODEL_PATH"] = str(model)
    except Exception as exc:
        print(f"Model setup failed: {exc}")
        print("You can retry by running: python -m scripts.setup_local_model")
        return

    from apps.desktop import main as desktop_main
    desktop_main()


if __name__ == "__main__":
    main()
