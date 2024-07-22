import requests
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
api_key = config['API']['api_key']

HEADERS_DEFAULT = {
    "x-nxopen-api-key": api_key
}


def main():
    pass


def call_api(urlString, headers = HEADERS_DEFAULT):
    return requests.get(urlString, headers = headers)


if __name__ == '__main__':
    main()