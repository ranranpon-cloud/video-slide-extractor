import argparse
import sys
from extractor import extract_slides, save_as_pdf, save_images


def main():
    parser = argparse.ArgumentParser(
        description="動画からスライドの切り替わりを検出し、PDFとして出力します"
    )
    parser.add_argument("input", help="入力動画ファイルのパス")
    parser.add_argument(
        "-o", "--output", default="output.pdf", help="出力PDFファイルのパス (デフォルト: output.pdf)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="SSIM閾値。低いほど変化に鈍感 (デフォルト: 0.85)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="フレームサンプリング間隔（秒） (デフォルト: 0.5)",
    )
    parser.add_argument(
        "--min-duration",
        type=float,
        default=2.0,
        help="スライドの最低表示時間（秒） (デフォルト: 2.0)",
    )
    parser.add_argument(
        "--save-images", action="store_true", help="個別のPNG画像も保存する"
    )
    parser.add_argument(
        "--rotate",
        type=int,
        default=0,
        choices=[0, 90, 180, 270],
        help="出力画像の回転角度 (デフォルト: 0)",
    )
    parser.add_argument(
        "--debug", action="store_true", help="デバッグモード（SSIMグラフを表示）"
    )

    args = parser.parse_args()

    try:
        slides, ssim_values, timestamps = extract_slides(
            args.input,
            threshold=args.threshold,
            interval=args.interval,
            min_slide_duration=args.min_duration,
        )

        if not slides:
            print("スライドが検出されませんでした。閾値を調整してみてください。")
            sys.exit(1)

        save_as_pdf(slides, args.output, rotate=args.rotate)

        if args.save_images:
            output_dir = args.output.rsplit(".", 1)[0] + "_images"
            save_images(slides, output_dir, rotate=args.rotate)

        if args.debug:
            try:
                import matplotlib.pyplot as plt

                plt.figure(figsize=(12, 4))
                plt.plot(timestamps, ssim_values, linewidth=0.8)
                plt.axhline(y=args.threshold, color="r", linestyle="--", label=f"閾値={args.threshold}")
                plt.xlabel("時間 (秒)")
                plt.ylabel("SSIM")
                plt.title("フレーム間SSIM変化")
                plt.legend()
                plt.tight_layout()
                debug_path = args.output.rsplit(".", 1)[0] + "_debug.png"
                plt.savefig(debug_path, dpi=150)
                print(f"デバッググラフ保存: {debug_path}")
                plt.show()
            except ImportError:
                print("デバッグモードには matplotlib が必要です: pip install matplotlib")

    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
