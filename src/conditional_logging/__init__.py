import argparse
import datetime
import logging
import logging.config
import os
import pathlib
import subprocess
import sys


DEFAULT_NUM_FILES = 10          # the default # of log files to preserve if not otherwise specified
DEFAULT_LOG_SUFFIX = 'log'     # the default suffix for log file names

def main() -> None:
    init_logging()
    args, extra_args = init_args()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        log.debug("debug devel logging is working")

    result = None
    # spawn the subprocess
    try:
        result = subprocess.run(extra_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        log.debug(f"after subprocess.run: result { result }")
    except OSError as e:
        raise

    log_prefix = args.log_prefix

    if log_prefix is None:
        log_prefix = extra_args[0]

    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    log_suffix = DEFAULT_LOG_SUFFIX

    log_file_name = f"{ log_prefix }.{ timestamp }.{ log_suffix }"

    log_path = pathlib.Path('.') 
    if args.log_dir is not None:
        log_path = pathlib.Path(args.log_dir)
        if not log_path.exists():
            error_msg = f"specified log-dir path must already exist ({ log_path })"
            log.error(error_msg)
            print(error_msg, file=sys.stderr)
            return 1

        if not log_path.is_dir():
            error_msg = f"specified log-dir path is not a directory ({ log_path })"
            log.error(error_msg)
            print(error_msg, file=sys.stderr)
            return 1

        log_file_name = log_path.joinpath(log_file_name).resolve()

    log.debug(f"creating log file '{ log_file_name }'")

    # remove files that are over num_backups
    num_backups = args.num_backups
    log.debug(f"num_backups = { num_backups }")
    log_pattern = f"{ log_prefix }.*.{ log_suffix }"
    log.debug(f"log_pattern '{ log_pattern }'")
    existing_backups = sorted(log_path.glob(log_pattern))
    log.debug(f"len { len(existing_backups) } sorted_backups = { existing_backups }")

    if len(existing_backups) >= args.num_backups:
        backups_to_remove = existing_backups[0:len(existing_backups)-num_backups+1]
        for log_to_remove in backups_to_remove:
            log.debug(f"need to remove '{ log_to_remove }'")
            pathlib.Path(log_to_remove).unlink()
    else:
        log.debug(f"have { len(existing_backups) }, num_backups { num_backups }: no need to remove files")


    # now actually save the file
    with open(log_file_name, "w") as log_fd:
        print(f"command: { " ".join(result.args) }", file=log_fd)
        print(f"returncode: { result.returncode }", file=log_fd)
        print(f"", file=log_fd)
        print(f"---", file=log_fd)
        print(f"", file=log_fd)
        log_fd.write(result.stdout)



    if result != None:

        if result.returncode != 0:
            print(result.stdout)
        return result.returncode
    else:
        return 1



def init_logging() -> None:
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'level': 'DEBUG',
                'stream': 'ext://sys.stderr'
            },
        },
        'formatters': {
            'default': {
                'format': '%(asctime)s %(levelname)-5s %(name)-10s %(funcName)-.15s:%(lineno)d %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
        },
        'root': {
            'level': 'INFO',
            'handlers': [ 'console' ],
        },
    }

    logging.config.dictConfig(logging_config)

def init_args() -> Tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
            description="tool to only pass stdout if there was a program error",
            allow_abbrev=False)
    parser.add_argument("--debug", help="turn on debugging output", action="store_true")
    parser.add_argument("--num-backups", help="number of log files to save", type=int, default=DEFAULT_NUM_FILES, action="store")
    parser.add_argument("--log-dir", help="directory to save logs to", action="store")
    parser.add_argument("--log-prefix", help="prefix for log file names", action="store")

    # split our arguments into the part before '--' and everything after
    raw_args = sys.argv[1:]
    if "--" in raw_args:
        idx = raw_args.index("--")
        app_args = raw_args[:idx]
        passthrough_args = raw_args[idx + 1:]
    else:
        app_args = raw_args
        passthrough_args = []


    args = parser.parse_args(app_args)

    if len(passthrough_args) == 0:
        print("no argument or args passed", file=sys.stderr)
        sys.exit(1)

    return args, passthrough_args


log = logging.getLogger(__name__)
