import os
import time
import subprocess
import json
import re
from pathlib import Path

UPLOADS = "/app/uploads"
OUTPUT = "/app/output"
MODEL = os.environ.get("DEMUCS_MODEL", "htdemucs_6s")
SLEEP = 2

STATUS_DIR = Path(OUTPUT) / "status"
MAX_LOG_LINES = 200

def ensure_status_dir():
    STATUS_DIR.mkdir(parents=True, exist_ok=True)

def atomic_write(path: Path, data: str):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(data, encoding="utf-8")
    tmp.replace(path)

def write_status(filename, obj):
    try:
        fp = STATUS_DIR / f"{filename}.json"
        atomic_write(fp, json.dumps(obj, indent=2, ensure_ascii=False))
    except Exception as e:
        print("[demucs] failed to write status:", e)

def already_processed(filename):
    stem = Path(filename).stem
    out_dir = Path(OUTPUT) / MODEL / stem
    return out_dir.exists()

def infer_progress_from_line(line):
    # try explicit percent first
    m = re.search(r'(\d{1,3})\s*%', line)
    if m:
        val = int(m.group(1))
        return max(0, min(100, val))
    # heuristics for demucs phases
    low = line.lower()
    if any(k in low for k in ("loading", "model", "weights")):
        return 5
    if any(k in low for k in ("conditioning", "preparing", "segment")):
        return 25
    if any(k in low for k in ("separate", "separating", "mix")):
        return 50
    if any(k in low for k in ("writing", "saved", "export")):
        return 85
    if "done" in low or "finished" in low:
        return 100
    return None

def process_file(filepath):
    filename = Path(filepath).name
    log_lines = []
    progress = 0
    started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    write_status(filename, {"status": "processing", "filename": filename, "startedAt": started_at, "progress": progress, "logs": []})

    cmd = ["python", "-m", "demucs.separate", "-n", MODEL, "-o", OUTPUT, filepath]
    print(f"[demucs] running: {' '.join(cmd)}")

    try:
        # stream stdout/stderr combined, handle '\r' progress updates and strip ANSI
        ansi_re = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
        def process_line(raw_line):
            nonlocal progress, log_lines
            # clean and normalize
            line = ansi_re.sub('', raw_line).rstrip()
            if not line:
                return
            print("[demucs]", line)
            log_lines.append(line)
            if len(log_lines) > MAX_LOG_LINES:
                log_lines = log_lines[-MAX_LOG_LINES:]
            p = infer_progress_from_line(line)
            if p is not None:
                progress = max(progress, p)
            write_status(filename, {
                "status": "processing",
                "filename": filename,
                "startedAt": started_at,
                "progress": progress,
                "lastLine": line,
                "logs": log_lines[-50:]
            })

        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1) as proc:
            buf = ""
            while True:
                ch = proc.stdout.read(1)
                if ch == "" or ch is None:
                    # EOF
                    if buf:
                        process_line(buf)
                        buf = ""
                    break
                if ch in ("\r", "\n"):
                    if buf:
                        process_line(buf)
                        buf = ""
                    else:
                        # some progress bars update with '\r' only; still attempt to flush
                        continue
                else:
                    buf += ch
            ret = proc.wait()
        if ret != 0:
            raise subprocess.CalledProcessError(ret, cmd)

        # collect outputs
        stem = Path(filename).stem
        out_dir = Path(OUTPUT) / MODEL / stem
        outputs = []
        if out_dir.exists():
            for p in sorted(out_dir.iterdir()):
                if p.is_file():
                    outputs.append(str(p.relative_to(OUTPUT)))

        finished_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        write_status(filename, {
            "status": "done",
            "filename": filename,
            "startedAt": started_at,
            "finishedAt": finished_at,
            "progress": 100,
            "outputs": outputs,
            "logs": log_lines[-200:]
        })
        # remove source file
        try:
            os.remove(filepath)
            print(f"[demucs] removed input file: {filepath}")
        except Exception as e:
            print(f"[demucs] warning: failed to remove {filepath}: {e}")

    except subprocess.CalledProcessError as e:
        stderr_msg = getattr(e, "stderr", None)
        finished_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        log_lines.append(f"Process exited with {e.returncode}")
        write_status(filename, {
            "status": "error",
            "filename": filename,
            "error": str(e),
            "stderr": stderr_msg,
            "finishedAt": finished_at,
            "progress": progress,
            "logs": log_lines[-200:]
        })
        print(f"[demucs] error processing {filepath}: returncode={e.returncode}")

def main():
    os.makedirs(UPLOADS, exist_ok=True)
    os.makedirs(OUTPUT, exist_ok=True)
    ensure_status_dir()

    print("[demucs] watcher started, watching:", UPLOADS)
    while True:
        try:
            for entry in os.listdir(UPLOADS):
                pathp = os.path.join(UPLOADS, entry)
                if os.path.isdir(pathp):
                    continue
                if entry.endswith(".tmp") or entry.endswith(".partial"):
                    continue
                if not already_processed(entry):
                    qpath = STATUS_DIR / f"{entry}.json"
                    if not qpath.exists():
                        write_status(entry, {"status": "queued", "filename": entry, "queuedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "progress": 0, "logs": []})
                    process_file(pathp)
            time.sleep(SLEEP)
        except Exception as exc:
            print("[demucs] watcher error:", exc)
            time.sleep(SLEEP)

if __name__ == "__main__":
    main()