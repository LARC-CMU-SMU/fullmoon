log_levels = dict(
    critical='CRITICAL',
    error='ERROR',
    warning='WARNING',
    info='INFO',
    debug='DEBUG',
)

postgres = dict(
    database="fullmoon",
    user="fullmoon",
    password="fullmoon",
    host="postgre",
    port="5432",
)

general = dict(
    log_file_name="docker_mount/logs/control.log",
    log_level=log_levels["debug"],
    max_log_size=1024 ** 3,  # 1GB
    max_log_file_count=3,
    wait_time_for_db=10,
    mails_per_day=10,
    handle_newly_occupied_thread_sleep_time=1,  # seconds
    calculate_optimized_lux_thread_sleep_time=60,  # seconds
    set_optimized_dc_in_device_thread_sleep_time=3,  # seconds
    wait_between_optimize_and_control=10,
    dc_freq=300,
)


DEVICES = {
    'a': {'url': 'http://192.168.1.11:8000/', 'dc_pin': 13},
    'b': {'url': 'http://192.168.1.10:8000/', 'dc_pin': 13},
    'c': {'url': 'http://192.168.1.14:8000/', 'dc_pin': 13},
    'd': {'url': 'http://192.168.1.15:8000/', 'dc_pin': 13},
    'e': {'url': 'http://192.168.1.17:8000/', 'dc_pin': 13},
    'f': {'url': 'http://192.168.1.19:8000/', 'dc_pin': 13},
}