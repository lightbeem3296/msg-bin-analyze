import argparse
import json
import os
import traceback
from pathlib import Path

CUR_DIR = Path(__file__).parent.absolute()
os.chdir(CUR_DIR)


def work(json_path: str, trans_path: str, out_path: str):
    try:
        with open(json_path, "r", encoding="utf-8") as f_json:
            data = json.load(f_json)
            with open(trans_path, "r", encoding="utf-8") as f_trans:
                lines = f_trans.readlines()
                for line in lines:
                    words = line.strip().split("=", 1)
                    chain = words[0].split(":")
                    val = words[1].replace(
                        "=*=*=*=*=", "\n"
                    )

                    expression = "data"
                    for i in range(len(chain)):
                        expression += f"[chain[{i}]]"
                    expression += " = val"
                    exec(expression)

                with open(out_path, "w", encoding="utf-8") as f_out:
                    json.dump(data, f_out, indent=2, ensure_ascii=True)

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
        "--trans",
        dest="trans_path",
        type=str,
        required=True,
        help="Input translated text file path.",
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
        work(args.json_path, args.trans_path, args.out_path)
    except:
        traceback.print_exc()


def test():
    work("tips.bin.json", "res_trans.txt", "res.json")


if __name__ == "__main__":
    main()
    # test()
                                                                                      