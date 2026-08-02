from pathlib import Path
from datetime import datetime

MAX_LOG_LEN = 200

class Logger:
    """
    Basic logging class with some basic capabilities to replace prints and keep terminal and logging clean.
    """

    def __init__(
        self,
        name: str,
        save_dir: str | None = None,
        save: bool = False,
        verbose: bool = False,
    ):
        self.name = name
        self.save = save
        self.verbose = verbose

        if save_dir:
            save_dir = Path(save_dir)
            save_dir.mkdir(parents=True, exist_ok=True)
            self.log_path = save_dir / f"{name}.log"
        else:
            self.log_path = None

    def _log(
        self,
        level: str,
        message: str,
        *,
        verbose: bool | None = None,
        save: bool | None = None,
    ):
        # If not set, use the default values from the logger instance
        verbose = self.verbose if verbose is None else verbose
        save = self.save if save is None else save

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(message, bytes):
            line = f"[{timestamp}] [{level}] binary len={len(message)} bytes"
        else:
            preview = repr(message)
            if len(preview) > MAX_LOG_LEN:
                preview = preview[:MAX_LOG_LEN] + "... (truncated)"
            line = f"[{timestamp}] [{level}] {preview}"

        if verbose:
            print(line)

        if self.log_path and save:
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")

    def debug(self, message: str, *, verbose: bool | None = None, save: bool | None = None):
        self._log("DEBUG", message, verbose=verbose, save=save)

    def info(self, message: str, *, verbose: bool | None = None, save: bool | None = None):
        self._log("INFO", message, verbose=verbose, save=save)

    def warning(self, message: str, *, verbose: bool | None = None, save: bool | None = None):
        self._log("WARNING", message, verbose=verbose, save=save)

    def error(self, message: str, *, verbose: bool | None = None, save: bool | None = None):
        self._log("ERROR", message, verbose=verbose, save=save)