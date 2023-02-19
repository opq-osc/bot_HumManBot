import configparser
from random import randint

import jieba
from .crawler import crawl
from .deeplearning.HumManBot import HumManBot
from .tool import filter
from .py3Aiml_Chinese.Kernel import Kernel

jieba.setLogLevel(jieba.logging.INFO)  # 关闭分词日志


def random_index(rate):
    start = 0
    randnum = randint(1, sum(rate))
    for index, scope in enumerate(rate):
        start += scope
        if start >= randnum:
            return index


class ChatBot:
    """
        基于 GPT-2 和 WebQA 的智能对话模型
    """

    def __init__(self, config_file='botoy/plugins/bot_HumManBot/core/config.txt'):
        config = configparser.ConfigParser()
        config.read(config_file)
        self.load_file = config.get('resource', 'load_file')  # AIML内核指定的文件路径
        self.sensitive_file = config.get('resource', 'sensitive_file')  # 敏感词库路径
        self.vocab_file = config.get('resource', 'vocab_file')  # 词库路径
        self.gpt2_model_path = config.get('resource', 'gpt2_model_path')  # GPT2模型路径

        # 初始化分词器
        jieba.initialize()
        jieba.load_userdict(self.sensitive_file)  # 定义分词字典

        # 初始化过滤器
        self.gfw = filter.BSFilter()
        self.gfw.parse(self.sensitive_file)

        # 初始化知识库
        self.mybot = Kernel()
        self.mybot.bootstrap(learnFiles=self.load_file, commands='load aiml b')

        # 初始化学习库
        self.template = '<aiml version="1.0" encoding="UTF-8">\n{rule}\n</aiml>'
        self.category_template = '<category><pattern>{pattern}</pattern><template>{answer}</template></category>'

        # 初始化HumManBot
        self.humbot = HumManBot(model_path=self.gpt2_model_path, vocab_path=self.vocab_file)

    def response(self, message):
        # 限制字数
        if len(message) > 60:
            return self.mybot.respond('MAX')
        elif len(message) == 0:
            return self.mybot.respond('MIN')

        # 过滤敏感词
        message_list = list(jieba.cut(message))
        message_new = ""
        for i in message_list:
            if self.gfw.filter(i, "*").count("*") == len(i):
                message_new = message_new + self.gfw.filter(i, "*").decode()
            else:
                message_new = message_new + i
        if message_new.find("*") != -1:
            return self.mybot.respond('过滤')

        # 结束聊天
        if message == 'exit' or message == 'quit':
            return self.mybot.respond('再见')
        else:
            ########
            # AIML #
            ########
            result = self.mybot.respond(''.join(jieba.cut(message)))
            # 匹配模式
            # try:
            if result[0] != '#':
                if message.find("机器人") != -1 or message.find("bot") != -1 or message.find(
                "BOT") != -1 or message.find(
                "猪猪侠") != -1 or message.find("小猪仔") != -1 or message.find(
                "火车头") != -1:  # 此处填BOT名称，判断消息中含BOT名称，回复概率增加
                    if random_index([5, 95]) == 1:
                        return result
                    else:
                        return ''
                else:
                    if random_index([60, 40]) == 1:
                        return result
                    else:
                        return ''
            # 搜索模式
            elif result.find('#NONE#') != -1:
                #########
                # WebQA #
                #########
                ans = crawl.search(message)
                if ans != '':
                    return ans
                else:
                    ###############
                    # Deeplearing #
                    ###############
                    if message.find("机器人") != -1 or message.find("bot") != -1 or message.find(
                            "BOT") != -1 or message.find(
                        "猪猪侠") != -1 or message.find("小猪仔") != -1 or message.find(
                        "火车头") != -1:  # 此处填BOT名称，判断消息中含BOT名称，回复概率增加
                        if random_index([20, 80]) == 1:
                            ans = self.humbot.generate_response(message)
                            return ans
                        else:
                            return ''
                    else:
                        if random_index([95, 5]) == 1:
                            ans = self.humbot.generate_response(message)
                            return ans
                        else:
                            return ''
            # MAY BE BUG
            else:
                return self.mybot.respond('无答案')
