from cryptography.fernet import Fernet

key = Fernet.generate_key()
cipher = Fernet(key)

print(f"Your secret key:\n{key.decode()}")

with open("ground_truth.csv", "rb") as f:
    plaintext = f.read()

ciphertext = cipher.encrypt(plaintext)

with open("ground_truth.encrypted", "wb") as f:
    f.write(ciphertext)

print("Encrypted file saved as ground_truth.encrypted")