class CertificateConfig:

    def __init__(self, certificate_config: dict):
        self.ssl_cert_file = certificate_config['ssl_cert_file']
        self.ssl_ca_cert = certificate_config['ssl_ca_cert']
        self.ssl_key_file = certificate_config['ssl_key_file']
