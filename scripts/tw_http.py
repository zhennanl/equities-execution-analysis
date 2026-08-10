#!/usr/bin/env python3
"""One HTTP session for the Taiwanese sources, with the TLS
quirk handled in exactly one place.

    from tw_http import session, get, post

THE BUG THIS EXISTS TO FIX (c-330). On Python 3.14, TDCC fails
the handshake:

    ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED]
    certificate verify failed: Missing Subject Key Identifier

That is NOT an expired certificate, a bad CA bundle, or a
man-in-the-middle. Python 3.13 turned ON `ssl.VERIFY_X509_STRICT`
in `ssl.create_default_context()`, which enforces a set of RFC
5280 structural rules that OpenSSL previously skipped. One of
them requires every CA certificate in the chain to carry a
Subject Key Identifier extension. TDCC's intermediate does not.
The certificate is otherwise valid and the site is fine in a
browser — browsers do not apply this check.

WHAT THIS DOES ABOUT IT, AND WHAT IT REFUSES TO DO.

  It clears ONE flag: VERIFY_X509_STRICT. Everything that
  actually protects the connection stays on — the CA chain is
  still verified against the system trust store, the hostname is
  still checked, and an expired or self-signed certificate is
  still rejected.

  It does NOT set `verify=False`. That is the fix the internet
  will suggest and it is the wrong one: it disables verification
  entirely, so any machine on the path can serve you whatever it
  likes and the harvest would silently ingest it. A data
  pipeline that cannot tell TDCC from an intercepting proxy is
  worse than a pipeline that fails loudly.

  It does NOT suppress urllib3's InsecureRequestWarning,
  because with the above there is nothing insecure to suppress.

THE FLAG IS APPLIED PER-HOST, NOT GLOBALLY. `RELAXED_HOSTS` is
an explicit list. A site that starts failing strict validation
gets added deliberately, with a note, rather than the whole
project quietly running relaxed. Everything else uses the stock
context.

ALSO IN HERE, because every harvester was reinventing them:
retry with exponential backoff, a shared UA, and a `probe()` that
reports what a URL actually returns without parsing it.
"""
from __future__ import annotations

import ssl
import sys
import time

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")

# Hosts whose certificate chain fails Python 3.13+ strict X.509
# validation. Each entry needs a reason.
RELAXED_HOSTS = {
    # c-330: intermediate CA lacks a Subject Key Identifier.
    # Observed 2026-08-10 on Python 3.14 / OpenSSL 3.x.
    "www.tdcc.com.tw",
    "openapi.tdcc.com.tw",
    "opendata.tdcc.com.tw",
}


def relaxed_context():
    """A verifying context with the strict structural check off."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED
    # Present from 3.13; guarded so this file still imports on
    # older interpreters, where the flag does not exist and the
    # problem does not either.
    strict = getattr(ssl, "VERIFY_X509_STRICT", 0)
    if strict:
        ctx.verify_flags &= ~strict
    return ctx


class _RelaxedAdapter:
    """Built lazily so importing this module never needs requests."""


def _make_adapter():
    from requests.adapters import HTTPAdapter
    from urllib3.poolmanager import PoolManager

    class RelaxedAdapter(HTTPAdapter):
        def init_poolmanager(self, connections, maxsize,
                             block=False, **kw):
            kw["ssl_context"] = relaxed_context()
            self.poolmanager = PoolManager(
                num_pools=connections, maxsize=maxsize,
                block=block, **kw)

        def proxy_manager_for(self, proxy, **kw):
            kw["ssl_context"] = relaxed_context()
            return super().proxy_manager_for(proxy, **kw)

    return RelaxedAdapter()


_SESSION = None


def session():
    """A module-level requests.Session with the relaxed adapter
    mounted for the hosts that need it.

    One session for the process means connection reuse, which
    matters when a harvest makes 200 sequential requests to the
    same host."""
    global _SESSION
    if _SESSION is not None:
        return _SESSION
    import requests
    s = requests.Session()
    s.headers.update({"User-Agent": UA})
    ad = _make_adapter()
    for host in RELAXED_HOSTS:
        s.mount(f"https://{host}/", ad)
    _SESSION = s
    return s


def _call(method, url, tries=4, timeout=30, **kw):
    import requests
    last = None
    for k in range(tries):
        try:
            r = session().request(method, url, timeout=timeout, **kw)
            r.raise_for_status()
            return r
        except requests.exceptions.SSLError as ex:
            # Never retried. A TLS failure is a configuration
            # fact, not a transient one, and retrying it four
            # times only delays the message by two minutes.
            raise SystemExit(
                f"\nTLS verification failed for {url}\n  {ex}\n\n"
                f"If the host is not in tw_http.RELAXED_HOSTS, add "
                f"it there WITH A REASON — do not reach for "
                f"verify=False.\n") from ex
        except Exception as ex:                        # noqa: BLE001
            last = ex
            if k < tries - 1:
                time.sleep(2 ** k * 2)
    raise last


def get(url, **kw):
    return _call("GET", url, **kw)


def post(url, **kw):
    return _call("POST", url, **kw)


def probe(url):
    """Report what a URL returns, without parsing it. Run this
    first when a source misbehaves — it separates 'the network
    is refusing me' from 'the parser is wrong', which are the two
    failures that look identical from a traceback."""
    import requests
    print(f"python  {sys.version.split()[0]}")
    print(f"strict  VERIFY_X509_STRICT="
          f"{bool(getattr(ssl, 'VERIFY_X509_STRICT', 0))}")
    host = url.split("/")[2]
    print(f"host    {host}  "
          f"{'RELAXED' if host in RELAXED_HOSTS else 'stock context'}")
    try:
        r = session().get(url, timeout=30)
        body = r.text
        print(f"status  {r.status_code}")
        print(f"type    {r.headers.get('Content-Type')}")
        print(f"bytes   {len(body):,}")
        print(f"head    {body[:200]!r}")
        return r
    except requests.exceptions.SSLError as ex:
        print(f"TLS FAILED: {ex}")
        return None


if __name__ == "__main__":
    probe(sys.argv[1] if len(sys.argv) > 1
          else "https://www.tdcc.com.tw/portal/zh/smWeb/qryStock")
