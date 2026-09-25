import os
import sys
import base64
import tempfile
import subprocess
from pathlib import Path
import runpod

SEEDVC_DIR = Path("/app/seed-vc")

def decode_file(b64_str: str, out_path: Path):
    out_path.write_bytes(base64.b64decode(b64_str))

def convert_to_wav(in_path: Path, out_path: Path):
    subprocess.run([
        "ffmpeg", "-y", "-i", str(in_path),
        "-ac", "1", "-ar", "44100",
        "-c:a", "pcm_s16le", str(out_path)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def handler(job):
    job_input = job.get("input", {})
    source_b64 = job_input.get("source_b64")
    reference_b64 = job_input.get("reference_b64")

    # Your proven 5-step fast default
    steps = int(job_input.get("steps", 5))
    cfg = float(job_input.get("cfg", 0.7))
    length_adjust = float(job_input.get("length_adjust", 1.0))
    f0 = str(job_input.get("f0_condition", False)).capitalize()
    auto_f0 = str(job_input.get("auto_f0_adjust", False)).capitalize()
    semitone = int(job_input.get("semitone_shift", 0))

    if not source_b64 or not reference_b64:
        return {"error": "Missing source_b64 or reference_b64 audio"}

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        src_raw = tmp / "src.raw"
        ref_raw = tmp / "ref.raw"
        src_wav = tmp / "source.wav"
        ref_wav = tmp / "reference.wav"
        out_dir = tmp / "output"
        out_dir.mkdir(parents=True, exist_ok=True)

        decode_file(source_b64, src_raw)
        decode_file(reference_b64, ref_raw)
        convert_to_wav(src_raw, src_wav)
        convert_to_wav(ref_raw, ref_wav)

        cmd = [
            sys.executable, "inference.py",
            "--source", str(src_wav),
            "--target", str(ref_wav),
            "--output", str(out_dir),
            "--diffusion-steps", str(steps),
            "--length-adjust", str(length_adjust),
            "--inference-cfg-rate", str(cfg),
            "--f0-condition", f0,
            "--auto-f0-adjust", auto_f0,
            "--semi-tone-shift", str(semitone),
            "--fp16", "True"
        ]

        result = subprocess.run(
            cmd,
            cwd=SEEDVC_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        if result.returncode != 0:
            return {"error": f"Seed-VC failed:\n{result.stdout[-2000:]}"}

        out_files = list(out_dir.glob("*.wav"))
        if not out_files:
            return {"error": "Inference succeeded but no output WAV was generated."}

        out_b64 = base64.b64encode(out_files[0].read_bytes()).decode("ascii")
        return {"audio_b64": out_b64, "filename": "converted.wav"}

runpod.serverless.start({"handler": handler})
