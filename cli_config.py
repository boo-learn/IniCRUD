import click
import re
import paramiko
from paramiko.ssh_exception import AuthenticationException
from commentedconfigparser import CommentedConfigParser
import settings
from collections.abc import MutableMapping
from pathlib import Path
from contextlib import contextmanager


def parse_address(address: str) -> list[str]:
    pattern = r"^(\w+)@(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+):(.+)$"
    return re.findall(pattern, address)[0]


def parse_params(params: str) -> list[str] | None:
    return params.split('.')


def build_full_path(cfg_dir, dir_name, file_name) -> Path:
    return Path(cfg_dir) / Path(dir_name) / Path(f"{file_name}.{settings.REMOTE_CONFIG_EXTENSION}")


@contextmanager
def connect_ssh(host, port, username, password) -> paramiko.SSHClient:
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh_client.connect(host, port=port, username=username, password=password)
        yield ssh_client
    except AuthenticationException as e:
        print(f"An error occurred: {e}")
        raise e
    finally:
        ssh_client.close()


def create_folder_if_not_exists_ssh(ssh_client, remote_folder_path: Path):
    try:
        ssh_client.open_sftp().mkdir(remote_folder_path.as_posix())
    except IOError:
        pass


def read_ini_ssh(host, port, username, password, remote_ini_file_path: Path):
    config = CommentedConfigParser(inline_comment_prefixes="#")
    with connect_ssh(host, port, username, password) as ssh_client:
        with ssh_client.open_sftp().file(remote_ini_file_path.as_posix(), 'r') as remote_file:
            config.read_file(remote_file)
        return config


def write_to_ini_ssh(host, port, username, password, remote_ini_file_path: Path, section, param_name, param_value):
    with connect_ssh(host, port, username, password) as ssh_client:
        try:
            config = read_ini_ssh(host, port, username, password, remote_ini_file_path)
        except FileNotFoundError:  # Create file is not exist
            create_folder_if_not_exists_ssh(ssh_client, remote_folder_path=remote_ini_file_path.parent)
            with ssh_client.open_sftp().file(remote_ini_file_path.as_posix(), 'w') as remote_file:
                remote_file.write('')
            config = read_ini_ssh(host, port, username, password, remote_ini_file_path)
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, param_name, param_value)

        with ssh_client.open_sftp().file(remote_ini_file_path.as_posix(), 'w') as remote_file:
            config.write(remote_file)


@click.group()
def cli():
    pass


@cli.command()
@click.option('--addr', type=str, help='<user>@<host>:<port>:<path-to-cfgdir>')
@click.argument('params', type=str, required=True)
def get(addr: str, params: str):
    """
    Get config param

    PARAMS: <dir>.<cfg_name>.<section_name>.<param_name>
    """
    try:
        dir_name, file_name, section_name, param_name = parse_params(params)
    except ValueError:
        print("incorrect parameter format")
        return

    try:
        user, host, port, cfg_dir = parse_address(addr)
    except ValueError:
        print("incorrect address format")
        return
    try:
        config_data = read_ini_ssh(
            host=host, port=port,
            username=user, password=settings.SSH_PASSWORD,
            remote_ini_file_path=build_full_path(cfg_dir, dir_name, file_name)
        )
    except FileNotFoundError as e:
        print(e)
        return

    try:
        section = config_data[section_name]
    except KeyError:
        print(f'Section "{section_name}" does not exist')
        return
    try:
        value = section[param_name]
    except KeyError:
        print(f'Param "{param_name}" does not exist')
        return

    print(value)


@cli.command()
@click.option('--addr', type=str, default="local", help='<user>@<host>:<port>:<path-to-cfgdir>')
@click.argument('params', type=str, required=True)
@click.argument("param_value", type=str, required=True)
def set(addr: str, params: str, param_value: str):
    """
    Set config param

    PARAMS: <dir>.<cfg_name>.<section_name>.<param_name>
    PARAM_VALUE: set parameter value
    """
    try:
        dir_name, file_name, section_name, param_name = parse_params(params)
    except ValueError:
        print("incorrect parameter format")
        return

    user, host, port, cfg_dir = parse_address(addr)
    try:
        write_to_ini_ssh(
            host=host, port=port,
            username=user, password=settings.SSH_PASSWORD,
            section=section_name,
            remote_ini_file_path=build_full_path(cfg_dir, dir_name, file_name),
            param_name=param_name, param_value=param_value
        )
    except Exception as e:
        print(f"An error occurred: {e}")
    else:
        print(f"Operation successful")


if __name__ == '__main__':
    cli()
