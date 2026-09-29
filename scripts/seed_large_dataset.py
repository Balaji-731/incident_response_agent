import asyncio
import json
import datetime
import uuid
from backend.database.db import SessionLocal, init_db
from backend.database.models import IncidentRecord
from backend.models.incident import Incident
from backend.models.feedback import ResolutionConfirm
from backend.hindsight.memory_manager import memory_manager

DATASET = [
    # --- DOMAIN 1: GPU & MACHINE LEARNING INFERENCE ---
    {
        "service": "recommendation-engine",
        "severity": "high",
        "summary": "Inference requests timing out with CUDA memory exhaustion",
        "symptoms": ["CUDA out of memory", "P99 latency > 5000ms"],
        "logs": ["RuntimeError: CUDA out of memory. Tried to allocate 2.00 GiB on GPU 0"],
        "recent_changes": ["Batch size increased from 16 to 64 two hours ago"],
        "root_cause": "Batch size 64 exceeded GPU VRAM during concurrent inference",
        "resolution": "Reduced batch size from 64 to 16 in recommendation-engine config",
        "failed_attempts": ["Restarted GPU inference pods"]
    },
    {
        "service": "llm-inference-service",
        "severity": "critical",
        "summary": "vLLM worker process crash loop with segmentation fault",
        "symptoms": ["vLLM worker process crash", "SIGSEGV segmentation fault"],
        "logs": ["Process 42 killed by signal 11 (SIGSEGV) in libtorch_cuda.so"],
        "recent_changes": ["Upgraded PyTorch to 2.4.0-cuda12.1"],
        "root_cause": "FlashAttention CUDA kernel incompatibility with PyTorch 2.4.0",
        "resolution": "Rolled back PyTorch to 2.3.1 and pinned FlashAttention 2.5.8",
        "failed_attempts": ["Increased VRAM allocation", "Restarted vLLM container"]
    },
    {
        "service": "image-generation-worker",
        "severity": "high",
        "summary": "Stable Diffusion pipeline GPU memory fragmentation",
        "symptoms": ["GPU Memory Fragmentation", "Allocated VRAM 99%"],
        "logs": ["torch.cuda.OutOfMemoryError: PyTorch allocator cached 14.2GB VRAM"],
        "recent_changes": ["Enabled high-resolution generation endpoint"],
        "root_cause": "PyTorch allocator memory fragmentation under varying image dimensions",
        "resolution": "Set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True in container environment",
        "failed_attempts": ["Cleared model weights cache"]
    },

    # --- DOMAIN 2: DATABASES (POSTGRES, MYSQL, REDIS) ---
    {
        "service": "auth-service",
        "severity": "high",
        "summary": "Auth token verification failing with HTTP 500",
        "symptoms": ["Redis connection pool exhausted", "HTTP 500 Auth Error"],
        "logs": ["io.lettuce.core.RedisConnectionException: Connection pool exhausted"],
        "recent_changes": ["Token TTL reduced from 3600s to 60s"],
        "root_cause": "Redis lettuce connection pool exhausted due to short token TTL",
        "resolution": "Restarted Redis cluster nodes and increased max connections from 50 to 200",
        "failed_attempts": ["Cleared token cache"]
    },
    {
        "service": "order-processing-db",
        "severity": "critical",
        "summary": "PostgreSQL database CPU 100% with transaction deadlocks",
        "symptoms": ["Postgres CPU 100%", "Lock timeout on orders table"],
        "logs": ["ERROR: deadlock detected; Process 14210 waits for ShareLock on transaction 8812"],
        "recent_changes": ["Deployed parallel checkout worker feature"],
        "root_cause": "Unindexed row-level locking during concurrent inventory deduction",
        "resolution": "Added composite index on (order_id, product_id) and ordered lock acquisition alphabetically",
        "failed_attempts": ["Increased Postgres max_connections", "Restarted database read-replica"]
    },
    {
        "service": "user-profile-db",
        "severity": "high",
        "summary": "PostgreSQL read replica replication lag > 45 minutes",
        "symptoms": ["Replication Lag Spike", "Stale User Data Read"],
        "logs": ["FATAL: requested WAL segment 00000001000000A2 has already been removed"],
        "recent_changes": ["Bulk data migration script ran on primary DB"],
        "root_cause": "Primary PostgreSQL node purged WAL logs before read replica fetched them",
        "resolution": "Increased wal_keep_size to 64GB and re-synced replica via pg_basebackup",
        "failed_attempts": ["Restarted replication daemon"]
    },
    {
        "service": "session-cache",
        "severity": "medium",
        "summary": "Redis cluster evicted active user session keys",
        "symptoms": ["User Logout Spike", "Redis OOM eviction"],
        "logs": ["OOM command not allowed when used memory > 'maxmemory'"],
        "recent_changes": ["Added analytics payload to session object"],
        "root_cause": "Redis maxmemory policy was set to volatile-lru instead of allkeys-lru",
        "resolution": "Updated Redis maxmemory-policy to volatile-ttl and set session TTL explicitly",
        "failed_attempts": ["Flushed all session keys"]
    },

    # --- DOMAIN 3: MESSAGING & STREAMING (KAFKA, RABBITMQ) ---
    {
        "service": "payment-reconciliation-worker",
        "severity": "high",
        "summary": "Kafka consumer group offset lag exceeding 2,000,000 messages",
        "symptoms": ["Kafka Consumer Lag Spike", "Payment Notification Delay"],
        "logs": ["org.apache.kafka.clients.consumer.CommitFailedException: Commit cannot be completed"],
        "recent_changes": ["Added third-party webhook verification during message processing"],
        "root_cause": "Third-party HTTP API timeout caused message processing to exceed max.poll.interval.ms",
        "resolution": "Increased max.poll.interval.ms to 600,000ms and wrapped external HTTP call in async worker pool",
        "failed_attempts": ["Restarted Kafka consumer pods", "Increased partition count"]
    },
    {
        "service": "event-notification-bus",
        "severity": "critical",
        "summary": "Kafka broker rejected message payloads with RecordTooLargeException",
        "symptoms": ["Message Drop", "RecordTooLargeException"],
        "logs": ["org.apache.kafka.common.errors.RecordTooLargeException: Message size is 12582912 bytes"],
        "recent_changes": ["Attached raw PDF attachments to notification events"],
        "root_cause": "Message payload size (12MB) exceeded Kafka topic max.message.bytes (1MB)",
        "resolution": "Uploaded PDF attachments to S3 bucket and passed presigned URL in Kafka event payload",
        "failed_attempts": ["Increased container memory limit"]
    },

    # --- DOMAIN 4: KUBERNETES & CLOUD INFRASTRUCTURE ---
    {
        "service": "checkout-frontend",
        "severity": "critical",
        "summary": "Kubernetes pods stuck in CrashLoopBackOff due to OOMKilled",
        "symptoms": ["Pod CrashLoopBackOff", "OOMKilled exit code 137"],
        "logs": ["State: Waiting / Reason: CrashLoopBackOff / Last State: Terminated (Exit Code: 137)"],
        "recent_changes": ["Increased node SSR concurrency"],
        "root_cause": "Node.js heap limit exceeded pod memory request (512Mi)",
        "resolution": "Increased Kubernetes memory limits to 2Gi and set --max-old-space-size=1536 in Node.js startup script",
        "failed_attempts": ["Restarted Kubernetes deployment", "Scaled pod replicas from 3 to 10"]
    },
    {
        "service": "ingress-controller",
        "severity": "critical",
        "summary": "NGINX Ingress Controller returning 504 Gateway Timeout",
        "symptoms": ["HTTP 504 Gateway Timeout", "Upstream Connection Timeout"],
        "logs": ["[error] 142#142: *8912 upstream timed out (110: Connection timed out) while reading response header"],
        "recent_changes": ["Enabled gzip compression on NGINX"],
        "root_cause": "NGINX proxy-read-timeout (60s) was shorter than upstream backend processing time",
        "resolution": "Annotated Ingress resource with nginx.ingress.kubernetes.io/proxy-read-timeout: '300'",
        "failed_attempts": ["Restarted NGINX ingress pods"]
    },
    {
        "service": "internal-dns-resolver",
        "severity": "high",
        "summary": "CoreDNS pods dropping 40% of internal cluster DNS lookups",
        "symptoms": ["DNS Lookup Timeout", "i/o timeout on service name resolution"],
        "logs": ["[ERROR] plugin/errors: 2 auth-service.default.svc.cluster.local. A: read udp 10.244.0.5:53: i/o timeout"],
        "recent_changes": ["Cluster auto-scaled from 20 to 150 worker nodes"],
        "root_cause": "CoreDNS deployment replicas (2) insufficient for 150 worker nodes",
        "resolution": "Deployed coredns-autoscaler and enabled CoreDNS autoscale based on cluster node count",
        "failed_attempts": ["Restarted CoreDNS pods"]
    },

    # --- DOMAIN 5: AUTHENTICATION & SECURITY (VAULT, OAUTH, JWT) ---
    {
        "service": "api-gateway",
        "severity": "critical",
        "summary": "API Gateway rejecting all traffic with HTTP 401 Unauthorized",
        "symptoms": ["HTTP 401 Unauthorized", "HashiCorp Vault Token Expired"],
        "logs": ["Error fetching database credentials from Vault: Code 403: permission denied / token expired"],
        "recent_changes": ["Vault policy rotation ran overnight"],
        "root_cause": "Vault agent token renewed count exceeded max TTL without auto-auth re-authentication",
        "resolution": "Enabled Vault Agent sidecar with auto-auth AppRole method in Kubernetes pod spec",
        "failed_attempts": ["Restarted API Gateway pods"]
    },
    {
        "service": "user-auth-service",
        "severity": "high",
        "summary": "OAuth2 provider returning 429 Too Many Requests rate limit",
        "symptoms": ["HTTP 429 Rate Limited", "OAuth Token Throttled"],
        "logs": ["ClientError: 429 Client Error: Too Many Requests for url: https://oauth2.provider.com/token"],
        "recent_changes": ["Ran automated load testing script against staging environment"],
        "root_cause": "Staging load test used production OAuth2 client credentials",
        "resolution": "Isolated staging OAuth2 client ID and implemented token caching with local TTL",
        "failed_attempts": ["Rotated OAuth client secret"]
    },

    # --- DOMAIN 6: STORAGE & CLOUD SERVICES (AWS S3, BLOB STORAGE) ---
    {
        "service": "document-exporter-service",
        "severity": "high",
        "summary": "AWS S3 upload requests failing with 503 SlowDown rate limit",
        "symptoms": ["S3 503 SlowDown", "Document Upload Failure"],
        "logs": ["botocore.exceptions.ClientError: An error occurred (SlowDown) when calling the PutObject operation"],
        "recent_changes": ["Exported 500,000 PDF files to a single S3 prefix directory"],
        "root_cause": "S3 partition request limit (3,500 PUTs/sec) exceeded due to single folder prefix usage",
        "resolution": "Hashed object key prefixes (e.g. s3://bucket/a1b2/doc.pdf) to distribute partition load across S3",
        "failed_attempts": ["Increased Boto3 retry attempt counter"]
    },
    {
        "service": "media-processing-worker",
        "severity": "medium",
        "summary": "File descriptor exhaustion on media processing nodes",
        "symptoms": ["Too many open files", "Errno 24 EMFILE"],
        "logs": ["OSError: [Errno 24] Too many open files: '/tmp/thumbnail_4012.png'"],
        "recent_changes": ["Added video frame extractor feature"],
        "root_cause": "PIL Image object handles were not closed inside processing loop",
        "resolution": "Wrapped image processing logic in context manager (with Image.open(...) as img)",
        "failed_attempts": ["Increased system ulimit -n to 65536"]
    },

    # --- DOMAIN 7: NETWORKING & APIS ---
    {
        "service": "payment-gateway-connector",
        "severity": "critical",
        "summary": "TLS Handshake failure on external payment gateway requests",
        "symptoms": ["TLS Certificate Verification Error", "SSLError"],
        "logs": ["ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate has expired (_ssl.c:997)"],
        "recent_changes": ["Payment provider updated intermediate CA certificate"],
        "root_cause": "Container root CA store lacked newly updated intermediate CA certificate",
        "resolution": "Updated ca-certificates package in Dockerfile base image and rebuilt deployment",
        "failed_attempts": ["Set verify=False in requests call (Blocked by security audit)"]
    },
    {
        "service": "realtime-websocket-service",
        "severity": "high",
        "summary": "WebSocket server disconnecting 10,000 active clients every 5 minutes",
        "symptoms": ["WebSocket Connection Dropped", "1006 Abnormal Closure"],
        "logs": ["WebSocket disconnect code 1006: Connection reset by peer"],
        "recent_changes": ["Deployed AWS ALB in front of WebSocket cluster"],
        "root_cause": "AWS ALB idle timeout (60s) closed silent WebSocket connections",
        "resolution": "Implemented 30-second ping/pong heartbeat frame protocol between client and server",
        "failed_attempts": ["Restarted WebSocket server nodes"]
    },
    {
        "service": "inventory-grpc-service",
        "severity": "high",
        "summary": "gRPC calls timing out with DEADLINE_EXCEEDED code 4",
        "symptoms": ["gRPC DEADLINE_EXCEEDED", "RPC Timeout"],
        "logs": ["grpc._channel._InactiveRpcError: <_InactiveRpcError of RPC that terminated with StatusCode.DEADLINE_EXCEEDED>"],
        "recent_changes": ["Added inventory check to search endpoint"],
        "root_cause": "gRPC deadline was set to 500ms while inventory query required 800ms during peak load",
        "resolution": "Increased gRPC client deadline to 2000ms and added Redis caching for inventory reads",
        "failed_attempts": ["Increased gRPC thread pool size"]
    },
    {
        "service": "analytics-ingestion-api",
        "severity": "medium",
        "summary": "HTTP POST request body buffering memory leak",
        "symptoms": ["High RAM Usage", "GC Pause Time > 3s"],
        "logs": ["java.lang.OutOfMemoryError: Java heap space at org.apache.coyote.http11.Http11OutputBuffer"],
        "recent_changes": ["Allowed batch event payloads up to 50MB"],
        "root_cause": "Tomcat buffered 50MB payload in memory per thread instead of streaming request body",
        "resolution": "Replaced Tomcat blocking buffer with Spring WebFlux reactive streaming endpoint",
        "failed_attempts": ["Increased JVM heap size (-Xmx4g to -Xmx8g)"]
    }
]

async def seed_dataset():
    print(f"--- Seeding {len(DATASET)} Production Incidents into SQLite & Hindsight Cloud ---")
    db = SessionLocal()
    
    retained_count = 0
    for idx, item in enumerate(DATASET, 1):
        inc_id = f"INC-SEED-{idx:02d}"
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"

        # 1. Create SQLite Record
        db_rec = IncidentRecord(
            incident_id=inc_id,
            timestamp=timestamp,
            service=item["service"],
            environment="production",
            severity=item["severity"],
            summary=item["summary"],
            symptoms_json=json.dumps(item["symptoms"]),
            logs_json=json.dumps(item["logs"]),
            metrics_json=json.dumps({"source": "Seeded Dataset"}),
            recent_changes_json=json.dumps(item["recent_changes"]),
            status="resolved",
            root_cause=item["root_cause"],
            actual_resolution=item["resolution"],
            outcome="resolved"
        )
        db.merge(db_rec)
        db.commit()

        # 2. Formulate & Retain into Vectorize Hindsight Cloud Bank
        incident = Incident(**db_rec.to_dict())
        resolution = ResolutionConfirm(
            confirmed_root_cause=item["root_cause"],
            actual_resolution=item["resolution"],
            failed_attempts=item["failed_attempts"]
        )

        res = await memory_manager.retain_confirmed_resolution(incident, resolution)
        print(f"[{idx}/{len(DATASET)}] Retained {inc_id} ({item['service']}) -> Hindsight Status: {res.get('status', 'success')}")
        retained_count += 1
        
        # Brief pause between cloud vector API calls
        await asyncio.sleep(0.3)

    db.close()
    print(f"\n[SUCCESS] Seeded {retained_count} incidents into SQLite database & Hindsight Cloud bank!")

if __name__ == "__main__":
    init_db()
    asyncio.run(seed_dataset())