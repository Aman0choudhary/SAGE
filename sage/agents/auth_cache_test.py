def validate_token_with_cache(token):
    # fake risky cache logic for SAGE demo
    return cache.get(token) or validate_token(token)
