import sqlite3
import blackboxprotobuf
import os

def rename_conversation(old_title, new_title):
    conversations_dir = r"C:\Users\adarmawan117\.gemini\antigravity-ide\conversations"
    if not os.path.exists(conversations_dir):
        return False, f"Direktori percakapan tidak ditemukan: {conversations_dir}"

    db_files = [f for f in os.listdir(conversations_dir) if f.endswith('.db')]
    
    found = False
    for db_file in db_files:
        db_path = os.path.join(conversations_dir, db_file)
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT rowid, step_payload FROM steps")
            rows = cursor.fetchall()
            
            for row in rows:
                rowid = row[0]
                if row[1] is None:
                    continue
                blob_data = bytearray(row[1])
                
                # Cek secara kasar dulu apakah string lamanya ada di dalam raw biner
                if old_title.encode('utf-8') in blob_data:
                    try:
                        # Decode struktur Protobuf
                        message, typedef = blackboxprotobuf.decode_message(blob_data)
                        
                        # Biasanya judul disimpan di field 30 -> 4, digabung dengan summary
                        if '30' in message and '4' in message['30']:
                            current_text = message['30']['4'].decode('utf-8', 'ignore')
                            if current_text.startswith(old_title):
                                # Ganti judulnya saja, biarkan deskripsinya utuh
                                parts = current_text.split('\n\n', 1)
                                if len(parts) > 1:
                                    new_text = new_title + '\n\n' + parts[1]
                                else:
                                    new_text = new_title
                                    
                                message['30']['4'] = new_text.encode('utf-8')
                                
                                # Re-Encode Protobuf!
                                new_blob = blackboxprotobuf.encode_message(message, typedef)
                                
                                cursor.execute("UPDATE steps SET step_payload = ? WHERE rowid = ?", (new_blob, rowid))
                                conn.commit()
                                found = True
                                return True, f"Berhasil merename di database: {db_file}"
                    except Exception as e:
                        # Abaikan jika gagal decode
                        pass
            conn.close()
        except Exception as e:
            pass
            
    if not found:
        return False, f"Gagal menemukan percakapan dengan judul: '{old_title}'"
