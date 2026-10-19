import subprocess
import re
import sys

def main():
    tracked = subprocess.check_output(["git", "ls-files"], text=True).splitlines()
    patterns = [
        (re.compile(r"BEGIN (?:RSA|OPENSSH|DSA|EC|PGP) PRIVATE KEY"), "Private Key"),
        (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key"),
        (re.compile(r"ghp_[A-Za-z0-9]{36}"), "GitHub Personal Access Token"),
        (re.compile(r"(?i)(?:api[_-]?key|secret[_-]?key|password)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]"), "Secret Key / Password"),
    ]

    found = []
    for f in tracked:
        if f.endswith((".wav", ".mp3", ".png", ".jpg", ".ico")):
            continue
        try:
            with open(f, "r", encoding="utf-8", errors="ignore") as fp:
                for idx, line in enumerate(fp, 1):
                    if any(x in line for x in ["minioadmin", "dummy", "placeholder", "EXAMPLE", "your-", "test_secret"]):
                        continue
                    for pat, label in patterns:
                        if pat.search(line):
                            found.append((f, idx, label))
        except Exception:
            pass

    print(f"Secret scan completed. Found: {len(found)}")
    for f, idx, label in found:
        print(f"  {f}:{idx} - {label}")
    return 1 if found else 0

if __name__ == "__main__":
    sys.exit(main())
