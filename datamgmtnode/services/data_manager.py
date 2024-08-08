import os

class DataManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.db = self._init_database()

    def _init_database(self):
        try:
            import rocksdb
            print("Using RocksDB for data storage")
            return rocksdb.DB(self.db_path, rocksdb.Options(create_if_missing=True))
        except ImportError:
            try:
                import plyvel
                print("RocksDB not available. Using LevelDB for data storage")
                return plyvel.DB(self.db_path, create_if_missing=True)
            except ImportError:
                raise ImportError("Neither RocksDB nor LevelDB (Plyvel) are available. Please install one of them.")

    def store_data(self, key, value):
        key_bytes = key.encode() if isinstance(key, str) else key
        value_bytes = value.encode() if isinstance(value, str) else value
        self.db.put(key_bytes, value_bytes)

    def get_data(self, key):
        key_bytes = key.encode() if isinstance(key, str) else key
        value = self.db.get(key_bytes)
        return value.decode() if value else None

    def delete_data(self, key):
        key_bytes = key.encode() if isinstance(key, str) else key
        self.db.delete(key_bytes)

    def close(self):
        if hasattr(self.db, 'close'):
            self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()