"""
Database Infrastructure Generator - Database provisioning, replication, and backup

Generates:
- PostgreSQL replication and failover
- Redis cluster configurations
- Backup strategies (automated, incremental, point-in-time)
- Database monitoring
- Connection pooling (PgBouncer, Pgpool)
- High availability configurations
"""

from typing import Dict, Any


class DatabaseInfrastructureGenerator:
    """Generate database infrastructure configurations"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_postgresql_ha(self, app_name: str = "app") -> str:
        """Generate PostgreSQL HA with Patroni"""
        return f"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: {app_name}-postgresql-config
  namespace: default
data:
  patroni.yml: |
    scope: {app_name}-postgresql
    namespace: default
    name: postgresql-0

    restapi:
      listen: 0.0.0.0:8008
      connect_address: postgresql-0.postgresql:8008

    etcd:
      hosts:
        - etcd:2379

    postgresql:
      data_dir: /var/lib/postgresql/data
      pgpass: /var/lib/postgresql/.pgpass
      parameters:
        max_connections: 200
        max_prepared_transactions: 200
        shared_buffers: 256MB
        effective_cache_size: 1GB
        work_mem: 4MB
        wal_level: replica
        max_wal_senders: 10
        max_replication_slots: 10
        hot_standby: 'on'
        hot_standby_feedback: 'on'

      initdb:
        - encoding: UTF8
        - locale: C
        - data-checksums

      pg_hba:
        - local: all
          user: postgres
          auth_method: trust
        - local: replication
          user: postgres
          auth_method: trust
        - host: all
          user: all
          address: 127.0.0.1/32
          auth_method: md5
        - host: all
          user: all
          address: ::1/128
          auth_method: md5
        - host: replication
          user: postgres
          address: 0.0.0.0/0
          auth_method: md5
        - host: all
          user: all
          address: 0.0.0.0/0
          auth_method: md5

    bootstrap:
      dcs:
        ttl: 30
        loop_wait: 10
        retry_timeout: 10
        maximum_lag_on_failover: 1048576
        postgresql:
          use_pg_rewind: true
      initdb:
        - username: postgres
          password: secretpassword
        - username: {app_name}
          password: {app_name}password
          options:
            - createrole
            - createdb
      pg_hba:
        - local: all
          user: postgres
          auth_method: trust
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgresql
  namespace: default
spec:
  serviceName: postgresql
  replicas: 3
  selector:
    matchLabels:
      app: postgresql
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      serviceAccountName: postgresql
      containers:
        - name: postgresql
          image: patroni:latest
          ports:
            - containerPort: 5432
              name: postgresql
            - containerPort: 8008
              name: patroni
          volumeMounts:
            - name: pgdata
              mountPath: /var/lib/postgresql
            - name: config
              mountPath: /etc/patroni
          resources:
            requests:
              cpu: 500m
              memory: 512Mi
            limits:
              cpu: 1000m
              memory: 1Gi
          livenessProbe:
            exec:
              command:
                - /bin/sh
                - -c
                - pg_isready -U postgres
            initialDelaySeconds: 30
            periodSeconds: 10
  volumeClaimTemplates:
    - metadata:
        name: pgdata
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 10Gi
"""

    def generate_redis_cluster(self, app_name: str = "app") -> str:
        """Generate Redis cluster configuration"""
        return f"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: {app_name}-redis-cluster-config
  namespace: default
data:
  redis-cluster.conf: |
    port 6379
    cluster-enabled yes
    cluster-config-file nodes.conf
    cluster-node-timeout 5000
    appendonly yes
    appendfsync everysec
    appendfilename "appendonly.aof"
    dbfilename "dump.rdb"
    save 900 1
    save 300 10
    save 60 10000
    maxmemory 512mb
    maxmemory-policy allkeys-lru
    timeout 0
    tcp-keepalive 60
    loglevel notice
    logfile ""
    databases 16
    slowlog-log-slower-than 10000
    slowlog-max-len 128
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis-cluster
  namespace: default
spec:
  serviceName: redis-cluster
  replicas: 6
  selector:
    matchLabels:
      app: redis-cluster
  template:
    metadata:
      labels:
        app: redis-cluster
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          command:
            - redis-server
            - /conf/redis-cluster.conf
          ports:
            - containerPort: 6379
              name: redis
          volumeMounts:
            - name: conf
              mountPath: /conf
            - name: data
              mountPath: /data
          resources:
            requests:
              cpu: 250m
              memory: 512Mi
            limits:
              cpu: 500m
              memory: 1Gi
          livenessProbe:
            exec:
              command:
                - redis-cli
                - ping
            initialDelaySeconds: 30
            periodSeconds: 10
      volumes:
        - name: conf
          configMap:
            name: {app_name}-redis-cluster-config
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 5Gi
"""

    def generate_backup_strategy(self, app_name: str = "app") -> str:
        """Generate backup and recovery strategy"""
        return f"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: {app_name}-backup-strategy
  namespace: default
data:
  backup-strategy.yaml: |
    # Daily full backup at 2 AM UTC
    full_backup:
      schedule: "0 2 * * *"
      retention: 30 days
      destination: s3://{app_name}-backups/full/

    # Hourly incremental backup
    incremental_backup:
      schedule: "0 * * * *"
      retention: 7 days
      destination: s3://{app_name}-backups/incremental/

    # WAL archiving for point-in-time recovery
    wal_archiving:
      enabled: true
      destination: s3://{app_name}-backups/wal/
      retention: 30 days

    # Database snapshots for fast recovery
    snapshots:
      schedule: "0 3 * * 0"  # Weekly on Sunday
      retention: 4 weeks
      destination: ebs-snapshots

---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: {app_name}-backup-full
  namespace: default
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: {app_name}-backup
          containers:
            - name: backup
              image: postgres:15
              env:
                - name: PGPASSWORD
                  valueFrom:
                    secretKeyRef:
                      name: postgresql-backup
                      key: password
              command:
                - /bin/sh
                - -c
                - |
                  pg_dump -h postgresql -U postgres -F c -b -v -f /backup/dump_$(date +%Y%m%d_%H%M%S).bak {app_name}
                  aws s3 cp /backup/ s3://{app_name}-backups/full/ --recursive
              volumeMounts:
                - name: backup
                  mountPath: /backup
          volumes:
            - name: backup
              emptyDir: {{}}
          restartPolicy: OnFailure

---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {app_name}-backup
  namespace: default
"""

    def generate_pgbouncer_config(self, app_name: str = "app") -> str:
        """Generate PgBouncer connection pooling configuration"""
        return f"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: {app_name}-pgbouncer-config
  namespace: default
data:
  pgbouncer.ini: |
    [databases]
    {app_name} = host=postgresql port=5432 user={app_name}

    [pgbouncer]
    pool_mode = transaction
    max_client_conn = 1000
    default_pool_size = 25
    reserve_pool_size = 5
    reserve_pool_timeout = 3
    max_db_connections = 100
    max_user_connections = 50
    min_pool_size = 10
    application_name_pull_interval = 0
    query_wait_timeout = 120
    client_idle_timeout = 600
    idle_in_transaction_session_timeout = 0
    listen_addr = 0.0.0.0
    listen_port = 6432
    unix_socket_dir = /tmp
    logfile = /var/log/pgbouncer/pgbouncer.log
    pidfile = /var/run/pgbouncer/pgbouncer.pid
    admin_users = postgres,pgbouncer
    stats_period = 60
    verbose = 1
    log_connections = 1
    log_disconnections = 1
    log_pooler_errors = 1

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pgbouncer
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: pgbouncer
  template:
    metadata:
      labels:
        app: pgbouncer
    spec:
      containers:
        - name: pgbouncer
          image: pgbouncer:1.18
          ports:
            - containerPort: 6432
          volumeMounts:
            - name: config
              mountPath: /etc/pgbouncer
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 512Mi
          livenessProbe:
            tcpSocket:
              port: 6432
            initialDelaySeconds: 10
            periodSeconds: 10
      volumes:
        - name: config
          configMap:
            name: {app_name}-pgbouncer-config
"""

    def generate_database_monitoring(self, app_name: str = "app") -> str:
        """Generate database monitoring rules"""
        return f"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: {app_name}-postgres-monitoring
  namespace: default
data:
  postgres-rules.yaml: |
    groups:
      - name: postgresql
        interval: 30s
        rules:
          - alert: PostgreSQLDown
            expr: pg_up{{job="{app_name}-postgres"}} == 0
            for: 5m
            labels:
              severity: critical
            annotations:
              summary: "PostgreSQL down on {{ $labels.instance }}"

          - alert: PostgreSQLSlowQueries
            expr: pg_slow_queries{{job="{app_name}-postgres"}} > 10
            for: 10m
            labels:
              severity: warning
            annotations:
              summary: "Slow queries detected on {{ $labels.instance }}"

          - alert: PostgreSQLConnectionsHigh
            expr: pg_stat_activity_count{{job="{app_name}-postgres"}} > 150
            for: 5m
            labels:
              severity: warning
            annotations:
              summary: "High PostgreSQL connections: {{ $value }}"

          - alert: PostgreSQLCacheHitRatio
            expr: pg_cache_hit_ratio{{job="{app_name}-postgres"}} < 0.99
            for: 15m
            labels:
              severity: warning
            annotations:
              summary: "Low cache hit ratio on {{ $labels.instance }}"

          - alert: PostgreSQLReplicationLag
            expr: pg_replication_lag_seconds{{job="{app_name}-postgres"}} > 10
            for: 5m
            labels:
              severity: warning
            annotations:
              summary: "Replication lag on {{ $labels.instance }}: {{ $value }}s"
"""


def generate_database_infrastructure_configs(framework: str, language: str, app_name: str = "app") -> Dict[str, str]:
    """
    Generate database infrastructure configurations.

    Args:
        framework: django, fastapi, spring
        language: python, javascript
        app_name: application name

    Returns: dict of {filename: code_content}
    """
    generator = DatabaseInfrastructureGenerator(framework, language)
    output = {}

    output["database/postgresql-ha.yaml"] = generator.generate_postgresql_ha(app_name)
    output["database/redis-cluster.yaml"] = generator.generate_redis_cluster(app_name)
    output["database/backup-strategy.yaml"] = generator.generate_backup_strategy(app_name)
    output["database/pgbouncer-config.yaml"] = generator.generate_pgbouncer_config(app_name)
    output["database/postgres-monitoring.yaml"] = generator.generate_database_monitoring(app_name)

    return output
