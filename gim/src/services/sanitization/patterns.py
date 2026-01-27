"""Regex patterns for secret and PII detection."""

import re
from typing import Dict, Pattern

# Secret detection patterns
SECRET_PATTERNS: Dict[str, Pattern] = {
    # Cloud provider keys
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "aws_secret_key": re.compile(
        r"(?:aws[_-]?secret[_-]?(?:access[_-]?)?key|secret[_-]?key)"
        r"['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{40})",
        re.IGNORECASE,
    ),
    "gcp_api_key": re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    "azure_key": re.compile(
        r"(?:azure|storage)[_-]?(?:account)?[_-]?key['\"]?\s*[:=]\s*['\"]?"
        r"([A-Za-z0-9+/=]{88})",
        re.IGNORECASE,
    ),

    # AI/ML provider keys
    "openai_key": re.compile(r"sk-[A-Za-z0-9]{48,}"),
    "openai_key_short": re.compile(r"sk-[A-Za-z0-9]{3,47}"),  # Catch shorter sk- patterns too
    "anthropic_key": re.compile(r"sk-ant-[A-Za-z0-9\-]{90,}"),
    "google_ai_key": re.compile(r"AIzaSy[A-Za-z0-9_-]{33}"),
    "huggingface_token": re.compile(r"hf_[A-Za-z0-9]{34,}"),
    "replicate_token": re.compile(r"r8_[A-Za-z0-9]{36,}"),

    # Version control tokens
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),
    "github_token_short": re.compile(r"gh[pousr]_[A-Za-z0-9]{3,35}"),  # Catch shorter ghp_ patterns
    "github_oauth": re.compile(r"gho_[A-Za-z0-9]{36,}"),
    "gitlab_token": re.compile(r"glpat-[A-Za-z0-9\-]{20,}"),
    "bitbucket_token": re.compile(r"ATBB[A-Za-z0-9]{32,}"),

    # Communication platform tokens
    "slack_token": re.compile(r"xox[baprs]-[A-Za-z0-9\-]+"),
    "slack_webhook": re.compile(
        r"https://hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]+"
    ),
    "discord_token": re.compile(r"[MN][A-Za-z0-9]{23,}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27,}"),
    "discord_webhook": re.compile(
        r"https://discord(?:app)?\.com/api/webhooks/[0-9]+/[A-Za-z0-9_-]+"
    ),

    # Database connection strings (capture full URL including credentials)
    "postgres_url": re.compile(
        r"postgres(?:ql)?://[^\s\"']+",
        re.IGNORECASE,
    ),
    "mysql_url": re.compile(
        r"mysql://[^:]+:[^@]+@[^/]+/[^\s\"']+",
        re.IGNORECASE,
    ),
    "mongodb_url": re.compile(
        r"mongodb(?:\+srv)?://[^:]+:[^@]+@[^\s\"']+",
        re.IGNORECASE,
    ),
    "redis_url": re.compile(
        r"redis://[^:]*:[^@]+@[^\s\"']+",
        re.IGNORECASE,
    ),

    # Authentication tokens
    "jwt_token": re.compile(
        r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"
    ),
    "bearer_token": re.compile(
        r"[Bb]earer\s+[A-Za-z0-9_\-\.]+",
    ),

    # Private keys
    "private_key_rsa": re.compile(
        r"-----BEGIN RSA PRIVATE KEY-----[\s\S]+?-----END RSA PRIVATE KEY-----"
    ),
    "private_key_ec": re.compile(
        r"-----BEGIN EC PRIVATE KEY-----[\s\S]+?-----END EC PRIVATE KEY-----"
    ),
    "private_key_openssh": re.compile(
        r"-----BEGIN OPENSSH PRIVATE KEY-----[\s\S]+?-----END OPENSSH PRIVATE KEY-----"
    ),
    "private_key_generic": re.compile(
        r"-----BEGIN PRIVATE KEY-----[\s\S]+?-----END PRIVATE KEY-----"
    ),

    # Generic patterns
    "generic_api_key": re.compile(
        r"['\"]?api[_-]?key['\"]?\s*[:=]\s*['\"]([^'\"]{20,})['\"]",
        re.IGNORECASE,
    ),
    "generic_secret": re.compile(
        r"['\"]?(?:secret|password|passwd|pwd)['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]",
        re.IGNORECASE,
    ),
    "generic_token": re.compile(
        r"['\"]?(?:access[_-]?)?token['\"]?\s*[:=]\s*['\"]([^'\"]{20,})['\"]",
        re.IGNORECASE,
    ),
}

# PII detection patterns
PII_PATTERNS: Dict[str, Pattern] = {
    # Email addresses
    "email": re.compile(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    ),

    # File paths with usernames
    "unix_home_path": re.compile(
        r"/(?:Users|home)/([a-zA-Z0-9._-]+)",
    ),
    "windows_user_path": re.compile(
        r"C:\\Users\\([a-zA-Z0-9._-]+)",
        re.IGNORECASE,
    ),

    # IP addresses
    "ipv4_address": re.compile(
        r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
    ),
    "ipv6_address": re.compile(
        r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"
    ),

    # Internal URLs
    "internal_url": re.compile(
        r"https?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0|"
        r"[a-zA-Z0-9.-]+\.(?:local|internal|corp|lan))"
        r"(?::\d+)?(?:/[^\s]*)?",
        re.IGNORECASE,
    ),

    # Phone numbers (basic patterns)
    "phone_us": re.compile(
        r"\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b"
    ),

    # Credit card numbers (basic pattern)
    "credit_card": re.compile(
        r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|"
        r"3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b"
    ),

    # Social Security Number (US)
    "ssn": re.compile(
        r"\b[0-9]{3}[-\s]?[0-9]{2}[-\s]?[0-9]{4}\b"
    ),
}

# Placeholder replacements for PII
PII_REPLACEMENTS: Dict[str, str] = {
    "email": "user@example.com",
    "unix_home_path": "/path/to/project",
    "windows_user_path": "C:\\path\\to\\project",
    "ipv4_address": "0.0.0.0",
    "ipv6_address": "::1",
    "internal_url": "https://api.example.com",
    "phone_us": "000-000-0000",
    "credit_card": "0000-0000-0000-0000",
    "ssn": "000-00-0000",
}

# Code name patterns for MRE synthesis
CODE_NAME_PATTERNS: Dict[str, Pattern] = {
    # Class names (CamelCase with specific domain words - either containing or ending with these)
    "domain_class": re.compile(
        r"\b([A-Z][a-z]+(?:User|Customer|Order|Product|Payment|Invoice|"
        r"Account|Employee|Company|Project|Task|Service|Handler|Manager|"
        r"Controller|Processor|Client|Repository|Factory)[A-Za-z]*)\b"
    ),
    # Also catch classes starting with domain words
    "domain_class_prefix": re.compile(
        r"\b((?:User|Customer|Order|Product|Payment|Invoice|Account|"
        r"Employee|Company|Project|Task)[A-Z][A-Za-z]*)\b"
    ),
    # Function/method names with domain words
    "domain_function": re.compile(
        r"\b((?:get|set|create|update|delete|process|handle|validate|fetch|save|load)"
        r"_?(?:user|customer|order|product|payment|invoice|account|"
        r"employee|company|project|task|service|data|record|item)[_a-z]*)\b",
        re.IGNORECASE,
    ),
    # Variable names with domain words
    "domain_variable": re.compile(
        r"\b((?:user|customer|order|product|payment|invoice|account|"
        r"employee|company|project|task|service)_?[a-z_]*)\b",
        re.IGNORECASE,
    ),
}
