import argparse
import json
import os
import traceback
from pathlib import Path

CUR_DIR = Path(__file__).parent.absolute()
os.chdir(CUR_DIR)


def walk_json(json_data, chain: list, out_path: str):
    try:
        if isinstance(json_data, list):
            for i, val in enumerate(json_data):
                sub_chain = chain.copy()
                sub_chain.append(f"{i}")
                walk_json(val, sub_chain, out_path)
        elif isinstance(json_data, dict):
            for key, value in json_data.items():
                sub_chain = chain.copy()
                sub_chain.append(key)
                walk_json(value, sub_chain, out_path)
        else:
            d = ":".join(chain)
            if isinstance(json_data, str) and json_data.isascii():
                json_data = json_data.replace(
                    "\n", "=*=*=*=*="
                )
                is_english = False
                for ch in json_data:
                    if ch.isalpha():
                        is_english = True
                        break
                if is_english:
                    with open(out_path, "a+", encoding="utf-8") as f:
                        f.write(f"{d}={json_data}\n")
    except:
        traceback.print_exc()


def work(json_path: str, out_path: str):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(fp=f)

            if os.path.isfile(out_path):
                os.remove(out_path)

            walk_json(data, [], out_path)
    except:
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json",
        dest="json_path",
        type=str,
        required=True,
        help="Input json file path.",
    )
    parser.add_argument(
        "--out",
        dest="out_path",
        type=str,
        required=True,
        help="Output txt file path.",
    )
    args = parser.parse_args()
    try:
        work(args.json_path, args.out_path)
    except:
        traceback.print_exc()


def test():
    # work("tips.bin.json", "res.txt")
    work("res.json", "res-m.txt")


if __name__ == "__main__":
    main()
    # test()
                                                                                                 