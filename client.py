# client
from socket import *
import sys, time, os
from settings import *

ADDR = SERVER_ADDR

# FTP客户端
class FtpClient:
    def __init__(self):
        self.create_sockfd()
        self.connect_server()
    
    # 创建套接字
    def create_sockfd(self):
        self.sockfd = socket()

    # 连接服务器
    def connect_server(self):
        # 准备连接服务器
        try:
            self.sockfd.connect(ADDR)
        except Exception as e:
            # 无法连接服务器，直接退出
            self.sockfd.close()
            sys.exit('【服务器无法连接】' + str(e))

    # 启动服务
    def run(self, cmd=None):
        # 未传递命令，退出
        if cmd is None:
            return
        # 解析命令，此时的命令是用户输入的命令
        self.analyzing(cmd)
    
    # 关闭
    def end(self):
        # 关闭套接字
        self.sockfd.close()

    # 解析用户命令
    def analyzing(self, strinput):
        res = strinput.split("'")
        for i in range(len(res)):
            res[i] = res[i].strip()
        cmd = CMD_SPLIT.join(res[0].strip().split(' ')) + CMD_SPLIT
        rest = CMD_SPLIT.join(res[1:])
        cmd += rest
        # 转换成约定格式命令
        self.handle(cmd)

    # 处理请求
    def handle(self, command):
        # 分解命令
        cmd = command.split(CMD_SPLIT)
        # 第一个元素为命令类型
        cmd_type = cmd[0].upper()
        # 不同类型不同处理
        # 登录
        if cmd_type == LOGIN:
            self.do_login(command)
        # 注册
        elif cmd_type == REG:
            self.do_reg(command)
        # 获取文件列表
        elif cmd_type ==LIST:
            self.do_list(command)
        # 下载文件
        elif cmd_type == DOWN:
            self.do_down(command)
        elif cmd_type == UPLOAD:
            self.do_load(command)
        # 忽略
        elif cmd_type == IGNORE:
            self.do_ignore(cmd)
        # 其他
        else:
            self.do_ignore(cmd)
    
    # 处理登录请求
    def do_login(self, cmd):
        # 发送命令
        self.sockfd.send(cmd.encode())
        # 接收响应
        resp = self.sockfd.recv(MAX_TRANSFER_BLOCK).decode()
        resp = resp.split(CMD_SPLIT)
        if resp[0] == SUCCESS:
            print('登录成功！')
        else:
            print('登录失败！')
    
    # 注册请求
    def do_reg(self, cmd):
        # 发送命令
        self.sockfd.send(cmd.encode())
        # 接收响应
        resp = self.sockfd.recv(MAX_TRANSFER_BLOCK).decode()
        resp = resp.split(CMD_SPLIT)
        if resp[0] == SUCCESS:
            print('注册成功！')
        else:
            print('注册失败！')

    # 请求文件列表
    def do_list(self, cmd):
        # 发送命令
        self.sockfd.send(cmd.encode())
        # 接收响应
        resp = self.sockfd.recv(MAX_TRANSFER_BLOCK).decode()
        resp = resp.split(CMD_SPLIT)
        if resp[0] != SUCCESS:
            print('获取文件列表失败')
            return
        # 打印出列表
        for i in range(1, len(resp)):
            print(resp[i])
    
    # 下载文件
    def do_down(self, cmd):
        # 发送命令
        self.sockfd.send(cmd.encode())
        # 接收响应
        resp = self.sockfd.recv(MAX_TRANSFER_BLOCK).decode()
        resp = resp.split(CMD_SPLIT)
        if resp[0] != SUCCESS:
            print('服务器不允许下载该文件')
            return
        # 文件名
        filename = resp[1].split('\\')[-1]
        # 文件大小
        filesize = int(resp[2])
        # 百分比
        percent = 0
        # 开始接收
        bs = b''
        while True:
            try:
                data = self.sockfd.recv(MAX_TRANSFER_BLOCK)
                # 文件发送结束
                if data.decode() == FILE_END_TAG:
                    print('接收完毕[100%%]... 共计 %s KB.' % (round(filesize / 1024, 2)))
                    break
            except Exception as e:
                percent = round(len(bs) / filesize, 4) * 100
                print('已完成 %.2f%% ...[%s]' % (percent, str(time.ctime())))
            
            bs += data
        # 保存文件
        try:
            with open(DOWNLOAD + filename, 'wb') as f:
                f.write(bs)
        except Exception as e:
            print('文件保存出错了！', e)
        else:
            print('[%s]文件下载完成！' % filename)


    # 上传文件
    def do_load(self, cmd):
        # 发送命令
        self.sockfd.send(cmd.encode())
        # 接收响应
        resp = self.sockfd.recv(MAX_TRANSFER_BLOCK).decode()
        resp = resp.split(CMD_SPLIT)
        if resp[0] != SUCCESS:
            print('服务器不允许上传该文件')
            return
        
        filename = resp[1]
        # 读取文件
        try:
            f = open(DOWNLOAD + filename, 'rb')
        except Exception as e:
            print('文件打开失败...', e)
            self.sockfd.send(CMD_SPLIT.join([FAILED, filename, '0']).encode())
            return
        # 确定可以上传
        # 文件大小
        filesize = os.path.getsize(DOWNLOAD + filename)
        # 发送文件名称，文件大小
        self.sockfd.send(CMD_SPLIT.join([SUCCESS, filename, str(filesize)]).encode())
        # 文件大小为0则不再继续发送
        if filesize <= 0:
            print('文件大小为0，不予发送。')
            return
        # 已发送大小
        done = 0
        # 百分比
        percent = 0

        # 开始上传
        while True:
            time.sleep(SLEEP_TIME)
            data = f.read(MAX_TRANSFER_BLOCK)
            if not data:
                self.sockfd.send(FILE_END_TAG.encode())
                print('[%s]全部上传完毕！' % filename)
                break
            self.sockfd.send(data)
            done += len(data)
            percent = round(done / filesize, 4) * 100
            print('已发送 %.2f %%..[%s]'%(percent, str(time.ctime())))
        
        # 关闭文件
        f.close()

    # 忽略处理
    def do_ignore(self, cmd):
        print('命令未识别:', end='')
        print(cmd)

if __name__ == '__main__':
    c = FtpClient()
    cmd = None
    while True:
        cmd = input('>>>')
        if not cmd:
            break
        c.run(cmd)
    c.end()
