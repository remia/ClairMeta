# Clairmeta - (C) YMAGIS S.A.
# See LICENSE for more information

import base64
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


def decrypt_b64(cipher, key):
    """Decrypt encoded cipher with specified private key.

    Args:
        cipher (str): Base64 encoded message.
        key (str): Absolute path to PEM private key.

    Returns:
        Decoded message.

    Raises:
        ValueError: If ``key`` is not a valid file.

    """
    if not os.path.isfile(key):
        raise ValueError(f"{key} file not found")

    with open(key, "rb") as f:
        key = serialization.load_pem_private_key(
            f.read(), password=None, backend=default_backend()
        )

        return key.decrypt(
            base64.b64decode(cipher),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA1()),
                algorithm=hashes.SHA1(),
                label=None,
            ),
        )
