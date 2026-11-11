#!/usr/bin/env bash
# -----------------------------------------------------------------------------------
# Creates Stackademy's course database, smarter_test_db, from smarter_test_db.sql.
#
# The script creates the database, its courses table and the 48 courses, and two
# read-only users, smarter_test_user and smarter_test_proxy_user, whose passwords are
# their names. It replaces the database if it already exists, so running it again
# resets the catalogue. Then it checks the result: the courses, and that each user may
# read the database and do nothing else.
#
# It connects as a user that may create databases and users, e.g. root, and reads that
# user's password from the MYSQL_PWD environment variable. Without MYSQL_PWD, it asks
# for the password, except in the smarter-mariadb container of Smarter's local
# development environment, whose root password is "smarter".
#
# Smarter runs it when it sets up a platform, before it applies this repository's
# manifests (see scripts.yaml), with no arguments, and with the platform's database
# server in SMARTER_DATABASE_HOST, SMARTER_DATABASE_PORT and
# SMARTER_DATABASE_ADMIN_USERNAME, and the administrator's password in MYSQL_PWD. Smarter
# logs each line that it writes: its report on stdout, and problems on stderr.
#
# Usage:
#   scripts/create-course-database.sh                         # into the smarter-mariadb Docker container
#   scripts/create-course-database.sh --container my-mariadb  # into another Docker container
#   scripts/create-course-database.sh --host db.example.com   # into a server, with a MariaDB or MySQL client
#
# Options:
#   --container NAME   the Docker container that runs MariaDB or MySQL (default: smarter-mariadb)
#   --host HOST        connect to this server instead of a container (default: SMARTER_DATABASE_HOST)
#   --port PORT        the server's port (default: SMARTER_DATABASE_PORT, or 3306)
#   --user USER        the user to connect as (default: SMARTER_DATABASE_ADMIN_USERNAME, or root)
#   -h, --help         show this help
# -----------------------------------------------------------------------------------
set -euo pipefail

SQL_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/smarter_test_db.sql"
DATABASE="smarter_test_db"
TEST_USERS=(smarter_test_user smarter_test_proxy_user)
EXPECTED_COURSES=48
DEFAULT_CONTAINER="smarter-mariadb"
DEFAULT_CONTAINER_PASSWORD="smarter"

container="$DEFAULT_CONTAINER"
host="${SMARTER_DATABASE_HOST:-}"
port="${SMARTER_DATABASE_PORT:-3306}"
user="${SMARTER_DATABASE_ADMIN_USERNAME:-root}"

usage() {
    sed -n '/^# Usage:/,/^# ---/p' "${BASH_SOURCE[0]}" | sed -e '$d' -e 's/^# \{0,1\}//'
}

# The report, on stdout. Each line stands on its own, because Smarter logs it as one line, after the
# script's name.
report() {
    printf '%s\n' "$*"
}

# Stop, with the reason on stderr, and exit status 1.
fail() {
    printf 'FAILED: %s\n' "$*" >&2
    exit 1
}

sha256() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | cut -c1-12
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$1" | cut -c1-12
    else
        echo "unknown"
    fi
}

while [ $# -gt 0 ]; do
    case "$1" in
        --container) container="${2:?--container needs a name}"; shift 2 ;;
        --host) host="${2:?--host needs a host name}"; shift 2 ;;
        --port) port="${2:?--port needs a number}"; shift 2 ;;
        --user) user="${2:?--user needs a user name}"; shift 2 ;;
        -h | --help) usage; exit 0 ;;
        *) usage >&2; fail "unknown option: $1" ;;
    esac
done

[ -r "$SQL_FILE" ] || fail "can't read $SQL_FILE"

# -----------------------------------------------------------------------------------
# Where to connect, and how.
# -----------------------------------------------------------------------------------
client_args=(--default-character-set=utf8mb4)
if [ -n "$host" ]; then
    if command -v mariadb >/dev/null 2>&1; then
        client=mariadb
        # With the password in MYSQL_PWD, the MariaDB client can't verify the server's
        # certificate, and says so on every connection. Say it once, here, instead.
        client_args+=(--skip-ssl-verify-server-cert)
    elif command -v mysql >/dev/null 2>&1; then
        client=mysql
    else
        fail "install a MariaDB or MySQL client (mariadb or mysql) to connect to $host"
    fi
    target="$host:$port"
else
    command -v docker >/dev/null 2>&1 || fail "Docker isn't installed. Use --host to connect to a server instead."
    docker inspect --format '{{.State.Running}}' "$container" 2>/dev/null | grep -q true ||
        fail "the Docker container $container isn't running"
    target="the $container container"
fi

if [ -z "${MYSQL_PWD:-}" ]; then
    if [ -z "$host" ] && [ "$container" = "$DEFAULT_CONTAINER" ]; then
        MYSQL_PWD="$DEFAULT_CONTAINER_PASSWORD"
    elif [ -t 0 ]; then
        read -r -s -p "Password for $user: " MYSQL_PWD
        echo
    else
        fail "set MYSQL_PWD to the password of $user"
    fi
fi
# The clients read the password from MYSQL_PWD, which keeps it off the command line.
export MYSQL_PWD

# Run SQL as $user, or as $as_user, with $MYSQL_PWD, e.g.
#   run_sql -e 'SELECT 1'
#   as_user=smarter_test_user MYSQL_PWD=smarter_test_user run_sql -e 'SELECT 1'
run_sql() {
    local login="${as_user:-$user}"
    if [ -n "$host" ]; then
        "$client" "${client_args[@]}" --user="$login" --host="$host" --port="$port" "$@"
    else
        # MariaDB's images have the mariadb client, and MySQL's have mysql.
        docker exec -i -e MYSQL_PWD "$container" sh -c \
            'if command -v mariadb >/dev/null 2>&1; then exec mariadb "$@"; else exec mysql "$@"; fi' \
            sh "${client_args[@]}" --user="$login" "$@"
    fi
}

query() {
    run_sql --batch --skip-column-names -e "$1"
}

# -----------------------------------------------------------------------------------
# Create the database.
# -----------------------------------------------------------------------------------
started=$SECONDS
report "creating Stackademy's course database, $DATABASE"

version="$(query 'SELECT VERSION();')" || fail "can't connect to $target as $user (see the error above)"
report "server: $target, version $version, as $user"
report "sql file: $(basename "$SQL_FILE"), sha256 $(sha256 "$SQL_FILE")"

run_sql <"$SQL_FILE" || fail "$(basename "$SQL_FILE") failed in $target (see the error above)"
report "loaded in $((SECONDS - started))s"

# -----------------------------------------------------------------------------------
# Check the result.
# -----------------------------------------------------------------------------------
courses="$(query "SELECT COUNT(*) FROM $DATABASE.courses;")" || fail "can't read $DATABASE.courses"
[ "$courses" = "$EXPECTED_COURSES" ] || fail "$DATABASE.courses has $courses courses, not $EXPECTED_COURSES"
report "checked: $DATABASE.courses has $courses courses"

for test_user in "${TEST_USERS[@]}"; do
    readable="$(as_user="$test_user" MYSQL_PWD="$test_user" query "SELECT COUNT(*) FROM $DATABASE.courses;")" ||
        fail "$test_user can't log in, or can't read $DATABASE.courses"
    [ "$readable" = "$courses" ] || fail "$test_user reads $readable courses, not $courses"
    # Exactly two grants: USAGE, i.e. may log in, and SELECT on the database. Anything else is too much.
    grants="$(query "SHOW GRANTS FOR '$test_user'@'%';")" || fail "can't read the grants of $test_user"
    others="$(printf '%s\n' "$grants" | grep -v -e '^GRANT USAGE ON \*\.\* TO ' -e "^GRANT SELECT ON \`$DATABASE\`\.\* TO " || true)"
    [ -z "$others" ] || fail "$test_user has more than read access: $others"
    report "checked: $test_user may read $DATABASE, and nothing else"
done

report "done in $((SECONDS - started))s"
