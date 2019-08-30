# -*- coding: utf-8 -*-
# @File  : client.py
# @Date  : 2019/8/28
# @Desc  :
# @license : Copyright(C), funnywolf 
# @Author: funnywolf
# @Contact : github.com/FunnyWolf
import json
import os
import socket
import sys
import time
from socket import AF_INET, SOCK_STREAM

try:
    import configparser as conp
except Exception as E:
    import ConfigParser as conp
import requests

from config import *

global LOG_LEVEL, SLEEP_TIME, READ_BUFF_SIZE, WEBSHELL, REMOVE_SERVER, TARGET_LISTEN


class Client(object):
    def __init__(self):
        self.cache_data = {}
        self.die_client_address = []

    def check_server(self):
        payload = {
            "Remoteserver": REMOVE_SERVER,
            "Endpoint": "/check/",

        }
        for i in range(10):
            try:
                r = requests.post(WEBSHELL, data=payload, timeout=3)
                web_return_data = json.loads(b64decodeX(r.content).decode("utf-8"))
            except Exception as E:
                logger.warning("Try to connet to server, count {}".format(i))
                time.sleep(1)
                continue
            logger.info(" ------------Server Config------------")
            logger.info(
                "\nLOG_LEVEL: {}\nREAD_BUFF_SIZE: {}\nSERVER_LISTEN: {}\nLOCAL_LISTEN: {}\n".format(
                    web_return_data.get("LOG_LEVEL"), web_return_data.get("READ_BUFF_SIZE"),
                    web_return_data.get("SERVER_LISTEN"), web_return_data.get("LOCAL_LISTEN")
                ))

            logger.info("Connet to server success")
            return True

        logger.warning("Connet to server failed,please check server and webshell")
        return False

    def update_conns(self):
        payload = {
            "Remoteserver": REMOVE_SERVER,
            "Endpoint": "/conn/",
            "DATA": None
        }
        logger.debug("cache_data : {}".format(len(self.cache_data)))
        logger.debug("die_client_address : {}".format(len(self.die_client_address)))

        # 发送client已经die的连接
        try:
            payload["DATA"] = b64encodeX(json.dumps(self.die_client_address).encode("utf-8"))
            self.die_client_address = []
        except Exception as E:
            logger.exception(E)
            return

        try:
            r = requests.post(WEBSHELL, data=payload)
            web_return_data = json.loads(b64decodeX(r.content).decode("utf-8"))
        except Exception as E:
            logger.warning("Get server exist socket failed")
            web_return_data = None
            return

        # 删除不在server端存在的client端连接
        for client_address in list(self.cache_data.keys()):
            if client_address not in web_return_data:
                logger.warning("CLIENT_ADDRESS:{} Not in server socket list, remove".format(client_address))
                client = self.cache_data.get(client_address).get("conn")
                try:
                    client.close()
                    self.cache_data.pop(client_address)
                except Exception as E:
                    logger.exception(E)

        # 新建server端新增的连接
        for client_address in web_return_data:
            if self.cache_data.get(client_address) is None:
                # 新建对应的连接
                client = socket.socket(AF_INET, SOCK_STREAM)
                client.settimeout(0.1)
                client.connect((TARGET_LISTEN.split(":")[0], int(TARGET_LISTEN.split(":")[1])))
                logger.warning("CLIENT_ADDRESS:{} Create new tcp socket".format(client_address))
                self.cache_data[client_address] = {"conn": client, "post_send_cache": b""}

    def sync_data(self):
        payload = {
            "Remoteserver": REMOVE_SERVER,
            "Endpoint": "/sync/",
            "DATA": None,
            "Client_address": None
        }

        for client_address in list(self.cache_data.keys()):
            client = self.cache_data.get(client_address).get("conn")
            try:
                tcp_recv_data = client.recv(READ_BUFF_SIZE)
                logger.debug("CLIENT_ADDRESS:{} TCP_RECV_DATA:{}".format(client_address, tcp_recv_data))
                if len(tcp_recv_data) > 0:
                    logger.info("CLIENT_ADDRESS:{} TCP_RECV_LEN:{}".format(client_address, len(tcp_recv_data)))
            except Exception as err:
                tcp_recv_data = b""
                logger.debug("TCP_RECV_NONE")

            # 获取缓存数据+新读取的数据
            post_send_cache = self.cache_data.get(client_address).get("post_send_cache")
            post_send_cache = post_send_cache + tcp_recv_data

            # 填充数据
            payload["DATA"] = b64encodeX(post_send_cache)
            payload["Client_address"] = client_address

            try:
                r = requests.post(WEBSHELL, data=payload)
            except Exception as E:
                logger.warning("Post data to webshell failed")
                continue

            try:
                web_return_data = b64decodeX(r.content)
            except Exception as E:
                # webshell 脚本没有正确请求到服务器数据或脚本本身报错
                logger.warning("Webshell return error data")
                logger.warning(r.content)
                continue

            if web_return_data == WRONG_DATA:
                logger.error("CLIENT_ADDRESS:{} Wrong b64encode data".format(client_address))
                logger.error(b64encodeX(post_send_cache))
                continue
            elif web_return_data == INVALID_CONN:  # 无效的tcp连接
                logger.warning("CLIENT_ADDRESS:{} invalid conn".format(client_address))
                try:
                    client.close()
                    self.cache_data.pop(client_address)
                except Exception as E:
                    logger.exception(E)
                continue

            logger.debug("CLIENT_ADDRESS:{} TCP_SEND_DATA:{}".format(client_address, web_return_data))
            if len(web_return_data) > 0:
                logger.info("CLIENT_ADDRESS:{} TCP_SEND_DATA:{}".format(client_address, len(web_return_data)))
            try:
                client.send(web_return_data)
            except Exception as E:
                logger.warning("CLIENT_ADDRESS:{} Client socket closed".format(client_address))
                self.die_client_address.append(client_address)
                client.close()
            finally:
                self.cache_data[client_address]["post_send_cache"] = b""

    def run(self):
        while True:
            self.update_conns()
            self.sync_data()
            time.sleep(SLEEP_TIME)


if __name__ == '__main__':
    if os.path.exists("config.ini") is not True:
        print("Please copy config.ini into same folder!")
        sys.exit(1)
    configini = conp.ConfigParser()
    configini.read("config.ini")

    try:
        LOG_LEVEL = configini.get("TOOL-CONFIG", "LOG_LEVEL")
    except Exception as E:
        LOG_LEVEL = "INFO"
    logger = get_logger(level=LOG_LEVEL, name="StreamLogger")

    try:
        READ_BUFF_SIZE = int(configini.get("TOOL-CONFIG", "READ_BUFF_SIZE"))
    except Exception as E:
        logger.exception(E)
        READ_BUFF_SIZE = 10240

    try:
        SLEEP_TIME = float(configini.get("TOOL-CONFIG", "SLEEP_TIME"))
        if SLEEP_TIME <= 0:
            SLEEP_TIME = 0.01
    except Exception as E:
        logger.exception(E)
        SLEEP_TIME = 0.1

    READ_BUFF_SIZE = 10240

    # 获取核心参数
    try:
        WEBSHELL = configini.get("NET-CONFIG", "WEBSHELL")
        REMOVE_SERVER = "http://{}".format(configini.get("NET-CONFIG", "SERVER_LISTEN"))
        TARGET_LISTEN = configini.get("NET-CONFIG", "LOCAL_LISTEN")
    except Exception as E:
        logger.exception(E)
        sys.exit(1)

    try:
        REMOVE_SERVER = configini.get("ADVANCED-CONFIG", "REMOVE_SERVER")
        TARGET_LISTEN = configini.get("ADVANCED-CONFIG", "TARGET_LISTEN")
    except Exception as E:
        logger.debug(E)
    logger.info(" ------------Client Config------------")
    logger.info(
        "\nLOG_LEVEL: {}\nSLEEP_TIME:{}\nREAD_BUFF_SIZE: {}\nWEBSHELL: {}\nREMOVE_SERVER: {}\nTARGET_LISTEN: {}\n".format(
            LOG_LEVEL, SLEEP_TIME, READ_BUFF_SIZE, WEBSHELL, REMOVE_SERVER, TARGET_LISTEN
        ))

    client = Client()
    if client.check_server():
        client.run()
