"""Config"""
import os

class Config:
    """Confiig for Secrets."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "default_secret")

class ProductionConfig(Config):
    """Config for Flask Production environment"""
    DEBUG = False

class DevelopmentConfig(Config):
    """Config for Flask Development environment"""
    DEBUG = True
