import os
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "frontend", "public", "videos", "production")
OUTPUT_FILE = os.path.join(BASE_DIR, "frontend", "public", "videos", "tema4_intersecciones_final.mp4")

ASSETS = {
    "closed": os.path.join(ASSETS_DIR, "mouth_closed.png"),
    "mid": os.path.join(ASSETS_DIR, "mouth_mid.png"),
    "open": os.path.join(ASSETS_DIR, "mouth_open.png"),
    "blink": os.path.join(ASSETS_DIR, "blink.png"),
}


def run_ffmpeg(args: list[str]) -> bool:
    try:
        subprocess.run(args, check=True)
        return True
    except subprocess.CalledProcessError as exc:
        print(f"Error ejecutando ffmpeg: {exc}")
        return False


def build_filter_complex() -> str:
    return ";".join(
        [
            "[0:v]format=rgba[closed]",
            "[1:v]format=rgba[mid]",
            "[2:v]format=rgba[open]",
            "[3:v]format=rgba[blink]",
            (
                "[closed][mid]blend="
                "all_expr='A*(1-0.30*pow(sin(T*7.8),2))+B*(0.30*pow(sin(T*7.8),2))'"
                "[mouth_mid]"
            ),
            (
                "[mouth_mid][open]blend="
                "all_expr='A*(1-0.22*pow(max(sin(T*7.8-0.48),0),2))+B*(0.22*pow(max(sin(T*7.8-0.48),0),2))'"
                "[mouth_open]"
            ),
            (
                "[mouth_open][blink]blend="
                "all_expr='if(lte(mod(T,4.7),0.08),B,"
                "if(lte(mod(T,4.7),0.15),"
                "(A*(mod(T,4.7)-0.08)/0.07)+(B*(1-(mod(T,4.7)-0.08)/0.07)),A))'"
                "[talking]"
            ),
            (
                "[talking]scale=1100:1100,"
                "rotate='0.0012*sin(t*1.12)+0.0006*sin(t*0.43)':fillcolor=white,"
                "crop=960:540:"
                "x='70+16*sin(t*0.21)+8*sin(t*0.53)':"
                "y='150+10*cos(t*0.24)+5*sin(t*0.47)',"
                "fps=24[final]"
            ),
        ]
    )


def build_command() -> list[str]:
    args = ["ffmpeg", "-y", "-loglevel", "error"]
    for asset_name in ["closed", "mid", "open", "blink"]:
        args.extend(["-loop", "1", "-t", "30", "-i", ASSETS[asset_name]])

    args.extend(
        [
            "-filter_complex",
            build_filter_complex(),
            "-map",
            "[final]",
            "-t",
            "30",
            "-r",
            "24",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "ultrafast",
            "-crf",
            "20",
            OUTPUT_FILE,
        ]
    )
    return args


def generate_video() -> None:
    print("Generando video continuo y fluido del instructor...")
    if run_ffmpeg(build_command()):
        print(f"Video generado correctamente en: {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_video()
