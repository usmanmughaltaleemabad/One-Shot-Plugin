"""
Backup Generator - Disaster recovery and backup automation

Generates:
- Kubernetes cluster backups (Velero)
- Database point-in-time recovery
- Backup schedules and policies
- Recovery procedures
- Backup validation
- Cross-region replication
"""

from typing import Dict, Any


class BackupGenerator:
    """Generate backup and disaster recovery configurations"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_velero_config(self, app_name: str = "app") -> str:
        """Generate Velero backup configuration for Kubernetes clusters"""
        return f"""
apiVersion: v1
kind: Namespace
metadata:
  name: velero
---
apiVersion: v1
kind: Secret
metadata:
  namespace: velero
  name: cloud-credentials
type: Opaque
stringData:
  cloud: |
    [default]
    aws_access_key_id = $AWS_ACCESS_KEY_ID
    aws_secret_access_key = $AWS_SECRET_ACCESS_KEY
---
apiVersion: velero.io/v1
kind: BackupStorageLocation
metadata:
  namespace: velero
  name: aws-s3
spec:
  provider: aws
  bucket: {app_name}-velero-backups
  config:
    region: us-east-1
    s3ForcePathStyle: "false"
    s3Url: https://s3.amazonaws.com
  accessMode: ReadWrite
  default: true
---
apiVersion: velero.io/v1
kind: VolumeSnapshotLocation
metadata:
  namespace: velero
  name: aws-ebs
spec:
  provider: aws
  config:
    region: us-east-1
    snapshotLocation: us-east-1a
---
apiVersion: velero.io/v1
kind: Schedule
metadata:
  namespace: velero
  name: {app_name}-daily-backup
spec:
  schedule: "0 2 * * *"
  template:
    metadata:
      labels:
        app: {app_name}
    spec:
      backupStorageLocation: aws-s3
      volumeSnapshotLocation: aws-ebs
      defaultVolumesToRestic: true
      includedNamespaces:
        - {app_name}
        - monitoring
        - security
      excludedNamespaces:
        - kube-system
        - kube-public
      includeClusterResources: true
      storageLocation: aws-s3
      ttl: 720h
      snapshotVolumes: true
      snapshotVolumesDefaultToFsBackup: false
---
apiVersion: velero.io/v1
kind: Schedule
metadata:
  namespace: velero
  name: {app_name}-hourly-backup
spec:
  schedule: "0 * * * *"
  template:
    metadata:
      labels:
        app: {app_name}
    spec:
      backupStorageLocation: aws-s3
      includedNamespaces:
        - {app_name}
      excludedResources:
        - events
        - events.events.k8s.io
      storageLocation: aws-s3
      ttl: 168h  # 7 days
      snapshotVolumes: false
"""

    def generate_backup_script(self, app_name: str = "app") -> str:
        """Generate backup automation script"""
        return f"""
#!/bin/bash
set -e

APP_NAME={app_name}
BACKUP_DIR="/backup/${{APP_NAME}}_$(date +%Y%m%d_%H%M%S)"
S3_BUCKET="${{APP_NAME}}-backups"
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"

echo "Starting backup at $(date)"

# PostgreSQL full backup
echo "Backing up PostgreSQL..."
pg_dump -h postgresql -U postgres -F c -b -v \
  -f "$BACKUP_DIR/postgres_full_$(date +%Y%m%d_%H%M%S).bak" \
  {app_name}

# PostgreSQL backup metrics
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
echo "PostgreSQL backup size: $BACKUP_SIZE"

# Upload to S3
echo "Uploading to S3..."
aws s3 cp "$BACKUP_DIR/" "s3://$S3_BUCKET/full/" --recursive

# Cleanup old backups (local)
echo "Cleaning up old local backups..."
find /backup -type d -name "*_*" -mtime +7 -exec rm -rf {{}} \;

# Cleanup old backups (S3)
echo "Cleaning up old S3 backups..."
CUTOFF_DATE=$(date -d "$RETENTION_DAYS days ago" +%Y-%m-%d)
aws s3api list-objects-v2 \
  --bucket "$S3_BUCKET" \
  --prefix "full/" \
  --query "Contents[?LastModified<'$CUTOFF_DATE'].Key" \
  --output text | xargs -I {{}} aws s3 rm s3://$S3_BUCKET/{{}}

# Verify backup
echo "Verifying backup integrity..."
if pg_restore -l "$BACKUP_DIR"/*.bak > /dev/null 2>&1; then
    echo "✓ Backup verification passed"
else
    echo "✗ Backup verification failed"
    exit 1
fi

# Send notification
WEBHOOK_URL="$SLACK_WEBHOOK_URL"
curl -X POST "$WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d "{{
    \"text\": \"✓ Backup successful for $APP_NAME\",
    \"attachments\": [{{
      \"color\": \"good\",
      \"fields\": [
        {{\"title\": \"Size\", \"value\": \"$BACKUP_SIZE\", \"short\": true}},
        {{\"title\": \"Timestamp\", \"value\": \"$(date)\", \"short\": true}}
      ]
    }}]
  }}"

echo "Backup completed at $(date)"
"""

    def generate_recovery_script(self, app_name: str = "app") -> str:
        """Generate recovery/restore script"""
        return f"""
#!/bin/bash
set -e

APP_NAME={app_name}
S3_BUCKET="${{APP_NAME}}-backups"
RESTORE_DATE="${{1:?Usage: $0 <YYYY-MM-DD> [<HH:MM:SS>]}}"
RESTORE_TIME="${{2:-00:00:00}}"

echo "Starting recovery for $RESTORE_DATE $RESTORE_TIME"

# List available backups
echo "Available backups:"
aws s3 ls s3://$S3_BUCKET/full/ \
  --recursive | grep "$RESTORE_DATE"

# Download backup
BACKUP_FILE="postgres_full_${{RESTORE_DATE}}T${{RESTORE_TIME}}.bak"
echo "Downloading $BACKUP_FILE from S3..."

if ! aws s3 cp "s3://$S3_BUCKET/full/$BACKUP_FILE" "./recovery.bak"; then
    echo "Backup not found for exact timestamp"
    echo "Available backups for $RESTORE_DATE:"
    aws s3 ls "s3://$S3_BUCKET/full/" | grep "$RESTORE_DATE" || true
    exit 1
fi

# Verify backup
echo "Verifying backup..."
if ! pg_restore -l ./recovery.bak > /dev/null; then
    echo "Backup is corrupted"
    exit 1
fi

# Create recovery database
echo "Creating recovery database..."
psql -h postgresql -U postgres \
  -c "CREATE DATABASE ${{APP_NAME}}_recovery;" || true

# Restore
echo "Restoring database (this may take a while)..."
pg_restore -h postgresql -U postgres \
  -d ${{APP_NAME}}_recovery \
  --clean --if-exists \
  ./recovery.bak

# Verify recovery
echo "Verifying recovery..."
RESTORED_ROWS=$(psql -h postgresql -U postgres \
  -d ${{APP_NAME}}_recovery \
  -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';")

if [ "$RESTORED_ROWS" -gt 0 ]; then
    echo "✓ Recovery successful ($RESTORED_ROWS tables)"
else
    echo "✗ Recovery appears empty"
    exit 1
fi

# Prepare for cutover
echo "Recovery database ready: ${{APP_NAME}}_recovery"
echo "To complete cutover:"
echo "  1. Verify recovered data"
echo "  2. Rename: ALTER DATABASE ${{APP_NAME}}_recovery RENAME TO ${{APP_NAME}}_backup;"
echo "  3. Rename: ALTER DATABASE ${{APP_NAME}} RENAME TO ${{APP_NAME}}_old;"
echo "  4. Rename: ALTER DATABASE ${{APP_NAME}}_backup RENAME TO ${{APP_NAME}};"
echo "  5. Restart application"
echo "  6. Run: DROP DATABASE ${{APP_NAME}}_old;"

# Cleanup
rm -f ./recovery.bak
echo "Recovery completed at $(date)"
"""

    def generate_backup_policy(self, app_name: str = "app") -> str:
        """Generate backup policy document"""
        return f"""
# Backup Policy for {app_name}

## Backup Strategy

### Full Backups
- **Schedule**: Daily at 2:00 AM UTC
- **Retention**: 30 days
- **Location**: S3 (standard storage)
- **Compression**: Enabled (pg_dump -F c)
- **Encryption**: AES-256 (S3 default)

### Incremental Backups
- **Schedule**: Hourly at :00 minutes
- **Retention**: 7 days
- **Location**: S3 (standard storage)
- **Type**: PostgreSQL WAL archiving
- **Enables**: Point-in-time recovery (PITR)

### Database Snapshots
- **Schedule**: Weekly on Sunday at 3:00 AM UTC
- **Retention**: 4 weeks
- **Location**: EBS snapshots (AWS)
- **Purpose**: Fast recovery without restore time

### Velero Cluster Backups
- **Schedule**: Daily at 1:00 AM UTC
- **Retention**: 30 days
- **Location**: S3 (cross-region replica)
- **Includes**: All namespaces except system
- **Volume backups**: Enabled (Restic)

## Recovery Objectives

| Metric | Target |
|--------|--------|
| RPO (Recovery Point Objective) | < 1 hour |
| RTO (Recovery Time Objective) | < 30 minutes |
| Backup window | < 1 hour |
| Backup verification | Daily automated test |
| Restore test | Monthly manual test |

## Backup Verification

### Automated Verification (daily)
```bash
pg_restore -l <backup_file>  # List backup contents
psql -c "SELECT count(*) FROM table"  # Verify row counts
```

### Manual Verification (monthly)
1. Restore to recovery database
2. Run application test suite
3. Compare checksums with production
4. Document results

## Disaster Scenarios

### Scenario 1: Single pod failure
- **Impact**: Brief service disruption (load balancer reroutes)
- **Recovery**: Kubernetes automatically restarts pod
- **Time**: < 30 seconds

### Scenario 2: Database corruption
- **Impact**: Read errors, possible data inconsistency
- **Recovery**: Restore from hourly backup (PITR)
- **Time**: 5-15 minutes depending on recovery point

### Scenario 3: Data center failure
- **Impact**: Complete unavailability
- **Recovery**: Fail over to backup region
- **Time**: 5-15 minutes (manual switchover)

### Scenario 4: Ransomware infection
- **Impact**: All data encrypted
- **Recovery**: Restore from encrypted backup
- **Time**: 30-60 minutes

## Backup Lifecycle

```
Day 1: Full backup + Hourly incremental
Day 2-7: Hourly incremental only
Day 8-30: Keep full backups
Day 31+: Delete (automatic)

Snapshots:
Week 1-4: Retain (weekly)
Week 5+: Delete (automatic)
```

## Change Management

- **Backup script updates**: Test on staging first
- **Retention policy changes**: Announce 30 days in advance
- **Recovery testing**: Schedule monthly
- **Disaster recovery drill**: Quarterly

## Monitoring & Alerts

- **Backup success**: CloudWatch metric + Slack notification
- **Backup failure**: PagerDuty alert
- **Backup size increase**: Alert if > 20% from last week
- **Backup age**: Alert if backup older than 25 hours
- **S3 storage cost**: Monthly review and optimization

## Compliance

- **Data residency**: All backups in us-east-1
- **Encryption**: AES-256 at rest, TLS in transit
- **Access control**: Vault-managed IAM credentials
- **Audit logging**: CloudTrail for all S3 access
- **Retention**: Minimum 30 days per compliance

## Emergency Contacts

- **Database Administrator**: dbadmin@company.com
- **DevOps Lead**: devops-lead@company.com
- **On-call**: PagerDuty (devops-oncall)

## Testing Schedule

| Month | Test | Owner |
|-------|------|-------|
| Monthly | Restore to staging | DBA |
| Quarterly | Full DR drill | DevOps + Eng |
| Annually | Security audit | Security Team |
"""

    def generate_backup_validation(self, app_name: str = "app") -> str:
        """Generate backup validation checks"""
        return f"""
apiVersion: batch/v1
kind: CronJob
metadata:
  name: {app_name}-backup-validation
  namespace: default
spec:
  schedule: "0 3 * * *"  # 3 AM daily
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: {app_name}-backup
          containers:
            - name: validation
              image: postgres:15
              env:
                - name: PGPASSWORD
                  valueFrom:
                    secretKeyRef:
                      name: postgresql-backup
                      key: password
                - name: S3_BUCKET
                  value: {app_name}-backups
              command:
                - /bin/bash
                - -c
                - |
                  set -e

                  echo "Backup Validation Report"
                  echo "========================"
                  echo "Time: $(date)"

                  # Check latest backup exists
                  LATEST_BACKUP=$(aws s3 ls s3://$S3_BUCKET/full/ | tail -1 | awk '{{print $NF}}')
                  echo "Latest backup: $LATEST_BACKUP"

                  # Check backup size
                  BACKUP_SIZE=$(aws s3api head-object \
                    --bucket $S3_BUCKET \
                    --key "full/$LATEST_BACKUP" \
                    --query 'ContentLength' --output text)
                  echo "Backup size: $((BACKUP_SIZE / 1024 / 1024)) MB"

                  # Check backup age
                  BACKUP_TIME=$(aws s3api head-object \
                    --bucket $S3_BUCKET \
                    --key "full/$LATEST_BACKUP" \
                    --query 'LastModified' --output text)
                  echo "Backup time: $BACKUP_TIME"

                  # Download and verify
                  echo "Downloading backup for verification..."
                  aws s3 cp "s3://$S3_BUCKET/full/$LATEST_BACKUP" ./verify.bak

                  # List backup contents
                  echo ""
                  echo "Backup contents:"
                  pg_restore -l ./verify.bak | head -20

                  # Verify integrity
                  echo ""
                  if pg_restore -l ./verify.bak > /dev/null 2>&1; then
                      echo "✓ Backup integrity: PASS"
                      EXIT_CODE=0
                  else
                      echo "✗ Backup integrity: FAIL"
                      EXIT_CODE=1
                  fi

                  # Cleanup
                  rm -f ./verify.bak

                  exit $EXIT_CODE
          restartPolicy: OnFailure
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {app_name}-backup
  namespace: default
"""


def generate_backup_configs(framework: str, language: str, app_name: str = "app") -> Dict[str, str]:
    """
    Generate backup and disaster recovery configurations.

    Args:
        framework: django, fastapi, spring
        language: python, javascript
        app_name: application name

    Returns: dict of {filename: code_content}
    """
    generator = BackupGenerator(framework, language)
    output = {}

    output["backup/velero-config.yaml"] = generator.generate_velero_config(app_name)
    output["backup/backup-script.sh"] = generator.generate_backup_script(app_name)
    output["backup/recovery-script.sh"] = generator.generate_recovery_script(app_name)
    output["backup/backup-policy.md"] = generator.generate_backup_policy(app_name)
    output["backup/backup-validation.yaml"] = generator.generate_backup_validation(app_name)

    return output
