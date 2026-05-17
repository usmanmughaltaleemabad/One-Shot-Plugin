#!/usr/bin/env python3
"""Phase 5 Content Delivery: CDN Integration & Cache Headers"""

from typing import Dict, Optional
from datetime import datetime, timedelta


def generate_content_delivery() -> str:
    return '''
class CDNIntegration:
    """Serve content from CDN with proper cache headers."""

    def __init__(self):
        self._cache_policies = {}

    def set_cache_headers(self, path: str, max_age: int, public: bool = True) -> Dict:
        """Set cache policy for path"""
        return {
            "Cache-Control": f"{'public' if public else 'private'}, max-age={max_age}",
            "ETag": f'\\"{hash(path)}\\"',
            "Last-Modified": datetime.utcnow().isoformat()
        }

    def invalidate_cdn(self, paths: list) -> None:
        """Purge paths from CDN cache"""
        for path in paths:
            self._cache_policies.pop(path, None)
'''
    return generate_content_delivery()


def generate_cdn_system() -> dict:
    return {
        "code": "from typing import Dict, Optional\\nfrom datetime import datetime, timedelta\\n\\n\\n" + \
                '"""CDN integration with cache headers (CloudFlare, Akamai pattern)."""\\n' + \
                generate_content_delivery(),
        "pattern": "Content Delivery",
        "module": "phase5_content_delivery.py"
    }


if __name__ == "__main__":
    print(generate_cdn_system()["code"])
