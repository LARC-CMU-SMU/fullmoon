log_levels = dict(
    critical='CRITICAL',
    error='ERROR',
    warning='WARNING',
    info='INFO',
    debug='DEBUG'
)

postgres = dict(
    database="fullmoon",
    user="fullmoon",
    password="fullmoon",
    host="postgre",
    # host="10.4.12.95",
    port="5432",
)

mail = dict(
    sender="sender email",
    recipients=["recipient1 email","recipient2 email"],
    smtp_server="smtp.smu.edu.sg",
    port=25,
)

general = dict(
    sleep_time=5,
    log_file_name="docker_mount/logs/alerts.log",
    log_level=log_levels["debug"],
    max_log_size=1024 ** 3,  # 1GB
    max_log_file_count=3,
    wait_time_for_db=20,
    mails_per_day=10,
)

