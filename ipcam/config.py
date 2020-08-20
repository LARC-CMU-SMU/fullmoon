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
    handle_ip_cam_thread_sleep_time=5,  # seconds
    log_file_name="docker_mount/logs/ipcam.log",
    log_level=log_levels["debug"],
    max_log_size=1024 ** 3,  # 1GB
    max_log_file_count=3,
    wait_time_for_db=20,
    mails_per_day=10,
)

ip_cam_meta = dict(
    username='admin',
    password='password12',
    port=554
)

IP_CAM_DEVICES = {
    'a': {'ip': '192.168.1.110','patch_coordinates':{'a':((10,20),(20,30)), 'b':((40,50),(50,60))}},
    'b': {'ip': '192.168.1.109','patch_coordinates':{'a':((10,20),(20,30)), 'b':((40,50),(50,60))}},
}