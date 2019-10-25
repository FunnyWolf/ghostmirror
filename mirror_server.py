# -*- coding: utf-8 -*-
# @File  : server.py
# @Date  : 2019/8/28
# @Desc  :
# @license : Copyright(C), funnywolf 
# @Author: funnywolf
# @Contact : github.com/FunnyWolf 
import json
import os
import sys
import time

try:
    from socketserver import BaseRequestHandler
    from socketserver import ThreadingTCPServer
    import configparser as conp
except Exception as E:
    from SocketServer import BaseRequestHandler
    from SocketServer import ThreadingTCPServer
    import ConfigParser as conp
from threading import Thread
from bottle import request
from bottle import route
from bottle import run as bottle_run

from config import *

cache_data = {}

global READ_BUFF_SIZE, LOG_LEVEL, SERVER_LISTEN, LOCAL_LISTEN, SOCKET_TIMEOUT


class Servers(BaseRequestHandler):
    def handle(self):
        logger.warning('Got connection from {}'.format(self.client_address))
        self.request.settimeout(SOCKET_TIMEOUT)
        key = "{}:{}".format(self.client_address[0], self.client_address[1])
        cache_data[key] = {"conn": self.request}
        while True:
            time.sleep(3)  # 维持tcp连接


class WebThread(Thread):  # 继承父类threading.Thread
    def __init__(self, ):
        Thread.__init__(self)

    def run(self):
        logger.warning("Webserver start")
        bottle_run(host=SERVER_LISTEN.split(":")[0], port=int(SERVER_LISTEN.split(":")[1]), quiet=True)
        logger.warning("Webserver exit")

    @staticmethod
    @route('/check/', method='POST')
    def check():
        """自检函数"""
        logger.debug("cache_data : {}".format(len(cache_data)))
        # 返回现有连接
        key_list = []
        for key in cache_data:
            key_list.append(key)
        data = {
            "client_address_list": key_list,
            "LOG_LEVEL": LOG_LEVEL,
            "READ_BUFF_SIZE": READ_BUFF_SIZE,
            "SERVER_LISTEN": SERVER_LISTEN,
            "LOCAL_LISTEN": LOCAL_LISTEN,
            "SOCKET_TIMEOUT": SOCKET_TIMEOUT,
        }
        return b64encodeX(json.dumps(data).encode("utf-8"))

    @staticmethod
    @route('/conn/', method='POST')
    def conn():
        """返回所有连接"""
        logger.debug("cache_data : {}".format(len(cache_data)))
        # 清除已经关闭的连接
        die_client_address = json.loads(b64decodeX(request.forms.get("DATA")).decode("utf-8"))
        for client_address in die_client_address:
            one = cache_data.get(client_address)
            if one is not None:
                try:
                    conn = one.get("conn")
                    conn.close()
                    del cache_data[client_address]
                except Exception as E:
                    logger.error(E)
        # 返回现有连接
        key_list = []
        for key in cache_data:
            key_list.append(key)
        return b64encodeX(json.dumps(key_list).encode("utf-8"))

    @staticmethod
    @route('/sync/', method='POST')
    def sync():
        client_address = request.forms.get("Client_address")
        try:
            conn = cache_data.get(client_address).get("conn")
        except Exception as E:
            logger.exception(E)
            tcp_recv_data = INVALID_CONN
            return b64encodeX(tcp_recv_data)
        try:
            post_get_data = b64decodeX(request.forms.get("DATA"))
            logger.debug("CLIENT_ADDRESS:{} POST_GET_DATA:{}".format(client_address, post_get_data))
            if len(post_get_data) > 0:
                logger.info("CLIENT_ADDRESS:{} POST_GET_LEN:{}".format(client_address, len(post_get_data)))
        except Exception as E:
            logger.exception(E)
            logger.error(request.forms.get("DATA"))
            tcp_recv_data = WRONG_DATA
            return b64encodeX(tcp_recv_data)

        send_flag = False
        for i in range(20):
            # 发送数据
            try:
                conn.sendall(post_get_data)
                if len(post_get_data) > 0:
                    logger.info("CLIENT_ADDRESS:{} TCP_SEND_LEN:{}".format(client_address, len(post_get_data)))
                send_flag = True
                break
            except Exception as E:  # socket 已失效
                logger.debug("CLIENT_ADDRESS:{} Client send failed".format(client_address))

        if send_flag is not True:
            logger.warning("CLIENT_ADDRESS:{} Client send failed".format(client_address))
            tcp_recv_data = INVALID_CONN
            try:
                conn.close()
                cache_data.pop(client_address)
            except Exception as E:
                logger.exception(E)
            return b64encodeX(tcp_recv_data)

        tcp_recv_data = b""
        for i in range(5):
            # 读取数据
            try:
                tcp_recv_data = conn.recv(READ_BUFF_SIZE)
                logger.debug("CLIENT_ADDRESS:{} TCP_RECV_DATA:{}".format(client_address, tcp_recv_data))
                if len(tcp_recv_data) > 0:
                    logger.info("CLIENT_ADDRESS:{} TCP_RECV_LEN:{}".format(client_address, len(tcp_recv_data)))
                break
            except Exception as err:
                pass

        logger.debug("CLIENT_ADDRESS:{} POST_RETURN_DATA:{}".format(client_address, tcp_recv_data))
        if len(tcp_recv_data) > 0:
            logger.info("CLIENT_ADDRESS:{} POST_RETURN_LEN:{}".format(client_address, len(tcp_recv_data)))
        return b64encodeX(tcp_recv_data)


if __name__ == '__main__':

    if os.path.exists("config.ini") is not True:
        print("Please copy config.ini into same folder!")
        sys.exit(1)
    configini = conp.ConfigParser()
    configini.read("config.ini")
    # 设置日志级别
    try:
        LOG_LEVEL = configini.get("TOOL-CONFIG", "LOG_LEVEL")
    except Exception as E:
        LOG_LEVEL = "INFO"
    try:
        no_log_flag = configini.get("ADVANCED-CONFIG", "NO_LOG")
        if no_log_flag.lower() == "true":
            logger = get_logger(level=LOG_LEVEL, name="StreamLogger")
        else:
            logger = get_logger(level=LOG_LEVEL, name="FileLogger")
    except Exception as E:
        logger = get_logger(level=LOG_LEVEL, name="FileLogger")

    # READ_BUFF_SIZE
    try:
        READ_BUFF_SIZE = int(configini.get("TOOL-CONFIG", "READ_BUFF_SIZE"))
    except Exception as E:
        logger.exception(E)
        READ_BUFF_SIZE = 10240

    # socket_timeout
    try:
        SOCKET_TIMEOUT = float(configini.get("TOOL-CONFIG", "SOCKET_TIMEOUT"))
    except Exception as E:
        SOCKET_TIMEOUT = 0.1

    # 获取核心参数
    try:
        SERVER_LISTEN = configini.get("NET-CONFIG", "SERVER_LISTEN")
        LOCAL_LISTEN = configini.get("NET-CONFIG", "LOCAL_LISTEN")
    except Exception as E:
        logger.exception(E)
        sys.exit(1)

    logger.info(
        "\nLOG_LEVEL: {}\nREAD_BUFF_SIZE: {}\nSERVER_LISTEN: {}\nLOCAL_LISTEN: {}\n".format(
            LOG_LEVEL, READ_BUFF_SIZE, SERVER_LISTEN, LOCAL_LISTEN
        ))

    try:
        webthread = WebThread()
        webthread.start()
        server = ThreadingTCPServer((LOCAL_LISTEN.split(":")[0], int(LOCAL_LISTEN.split(":")[1])), Servers)
        logger.warning("Tcpserver start")
        server.serve_forever()
        logger.warning("Tcpserver exit")
    except Exception as E:
        logger.exception(E)
