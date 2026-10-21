import base64
import os
import shutil
import sqlite3
import time
from pathlib import Path
import blackboxprotobuf


def get_conversations_dir() -> str:
    """Returns dynamic path to Antigravity IDE conversations directory."""
    return os.path.expanduser(r"~/.gemini/antigravity-ide/conversations")


def get_global_storage_path() -> str:
    """Returns dynamic path to Antigravity IDE globalStorage state.vscdb."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        p = os.path.join(appdata, "Antigravity", "User", "globalStorage", "state.vscdb")
        if os.path.exists(p):
            return p
    return os.path.expanduser(r"~/AppData/Roaming/Antigravity/User/globalStorage/state.vscdb")


def backup_file(file_path: str) -> bool:
    """Creates a .bak backup of the specified file."""
    try:
        if os.path.exists(file_path):
            bak_path = file_path + ".bak"
            shutil.copy2(file_path, bak_path)
            return True
    except Exception as e:
        print(f"[Warning] Failed to backup {file_path}: {e}")
    return False


def list_conversations() -> list[dict]:
    """
    Scans all .db conversation files and returns a list of conversation metadata dicts.
    Sorted by mtime descending (most recently modified first).
    """
    conversations_dir = get_conversations_dir()
    if not os.path.exists(conversations_dir):
        return []

    results = []
    db_files = [f for f in os.listdir(conversations_dir) if f.endswith(".db")]

    for db_file in db_files:
        conv_id = db_file[:-3]
        db_path = os.path.join(conversations_dir, db_file)
        try:
            mtime = os.path.getmtime(db_path)
            size_bytes = os.path.getsize(db_path)
            title = None
            raw_summary = None

            # Open in read-only mode with timeout to prevent locking
            with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5.0) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT rowid, step_payload FROM steps ORDER BY idx LIMIT 20")
                rows = cursor.fetchall()
                for rowid, payload in rows:
                    if not payload:
                        continue
                    try:
                        msg, _ = blackboxprotobuf.decode_message(payload)
                        if "30" in msg and "4" in msg["30"]:
                            val = msg["30"]["4"]
                            text = val.decode("utf-8", "ignore") if isinstance(val, bytes) else str(val)
                            parts = text.split("\n\n", 1)
                            title = parts[0].strip()
                            raw_summary = parts[1] if len(parts) > 1 else ""
                            break
                    except Exception:
                        pass

            results.append({
                "id": conv_id,
                "file": db_file,
                "path": db_path,
                "title": title or "[Tanpa Judul / Belum Terdeteksi]",
                "summary": raw_summary or "",
                "mtime": mtime,
                "size": size_bytes,
            })
        except Exception as e:
            results.append({
                "id": conv_id,
                "file": db_file,
                "path": db_path,
                "title": f"[Gagal Membaca: {e}]",
                "summary": "",
                "mtime": 0,
                "size": 0,
            })

    results.sort(key=lambda x: x["mtime"], reverse=True)
    return results


def update_db_title(db_path: str, new_title: str) -> tuple[bool, str]:
    """
    Updates the conversation title inside the SQLite .db steps payload.
    """
    if not os.path.exists(db_path):
        return False, f"File database tidak ditemukan: {db_path}"

    backup_file(db_path)

    try:
        with sqlite3.connect(db_path, timeout=5.0) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA wal_checkpoint(FULL)")
            cursor.execute("SELECT rowid, step_payload FROM steps ORDER BY idx LIMIT 20")
            rows = cursor.fetchall()

            updated = False
            for rowid, payload in rows:
                if not payload:
                    continue
                try:
                    blob_data = bytearray(payload)
                    msg, typedef = blackboxprotobuf.decode_message(blob_data)
                    if "30" in msg and "4" in msg["30"]:
                        val = msg["30"]["4"]
                        current_text = val.decode("utf-8", "ignore") if isinstance(val, bytes) else str(val)
                        parts = current_text.split("\n\n", 1)
                        if len(parts) > 1:
                            new_text = new_title + "\n\n" + parts[1]
                        else:
                            new_text = new_title

                        msg["30"]["4"] = new_text.encode("utf-8")
                        new_blob = blackboxprotobuf.encode_message(msg, typedef)
                        cursor.execute("UPDATE steps SET step_payload = ? WHERE rowid = ?", (new_blob, rowid))
                        updated = True
                        break
                except Exception:
                    pass

            if updated:
                conn.commit()
                cursor.execute("PRAGMA wal_checkpoint(FULL)")
                return True, "Berhasil memperbarui judul di database percakapan."
            else:
                return False, "Tidak dapat menemukan field judul di database percakapan."
    except Exception as e:
        return False, f"Error saat memperbarui database percakapan: {e}"


def update_global_storage_title(conv_id: str, new_title: str) -> tuple[bool, str]:
    """
    Dual-sync update: Updates or inserts (upsert) the conversation title in state.vscdb trajectorySummaries.
    Guarantees that the conversation is always present in the sidebar cache.
    """
    gs_path = get_global_storage_path()
    if not os.path.exists(gs_path):
        return False, f"state.vscdb tidak ditemukan di: {gs_path}"

    try:
        backup_file(gs_path)
        with sqlite3.connect(gs_path, timeout=5.0) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA wal_checkpoint(FULL)")
            cursor.execute("SELECT value FROM ItemTable WHERE key = 'antigravityUnifiedStateSync.trajectorySummaries'")
            row = cursor.fetchone()
            if not row or not row[0]:
                return False, "Kunci trajectorySummaries tidak ditemukan di state.vscdb."

            raw_proto = base64.b64decode(row[0])
            msg, typedef = blackboxprotobuf.decode_message(raw_proto)

            items = msg.get("1", [])
            inner_typedef = {
                "1": {"type": "bytes", "name": ""},
                "3": {"type": "message", "message_typedef": {"1": {"type": "int", "name": ""}}, "name": ""},
                "7": {"type": "message", "message_typedef": {"1": {"type": "int", "name": ""}}, "name": ""},
                "10": {"type": "message", "message_typedef": {"1": {"type": "int", "name": ""}}, "name": ""},
            }

            # Extract exact inner typedef from an existing entry if available
            for item in items:
                in_b64 = item.get("2", {}).get("1")
                if in_b64:
                    try:
                        _, detected_type = blackboxprotobuf.decode_message(base64.b64decode(in_b64))
                        if "1" in detected_type:
                            inner_typedef = detected_type
                            break
                    except Exception:
                        pass

            now_ts = int(time.time())
            found = False
            for item in items:
                cid = item.get("1", b"")
                if isinstance(cid, bytes):
                    cid = cid.decode("utf-8", "ignore")
                if cid == conv_id:
                    inner_b64 = item.get("2", {}).get("1")
                    if inner_b64:
                        inner_proto = base64.b64decode(inner_b64)
                        inner_msg, _ = blackboxprotobuf.decode_message(inner_proto)
                        inner_msg["1"] = new_title.encode("utf-8")
                        if "3" in inner_msg and isinstance(inner_msg["3"], dict):
                            inner_msg["3"]["1"] = now_ts
                        new_inner_bytes = blackboxprotobuf.encode_message(inner_msg, inner_typedef)
                        item["2"]["1"] = base64.b64encode(new_inner_bytes)
                    else:
                        inner_msg = {
                            "1": new_title.encode("utf-8"),
                            "3": {"1": now_ts},
                            "7": {"1": now_ts},
                            "10": {"1": now_ts},
                        }
                        new_inner_bytes = blackboxprotobuf.encode_message(inner_msg, inner_typedef)
                        item["2"] = {"1": base64.b64encode(new_inner_bytes)}
                    found = True
                    break

            if not found:
                # Upsert: Daftarkan percakapan di posisi paling atas jika belum ada di cache UI sidebar
                new_inner_msg = {
                    "1": new_title.encode("utf-8"),
                    "3": {"1": now_ts},
                    "7": {"1": now_ts},
                    "10": {"1": now_ts},
                }
                new_inner_bytes = blackboxprotobuf.encode_message(new_inner_msg, inner_typedef)
                new_item = {
                    "1": conv_id.encode("utf-8"),
                    "2": {"1": base64.b64encode(new_inner_bytes)},
                }
                items.insert(0, new_item)

            msg["1"] = items
            new_root_bytes = blackboxprotobuf.encode_message(msg, typedef)
            new_b64 = base64.b64encode(new_root_bytes).decode("ascii")
            cursor.execute(
                "UPDATE ItemTable SET value = ? WHERE key = 'antigravityUnifiedStateSync.trajectorySummaries'",
                (new_b64,)
            )
            conn.commit()
            cursor.execute("PRAGMA wal_checkpoint(FULL)")
            action_desc = "disinkronkan" if found else "didaftarkan baru"
            return True, f"Berhasil {action_desc} di cache UI sidebar (state.vscdb)."
    except Exception as e:
        return False, f"Error saat memperbarui state.vscdb: {e}"


def rename_conversation_by_id(conv_id: str, new_title: str) -> tuple[bool, str]:
    """
    Renames conversation with Dual-Sync:
    1. Updates ~/.gemini/antigravity-ide/conversations/<conv_id>.db
    2. Updates state.vscdb (antigravityUnifiedStateSync.trajectorySummaries)
    """
    conversations_dir = get_conversations_dir()
    db_file = f"{conv_id}.db"
    db_path = os.path.join(conversations_dir, db_file)

    if not os.path.exists(db_path):
        return False, f"File database percakapan tidak ditemukan: {db_file}"

    # 1. Update in conversation .db
    ok_db, msg_db = update_db_title(db_path, new_title)
    if not ok_db:
        return False, msg_db

    # 2. Dual-sync update in state.vscdb UI cache
    ok_ui, msg_ui = update_global_storage_title(conv_id, new_title)

    if ok_ui:
        sync_status = "Dual-Sync Berhasil (Database + UI Cache Sidebar)"
    else:
        sync_status = f"Database diperbarui ({msg_ui})"

    return True, f"{sync_status}.\nFile: {db_file}"


def rename_conversation(old_title: str, new_title: str) -> tuple[bool, str]:
    """
    Backward-compatible rename function by title search.
    Finds matching conversation by title and executes Dual-Sync.
    """
    conversations = list_conversations()
    target_conv = None

    # First attempt: exact title match
    for conv in conversations:
        if conv["title"].strip().lower() == old_title.strip().lower():
            target_conv = conv
            break

    # Second attempt: starts with match
    if not target_conv:
        for conv in conversations:
            if conv["title"].strip().lower().startswith(old_title.strip().lower()):
                target_conv = conv
                break

    # Third attempt: substring match
    if not target_conv:
        for conv in conversations:
            if old_title.strip().lower() in conv["title"].strip().lower():
                target_conv = conv
                break

    if not target_conv:
        return False, f"Gagal menemukan percakapan dengan judul: '{old_title}'"

    return rename_conversation_by_id(target_conv["id"], new_title)


def scan_zombie_conversations() -> tuple[int, list[dict]]:
    """
    Scans trajectorySummaries in state.vscdb and returns count and list of zombie entries
    whose .db or .pb file no longer exists on disk.
    """
    gs_path = get_global_storage_path()
    if not os.path.exists(gs_path):
        return 0, []

    conversations_dir = get_conversations_dir()
    existing_ids = {
        os.path.splitext(f)[0]
        for f in os.listdir(conversations_dir)
        if f.endswith((".db", ".pb"))
    } if os.path.exists(conversations_dir) else set()

    try:
        with sqlite3.connect(f"file:{gs_path}?mode=ro", uri=True, timeout=5.0) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM ItemTable WHERE key = 'antigravityUnifiedStateSync.trajectorySummaries'")
            row = cursor.fetchone()
            if not row or not row[0]:
                return 0, []

            raw_proto = base64.b64decode(row[0])
            msg, _ = blackboxprotobuf.decode_message(raw_proto)

            zombies = []
            for item in msg.get("1", []):
                cid = item.get("1", b"")
                if isinstance(cid, bytes):
                    cid = cid.decode("utf-8", "ignore")
                if cid and cid not in existing_ids:
                    title = "[Tanpa Judul]"
                    inner_b64 = item.get("2", {}).get("1")
                    if inner_b64:
                        try:
                            inner_msg, _ = blackboxprotobuf.decode_message(base64.b64decode(inner_b64))
                            t = inner_msg.get("1", b"")
                            title = t.decode("utf-8", "ignore") if isinstance(t, bytes) else str(t)
                        except Exception:
                            pass
                    zombies.append({"id": cid, "title": title})

            return len(zombies), zombies
    except Exception as e:
        print(f"[Warning] scan_zombie_conversations error: {e}")
        return 0, []


def clean_zombie_conversations() -> tuple[bool, str, int]:
    """
    Scans trajectorySummaries in state.vscdb and purges any orphaned entries
    whose .db or .pb file has already been deleted from disk.
    Returns (success, message, purged_count).
    """
    gs_path = get_global_storage_path()
    if not os.path.exists(gs_path):
        return False, f"state.vscdb tidak ditemukan: {gs_path}", 0

    conversations_dir = get_conversations_dir()
    existing_ids = {
        os.path.splitext(f)[0]
        for f in os.listdir(conversations_dir)
        if f.endswith((".db", ".pb"))
    } if os.path.exists(conversations_dir) else set()

    try:
        backup_file(gs_path)
        with sqlite3.connect(gs_path, timeout=5.0) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA wal_checkpoint(FULL)")
            cursor.execute("SELECT value FROM ItemTable WHERE key = 'antigravityUnifiedStateSync.trajectorySummaries'")
            row = cursor.fetchone()
            if not row or not row[0]:
                return False, "trajectorySummaries tidak ditemukan.", 0

            raw_proto = base64.b64decode(row[0])
            msg, typedef = blackboxprotobuf.decode_message(raw_proto)

            original_items = msg.get("1", [])
            cleaned_items = []
            seen_ids = set()

            for item in original_items:
                cid = item.get("1", b"")
                if isinstance(cid, bytes):
                    cid = cid.decode("utf-8", "ignore")
                if cid in existing_ids:
                    if cid not in seen_ids:
                        seen_ids.add(cid)
                        cleaned_items.append(item)

            purged_count = len(original_items) - len(cleaned_items)
            if purged_count > 0:
                msg["1"] = cleaned_items
                new_root_bytes = blackboxprotobuf.encode_message(msg, typedef)
                new_b64 = base64.b64encode(new_root_bytes).decode("ascii")
                cursor.execute(
                    "UPDATE ItemTable SET value = ? WHERE key = 'antigravityUnifiedStateSync.trajectorySummaries'",
                    (new_b64,)
                )
                conn.commit()
                cursor.execute("PRAGMA wal_checkpoint(FULL)")
                return True, f"Berhasil membersihkan {purged_count} percakapan zombie/hantu dari cache UI.", purged_count
            else:
                return True, "Tidak ada percakapan zombie/hantu yang ditemukan. Cache sudah bersih.", 0
    except Exception as e:
        return False, f"Gagal membersihkan percakapan zombie: {e}", 0


def sync_all_active_conversations_to_sidebar() -> tuple[bool, str, int]:
    """
    Memastikan seluruh percakapan aktif yang ada di disk (~/.gemini/antigravity-ide/conversations/*.db)
    terdaftar di cache UI sidebar (state.vscdb).
    Mencegah percakapan hilang dari sidebar.
    Returns (success, message, synced_count).
    """
    gs_path = get_global_storage_path()
    if not os.path.exists(gs_path):
        return False, f"state.vscdb tidak ditemukan: {gs_path}", 0

    convs = list_conversations()
    if not convs:
        return True, "Tidak ada percakapan aktif untuk disinkronkan.", 0

    try:
        backup_file(gs_path)
        with sqlite3.connect(gs_path, timeout=5.0) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA wal_checkpoint(FULL)")
            cursor.execute("SELECT value FROM ItemTable WHERE key = 'antigravityUnifiedStateSync.trajectorySummaries'")
            row = cursor.fetchone()
            if not row or not row[0]:
                return False, "trajectorySummaries tidak ditemukan.", 0

            raw_proto = base64.b64decode(row[0])
            msg, typedef = blackboxprotobuf.decode_message(raw_proto)
            items = msg.get("1", [])

            existing_items_map = {}
            for idx, item in enumerate(items):
                cid = item.get("1", b"")
                if isinstance(cid, bytes):
                    cid = cid.decode("utf-8", "ignore")
                existing_items_map[cid] = (idx, item)

            inner_typedef = {
                "1": {"type": "bytes", "name": ""},
                "3": {"type": "message", "message_typedef": {"1": {"type": "int", "name": ""}}, "name": ""},
                "7": {"type": "message", "message_typedef": {"1": {"type": "int", "name": ""}}, "name": ""},
                "10": {"type": "message", "message_typedef": {"1": {"type": "int", "name": ""}}, "name": ""},
            }
            for it in items:
                in_b64 = it.get("2", {}).get("1")
                if in_b64:
                    try:
                        _, detected = blackboxprotobuf.decode_message(base64.b64decode(in_b64))
                        if "1" in detected:
                            inner_typedef = detected
                            break
                    except Exception:
                        pass

            added_count = 0
            for conv in convs:
                cid = conv["id"]
                title = conv["title"]
                mtime = int(conv["mtime"]) if conv["mtime"] else int(time.time())

                if cid not in existing_items_map:
                    new_im = {
                        "1": title.encode("utf-8"),
                        "3": {"1": mtime},
                        "7": {"1": mtime},
                        "10": {"1": mtime},
                    }
                    new_in = blackboxprotobuf.encode_message(new_im, inner_typedef)
                    new_item = {
                        "1": cid.encode("utf-8"),
                        "2": {"1": base64.b64encode(new_in)},
                    }
                    items.append(new_item)
                    added_count += 1

            if added_count > 0:
                msg["1"] = items
                new_root_bytes = blackboxprotobuf.encode_message(msg, typedef)
                new_b64 = base64.b64encode(new_root_bytes).decode("ascii")
                cursor.execute(
                    "UPDATE ItemTable SET value = ? WHERE key = 'antigravityUnifiedStateSync.trajectorySummaries'",
                    (new_b64,)
                )
                conn.commit()
                cursor.execute("PRAGMA wal_checkpoint(FULL)")
                return True, f"Berhasil menyinkronkan {added_count} percakapan ke sidebar.", added_count
            else:
                return True, "Semua percakapan sudah tersinkronisasi di sidebar.", 0
    except Exception as e:
        return False, f"Gagal menyinkronkan percakapan ke sidebar: {e}", 0


