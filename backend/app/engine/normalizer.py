"""VIGILANT Engine - Layer 2: Normalization & De-obfuscation

Converts polymorphic attacks into analyzable signals.
This layer is critical for zero-day detection.
"""
import re
import urllib.parse
from dataclasses import dataclass, field
from typing import Optional
from bs4 import BeautifulSoup
import httpx

from app.core.config import settings


# Homoglyph mapping: Cyrillic and lookalike characters → Latin
HOMOGLYPH_MAP = {
    '\u0430': 'a', '\u0435': 'e', '\u043e': 'o', '\u0440': 'p',
    '\u0441': 'c', '\u0443': 'y', '\u0445': 'x', '\u0456': 'i',
    '\u0458': 'j', '\u04bb': 'h', '\u0501': 'd', '\u051b': 'q',
    '\u051d': 'w', '\u0405': 'S', '\u0406': 'I', '\u0408': 'J',
    '\u0410': 'A', '\u0412': 'B', '\u0415': 'E', '\u041a': 'K',
    '\u041c': 'M', '\u041d': 'H', '\u041e': 'O', '\u0420': 'P',
    '\u0421': 'C', '\u0422': 'T', '\u0425': 'X', '\u0427': 'Y',
    # Common number substitutions
    '0': 'o', '1': 'l', '3': 'e', '4': 'a', '5': 's', '7': 't', '8': 'b',
}

# Known short URL domains
SHORT_URL_DOMAINS = {
    'bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly',
    'is.gd', 'buff.ly', 'dlvr.it', 'j.mp', 'rb.gy',
    'shorturl.at', 'tiny.cc', 'lnkd.in', 'youtu.be',
}


@dataclass
class NormalizedArtifact:
    """Result of normalization."""
    normalized_url: Optional[str] = None
    original_url: Optional[str] = None
    clean_text: Optional[str] = None
    visible_text: Optional[str] = None
    hidden_text: Optional[str] = None
    signals: dict = field(default_factory=dict)


def decode_url(url: str) -> str:
    """Fully decode URL (hex encoding, percent encoding)."""
    if not url:
        return url
    # Decode up to 3 rounds (handles double/triple encoding)
    prev = ""
    decoded = url
    for _ in range(3):
        prev = decoded
        decoded = urllib.parse.unquote(decoded)
        if decoded == prev:
            break
    return decoded


def normalize_punycode(url: str) -> tuple[str, bool]:
    """Convert punycode (xn--) domains to unicode for analysis."""
    has_punycode = False
    try:
        parsed = urllib.parse.urlparse(url)
        hostname = parsed.hostname or ""
        if 'xn--' in hostname:
            has_punycode = True
            # Decode each label
            labels = hostname.split('.')
            decoded_labels = []
            for label in labels:
                if label.startswith('xn--'):
                    try:
                        decoded_labels.append(label.encode('ascii').decode('idna'))
                    except (UnicodeError, UnicodeDecodeError):
                        decoded_labels.append(label)
                else:
                    decoded_labels.append(label)
            decoded_host = '.'.join(decoded_labels)
            url = url.replace(hostname, decoded_host, 1)
    except (Exception, ValueError):
        pass
    return url, has_punycode


def normalize_homoglyphs(text: str) -> tuple[str, int]:
    """Replace homoglyph characters with their Latin equivalents."""
    count = 0
    result = []
    for char in text:
        if char in HOMOGLYPH_MAP:
            result.append(HOMOGLYPH_MAP[char])
            count += 1
        else:
            result.append(char)
    return ''.join(result), count


def is_short_url(url: str) -> bool:
    """Check if a URL is from a known URL shortener."""
    try:
        parsed = urllib.parse.urlparse(url)
        hostname = (parsed.hostname or "").lower()
        return hostname in SHORT_URL_DOMAINS
    except (Exception, ValueError):
        return False


async def expand_short_url(url: str) -> tuple[str, bool]:
    """Expand a shortened URL by following redirects."""
    if not is_short_url(url):
        return url, False
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=settings.SHORT_URL_TIMEOUT,
            verify=False,
        ) as client:
            response = await client.head(url)
            final_url = str(response.url)
            return final_url, final_url != url
    except Exception:
        # Timeout or error — return original
        return url, False


def canonicalize_url(url: str) -> str:
    """Canonicalize URL to a standard form."""
    if not url:
        return url
    
    # Ensure scheme
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        parsed = urllib.parse.urlparse(url)
        
        # Lowercase scheme and host
        scheme = parsed.scheme.lower()
        host = (parsed.hostname or "").lower()
        
        # Remove default ports
        port = parsed.port
        if (scheme == 'http' and port == 80) or (scheme == 'https' and port == 443):
            port = None
        
        # Normalize path  
        path = parsed.path or "/"
        path = re.sub(r'/+', '/', path)  # Remove duplicate slashes
        
        # Remove trailing slash (except root)
        if path != "/" and path.endswith("/"):
            path = path.rstrip("/")
        
        # Remove fragment
        # Keep query params (they matter for phishing)
        
        netloc = host
        if port:
            netloc = f"{host}:{port}"
        
        canonical = urllib.parse.urlunparse((
            scheme, netloc, path,
            parsed.params, parsed.query, ""
        ))
        return canonical
    except (Exception, ValueError):
        return url


def extract_html_content(html: str) -> tuple[str, str]:
    """Extract visible and hidden text from HTML."""
    if not html:
        return "", ""
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script and style elements
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    
    # Visible text
    visible_text = soup.get_text(separator=' ', strip=True)
    
    # Hidden elements (display:none, visibility:hidden, hidden attribute)
    hidden_parts = []
    for tag in soup.find_all(True):
        style = tag.get('style', '')
        if ('display:none' in style.replace(' ', '') or
            'display: none' in style or
            'visibility:hidden' in style.replace(' ', '') or
            'visibility: hidden' in style or
            tag.get('hidden') is not None or
            tag.get('type') == 'hidden'):
            hidden_parts.append(tag.get_text(separator=' ', strip=True))
    
    hidden_text = ' '.join(hidden_parts)
    
    return visible_text, hidden_text


def extract_link_mismatches(html: str) -> list[dict]:
    """Find mismatches between displayed link text and actual href."""
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    mismatches = []
    
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        display_text = a_tag.get_text(strip=True)
        
        # Check if display text looks like a URL
        if re.match(r'https?://', display_text) or 'www.' in display_text:
            # Compare domains
            try:
                href_parsed = urllib.parse.urlparse(href)
                display_parsed = urllib.parse.urlparse(
                    display_text if '://' in display_text else f"https://{display_text}"
                )
                if (href_parsed.hostname and display_parsed.hostname and
                    href_parsed.hostname.lower() != display_parsed.hostname.lower()):
                    mismatches.append({
                        'displayed': display_text,
                        'actual': href,
                        'displayed_domain': display_parsed.hostname,
                        'actual_domain': href_parsed.hostname,
                    })
            except (Exception, ValueError):
                pass
    
    return mismatches


def detect_login_forms(html: str) -> bool:
    """Detect if HTML contains login/credential forms."""
    if not html:
        return False
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Check for password fields
    password_inputs = soup.find_all('input', {'type': 'password'})
    if password_inputs:
        return True
    
    # Check for common login patterns
    login_patterns = ['login', 'signin', 'sign-in', 'log-in', 'password',
                      'credential', 'authenticate', 'verification']
    form_text = str(soup.find_all('form')).lower()
    
    return any(pattern in form_text for pattern in login_patterns)


async def normalize(artifact, skip_expansion: bool = False) -> NormalizedArtifact:
    """
    Layer 2: Normalize and de-obfuscate all inputs.
    
    If skip_expansion is True, it will bypass the network-bound short URL expansion
    to provide a fast preliminary result.
    """
    result = NormalizedArtifact()
    signals = {}
    
    # Process the primary URL
    url = artifact.raw_url or (artifact.extracted_urls[0] if artifact.extracted_urls else None)
    
    if url:
        result.original_url = url
        
        # Step 1: Decode URL encoding
        decoded = decode_url(url)
        signals['was_encoded'] = decoded != url
        
        # Step 2: Punycode normalization
        decoded, has_punycode = normalize_punycode(decoded)
        signals['has_punycode'] = has_punycode
        
        # Step 3: Homoglyph normalization
        decoded, homoglyph_count = normalize_homoglyphs(decoded)
        signals['homoglyph_count'] = homoglyph_count
        
        # Step 4: Short URL expansion (Conditional)
        if not skip_expansion:
            expanded, was_shortened = await expand_short_url(decoded)
            signals['was_shortened'] = was_shortened
            if was_shortened:
                decoded = expanded
        else:
            # Still flag it as likely shortened if it matches common patterns
            signals['was_shortened'] = is_short_url(decoded)
            signals['expansion_pending'] = True
        
        # Step 5: Canonicalize
        if '@' in decoded:
            signals['has_at_symbol'] = True
        result.normalized_url = canonicalize_url(decoded)
    
    # Process text content
    text = artifact.raw_text or ""
    if text:
        # Normalize homoglyphs in text
        clean_text, text_homoglyphs = normalize_homoglyphs(text)
        signals['text_homoglyph_count'] = text_homoglyphs
        result.clean_text = clean_text
    
    # Process HTML
    if artifact.raw_html:
        visible, hidden = extract_html_content(artifact.raw_html)
        result.visible_text = visible
        result.hidden_text = hidden
        signals['has_hidden_content'] = len(hidden) > 0
        
        # Link mismatches
        mismatches = extract_link_mismatches(artifact.raw_html)
        signals['link_mismatches'] = len(mismatches)
        signals['mismatch_details'] = mismatches
        
        # Login form detection
        signals['has_login_form'] = detect_login_forms(artifact.raw_html)
        
        # Use visible text as clean_text if no text was provided
        if not result.clean_text:
            result.clean_text = visible
    
    result.signals = signals
    return result
