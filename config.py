# config.py

class Config(object):
    NODE_URL = 'http://127.0.0.1:5001'
    #SECRET_KEY = '4Js-Ex%4t~a}IuTOPnMV$VOE4]y}R@&+V4P;+@N!H&bn.S&xd[6Ih;Y|]6Y'
    #FERNET_KEY = 'aqg0ahE_7tGYt8KauLRLNyeEhSAOm0nehgIlcQ-zbkg='
    #SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Common base config for all environments

class DevelopmentConfig(Config):
    NODE_URL = 'http://127.0.0.1:5001'
    SECRET_KEY = '4Js-Ex%4t~a}IuTOPnMV$VOE4]y}R@&+V4P;+@N!H&bn.S&xd[6Ih;Y|]6Y'
    FERNET_KEY = 'aqg0ahE_7tGYt8KauLRLNyeEhSAOm0nehgIlcQ-zbkg='
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///hgn.db'
    #Development-specific configurations

class ProductionConfig(Config):
    NODE_URL = 'http://127.0.0.1:5001'
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///hgn.db'
    #Production-specific configurations
