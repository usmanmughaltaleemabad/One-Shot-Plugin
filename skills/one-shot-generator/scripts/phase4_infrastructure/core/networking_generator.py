"""
Networking Generator - Load balancing, service mesh, and traffic management

Generates:
- Ingress configurations (NGINX, AWS ALB, GCP LB)
- Service mesh configs (Istio, Linkerd)
- Traffic management (VirtualService, DestinationRule)
- DNS configurations
- Load balancing policies
- Circuit breaking and retries
"""

from typing import Dict, Any


class NetworkingGenerator:
    """Generate networking and load balancing configurations"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_nginx_ingress(self, app_name: str = "app", domain: str = "example.com") -> str:
        """Generate NGINX Ingress configuration"""
        return f"""
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {app_name}
  namespace: default
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "600"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/enable-cors: "true"
    nginx.ingress.kubernetes.io/cors-allow-origin: "*"
    nginx.ingress.kubernetes.io/cors-allow-methods: "GET, POST, PUT, DELETE, OPTIONS"
    nginx.ingress.kubernetes.io/cors-allow-headers: "DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Authorization"
    nginx.ingress.kubernetes.io/cors-max-age: "86400"
    nginx.ingress.kubernetes.io/enable-modsecurity: "true"
    nginx.ingress.kubernetes.io/enable-owasp-core-rules: "true"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - {domain}
        - www.{domain}
        - api.{domain}
      secretName: {app_name}-tls
  rules:
    - host: {domain}
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {app_name}
                port:
                  number: 8000
    - host: www.{domain}
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {app_name}
                port:
                  number: 8000
    - host: api.{domain}
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {app_name}
                port:
                  number: 8000
"""

    def generate_aws_alb_ingress(self, app_name: str = "app", domain: str = "example.com") -> str:
        """Generate AWS ALB Ingress configuration"""
        return f"""
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {app_name}-alb
  namespace: default
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:us-east-1:ACCOUNT_ID:certificate/CERTIFICATE_ID
    alb.ingress.kubernetes.io/listen-ports: '[{{"HTTP": 80}}, {{"HTTPS": 443}}]'
    alb.ingress.kubernetes.io/ssl-redirect: '443'
    alb.ingress.kubernetes.io/healthcheck-path: /health
    alb.ingress.kubernetes.io/healthcheck-interval-seconds: '30'
    alb.ingress.kubernetes.io/healthcheck-timeout-seconds: '10'
    alb.ingress.kubernetes.io/healthy-threshold-count: '2'
    alb.ingress.kubernetes.io/unhealthy-threshold-count: '3'
    alb.ingress.kubernetes.io/load-balancer-attributes: >
      idle_timeout.connection_termination.enabled=true,
      idle_timeout.tcp.idle_timeout.seconds=60
    alb.ingress.kubernetes.io/tags: Environment=production,Team=backend
spec:
  ingressClassName: alb
  rules:
    - host: {domain}
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: {app_name}
                port:
                  number: 8000
          - path: /health
            pathType: Exact
            backend:
              service:
                name: {app_name}
                port:
                  number: 8000
"""

    def generate_istio_virtualservice(self, app_name: str = "app") -> str:
        """Generate Istio VirtualService for traffic management"""
        return f"""
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: {app_name}
  namespace: default
spec:
  selector:
    istio: ingressgateway
  servers:
    - port:
        number: 80
        name: http
        protocol: HTTP
      hosts:
        - "*.example.com"
    - port:
        number: 443
        name: https
        protocol: HTTPS
      tls:
        mode: SIMPLE
        credentialName: {app_name}-tls
      hosts:
        - "*.example.com"
---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: {app_name}
  namespace: default
spec:
  hosts:
    - {app_name}
  http:
    - name: primary
      match:
        - uri:
            prefix: "/api"
      route:
        - destination:
            host: {app_name}
            port:
              number: 8000
            subset: v1
          weight: 90
        - destination:
            host: {app_name}
            port:
              number: 8000
            subset: v2
          weight: 10
      timeout: 30s
      retries:
        attempts: 3
        perTryTimeout: 10s
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: {app_name}
  namespace: default
spec:
  host: {app_name}
  trafficPolicy:
    connectionPool:
      http:
        http1MaxPendingRequests: 100
        maxRequestsPerConnection: 2
        h2UpgradePolicy: UPGRADE
    loadBalancer:
      simple: ROUND_ROBIN
    outlierDetection:
      consecutiveErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      minRequestVolume: 10
      splitExternalLocalOriginErrors: true
  subsets:
    - name: v1
      labels:
        version: v1
    - name: v2
      labels:
        version: v2
---
apiVersion: networking.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: {app_name}
  namespace: default
spec:
  mtls:
    mode: STRICT
---
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: {app_name}
  namespace: default
spec:
  rules:
    - from:
        - source:
            principals: ["cluster.local/ns/default/sa/{app_name}"]
      to:
        - operation:
            methods: ["GET", "POST", "PUT", "DELETE"]
            paths: ["/api/*"]
"""

    def generate_linkerd_config(self, app_name: str = "app") -> str:
        """Generate Linkerd service mesh configuration"""
        return f"""
apiVersion: v1
kind: Namespace
metadata:
  name: {app_name}
  annotations:
    linkerd.io/inject: enabled
---
apiVersion: policy.linkerd.io/v1beta1
kind: Server
metadata:
  name: {app_name}
  namespace: {app_name}
spec:
  podSelector:
    matchLabels:
      app: {app_name}
  port: 8000
  proxyProtocol: HTTP/1
---
apiVersion: policy.linkerd.io/v1beta1
kind: ServerAuthorization
metadata:
  name: {app_name}
  namespace: {app_name}
spec:
  server:
    selector:
      matchLabels:
        app: {app_name}
  allowAnonymous: false
  authnPolicy: all-authenticated
---
apiVersion: policy.linkerd.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: {app_name}
  namespace: {app_name}
spec:
  targetRef:
    kind: Pod
    name: {app_name}
  requiredAuthenticationRef:
    kind: ServiceAccount
    name: {app_name}
"""

    def generate_service_loadbalancer(self, app_name: str = "app") -> str:
        """Generate Service with LoadBalancer type"""
        return f"""
apiVersion: v1
kind: Service
metadata:
  name: {app_name}-lb
  namespace: default
  labels:
    app: {app_name}
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
spec:
  type: LoadBalancer
  loadBalancerSourceRanges:
    - 0.0.0.0/0
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800
  externalTrafficPolicy: Local
  ports:
    - name: http
      port: 80
      targetPort: 8000
      protocol: TCP
    - name: https
      port: 443
      targetPort: 8443
      protocol: TCP
  selector:
    app: {app_name}
"""

    def generate_dns_config(self, app_name: str = "app", domain: str = "example.com") -> str:
        """Generate DNS records configuration"""
        return f"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: {app_name}-dns
  namespace: default
data:
  dns-records.txt: |
    # Main domain
    {domain} A 192.0.2.1
    {domain} AAAA 2001:db8::1

    # Subdomains
    api.{domain} CNAME {domain}
    www.{domain} CNAME {domain}

    # MX records for email
    {domain} MX 10 mail.example.com

    # TXT records
    {domain} TXT "v=spf1 include:_spf.google.com ~all"
    _dmarc.{domain} TXT "v=DMARC1; p=quarantine; rua=mailto:admin@{domain}"

---
apiVersion: external-dns.alpha.kubernetes.io/v1alpha1
kind: DNSEndpoint
metadata:
  name: {app_name}
  namespace: default
spec:
  endpoints:
    - dnsName: {domain}
      recordType: A
      targets:
        - 192.0.2.1
    - dnsName: www.{domain}
      recordType: A
      targets:
        - 192.0.2.1
    - dnsName: api.{domain}
      recordType: A
      targets:
        - 192.0.2.1
"""

    def generate_traffic_policies(self, app_name: str = "app") -> str:
        """Generate traffic management policies"""
        return f"""
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {app_name}-rate-limit
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: {app_name}
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8000
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: {app_name}-rate-limit-config
  namespace: default
data:
  rate-limit-config.yaml: |
    # Global rate limit: 1000 requests per minute
    global_limit: 1000/min

    # Per-user rate limit: 100 requests per minute
    user_limit: 100/min

    # Per-IP rate limit: 500 requests per minute
    ip_limit: 500/min

    # Burst allowance: 20% of limit
    burst_ratio: 0.2

    # Sliding window: 60 seconds
    window_size: 60s
"""


def generate_networking_configs(framework: str, language: str, app_name: str = "app", domain: str = "example.com") -> Dict[str, str]:
    """
    Generate networking and load balancing configurations.

    Args:
        framework: django, fastapi, spring
        language: python, javascript
        app_name: application name
        domain: domain name

    Returns: dict of {filename: code_content}
    """
    generator = NetworkingGenerator(framework, language)
    output = {}

    output["networking/nginx-ingress.yaml"] = generator.generate_nginx_ingress(app_name, domain)
    output["networking/aws-alb-ingress.yaml"] = generator.generate_aws_alb_ingress(app_name, domain)
    output["networking/istio-virtualservice.yaml"] = generator.generate_istio_virtualservice(app_name)
    output["networking/linkerd-config.yaml"] = generator.generate_linkerd_config(app_name)
    output["networking/service-loadbalancer.yaml"] = generator.generate_service_loadbalancer(app_name)
    output["networking/dns-config.yaml"] = generator.generate_dns_config(app_name, domain)
    output["networking/traffic-policies.yaml"] = generator.generate_traffic_policies(app_name)

    return output
