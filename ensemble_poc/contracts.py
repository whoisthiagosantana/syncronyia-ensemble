"""Data contracts shared by the trusted controller and untrusted producers."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

from jsonschema import Draft202012Validator

FILES = ("index.html", "style.css", "game.mjs", "ui.mjs")
MAX_BYTES = 262144
BUNDLE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["files"],
    "properties": {
        "files": {
            "type": "array",
            "minItems": 4,
            "maxItems": 4,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["path", "content"],
                "properties": {
                    "path": {"enum": list(FILES)},
                    "content": {"type": "string", "minLength": 1, "maxLength": 65536},
                },
            },
        }
    },
}


class Rejected(ValueError):
    """A bounded, public failure reason; never include provider output."""


def digest(value):
    raw = json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def parse(raw, limit=MAX_BYTES):
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    if len(raw) > limit:
        raise Rejected("OUTPUT_LIMIT")

    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise Rejected("DUPLICATE_KEY")
            result[k] = v
        return result

    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(Rejected("NONFINITE")),
        )
    except (ValueError, UnicodeError, RecursionError) as exc:
        if isinstance(exc, Rejected):
            raise
        raise Rejected("INVALID_JSON") from None


def validate_bundle(value):
    if not Draft202012Validator(BUNDLE_SCHEMA).is_valid(value):
        raise Rejected("BUNDLE_SCHEMA")
    if {item["path"] for item in value["files"]} != set(FILES):
        raise Rejected("BUNDLE_PATHS")
    # Encoding also rejects surrogate escapes before any filesystem mutation.
    try:
        size = sum(len(f["content"].encode("utf-8")) for f in value["files"])
    except UnicodeError:
        raise Rejected("BUNDLE_ENCODING") from None
    if size > MAX_BYTES:
        raise Rejected("BUNDLE_SIZE")
    return value


def materialize(value, target):
    """Write all-or-nothing into a new directory under a controller-owned parent."""
    validate_bundle(value)
    target = Path(target)
    parent = target.parent
    if parent.is_symlink() or parent.resolve() != parent.absolute():
        raise Rejected("UNTRUSTED_PARENT")
    if not parent.is_dir() or parent.stat().st_uid != os.getuid() or parent.stat().st_mode & 0o022:
        raise Rejected("UNTRUSTED_PARENT")
    if target.exists() or target.is_symlink():
        raise Rejected("TARGET_EXISTS")
    stage = Path(tempfile.mkdtemp(prefix=".bundle-", dir=parent))
    try:
        for item in value["files"]:
            with (stage / item["path"]).open("xb") as stream:
                stream.write(item["content"].encode("utf-8"))
        # Parent is exclusively controller-owned; no model can race this rename.
        stage.rename(target)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return {f: hashlib.sha256((target / f).read_bytes()).hexdigest() for f in FILES}


GAME_CONTRACT = """Generate a dependency-free static 2048 game in exactly index.html,
style.css, game.mjs, ui.mjs. Use relative imports and no remote assets, network calls,
package installers, inline scripts or event-handler attributes. index.html loads ui.mjs.
game.mjs exports pure functions:
move(board, direction) -> {board, score, moved}, directions left/right/up/down;
spawn(board, rng=Math.random) -> new board, using rng for empty cell then tile value;
getStatus(board) -> {won, lost}; won means a tile >=2048, lost means no legal moves.
Boards are arrays of four arrays of four nonnegative integers. Never mutate inputs.
A tile merges at most once per move; score is the sum of newly merged tile values.
spawn returns unchanged values on a full board; tile is 2 with 90% probability else 4.
UI exposes [data-testid=board], 16 [data-testid=cell], [data-testid=score],
[data-testid=status], button[data-testid=restart] and buttons[data-direction=left|right|up|down].
Start with two tiles. Arrow keys and direction buttons move the board; prevent scroll.
Only a changed move spawns one tile. Restart resets score and starts with two tiles.
Show victory and game-over text and make the layout usable on a 360px viewport.
The UI imports the game functions. No persistence, backend, analytics or external links.
Return only the JSON bundle requested by the supplied schema. All code uses English.
"""
