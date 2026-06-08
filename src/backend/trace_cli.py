"""Affiche les traces (logs/traces.jsonl) de maniere LISIBLE, comme en demo.

Lancement :
    uv run horragor-trace          # dernier run
    uv run horragor-trace -n 5     # les 5 derniers runs
"""

import argparse
import json

from backend.config import _PROJECT_ROOT

_ICONS = {
    "tool": "🔧",
    "embed": "🧬",
    "faiss": "🔎",
    "sql": "🗄️",
    "tmdb": "🎬",
    "pgvector": "🧭",
    "wikipedia": "🌐",
    "python": "🐍",
    "judge": "⚖️",
    "verdict": "🏁",
}
_LOG = _PROJECT_ROOT / "logs" / "traces.jsonl"


def _print_run(run: dict) -> None:
    print(f"\n🕒 {run.get('ts', '')[:19]} — « {run.get('question', '')} »")
    for step in run.get("trace", []):
        icon = _ICONS.get(step["kind"], "•")
        line = f"  {icon} {step['kind']:9} {step['name']:18} {step['detail']}"
        print(line.rstrip())
    print(f"  → {run.get('answer', '')[:200]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Affiche les traces d'agent lisiblement.")
    parser.add_argument("-n", type=int, default=1, help="nombre de runs recents a afficher")
    args = parser.parse_args()

    if not _LOG.exists():
        print("Aucune trace : logs/traces.jsonl absent. Pose d'abord une question dans le chat.")
        return

    lines = _LOG.read_text(encoding="utf-8").splitlines()
    for line in lines[-args.n :]:
        try:
            _print_run(json.loads(line))
        except json.JSONDecodeError:
            continue


if __name__ == "__main__":
    main()
