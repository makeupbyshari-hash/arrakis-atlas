#!/usr/bin/env python3
"""Encrypt/decrypt the permanent Android signing key, never print or commit unencrypted key.
The passphrase is read only from the GitHub Actions secret ATLAS_SIGNING_PASSWORD.
"""
import os, sys, pathlib, secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
MAGIC=b'ATLAS1'
AAD=b'Arrakis Atlas permanent Android signing key v1'
def derive(password,salt):
    if len(password) < 32: raise ValueError("Signing secret must be at least 32 characters")
    return Scrypt(salt=salt,length=32,n=2**15,r=8,p=1).derive(password.encode('utf-8'))
def main():
    if len(sys.argv)!=4 or sys.argv[1] not in ('encrypt','decrypt'):
        raise SystemExit("Usage: signing_vault.py encrypt|decrypt input output")
    secret=os.environ.get("ATLAS_SIGNING_PASSWORD","")
    src,dst=pathlib.Path(sys.argv[2]),pathlib.Path(sys.argv[3])
    if sys.argv[1]=='encrypt':
        salt=secrets.token_bytes(16);nonce=secrets.token_bytes(12)
        key=derive(secret,salt)
        ct=AESGCM(key).encrypt(nonce,src.read_bytes(),AAD)
        dst.parent.mkdir(parents=True,exist_ok=True)
        dst.write_bytes(MAGIC+salt+nonce+ct)
    else:
        d=src.read_bytes()
        if d[:6]!=MAGIC:raise ValueError("Unexpected signing vault format")
        key=derive(secret,d[6:22])
        dst.parent.mkdir(parents=True,exist_ok=True)
        dst.write_bytes(AESGCM(key).decrypt(d[22:34],d[34:],AAD))
        os.chmod(dst,0o600)
    print("Signing vault processed successfully (private key not printed).")
if __name__=="__main__":main()
