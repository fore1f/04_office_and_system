import os
import time
import logging
from faster_whisper import WhisperModel

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def transcribe_audio(file_path: str, model_size: str = "base"):
    """
    Faster-Whisperを使用して音声ファイルを文字起こしする。
    """
    if not os.path.exists(file_path):
        logger.error(f"ファイルが見つかりません: {file_path}")
        return

    logger.info(f"モデル '{model_size}' を読み込み中...")
    # CPUで動作させる設定 (GPUがある場合は 'cuda' に変更可能)
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    logger.info(f"文字起こしを開始します: {file_path}")
    start_time = time.time()

    # 文字起こし実行 (beam_size=5 は標準的な設定)
    segments, info = model.transcribe(file_path, beam_size=5, language="ja")

    logger.info(f"検知された言語: {info.language} (確信度: {info.language_probability:.2f})")

    results = []
    for segment in segments:
        text = f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}"
        print(text)
        results.append(text)

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(f"完了！ 処理時間: {elapsed_time:.2f}秒")

    # 結果をMarkdownファイルに保存
    output_meta = f"c:\\Users\\tked1\\py\\04_office_and_system\\transcription_demo\\transcript_metadata.md"
    with open(output_meta, "w", encoding="utf-8") as f:
        f.write("# 文字起こし結果\n\n")
        f.write(f"- **ファイル**: {os.path.basename(file_path)}\n")
        f.write(f"- **言語**: {info.language}\n")
        f.write(f"- **処理時間**: {elapsed_time:.2f}s\n\n")
        f.write("## 内容\n\n")
        for line in results:
            f.write(f"{line}  \n")

    logger.info(f"結果を保存しました: {output_meta}")

if __name__ == "__main__":
    target_file = r"C:\Users\tked1\マイドライブ（fore1f.gem@gmail.com）\新規録音 14.m4a"
    transcribe_audio(target_file)
