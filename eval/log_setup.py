"""
Logging setup for the validation pipeline.
Configures the valdb.* logger hierarchy with console and file handlers.
"""

import logging
import sys
from pathlib import Path

LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    run_id: str,
    log_dir: Path = Path("output/logs"),
    verbose: bool = False,
    quiet: bool = False,
) -> logging.Logger:
    """Configure the valdb.* logger hierarchy for this run.

    Args:
        run_id: Unique run identifier (e.g. timestamp).
        log_dir: Directory for log files.
        verbose: If True, console handler uses DEBUG level.
        quiet: If True, console handler uses WARNING level.

    Returns:
        The root valdb logger.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    run_log = log_dir / f"validate_{run_id}.log"

    root = logging.getLogger("valdb")
    root.setLevel(logging.DEBUG)
    root.handlers.clear()

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    fh = logging.FileHandler(str(run_log), encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    root.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    if verbose:
        ch.setLevel(logging.DEBUG)
    elif quiet:
        ch.setLevel(logging.WARNING)
    else:
        ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(ch)

    return root
