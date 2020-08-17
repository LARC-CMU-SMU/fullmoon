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

general = dict(
    collect_lux_thread_sleep_time=5,  # seconds
    collect_dc_thread_sleep_time=5,  # seconds
    log_file_name="docker_mount/logs/record.log",
    log_level=log_levels["debug"],
    max_log_size=1024 ** 3,  # 1GB
    max_log_file_count=3,
    wait_time_for_db=20,
    mails_per_day=10,
)

DEVICES = {
    'a': {'url': 'http://192.168.1.11:8000/', 'dc_pins': [13, ]},
    'b': {'url': 'http://192.168.1.10:8000/', 'dc_pins': [13, ]},
    'c': {'url': 'http://192.168.1.14:8000/', 'dc_pins': [13, ]},
    'd': {'url': 'http://192.168.1.15:8000/', 'dc_pins': [13, ]},
}