from .certificate_config import CertificateConfig


class Security:

    def __init__(self, security: dict):
        self.use_certificate = security['use_certificate']

        if self.use_certificate:
            self.certificate_config = CertificateConfig(security['certificate_config'])