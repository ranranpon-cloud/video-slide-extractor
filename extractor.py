import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
from PIL import Image
from tqdm import tqdm
import os


def compute_sharpness(frame):
    """Laplacian分散でフレームの鮮明度を計算する"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def preprocess_for_comparison(frame):
    """比較用にフレームを前処理（グレースケール + ブラー）"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (21, 21), 0)
    return blurred


def extract_slides(video_path, threshold=0.85, interval=0.5, min_slide_duration=2.0):
    """
    動画からスライドの切り替わりを検出し、各スライドのベストフレームを返す。

    Args:
        video_path: 動画ファイルのパス
        threshold: SSIM閾値（これ以下で切り替わり判定）
        interval: フレームサンプリング間隔（秒）
        min_slide_duration: スライドの最低表示時間（秒）

    Returns:
        slides: 各スライドのベストフレーム画像のリスト
        ssim_values: デバッグ用のSSIM値リスト
        timestamps: デバッグ用のタイムスタンプリスト
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"動画ファイルを開けません: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    frame_interval = int(fps * interval)

    print(f"動画情報: {duration:.1f}秒, {fps:.1f}fps, {total_frames}フレーム")
    print(f"サンプリング間隔: {interval}秒 ({frame_interval}フレームごと)")

    # フレームをサンプリング
    sampled_frames = []
    sampled_indices = []
    frame_idx = 0

    total_samples = total_frames // frame_interval
    pbar = tqdm(total=total_samples, desc="フレーム読み込み中")

    while True:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            break
        sampled_frames.append(frame)
        sampled_indices.append(frame_idx)
        frame_idx += frame_interval
        pbar.update(1)

    pbar.close()
    cap.release()

    if len(sampled_frames) < 2:
        raise ValueError("フレームが不足しています。動画が短すぎるか、間隔が大きすぎます。")

    # SSIM を計算してスライド切り替わりを検出
    ssim_values = []
    timestamps = []
    transition_points = []

    print("スライド切り替わりを検出中...")
    prev_processed = preprocess_for_comparison(sampled_frames[0])

    for i in tqdm(range(1, len(sampled_frames)), desc="SSIM計算中"):
        curr_processed = preprocess_for_comparison(sampled_frames[i])
        score = ssim(prev_processed, curr_processed)
        ssim_values.append(score)
        timestamps.append(sampled_indices[i] / fps)

        if score < threshold:
            transition_points.append(i)

        prev_processed = curr_processed

    # デバウンス: min_slide_duration 以内の連続した切り替わりをまとめる
    min_frames_between = int(min_slide_duration / interval)
    filtered_transitions = []
    for tp in transition_points:
        if not filtered_transitions or (tp - filtered_transitions[-1]) >= min_frames_between:
            filtered_transitions.append(tp)

    print(f"検出されたスライド切り替わり: {len(filtered_transitions)}箇所")

    # 各スライド区間でベストフレームを選択
    segments = []
    start = 0
    for tp in filtered_transitions:
        segments.append((start, tp))
        start = tp
    segments.append((start, len(sampled_frames)))

    slides = []
    for seg_start, seg_end in segments:
        if seg_start >= seg_end:
            continue
        best_frame = None
        best_sharpness = -1
        for j in range(seg_start, seg_end):
            sharpness = compute_sharpness(sampled_frames[j])
            if sharpness > best_sharpness:
                best_sharpness = sharpness
                best_frame = sampled_frames[j]
        if best_frame is not None:
            slides.append(best_frame)

    print(f"抽出されたスライド数: {len(slides)}")
    return slides, ssim_values, timestamps


def save_as_pdf(images, output_path):
    """OpenCVのBGR画像リストをPDFとして保存する"""
    if not images:
        raise ValueError("保存する画像がありません")

    pil_images = []
    for img in images:
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_images.append(Image.fromarray(rgb))

    pil_images[0].save(
        output_path,
        save_all=True,
        append_images=pil_images[1:],
        resolution=150,
    )
    print(f"PDF保存完了: {output_path} ({len(images)}ページ)")


def save_images(images, output_dir):
    """OpenCVのBGR画像リストを個別PNGとして保存する"""
    os.makedirs(output_dir, exist_ok=True)
    for i, img in enumerate(images):
        path = os.path.join(output_dir, f"slide_{i + 1:03d}.png")
        cv2.imwrite(path, img)
    print(f"画像保存完了: {output_dir}/ ({len(images)}枚)")
