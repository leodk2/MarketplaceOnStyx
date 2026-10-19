#!/usr/bin/env bash
# =============================================================================
# compose.sh — run the Marketplace-on-Styx supporting services with udocker
# (zookeeper, Kafka, RustFS, Styx coordinator and worker only)
#
# Usage:
#   ./compose.sh setup   # pull images + create containers (once)
#   ./compose.sh up      # start everything in the background
#   ./compose.sh status  # show which services are running
#   ./compose.sh logs [service]   # tail logs (default: all)
#   ./compose.sh down    # stop everything
#   ./compose.sh clean   # down + delete containers and data
#
# How this differs from docker compose:
#   * udocker has no network namespaces: every container shares the job's
#     network. Service names (zookeeper, kafka1, ...) are mapped to 127.0.0.1
#     via a generated /etc/hosts that is mounted into every container, so the
#     environment variables from the compose file work unchanged.
#   * `worker` with `scale: 10` CANNOT be 10 containers here: the Styx worker
#     hard-codes its ports (5000/6000/7000 + thread index), so 10 copies on one
#     network would collide. Instead we run ONE worker container with
#     WORKER_THREADS=10. Each thread is a separate Styx worker process with its
#     own ports and registers with the coordinator individually.
#   * The marketplace application is run separately; no marketplace image is needed.
# =============================================================================
set -euo pipefail

# ----------------------------- configuration --------------------------------
cd "$(dirname "$(readlink -f "$0")")"
STACK_DIR="$PWD"
export UDOCKER_DIR="${UDOCKER_DIR:-$STACK_DIR/.udocker}"   # images + containers
RUN_DIR="$STACK_DIR/.run"            # pid files + generated hosts file
LOG_DIR="$STACK_DIR/logs"
DATA_DIR="$STACK_DIR/data"

N_WORKERS="${N_WORKERS:-10}"         # replaces `scale: 10`

# udocker execution mode. P1 (proot) is the most compatible default.
# F3 (fakechroot) avoids ptrace overhead and is noticeably faster, so for
# benchmark runs try: EXECMODE_STYX=F3 ./compose.sh setup
EXECMODE_INFRA="${EXECMODE_INFRA:-P1}"   # zookeeper, kafka, rustfs
EXECMODE_STYX="${EXECMODE_STYX:-P1}"     # coordinator, worker

IMG_ZOOKEEPER="confluentinc/cp-zookeeper:7.4.0"   # do not go above 7.4.0 (aiokafka)
IMG_KAFKA="confluentinc/cp-kafka:7.4.0"
IMG_RUSTFS="rustfs/rustfs:latest"
IMG_COORDINATOR="ghcr.io/delftdata/styx-coordinator:latest"
IMG_WORKER="ghcr.io/delftdata/styx-worker:latest"

SERVICES=(zookeeper kafka1 rustfs coordinator worker)

# ------------------------------- helpers ------------------------------------
log()  { printf '\033[1;34m[styx]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[styx]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[styx]\033[0m %s\n' "$*" >&2; exit 1; }

command -v udocker >/dev/null || die "udocker not found (pip install udocker && udocker install)"

container_exists() { udocker inspect "$1" >/dev/null 2>&1; }

# Wait until a TCP port on localhost accepts connections.
wait_port() {   # name port timeout_s
  local name=$1 port=$2 timeout=${3:-120} t=0
  log "waiting for $name on port $port ..."
  until (exec 3<>"/dev/tcp/127.0.0.1/$port") 2>/dev/null; do
    sleep 2; t=$((t + 2))
    if ! is_running "$name"; then die "$name exited during startup — see $LOG_DIR/$name.log"; fi
    if (( t >= timeout )); then die "$name not reachable on port $port after ${timeout}s — see $LOG_DIR/$name.log"; fi
  done
}

# Wait until a line matching a regex appears in a service's log.
wait_log() {    # name regex timeout_s
  local name=$1 re=$2 timeout=${3:-180} t=0
  log "waiting for $name to report ready ..."
  until grep -qE "$re" "$LOG_DIR/$name.log" 2>/dev/null; do
    sleep 2; t=$((t + 2))
    if ! is_running "$name"; then die "$name exited during startup — see $LOG_DIR/$name.log"; fi
    if (( t >= timeout )); then die "$name not ready after ${timeout}s — see $LOG_DIR/$name.log"; fi
  done
}

pidfile()    { echo "$RUN_DIR/$1.pid"; }
is_running() { local p; p=$(cat "$(pidfile "$1")" 2>/dev/null) && kill -0 -- "-$p" 2>/dev/null; }

# Start a service in its own process group (so `down` can kill proot children).
start_bg() {    # name cmd...
  local name=$1; shift
  if is_running "$name"; then log "$name already running"; return; fi
  log "starting $name"
  setsid "$@" >>"$LOG_DIR/$name.log" 2>&1 < /dev/null &
  echo $! > "$(pidfile "$name")"
}

# Every container gets the shared hosts file (mounted via -v ...:/etc/hosts) so compose service names resolve.
# The job's own hostname is included because Styx advertises
# gethostbyname(gethostname()) to the coordinator.
write_hosts() {
  mkdir -p "$RUN_DIR"
  cat > "$RUN_DIR/hosts" <<EOF
127.0.0.1   localhost $(hostname) zookeeper kafka1 rustfs coordinator worker
::1         localhost ip6-localhost ip6-loopback
EOF
}


check_ports() {
  local busy=()
  for p in 2181 9092 19092 9000 8888 8889; do
    (exec 3<>"/dev/tcp/127.0.0.1/$p") 2>/dev/null && busy+=("$p")
  done
  for ((i = 0; i < N_WORKERS; i++)); do
    for base in 5000 6000 7000; do
      (exec 3<>"/dev/tcp/127.0.0.1/$((base + i))") 2>/dev/null && busy+=("$((base + i))")
    done
  done
  (( ${#busy[@]} == 0 )) || die "ports already in use: ${busy[*]} (is the stack already up? try '$0 down')"
}

# ------------------------------- commands -----------------------------------
cmd_setup() {
  mkdir -p "$UDOCKER_DIR" "$RUN_DIR" "$LOG_DIR" "$DATA_DIR/rustfs"

  for img in "$IMG_ZOOKEEPER" "$IMG_KAFKA" "$IMG_RUSTFS" "$IMG_COORDINATOR" "$IMG_WORKER"; do
    log "pulling $img"
    udocker pull "$img"
  done

  create() {    # name image execmode
    if container_exists "$1"; then log "container $1 exists"; else
      log "creating container $1"
      udocker create --name="$1" "$2" >/dev/null
    fi
    udocker setup --execmode="$3" "$1" >/dev/null
  }
  create zookeeper   "$IMG_ZOOKEEPER"   "$EXECMODE_INFRA"
  create kafka1      "$IMG_KAFKA"       "$EXECMODE_INFRA"
  create rustfs      "$IMG_RUSTFS"      "$EXECMODE_INFRA"
  create coordinator "$IMG_COORDINATOR" "$EXECMODE_STYX"
  create worker      "$IMG_WORKER"      "$EXECMODE_STYX"

  log "setup done — now run: $0 up"
}

cmd_up() {
  for s in "${SERVICES[@]}"; do
    container_exists "$s" || die "container '$s' missing — run '$0 setup' first"
  done
  mkdir -p "$RUN_DIR" "$LOG_DIR" "$DATA_DIR/rustfs"
  check_ports
  write_hosts

  # --- zookeeper ------------------------------------------------------------
  start_bg zookeeper udocker run -v "$RUN_DIR/hosts:/etc/hosts" \
    -e ZOOKEEPER_CLIENT_PORT=2181 \
    -e ZOOKEEPER_TICK_TIME=2000 \
    zookeeper
  wait_port zookeeper 2181 120          # healthcheck: cub zk-ready

  # --- kafka1 (depends_on zookeeper: healthy) -------------------------------
  start_bg kafka1 udocker run -v "$RUN_DIR/hosts:/etc/hosts" \
    -e KAFKA_BROKER_ID=1 \
    -e KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181 \
    -e KAFKA_ADVERTISED_LISTENERS="INTERNAL://kafka1:19092,EXTERNAL://${DOCKER_HOST_IP:-127.0.0.1}:9092" \
    -e KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=INTERNAL:PLAINTEXT,EXTERNAL:PLAINTEXT \
    -e KAFKA_INTER_BROKER_LISTENER_NAME=INTERNAL \
    -e KAFKA_MESSAGE_MAX_BYTES=134217728 \
    -e KAFKA_REPLICA_FETCH_MAX_BYTES=134217728 \
    -e KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=1 \
    -e KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=1 \
    -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 \
    -e KAFKA_MIN_INSYNC_REPLICAS=1 \
    -e KAFKA_ZOOKEEPER_SESSION_TIMEOUT_MS=6000 \
    -e KAFKA_ZOOKEEPER_CONNECTION_TIMEOUT_MS=6000 \
    kafka1

  # --- rustfs (no dependencies; start while kafka boots) --------------------
  start_bg rustfs udocker run -v "$RUN_DIR/hosts:/etc/hosts" \
    -v "$DATA_DIR/rustfs:/data" \
    rustfs

  wait_port kafka1 19092 180            # healthcheck: cub kafka-ready
  wait_log  kafka1 'started \(kafka\.server\.KafkaServer\)' 180
  wait_port rustfs 9000 120

  # --- coordinator (depends_on kafka1: healthy, rustfs: started) ------------
  start_bg coordinator udocker run -v "$RUN_DIR/hosts:/etc/hosts" \
    -e KAFKA_URL=kafka1:19092 \
    -e KAFKA_REPLICATION_FACTOR=1 \
    -e HEARTBEAT_LIMIT=5000 \
    -e HEARTBEAT_CHECK_INTERVAL=500 \
    -e S3_ENDPOINT=http://rustfs:9000 \
    -e S3_ACCESS_KEY=rustfsadmin \
    -e S3_SECRET_KEY=rustfsadmin \
    coordinator
  wait_port coordinator 8888 120

  # --- worker x N_WORKERS (one container, N worker processes) ---------------
  start_bg worker udocker run -v "$RUN_DIR/hosts:/etc/hosts" \
    -e INGRESS_TYPE=KAFKA \
    -e KAFKA_URL=kafka1:19092 \
    -e DISCOVERY_HOST=coordinator \
    -e DISCOVERY_PORT=8888 \
    -e S3_ENDPOINT=http://rustfs:9000 \
    -e S3_ACCESS_KEY=rustfsadmin \
    -e S3_SECRET_KEY=rustfsadmin \
    -e WORKER_THREADS="$N_WORKERS" \
    worker
  wait_port worker 5000 120

  log "supporting services are up"
  log "logs: $LOG_DIR/  |  stop with: $0 down"
}

cmd_down() {
  # Reverse dependency order, like compose.
  for ((i = ${#SERVICES[@]} - 1; i >= 0; i--)); do
    local s=${SERVICES[i]} p
    p=$(cat "$(pidfile "$s")" 2>/dev/null) || continue
    if kill -0 -- "-$p" 2>/dev/null; then
      log "stopping $s"
      kill -TERM -- "-$p" 2>/dev/null || true
      for _ in {1..10}; do kill -0 -- "-$p" 2>/dev/null || break; sleep 1; done
      kill -KILL -- "-$p" 2>/dev/null || true
    fi
    rm -f "$(pidfile "$s")"
  done
  log "stack stopped"
}

cmd_status() {
  for s in "${SERVICES[@]}"; do
    if is_running "$s"; then printf '  %-12s \033[32mrunning\033[0m\n' "$s"
    else                     printf '  %-12s \033[31mstopped\033[0m\n' "$s"; fi
  done
}

cmd_logs() {
  if [[ $# -gt 0 ]]; then tail -n 100 -f "$LOG_DIR/$1.log"
  else tail -n 20 -f "$LOG_DIR"/*.log; fi
}

cmd_clean() {
  cmd_down
  for s in "${SERVICES[@]}"; do
    container_exists "$s" && { log "removing container $s"; udocker rm "$s" >/dev/null; }
  done
  rm -rf "$DATA_DIR" "$RUN_DIR" "$LOG_DIR"
  log "containers and data removed (images kept in $UDOCKER_DIR)"
}

# -------------------------------- main --------------------------------------
case "${1:-}" in
  setup)  cmd_setup ;;
  up)     cmd_up ;;
  down)   cmd_down ;;
  status) cmd_status ;;
  logs)   shift; cmd_logs "$@" ;;
  clean)  cmd_clean ;;
  *)      sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'; exit 1 ;;
esac
