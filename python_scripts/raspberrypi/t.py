from datetime import datetime


def write_to_log(msg):
    with open("log.txt", "a") as f:
        f.write(msg + "\t" + get_date_and_time() + "\n")


def get_date_and_time():
    return datetime.now().strftime("%d.%m.%Y" + " -- " + "%H:%M:%S")


write_to_log("test")

try:
    a = 1/0
except Exception as e:
    write_to_log(str(e))
