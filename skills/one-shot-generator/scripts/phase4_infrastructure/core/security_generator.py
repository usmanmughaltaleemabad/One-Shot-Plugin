"""
Security Generator - Infrastructure security configurations

Generates:
- TLS certificate configurations
- Secret management (Vault, AWS Secrets Manager)
- Network policies
- Pod security policies
- RBAC and authorization
- Secrets encryption
- SSL/TLS certificates
"""

from typing import Dict, Any


class SecurityGenerator:
    """Generate security configurations"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_cert_manager_issuer(self, app_name: str = "app", domain: str = "example.com") -> str:
        """Generate cert-manager certificate issuer"""
        return f"""
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@{domain}
    privateKeySecretRef:
      name: letsencrypt-prod-key
    solvers:
      - http01:
          ingress:
            class: nginx
      - dns01:
          route53:
            region: us-east-1
            hostedZoneID: Z1234567890ABC
---
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: {app_name}-cert
  namespace: default
spec:
  secretName: {app_name}-tls-secret
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
    - {domain}
    - www.{domain}
    - api.{domain}
  duration: 2160h # 90 days
  renewBefore: 360h # 15 days
"""

    def generate_network_policies(self, app_name: str = "app") -> str:
        """Generate Kubernetes NetworkPolicies"""
        return f"""
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {app_name}-deny-all
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: {app_name}
  policyTypes:
    - Ingress
    - Egress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {app_name}-allow-ingress
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: {app_name}
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8000
    - from:
        - podSelector:
            matchLabels:
              app: {app_name}
      ports:
        - protocol: TCP
          port: 8000
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {app_name}-allow-egress
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: {app_name}
  policyTypes:
    - Egress
  egress:
    # DNS
    - to:
        - namespaceSelector: {{}}
      ports:
        - protocol: UDP
          port: 53
    # PostgreSQL
    - to:
        - namespaceSelector:
            matchLabels:
              name: default
          podSelector:
            matchLabels:
              app: postgres
      ports:
        - protocol: TCP
          port: 5432
    # Redis
    - to:
        - namespaceSelector:
            matchLabels:
              name: default
          podSelector:
            matchLabels:
              app: redis
      ports:
        - protocol: TCP
          port: 6379
    # HTTPS out to internet
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
            except:
              - 169.254.169.254/32  # Block metadata endpoint
      ports:
        - protocol: TCP
          port: 443
"""

    def generate_pod_security_policy(self, app_name: str = "app") -> str:
        """Generate Pod Security Policy"""
        return f"""
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: {app_name}-restricted
  annotations:
    seccomp.security.alpha.kubernetes.io/allowedProfileNames: 'runtime/default'
    apparmor.security.beta.kubernetes.io/allowedProfileNames: 'runtime/default'
    seccomp.security.alpha.kubernetes.io/defaultProfileName: 'runtime/default'
    apparmor.security.beta.kubernetes.io/defaultProfileName: 'runtime/default'
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  hostNetwork: false
  hostIPC: false
  hostPID: false
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'MustRunAs'
    seLinuxOptions:
      level: 's0:c123,c456'
  supplementalGroups:
    rule: 'MustRunAs'
    ranges:
      - min: 1000
        max: 65535
  fsGroup:
    rule: 'MustRunAs'
    ranges:
      - min: 1000
        max: 65535
  readOnlyRootFilesystem: true
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: {app_name}-psp-user
rules:
  - apiGroups: ['policy']
    resources: ['podsecuritypolicies']
    verbs: ['use']
    resourceNames:
      - {app_name}-restricted
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: {app_name}-psp-user
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: {app_name}-psp-user
subjects:
  - kind: ServiceAccount
    name: {app_name}
    namespace: default
"""

    def generate_secrets_vault_config(self, app_name: str = "app") -> str:
        """Generate HashiCorp Vault configuration"""
        return f"""
storage "s3" {{
  bucket = "{app_name}-vault-backend"
  region = "us-east-1"
  dynamodb_table = "{app_name}-vault-locks"
  encrypt = true
}}

ha_storage "dynamodb" {{
  ha_enabled = true
  table = "{app_name}-vault-ha"
  region = "us-east-1"
}}

listener "tcp" {{
  address       = "0.0.0.0:8200"
  tls_cert_file = "/vault/config/certs/tls.crt"
  tls_key_file  = "/vault/config/certs/tls.key"
}}

ui = true
disable_mlock = true
"""

    def generate_vault_policies(self, app_name: str = "app") -> str:
        """Generate Vault access policies"""
        return f"""
path "secret/data/{app_name}/*" {{
  capabilities = ["read", "list"]
}}

path "secret/metadata/{app_name}/*" {{
  capabilities = ["list", "read"]
}}

path "database/static-creds/{app_name}-*" {{
  capabilities = ["read"]
}}

path "pki_int/issue/{app_name}" {{
  capabilities = ["create", "update"]
}}

path "auth/token/renew-self" {{
  capabilities = ["update"]
}}

path "auth/token/lookup-self" {{
  capabilities = ["read"]
}}
"""

    def generate_external_secrets_operator(self, app_name: str = "app") -> str:
        """Generate External Secrets Operator configuration"""
        return f"""
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: default
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets-sa
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: {app_name}-secrets
  namespace: default
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: {app_name}-secrets
    creationPolicy: Owner
  data:
    - secretKey: database-url
      remoteRef:
        key: {app_name}/database-url
    - secretKey: api-key
      remoteRef:
        key: {app_name}/api-key
    - secretKey: jwt-secret
      remoteRef:
        key: {app_name}/jwt-secret
    - secretKey: redis-password
      remoteRef:
        key: {app_name}/redis-password
"""

    def generate_tls_certificate_secret(self, app_name: str = "app") -> str:
        """Generate TLS certificate secret"""
        return f"""
apiVersion: v1
kind: Secret
metadata:
  name: {app_name}-tls
  namespace: default
type: kubernetes.io/tls
stringData:
  tls.crt: |
    -----BEGIN CERTIFICATE-----
    MIIDXTCCAkWgAwIBAgIJAJC1/iNAZwqDMA0GCSqGSIb3DQEBBQUAMEUxCzAJBgNV
    BAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBX
    aWRnaXRzIFB0eSBMdGQwHhcNMjMwMTAxMDAwMDAwWhcNMjQwMTAxMDAwMDAwWjBF
    MQswCQYDVQQGEwJBVTETMBEGA1UECAwKU29tZS1TdGF0ZTEhMB8GA1UECgwYSW50
    ZXJuZXQgV2lkZ2l0cyBQdHkgTHRkMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIB
    ...
    -----END CERTIFICATE-----
  tls.key: |
    -----BEGIN PRIVATE KEY-----
    MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7...
    -----END PRIVATE KEY-----
"""

    def generate_kube_audit_policy(self, app_name: str = "app") -> str:
        """Generate Kubernetes audit policy"""
        return """
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  - level: None
    verbs: ["get", "watch", "list"]
    resources:
      - group: ""
        resources: ["events"]
  - level: None
    verbs: ["get"]
    resources:
      - group: ""
        resources: ["endpoints"]
  - level: Metadata
    verbs: ["delete", "deleteCollection"]
  - level: RequestResponse
    verbs: ["create", "update", "patch"]
    resources:
      - group: ""
        resources: ["secrets", "configmaps"]
  - level: RequestResponse
    verbs: ["create", "update", "patch"]
    resources:
      - group: "apps"
        resources: ["deployments", "statefulsets"]
  - level: Metadata
    resources:
      - group: ""
        resources: ["services"]
  - level: Metadata
    omitStages:
      - RequestReceived
"""

    def generate_rbac_policies(self, app_name: str = "app") -> str:
        """Generate RBAC policies for application"""
        return f"""
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {app_name}
  namespace: default
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: {app_name}
  namespace: default
rules:
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["secrets"]
    verbs: ["get"]
    resourceNames: ["{app_name}-secrets", "{app_name}-tls"]
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list"]
  - apiGroups: ["apps"]
    resources: ["deployments/status"]
    verbs: ["get"]
  - apiGroups: [""]
    resources: ["events"]
    verbs: ["create", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: {app_name}
  namespace: default
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: {app_name}
subjects:
  - kind: ServiceAccount
    name: {app_name}
    namespace: default
"""


def generate_security_configs(framework: str, language: str, app_name: str = "app", domain: str = "example.com") -> Dict[str, str]:
    """
    Generate security infrastructure configurations.

    Args:
        framework: django, fastapi, spring
        language: python, javascript
        app_name: application name
        domain: domain name

    Returns: dict of {filename: code_content}
    """
    generator = SecurityGenerator(framework, language)
    output = {}

    output["security/cert-manager-issuer.yaml"] = generator.generate_cert_manager_issuer(app_name, domain)
    output["security/network-policies.yaml"] = generator.generate_network_policies(app_name)
    output["security/pod-security-policy.yaml"] = generator.generate_pod_security_policy(app_name)
    output["security/vault-config.hcl"] = generator.generate_secrets_vault_config(app_name)
    output["security/vault-policies.hcl"] = generator.generate_vault_policies(app_name)
    output["security/external-secrets.yaml"] = generator.generate_external_secrets_operator(app_name)
    output["security/tls-secret.yaml"] = generator.generate_tls_certificate_secret(app_name)
    output["security/audit-policy.yaml"] = generator.generate_kube_audit_policy(app_name)
    output["security/rbac-policies.yaml"] = generator.generate_rbac_policies(app_name)

    return output
