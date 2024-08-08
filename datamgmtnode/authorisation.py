
# AuthorizationModule
class AuthorizationModule:
    def __init__(self, db_connection):
        self.db = db_connection
        self.authorized_keys = self._load_authorized_keys()

    def _load_authorized_keys(self):
        return {row[0]: row[1] for row in self.db.execute("SELECT user_id, public_key FROM authorized_users")}

    def authorize_transfer(self, data_hash, signature, user_id):
        if user_id not in self.authorized_keys:
            return False

        public_key = rsa.PublicKey.from_pem(self.authorized_keys[user_id].encode())

        try:
            public_key.verify(
                signature,
                data_hash.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except:
            return False

    def add_authorized_user(self, user_id, public_key_pem):
        self.db.execute("INSERT INTO authorized_users (user_id, public_key) VALUES (?, ?)",
                        (user_id, public_key_pem))
        self.db.commit()
        self.authorized_keys[user_id] = public_key_pem
