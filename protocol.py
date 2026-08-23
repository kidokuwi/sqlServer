__author__ = "Ido Keysar"

import os
import hashlib
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
from tcp_by_size import send_with_size, recv_by_size


PEPPER = "pepper"
try:
    if os.path.exists("pepper.txt"):
        with open("pepper.txt", "r") as f:
            PEPPER = f.read().strip()
except Exception:
    pass


class SecureSession:
    def __init__(self, key, aad=b""):
        self.aesgcm = AESGCM(key)
        self.aad = aad

    def encrypt(self, plaintext):
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, plaintext, self.aad)
        return nonce + ciphertext

    def decrypt(self, data):
        nonce = data[:12]
        ciphertext = data[12:]
        return self.aesgcm.decrypt(nonce, ciphertext, self.aad)


def load_rsa_keys(priv_file="private_key.pem", pub_file="public_key.pem"):
    password = b'mypassword'
    if os.path.exists(priv_file) and os.path.exists(pub_file):
        try:
            with open(priv_file, "rb") as f:
                priv_key = serialization.load_pem_private_key(f.read(), password=password, backend=default_backend())
            with open(pub_file, "rb") as f:
                pub_key = serialization.load_pem_public_key(f.read(), backend=default_backend())
            return priv_key, pub_key
        except Exception:
            pass

    priv_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem_priv = priv_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(password)
    )
    with open(priv_file, 'wb') as f:
        f.write(pem_priv)

    pub_key = priv_key.public_key()
    pem_pub = pub_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open(pub_file, 'wb') as f:
        f.write(pem_pub)

    return priv_key, pub_key


def perform_handshake_server(sock, server_private_key, server_public_key):
    method_data = recv_by_size(sock)
    if isinstance(method_data, bytes):
        method_data = method_data.decode('utf-8', errors='ignore')
    if not method_data or not method_data.startswith("KEY_METHOD|"):
        return None
    send_with_size(sock, "SUPPORTED")
    pem_pub = server_public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    send_with_size(sock, pem_pub)
    enc_aes_key = recv_by_size(sock)
    if not enc_aes_key:
        return None
    aes_key = server_private_key.decrypt(
        enc_aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return SecureSession(aes_key)


def perform_handshake_client(sock):
    send_with_size(sock, "KEY_METHOD|RSA")
    res = recv_by_size(sock)
    if isinstance(res, bytes):
        res = res.decode('utf-8', errors='ignore')
    if res != "SUPPORTED":
        return None
    pem_pub_bytes = recv_by_size(sock)
    pub_key = serialization.load_pem_public_key(pem_pub_bytes, backend=default_backend())
    aes_key = AESGCM.generate_key(bit_length=256)
    enc_aes_key = pub_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    send_with_size(sock, enc_aes_key)
    return SecureSession(aes_key)


def hash_password(password, salt):
    combined = password + salt + PEPPER
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()


def build_msg(action, *params):
    if not params:
        return action
    return action + "|" + "|".join(str(p) for p in params)


def parse_msg(msg_str):
    if isinstance(msg_str, bytes):
        msg_str = msg_str.decode('utf-8', errors='ignore')
    parts = msg_str.split('|')
    action = parts[0]
    params = parts[1:] if len(parts) > 1 else []
    return action, params
