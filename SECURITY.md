# 🔐 Security Policy / Политика безопасности / Xavfsizlik siyosati

## Supported / Поддержка / Qo'llab-quvvatlash

| Release | Status |
|---|---|
| `v0.4.1-enterprise` (Update #54) | ✅ Supported — current |
| Older `.bbx` v1 containers & pre-rotation keys | ⚠️ Revoked — deprecated |

## Reporting a Vulnerability / Сообщение об уязвимости

We take security seriously. **Do not open a public issue** for a security
vulnerability. Instead use GitHub's private vulnerability reporting:

- **https://github.com/TrueImmortal82/UniPlag/security/advisories/new**

Please include:
- affected component (launcher, `.bbx` container, seal, ledger, web server),
- minimal reproduction steps,
- impact description,
- your contact (optional).

We aim to acknowledge reports within **5 business days** and to ship a fix
within a reasonable timeline depending on severity. Researcher credits go to
the advisory and release notes (unless anonymity is requested).

## Security Principles / Принципы / Printsip

- **No secrets in this repository.** The master key, publisher private key,
  and signing material are **never committed**. `.security/` is gitignored.
- **Fail-closed launchers.** The public `run_blackbox.py` embeds only the
  **Ed25519 public key** and verifies publisher attestation (`--verify-only`);
  decryption requires a licensed master key (env `UNIPLAG_SOVEREIGN_KEY_512`
  or `.security/sovereign_512.key`).
- **Key rotation.** Compromised keys are revoked immediately and backed up
  under `.security/revoked/` (see Update #54 in RELEASE_NOTES.md).
- **Report seals** are keyed **MACs** (`HMAC-SHA512`) bound to report content;
  `.bbx` release integrity is a real asymmetric **Ed25519 signature**.

## Example Disclosure Timeline / Пример таймлайна

1. Reporter submits advisory (private).
2. Maintainer triages severity.
3. Fix ships, advisory published with credits.

## No Bug Bounty / Без вознаграждения

This is a university research project; we currently do **not** offer monetary
rewards. Thank you for your responsible disclosure.