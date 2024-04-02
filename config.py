# config.py

class Config(object):
    SECRET_KEY = '4Js-Ex%4t~a}IuTOPnMV$VOE4]y}R@&+V4P;+@N!H&bn.S&xd[6Ih;Y|]6Y'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Common base config for all environments

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///hgn.db'
    # Development-specific configurations

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///hgn.db'
    # Production-specific configurations
