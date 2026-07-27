"""sarf_client.py — Python wrapper for the Sarf Arabic morphology JAR.

Calls the Java-based Sarf CLI via subprocess, building the classpath
from the compiled classes directory and dependency JARs.

Requires:
  - Java 17+ (JRE) available on the system PATH
  - The compiled sarf-library output at sarf-source/sarf-library/target/

Usage:
    from sarf_client import SarfClient
    client = SarfClient()
    if client.is_available():
        result = client.analyze("كتب", bab=1)
        print(result["pastTense"])
"""

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

# Paths relative to this file
_HERE = Path(__file__).parent
_PROJECT_ROOT = _HERE.parent
_SARF_SOURCE = _PROJECT_ROOT / "sarf-source"
_SARF_CLASSES = _SARF_SOURCE / "sarf-library" / "target" / "classes"
_SARF_LIBS = _SARF_SOURCE / "sarf-library" / "target" / "libs"
_SARF_JAR = _HERE / "sarf-cli.jar"


class SarfClient:
    """Wrapper around the Sarf CLI Java process."""

    def __init__(self):
        self._classpath: Optional[str] = None
        self._java_cmd = self._find_java()

    # ── Helpers ────────────────────────────────────────────────────

    @staticmethod
    def _find_java() -> Optional[str]:
        """Find Java executable on the system."""
        # Check project-local JDK first
        local_jdk = _PROJECT_ROOT / "tools" / "jdk17_extracted"
        if local_jdk.exists():
            for jdk_dir in local_jdk.iterdir():
                java_exe = jdk_dir / "bin" / "java.exe"
                if java_exe.exists():
                    return str(java_exe)
        # Fall back to system PATH
        java = shutil_which("java")
        if java:
            return java
        # Check common Windows paths
        for path in [
            r"C:\Program Files\Java\jdk-17\bin\java.exe",
            r"C:\Program Files\Java\jdk-11\bin\java.exe",
            r"C:\Program Files\Eclipse Adoptium\jdk-17\bin\java.exe",
        ]:
            if os.path.isfile(path):
                return path
        return None

    def _build_classpath(self) -> Optional[str]:
        """Build the Java classpath from compiled classes and libs."""
        if self._classpath:
            return self._classpath

        if not _SARF_CLASSES.exists():
            logging.warning("Sarf classes not found at %s", _SARF_CLASSES)
            return None

        entries = [str(_SARF_CLASSES)]        # Add dependency JARs from target/libs
        if _SARF_LIBS.exists():
            for jar in sorted(_SARF_LIBS.glob("*.jar")):
                entries.append(str(jar))

        # Fallback: use the fat JAR (rebuilt with FileUtil fix)
        if _SARF_JAR.exists():
            entries.append(str(_SARF_JAR))

        self._classpath = ";".join(entries)
        return self._classpath

    # ── Public API ─────────────────────────────────────────────────

    def _ensure_java_args(self) -> list[str]:
        """Return the base Java command with flags, or raise if unavailable."""
        if not self._java_cmd:
            raise RuntimeError("Java not found. Install Java 17+.")
        cp = self._build_classpath()
        if not cp:
            raise RuntimeError(
                "Sarf classes not found. Run: cd sarf-source && mvn compile -pl sarf-library"
            )
        return [
            self._java_cmd,
            "-Dfile.encoding=UTF-8",   # ensure Java reads/writes UTF-8
            "-cp", cp,
            "sarf.SarfCLI", "--stdin",
        ]

    def is_available(self) -> bool:
        """Check if Java and the Sarf classes are available."""
        try:
            args = self._ensure_java_args()
            test_input = '{"root":"\u0643\u062a\u0628","bab":1}'.encode("utf-8")
            result = subprocess.run(args, input=test_input, capture_output=True, timeout=15)
            return result.returncode == 0
        except Exception:
            return False

    def analyze(self, root: str, bab: int = 1) -> dict[str, Any]:
        """Analyze a triliteral Arabic root.

        Args:
            root: 3 Arabic letters (e.g., "كتب").
            bab: Conjugation class 1-6 (default: 1).

        Returns:
            Dictionary with pastTense, presentTense, etc.

        Raises:
            RuntimeError: If Java/Sarf is not available or analysis fails.
        """
        args = self._ensure_java_args()

        stdin_input = json.dumps({"root": root, "bab": bab}, ensure_ascii=False).encode("utf-8")

        try:
            result = subprocess.run(
                args,
                input=stdin_input,
                capture_output=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Sarf analysis timed out (30s).")

        if result.returncode != 0:
            err_text = result.stderr.decode("utf-8", errors="replace").strip() if result.stderr else ""
            out_text = result.stdout.decode("utf-8", errors="replace").strip() if result.stdout else ""
            error_msg = err_text or out_text or f"Exit code {result.returncode}"
            raise RuntimeError(f"Sarf analysis failed: {error_msg}")

        if not result.stdout:
            raise RuntimeError("Sarf returned empty output.")

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Sarf returned invalid JSON: {e}\nOutput: {result.stdout[:500]}")


def shutil_which(cmd: str) -> Optional[str]:
    """Minimal 'which' replacement (avoids shutil import issues)."""
    try:
        import shutil
        return shutil.which(cmd)
    except Exception:
        return None
