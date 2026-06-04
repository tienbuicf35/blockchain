from __future__ import annotations

import argparse
import json
import os

from app.ledger import append_prediction
from app.model import load_image, load_model_bundle, predict_image, screen_image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Skin disease screening app")
    parser.add_argument("--image", required=True, help="Path to input image")
    parser.add_argument("--mode", choices=["predict", "screen"], default="predict")
    parser.add_argument("--top-k", type=int, default=int(os.getenv("TOP_K", "3")))
    parser.add_argument("--model-dir", default=os.getenv("MODEL_DIR"))
    parser.add_argument("--itch", default="no")
    parser.add_argument("--bleed", default="no")
    parser.add_argument("--grow", default="no")
    parser.add_argument("--pain", default="no")
    parser.add_argument("--change", default="no")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bundle = load_model_bundle(args.model_dir)
    image = load_image(args.image)
    if args.mode == "screen":
        result = screen_image(
            image,
            symptoms={
                "itch": args.itch,
                "bleed": args.bleed,
                "grow": args.grow,
                "pain": args.pain,
                "change": args.change,
            },
            top_k=args.top_k,
            model_dir=str(bundle["model_dir"]),
        )
        with open(args.image, "rb") as f:
            append_prediction(
                source="cli-screen",
                image_name=os.path.basename(args.image),
                image_bytes=f.read(),
                model_dir=str(bundle["model_dir"]),
                top_k=args.top_k,
                predictions=result["predictions"],
            )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    predictions = predict_image(image, top_k=args.top_k, model_dir=str(bundle["model_dir"]))
    print(json.dumps({"image": args.image, "mode": args.mode, "predictions": predictions}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
